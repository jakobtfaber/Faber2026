# undermind-mcp — Passive Auto-Capture Extension Spec

**Goal.** Replace the manual DevTools capture (checklist Steps 2–5) with passive, automatic
recording. You browse `app.undermind.ai` normally; the companion extension records
`api.undermind.ai` request/response pairs, **sanitizes them inside the extension** (secrets never
leave the browser), and POSTs sanitized fixtures to the loopback receiver, which writes them to
`tests/fixtures/`. No DevTools, no HAR, no copy-paste, no manual sanitize.

**What stays manual (by design, do not automate):** logging in to Undermind. The extension records
only traffic you generate by using the site while logged in. No programmatic login, no headless
browser, no synthetic activity — consistent with `project-outline.md` §0/§5.

---

## 1. Architecture

Two new pieces added to the existing `undermind-companion/` + receiver:

```
 app.undermind.ai tab
 ┌─────────────────────────────────────────────┐
 │ MAIN world:  capture-inject.js               │  ← wraps window.fetch (+ XHR)
 │   tees each api.undermind.ai request/response │     BEFORE the SPA bundle loads
 │   → window.postMessage(sanitized-ish record)  │
 ├─────────────────────────────────────────────┤
 │ ISOLATED world: capture-relay.js             │  ← receives postMessage,
 │   chrome.runtime.sendMessage(record)          │     forwards to service worker
 └─────────────────────────────────────────────┘
                     │
             background.js (service worker)
               • REDACTS record (authoritative sanitizer, JS port of sanitize.py)
               • if capture mode ON: POST http://127.0.0.1:8787/capture
                     │
             http_receiver.py
               • re-runs the secret-scan GATE server-side (defense in depth)
               • writes tests/fixtures/curl/NN.sh + responses/NN.json + endpoints_observed.json
```

**Why fetch-wrapping, not `chrome.webRequest`:** Chrome MV3 `webRequest` **cannot read response
bodies** — a hard platform limit. Wrapping `window.fetch` in the page's MAIN world is the only
permission-light way to capture full request+response pairs. (`chrome.debugger` also works but shows
a persistent "extension is debugging this browser" banner and needs the `debugger` permission — use
it only as a fallback if the SPA ever switches off `fetch`; see §7.)

**Natural safety property:** JS-visible `fetch` **cannot see the `Cookie` header** — browsers add it
after `fetch()` and mark it a forbidden header. So `sessionid` (HttpOnly) is *structurally* invisible
to the capture path. The only auth material the wrapper can see is the `X-CSRFToken` request header
(the app sets it from the readable `app-csrftoken` cookie); that is redacted (§4).

---

## 2. Manifest changes (`manifest.json`)

```jsonc
{
  "manifest_version": 3,
  "name": "Undermind Companion (local)",
  "version": "0.2.0",
  "permissions": ["cookies", "storage", "alarms"],   // NO new permissions needed for fetch-wrap
  "host_permissions": [
    "https://app.undermind.ai/*",
    "https://api.undermind.ai/*"
  ],
  "background": { "service_worker": "background.js" },
  "action": { "default_popup": "popup.html" },
  "content_scripts": [
    {
      "matches": ["https://app.undermind.ai/*"],
      "js": ["capture-inject.js"],
      "run_at": "document_start",   // MUST beat the SPA bundle's fetch reference
      "world": "MAIN"               // Chrome 111+; runs in page context
    },
    {
      "matches": ["https://app.undermind.ai/*"],
      "js": ["capture-relay.js"],
      "run_at": "document_start",
      "world": "ISOLATED"           // default; can use chrome.runtime
    }
  ]
}
```

**Do not widen `host_permissions`.** `matches` stays `app.undermind.ai` only. No `<all_urls>`, ever.

---

## 3. `capture-inject.js` (MAIN world — the fetch/XHR tap)

Runs at `document_start` so it wraps `window.fetch` before the Vite bundle captures its own reference.
Tees the response stream so the app is unaffected. Emits a **minimally-shaped** record via
`postMessage`; the authoritative redaction happens in the service worker (§4), but this script also
drops the obvious secret header so it never even crosses `postMessage`.

