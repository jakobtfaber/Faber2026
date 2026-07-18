# Brief for Claude Code — Passive auto-capture (extension + receiver `/capture`)

> Paste into Claude Code at the `undermind-mcp` repo root. **Branch off
> `fix/config-constants-and-create-flow`** (the current stacked head), suggested name
> `feat/passive-endpoint-capture`. Do not merge; keep stacking for one combined review.

**Goal.** Replace the manual DevTools capture with a passive recorder: you browse
`app.undermind.ai` logged in; the companion extension records `api.undermind.ai` request/response
pairs, redacts them, and POSTs them to a loopback `/capture` route that re-redacts (authoritative)
and writes sanitized fixtures. Output is exactly what Part B (fixes #3/#5) needs:
`tests/fixtures/endpoints_observed.json` + `curl/*.sh` + `responses/*.json`.

**Non-negotiable security posture (read first).**
- **Redaction happens in BOTH places, and the receiver side is authoritative.** The page/extension
  redacts early (so secrets don't even cross `postMessage`), but the receiver **re-runs the full
  redactor and a secret-scan GATE on every payload** and drops (HTTP 422) anything that still trips
  it. Never trust the page. This is the single most important requirement.
- **The redactor is provided below, verbatim, in both JS and Python, WITH its test vectors. Use it
  exactly. Do not regenerate, "improve", or re-derive the regex** — it was tested against 24 vectors
  including two bugs that silently corrupt fixtures (UUID `project_id`/`job_id` and `author` fields
  being over-redacted). Port the test vectors too and pin them.
- **Capture defaults OFF**, is an explicit visible toggle, and its state persists in
  `chrome.storage.local` — consistent with the P0 posture (persistence opt-in, nothing silently on).
- **No new browser permissions**; `host_permissions`/`matches` stay `undermind.ai` only.
- The receiver writes fixtures to `~/.config/undermind-mcp/captures/`, **never** directly into the
  repo's `tests/fixtures/`. A human (or a separate `import-captures` step) copies vetted files in.

**Scope fence.** You may create/modify:
`undermind-companion/*` (manifest, background.js, popup.*, new capture-inject.js, capture-relay.js),
`src/undermind_mcp/http_receiver.py` (now IN scope — the `/capture` route lands here),
`src/undermind_mcp/_sanitize.py` (NEW — shared redactor/gate),
and tests under `tests/`. Do **not** touch `server.py`, `cli.py`, `client.py`, `models.py`,
`auth_store.py`, or anything related to fixes #3/#5 — those are Part B.

---

## 1. Capture surfaces — which is authoritative, and the message shape

Two content scripts on `https://app.undermind.ai/*`, both at `run_at: document_start`:

- **`capture-inject.js` — MAIN world (page context).** Wraps `window.fetch` before the SPA bundle
  captures its reference. It is the *tap*, not the sanitizer. It drops the obvious secret header
  (`X-CSRFToken`) as a courtesy, then emits one message per `api.undermind.ai` call.
- **`capture-relay.js` — ISOLATED world (content-script context).** The bridge. It cannot see the
  page's JS but shares the DOM; it listens for the tap's `window.postMessage` and forwards via
  `chrome.runtime.sendMessage` to the service worker. **`background.js` (service worker) is where
  authoritative redaction happens before anything leaves the browser.**

**Message shape crossing page→content (`window.postMessage`).** Fixed contract — implement exactly:
```
window.postMessage({ __um_capture: 1, record: {
  method:      string,     // "GET" | "POST" | ...
  url:         string,     // full request URL
  reqHeaders:  object,     // header name -> value; X-CSRFToken already "<REDACTED>" by the tap
  reqBody:     string,     // request body text, "" if none
  status:      number,     // HTTP status
  respHeaders: object,     // response header name -> value (Set-Cookie is NOT visible to fetch — fine)
  respContentType: string,
  respBody:    string,     // response body text, capped at 200000 chars; "" for binary (PDF)
  ts:          number      // Date.now()
}}, window.location.origin);
```
- The relay validates `e.source === window && e.data && e.data.__um_capture === 1` before forwarding,
  and re-wraps as `chrome.runtime.sendMessage({ type: "um_capture_record", record })`.
- **Natural safety property to rely on, not defeat:** JS `fetch` cannot read the `Cookie` request
  header (browser-forbidden), so `sessionid` (HttpOnly) is structurally invisible to this path. The
  only auth material the tap can see is `X-CSRFToken`, which it pre-drops and the receiver re-redacts.
- **Ordering caveat:** if the SPA grabs `fetch` before the tap installs, calls are missed. MAIN world
  + `document_start` runs first in practice; verify on a real load (acceptance test 1 — captured
  files appearing / counter incrementing is what reveals an ordering miss). If it ever
  races, the documented fallback is `chrome.debugger` (Network domain) — do NOT implement that now,
  just leave a `// FALLBACK:` comment pointing at it.

Wrap responses with `resp.clone()` before reading the body so the app's own stream is untouched.

---

## 2. `POST /capture` contract (in `http_receiver.py`)

```
POST http://127.0.0.1:8787/capture
  Headers: X-Companion-Token: <same token as /auth/refresh>   # REUSE it, do not mint a new one
           Content-Type: application/json
  Body:    the record object from §1 (already page-redacted)
  Behavior:
    1. Validate companion token (same _validate_companion_token as the other routes). 401 if bad.
    2. Re-run redact_obj + redact_str over the WHOLE record (authoritative).
    3. Run the secret-scan gate over the redacted blob. If it finds anything → log
       "capture_rejected_secret_leak" (count only, NEVER the leak) and return 422, write nothing.
    4. Otherwise write fixtures (see §3) into CAPTURE_DIR and return {"status":"ok","n":<counter>}.
  Responses: 200 {"status":"ok","n":N} | 401 unauthorized | 422 {"error":"secret detected, dropped"}
```
- Add `CAPTURE_DIR = CONFIG_DIR / "captures"` next to the other constants in `http_receiver.py`
  (reuse the public `CONFIG_DIR` from the last batch). Create it lazily on first write.
- CORS: the existing middleware already allows `app.undermind.ai` + `chrome-extension://` with
  `X-Companion-Token`; `/capture` inherits it. Keep methods `GET, POST, OPTIONS`.
- The route only functions while `serve()` runs AND the popup toggle is ON (the extension simply
  won't POST when off; the receiver doesn't need to know about the toggle).

---

## 3. Fixture output layout (what Part B consumes)

Under `~/.config/undermind-mcp/captures/`:
- `curl/NN.sh` — sanitized cURL reconstructed from method/url/reqHeaders(minus secret headers)/reqBody.
- `responses/NN.json` — pretty-printed redacted `respBody` (or redacted text if not JSON).
- `endpoints_observed.json` — appended one entry per capture:
  ```json
  {"n":1,"method":"GET","path":"/api/v2/projects/","status":200,
   "resp_content_type":"application/json","csrf_cookie_names":[]}
  ```
  `csrf_cookie_names` stays `[]` from the extension (Set-Cookie invisible to fetch). **The receiver
  fills it in from its OWN authed client's cookie jar if available** — this is what answers fix #5's
  "is it `csrftoken` or `app-csrftoken`" question. If the receiver has no live session, leave `[]`
  and note it; the sanitized cURLs still show the `X-CSRFToken` header name.
- `NN` is a zero-padded monotonic counter persisted across restarts (a `captures/.counter` file).
- Deduping is not required; capturing the same endpoint twice is fine (Part B picks representative
  samples). Cap total captures at, say, 500 to avoid unbounded growth.

The repo's `tests/fixtures/` is populated by a human copying vetted files in (or a follow-up
`undermind-mcp import-captures` CLI — out of scope here). The pre-commit secret gate from the earlier
capture checklist still guards `tests/fixtures/` at commit time.

---

## 4. Popup toggle

Extend `popup.html/js`: a **"Record endpoints"** switch writing `captureOn` (bool) to
`chrome.storage.local`; a captured-count badge (read a counter the background increments on each 200);
one line of copy: "Recording sanitized API traffic to the local MCP server. Turn OFF when done."
Default OFF. `background.js` reads `captureOn` and only POSTs to `/capture` when true; it re-reads on
`chrome.storage.onChanged`.

---

## 5. The redactor — VERBATIM, both languages (DO NOT MODIFY)

Put the Python copy in `src/undermind_mcp/_sanitize.py` (shared by `/capture` and any CLI). Put the
JS copy in `background.js`. **The `redact_obj`/`redactObj` + key-matching logic must stay
byte-for-byte equivalent in behavior across the two languages** — a drift there is a security hole,
and both pass the 24-vector redaction battery in §6. Note `scan_for_secrets` (the gate) is
**Python/receiver-only** — the JS side redacts but does not gate; the receiver is the authoritative
gate (§2). The gate is verified separately (see §6 gate check), not part of the 24-vector redaction
battery.

### 5a. Python (`_sanitize.py`)
```python
import re

SENSITIVE_KEY = (r"(sessionid|session|(?:app-)?csrftoken|csrf|authorization|auth|bearer|token|"
    r"access[_-]?token|refresh[_-]?token|id[_-]?token|api[_-]?key|apikey|key|secret|"
    r"client[_-]?secret|password|passwd|pwd|sig|signature|code|state|nonce|companion[_-]?token)")
# Strong segments: never appear inside benign identifiers (author, status_code, keyboard, ...).
STRONG_SEG = {"csrftoken","csrf","token","sessionid","authorization","bearer","password",
    "passwd","secret","apikey","accesstoken","refreshtoken","idtoken","clientsecret",
    "companiontoken","signature"}
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_PATS = [
    (re.compile(r"sessionid=[^;&\s\"']+", re.I), None),
    (re.compile(r"(app-)?csrftoken=[A-Za-z0-9]{8,}", re.I), None),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-]{12,}", re.I), None),
    (re.compile(SENSITIVE_KEY + r"=[^;&\s\"']{6,}", re.I), None),
    (re.compile(SENSITIVE_KEY + r"\"\s*:\s*\"[^\"]{6,}\"", re.I), None),
    (re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"), "uuid_skip"),  # generic net, but keep UUIDs
]
_WHOLE_KEY = re.compile(r"^" + SENSITIVE_KEY + r"$", re.I)

def redact_str(s):
    if not isinstance(s, str):
        return s
    for pat, mode in _PATS:
        if mode == "uuid_skip":
            s = pat.sub(lambda m: m.group(0) if UUID.match(m.group(0)) else "<REDACTED>", s)
        else:
            s = pat.sub("<REDACTED>", s)
    return s

def _segs(k):
    k = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", k)
    return [x.lower() for x in re.split(r"[^A-Za-z0-9]+", k) if x]

def key_sensitive(k):
    norm = re.sub(r"[_\-\s]", "", k.lower())
    if _WHOLE_KEY.match(norm):          # whole key: code/state/key/apikey/csrftoken/...
        return True
    return any(seg in STRONG_SEG for seg in _segs(k))  # strong segments only

def redact_obj(o):
    if isinstance(o, list):
        return [redact_obj(x) for x in o]
    if isinstance(o, dict):
        return {k: ("<REDACTED>" if key_sensitive(k) else redact_obj(v)) for k, v in o.items()}
    return redact_str(o)

# Gate patterns: ONLY value-intrinsic secrets (the match itself IS a secret). The key=value /
# "key":"value" patterns (_PATS #4,#5) are DELIBERATELY EXCLUDED here — they are substring-keyed and
# would false-positive on benign fields like cite_key ('key' inside it), rejecting valid captures.
# Any real key=value secret is already turned into "<REDACTED>" during redaction, so it never
# reaches the gate raw; the gate is the backstop for value-shaped secrets. UUIDs are exempt.
_GATE_PATS = [
    re.compile(r"sessionid=[^;&\s\"']+", re.I),
    re.compile(r"(app-)?csrftoken=[A-Za-z0-9]{8,}", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{12,}", re.I),
    re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),  # long opaque token; UUIDs skipped below
]

def scan_for_secrets(blob: str) -> list[str]:
    """Gate: return non-empty list of offending fragments if a value-shaped secret survives.
    '<REDACTED>' and canonical UUIDs are never leaks. Tested: clean on all 24 §6 vectors
    (post-redaction), fires on planted raw sessionid/csrftoken/Bearer/opaque tokens."""
    leaks = []
    for pat in _GATE_PATS:
        for m in pat.finditer(blob):
            frag = m.group(0)
            if frag == "<REDACTED>" or "<REDACTED>" in frag or UUID.match(frag):
                continue
            leaks.append(frag[:12] + "…")
    return leaks
```

### 5b. JavaScript (`background.js` — redaction section)
```js
const SENSITIVE_KEY =
  "(sessionid|session|(?:app-)?csrftoken|csrf|authorization|auth|bearer|token|" +
  "access[_-]?token|refresh[_-]?token|id[_-]?token|api[_-]?key|apikey|key|secret|" +
  "client[_-]?secret|password|passwd|pwd|sig|signature|code|state|nonce|companion[_-]?token)";
const STRONG_SEG = new Set(["csrftoken","csrf","token","sessionid","authorization","bearer",
  "password","passwd","secret","apikey","accesstoken","refreshtoken","idtoken","clientsecret",
  "companiontoken","signature"]);
const UUID = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
const SECRET_PATTERNS = [
  /sessionid=[^;&\s"']+/gi,
  /(app-)?csrftoken=[A-Za-z0-9]{8,}/gi,
  /Bearer\s+[A-Za-z0-9._\-]{12,}/gi,
  new RegExp(SENSITIVE_KEY + "=[^;&\\s\"']{6,}", "gi"),
  new RegExp(SENSITIVE_KEY + "\"\\s*:\\s*\"[^\"]{6,}\"", "gi"),
  { g: /\b[A-Za-z0-9_\-]{32,}\b/g, skip: (m) => UUID.test(m) },
];
const WHOLE_KEY_RE = new RegExp("^" + SENSITIVE_KEY + "$", "i");
function redactStr(s) {
  if (typeof s !== "string") return s;
  for (const p of SECRET_PATTERNS) {
    if (p instanceof RegExp) s = s.replace(p, "<REDACTED>");
    else s = s.replace(p.g, (m) => (p.skip(m) ? m : "<REDACTED>"));
  }
  return s;
}
function keySegments(k) {
  return k.replace(/([a-z0-9])([A-Z])/g, "$1 $2").split(/[^A-Za-z0-9]+/)
          .map((x) => x.toLowerCase()).filter(Boolean);
}
function keySensitive(k) {
  const norm = k.toLowerCase().replace(/[_\-\s]/g, "");
  if (WHOLE_KEY_RE.test(norm)) return true;
  for (const seg of keySegments(k)) if (STRONG_SEG.has(seg)) return true;
  return false;
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
```

---

## 6. Test vectors — PIN THESE (both languages)

Port to `tests/test_redactor.py` (Python) and a small node/QUnit or hand-rolled JS check
(`undermind-companion/redactor.test.mjs`). Every MUST-REDACT asserts the raw secret is absent; every
MUST-SURVIVE asserts the benign value is present.

**MUST REDACT (secret gone):**
| input | note |
|-------|------|
| `{"X-CSRFToken":"CSRFbbb222ccc333"}` | CSRF header value |
| `sessionid=SESSaaa111xyz` | session cookie |
| `/cb?token=SHORTtok123&x=1` | short OAuth token in URL query |
| `/cb?a=1&state=STbcd999xx` | OAuth state in URL query |
| `{"api_key":"KsecretVAL9"}` and `{"apiKey":"KsecretVAL9"}` | snake + camel |
| `{"n":{"access_token":"ATshort77"}}` | nested |
| `{"refresh_token":"RTshort55"}` | |
| `{"code":"4slashAeanSxLongCode"}` | whole-key `code` |
| `{"state":"opaqueStateVal9"}` | whole-key `state` |
| `authorization=Bearer abcdefGHIJ1234567890xyz` | |
| `Bearer QQQQ1234567890abcdWXYZ` | plain bearer |
| `x9F3kQ2mZ7pL4nR8sT1vW6yB0cD5eG2hJ4k` | 32+ opaque token, non-UUID |

**MUST SURVIVE (benign value intact) — these are the ones that protect Part B's fixtures:**
| input | why it must survive |
|-------|---------------------|
| `{"project_id":"550e8400-e29b-41d4-a716-446655440000"}` | UUID id — fix #3 needs to see it |
| `/api/v2/projects/550e8400-e29b-41d4-a716-446655440000/jobs/` | UUID in path |
| `{"author":"Faber, J."}` / `{"authors":["Faber","Ravi"]}` | 'auth' substring must NOT trigger |
| `{"status_code":200}` | 'code' substring; int value |
| `{"error_code":"E501"}` / `{"zip_code":"90210"}` | 'code' substring, benign |
| `{"keyboard":"qwerty"}` | 'key' substring |
| `{"status":"completed"}` | plain status word |
| `{"title":"Scattering of FRBs"}` | title text |
| `{"cite_key":"Faber2026"}` | citation key |

If any vector fails, the redactor was modified — revert to §5 verbatim. Do not "fix" a failing
MUST-SURVIVE by loosening a MUST-REDACT.

**Gate check (separate from the redaction battery above).** For `scan_for_secrets`, assert two
properties: (a) **no false positives** — run each of the 24 vectors above through `redact_obj`/
`redact_str` first, then `scan_for_secrets` on the JSON blob; every result must be `[]` (in
particular `{"cite_key":"Faber2026"}` must NOT be flagged — this is the bug the value-only gate
patterns exist to avoid); (b) **catches real leaks** — `scan_for_secrets` on raw un-redacted
`"sessionid=RAWLEAK12345"`, `"csrftoken=RAWcsrf1234567890abcd"`, `"Bearer RAWbearer1234567890xyz"`,
and a 32+ opaque token must each return a non-empty list; and a benign blob
`{"cite_key":"Faber2026","project_id":"<a UUID>","author":"Faber"}` must return `[]`.

---

## 7. Acceptance tests
1. Load extension, log in, toggle Record ON; browse: projects list, open project, start+abandon a New
   Research Project, send one chat message. Confirm files appear under `~/.config/undermind-mcp/captures/`
   and the popup counter increments.
2. **Secret scan:** `grep -rEi 'sessionid=|(app-)?csrftoken=[A-Za-z0-9]{8,}|Bearer [A-Za-z0-9]{12,}'`
   over the captures dir → **0 matches**. Also confirm a known UUID and an `author` value ARE present
   (over-redaction regression check).
3. App still works with capture ON (streams render, no broken requests) — proves clone/tee is safe.
4. Toggle OFF → no further `/capture` POSTs.
5. `redact_obj` unit tests pass the full §6 24-vector battery in **both** languages (py + js);
   `scan_for_secrets` unit tests pass the §6 gate check in **Python only** (the gate is receiver-side;
   the JS side redacts but does not gate).
6. `ruff` + `pyright --strict src/` clean; existing suite still green.

## 8. Commits
- `feat: shared redactor + secret-scan gate (_sanitize.py)`
- `feat: POST /capture route writes sanitized fixtures`
- `feat: companion passive fetch-capture (inject + relay + background redactor)`
- `feat: popup capture toggle (default off, persisted)`
- `test: redactor 24-vector battery (py + js) + /capture route`

Stop and report when done; do not merge. This branch stays stacked for one combined review with the
P0 and config-constants work, after which the whole stack merges to `main` together.