```js
(() => {
  const API = "api.undermind.ai";
  const origFetch = window.fetch;
  if (!origFetch || origFetch.__um_wrapped) return;

  function post(record) {
    // Same-window signal; capture-relay.js (ISOLATED) listens and forwards.
    window.postMessage({ __um_capture: true, record }, window.location.origin);
  }

  function headerObj(h) {
    const out = {};
    if (!h) return out;
    // Headers or plain object
    const entries = h.entries ? h.entries() : Object.entries(h);
    for (const [k, v] of entries) {
      if (k.toLowerCase() === "x-csrftoken") { out[k] = "<REDACTED>"; continue; } // never emit CSRF
      out[k] = v;
    }
    return out;
  }

  window.fetch = async function (input, init) {
    const url = typeof input === "string" ? input : (input && input.url) || "";
    const method = (init && init.method) || (input && input.method) || "GET";
    const isApi = url.includes(API);

    let reqBody = "";
    if (isApi && init && typeof init.body === "string") reqBody = init.body;

    const resp = await origFetch.apply(this, arguments);
    if (!isApi) return resp;

    try {
      // Tee so the app still consumes its stream unmodified.
      const clone = resp.clone();
      const ct = clone.headers.get("content-type") || "";
      let respText = "";
      // Cap body capture; skip binary (PDFs) and giant streams.
      if (ct.includes("json") || ct.includes("text") || ct.includes("event-stream")) {
        respText = (await clone.text()).slice(0, 200000);
      }
      post({
        method, url,
        reqHeaders: headerObj(init && init.headers),
        reqBody,
        status: resp.status,
        respHeaders: headerObj(resp.headers),   // note: Set-Cookie NOT visible to JS — fine
        respContentType: ct,
        respBody: respText,
        ts: Date.now(),
      });
    } catch (_e) { /* never break the app on capture failure */ }
    return resp;
  };
  window.fetch.__um_wrapped = true;

  // Optional: wrap XMLHttpRequest too, in case any call path uses it. (Fetch is primary.)
  // Left as a follow-up; the SPA uses fetch per endpoints.md.
})();
```

Notes for the implementer:
- **Ordering is the fragile part.** If the bundle copies `fetch` before us, we miss calls. `document_start`
  + MAIN world runs before page scripts; verify against a real load. If it ever races, fall back to §7.
- Streaming (SSE chat): `resp.clone()` + `.text()` drains the clone, not the original, so the app's
  stream is intact. For very long streams the 200 KB cap applies.
- This script sees no `Cookie` header (forbidden) and redacts `X-CSRFToken` before it leaves the page.

---

## 4. `background.js` — authoritative redactor + relay

The service worker holds the **authoritative** sanitizer — a JS port of the tested `sanitize.py`
patterns. Treat `capture-inject.js`'s pre-drop as a courtesy, not the gate.

```js
// --- redaction (mirror of sanitize.py; keep in sync) ---
const SENSITIVE_KEY =
  "(sessionid|session|(?:app-)?csrftoken|csrf|authorization|auth|bearer|token|" +
  "access[_-]?token|refresh[_-]?token|id[_-]?token|api[_-]?key|apikey|key|secret|" +
  "client[_-]?secret|password|passwd|pwd|sig|signature|code|state|nonce|companion[_-]?token)";
const SECRET_PATTERNS = [
  /sessionid=[^;&\s"']+/gi,
  /(app-)?csrftoken=[A-Za-z0-9]{8,}/gi,
  /Bearer\s+[A-Za-z0-9._\-]{12,}/gi,
  new RegExp(SENSITIVE_KEY + "=[^;&\\s\"']{6,}", "gi"),        // key=value in url/cookie/form
  new RegExp(SENSITIVE_KEY + "\"\\s*:\\s*\"[^\"]{6,}\"", "gi"), // "key":"value" in JSON
  /\b[A-Za-z0-9_\-]{32,}\b/g,                                   // long opaque tokens
];
const SENSITIVE_KEY_RE = new RegExp("^" + SENSITIVE_KEY + "$", "i");
function redactStr(s) {
  if (typeof s !== "string") return s;
  for (const p of SECRET_PATTERNS) s = s.replace(p, "<REDACTED>");
  return s;
}
function keySensitive(k) {
  const norm = k.trim().toLowerCase().replace(/[_-]/g, "");
  return SENSITIVE_KEY_RE.test(norm) || new RegExp(SENSITIVE_KEY, "i").test(k);
}
function redactObj(o) {
  if (Array.isArray(o)) return o.map(redactObj);
  if (o && typeof o === "object") {
    const out = {};
    for (const [k, v] of Object.entries(o)) out[k] = keySensitive(k) ? "<REDACTED>" : redactObj(v);
    return out;
  }
  return redactStr(o);
}
function sanitizeRecord(r) {
  const hdr = (h) => Object.fromEntries(
    Object.entries(h || {}).map(([k, v]) => [k, keySensitive(k) ? "<REDACTED>" : redactStr(v)]));
  let respBody = r.respBody || "";
  try { respBody = JSON.stringify(redactObj(JSON.parse(respBody)), null, 2); }
  catch (_e) { respBody = redactStr(respBody).slice(0, 200000); }
  return {
    method: r.method, url: redactStr(r.url),
    path: redactStr(r.url).replace(/^https:\/\/api\.undermind\.ai/, ""),
    reqHeaders: hdr(r.reqHeaders), reqBody: redactStr(r.reqBody || ""),
    status: r.status, respContentType: r.respContentType, respBody,
    // for endpoints_observed.json:
    csrf_cookie_names: [],  // Set-Cookie not visible to fetch; receiver may fill from its own client
  };
}

// --- capture mode + relay ---
let CAPTURE_ON = false;
chrome.storage.local.get("captureOn", (d) => { CAPTURE_ON = !!d.captureOn; });
chrome.storage.onChanged.addListener((c) => { if (c.captureOn) CAPTURE_ON = !!c.captureOn.newValue; });

chrome.runtime.onMessage.addListener((msg) => {
  if (msg && msg.type === "um_capture_record" && CAPTURE_ON) {
    const token = /* read companionToken from chrome.storage.local as elsewhere */ null;
    const clean = sanitizeRecord(msg.record);
    chrome.storage.local.get("companionToken", ({ companionToken }) => {
      fetch("http://127.0.0.1:8787/capture", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Companion-Token": companionToken || "" },
        body: JSON.stringify(clean),
      }).catch(() => {/* receiver may be down; drop silently */});
    });
  }
});
```

`capture-relay.js` (ISOLATED world) is tiny — bridges `postMessage` → `runtime.sendMessage`:
```js
window.addEventListener("message", (e) => {
  if (e.source === window && e.data && e.data.__um_capture) {
    chrome.runtime.sendMessage({ type: "um_capture_record", record: e.data.record });
  }
});
```

---

## 5. `popup.html/js` — capture toggle

Add to the existing popup:
- A **"Record endpoints"** toggle → writes `captureOn` to `chrome.storage.local`.
- A live **captured-count** badge (increment on each successful `/capture` POST; store a counter).
- A one-line reminder: "Recording sanitized API traffic to the local MCP server. Turn OFF when done."

Default OFF. Capture is an explicit, visible mode — never silently always-on.

---

## 6. `http_receiver.py` — new `POST /capture` route (server-side gate)

Add a route that (a) requires the companion token, (b) **re-runs the secret-scan gate** on the
received record as defense-in-depth (the browser redactor is authoritative, but never trust a single
layer for secrets), and (c) writes fixtures.

```python
# reuse the SECRET_PATTERNS / gate from sanitize.py — factor them into undermind_mcp/_sanitize.py
from undermind_mcp._sanitize import scan_for_secrets   # returns list of leaks, [] if clean

_CAPTURE_DIR = _CONFIG_DIR / "captures"   # NOT inside the repo; user copies vetted files in

async def capture(request: Request) -> JSONResponse:
    if not _validate_companion_token(request, companion_token):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    rec = await request.json()
    blob = json.dumps(rec)
    leaks = scan_for_secrets(blob)
    if leaks:
        _log.warning("capture_rejected_secret_leak", n=len(leaks))   # do NOT log the leak itself
        return JSONResponse({"error": "secret detected, dropped"}, status_code=422)
    # write NN.sh (from method/path/reqHeaders/reqBody) + NN.json (respBody) + append endpoints_observed
    _write_fixture(_CAPTURE_DIR, rec)
    return JSONResponse({"status": "ok"})
```

Design points:
- **Write to `~/.config/undermind-mcp/captures/`, not directly into the repo.** The receiver must never
  have write access to `tests/fixtures/`; the user copies vetted captures in (checklist Step 5), or a
  separate `undermind-mcp import-captures` CLI does it with the pre-commit gate in force.
- The `/capture` route only functions while `serve()` is running AND the popup toggle is ON.
- CORS already allows `app.undermind.ai` + `chrome-extension://`; add `/capture` to allowed paths implicitly (it's same middleware). Keep methods `GET, POST, OPTIONS`.
- Factor `SECRET_PATTERNS` + gate out of `sanitize.py` into `undermind_mcp/_sanitize.py` so the CLI
  sanitizer, the standalone `sanitize.py`, and this route all share one tested implementation.

---

## 7. Fallback: `chrome.debugger` (only if fetch-wrap proves unreliable)

If the SPA ever grabs `fetch` before the content script, or moves to a transport the wrapper can't
see, use the `chrome.debugger` API: attach to the tab, `Network.enable`, capture
`Network.requestWillBeSent` + `Network.responseReceived`, call `Network.getResponseBody`. This DOES
read response bodies reliably. Costs: the `"debugger"` permission and a persistent browser banner
while attached. Same in-extension sanitizer (§4) applies before anything leaves. Prefer fetch-wrap;
keep this documented as the escape hatch.

---

## 8. Acceptance tests

1. Load extension, log in, toggle **Record ON**, browse: open projects, open a project, start+abandon
   a New Research Project, send one chat message. Confirm files appear in
   `~/.config/undermind-mcp/captures/` and the popup counter increments.
2. **Secret check:** `grep -rE 'sessionid=|(app-)?csrftoken=[A-Za-z0-9]{8,}|Bearer [A-Za-z0-9]{12,}'`
   over the captures dir returns **0 matches**. (The natural cookie-invisibility + two redaction
   layers should guarantee this.)
3. Confirm the app still works normally with capture ON (streams render, no broken requests) —
   proves the `tee`/`clone` didn't disturb the app.
4. Turn **Record OFF**; confirm no further `/capture` POSTs.
5. Reconcile `endpoints_observed.json` against the fix-list's open questions (#3 create flow, #5 CSRF
   cookie name) — the captures should answer both.

## 9. Keep the JS redactor in sync with the Python one
The regex set in §4 is a port of the tested `sanitize.py` patterns. When either changes, change both,
and port the four-case test battery (clean / URL-token / JSON-body-token / gate-fires) so the JS side
is covered too. Two redaction implementations that drift are a security hole.
