# undermind-mcp — Secure Endpoint-Capture Checklist

This is Step 6 of the build plan ("STOP AND ASK: Endpoint Capture") made concrete, with
sanitization enforced by default. Goal: capture real `api.undermind.ai` request/response pairs
so `models.py` and the V1/V2 flow can be validated — **without ever letting a live session
cookie, CSRF token, or bearer token reach disk or git.**

> ⚠️ **The hazard is your session cookie.** A raw "Copy as cURL" contains `Cookie: sessionid=…`,
> which is a live credential to your Undermind account. Treat every raw capture as a secret until
> it has passed the sanitizer's secret-scan gate. Do the capture on your own machine, in a
> throwaway working dir outside the repo, and only move sanitized files into `tests/fixtures/`.

---

## 0. Before you start

- [ ] Log in to `https://app.undermind.ai` in normal Chrome.
- [ ] Have a scratch dir **outside the repo** for raw dumps: `mkdir -p ~/um-capture-raw && cd ~/um-capture-raw`
- [ ] Decide you will NOT paste raw cURL into chat, Claude Code, or any file inside the repo until sanitized.
- [ ] (Optional but recommended) Do this in a Chrome profile you can log out of afterward, so the
      captured session can be invalidated when you're done.

---

## 1. Set up DevTools

- [ ] Open DevTools (`Cmd+Opt+I`) → **Network** tab.
- [ ] Filter row: click **Fetch/XHR** (not "All").
- [ ] In the filter box type: `api.undermind.ai`
- [ ] Check **Preserve log** (so navigation doesn't clear captures).
- [ ] Check **Disable cache**.
- [ ] Leave DevTools open for the whole session.

---

## 2. Exercise the app (in this order)

Each row is one user action. After the whole run you'll export everything at once (Step 3), so just
perform the actions cleanly and let the requests accumulate.

| # | Action | Endpoints you're trying to capture |
|---|--------|-------------------------------------|
| 1 | Reload `https://app.undermind.ai/projects` | `GET /auth/csrf/`, `GET /my/profile/`, `GET /my/subscriptions/`, `GET /projects/` (list + pagination) |
| 2 | Open an existing project | `GET /projects/{id}/`, `GET /projects/{id}/papers/`, `GET /projects/{id}/files/`, `GET /projects/{id}/jobs/` |
| 3 | Click **New Research Project**, type `test capture`, **submit the first step**, then abandon | **the create+submit flow** — `POST /projects/`, then whatever creates/launches the job (`POST /projects/{id}/jobs/` and/or `POST /projects/{id}/jobs/{job_id}/submit/`, or a V1 `POST /search/submit/`). **This is the request that resolves fix #3.** |
| 4 | On a project with results, open **one paper** | `POST /projects/{id}/papers/details/`, `GET /projects/{id}/papers/{cite_key}/pdf/` |
| 5 | If there's a chat/ask box, send **one short message** | `POST /projects/{id}/chats/` then `POST /projects/{id}/chats/{chat_id}/messages/` (streaming — note the `Content-Type`) |
| 6 | Let the search from #3 run ~30–60s, then click into it | `GET /projects/{id}/jobs/{job_id}/` **polled repeatedly** — capture 2–3 polls to see how `status`/`progress` evolve and what the terminal shape is |
| 7 | Visit the account/settings page | `GET /my/profile/`, `GET /my/subscriptions/` (confirm credit fields) |

**Watch specifically for the answers to the open questions in the fix-list:**
- [ ] **Fix #3:** In action #3, is the job created by `POST /projects/{id}/jobs/`, or auto-created with
      the project, or is it the V1 `/search/submit/`? Note the exact URL, method, request body, and
      what id comes back.
- [ ] **Fix #5:** In the response headers of any request, find the `Set-Cookie` — is the CSRF cookie
      named `csrftoken` or `app-csrftoken`? And which name is sent back in the `X-CSRFToken` **request**
      header on mutations?
- [ ] **Pagination:** Does `GET /projects/` return a bare list or an envelope with `next`/`results`?
- [ ] **Streaming:** In action #5, is the response `text/event-stream`, chunked, or a WebSocket upgrade?

---

## 3. Export (raw → scratch dir, NOT the repo)

For **every** `api.undermind.ai` row:
- [ ] Right-click → **Copy** → **Copy all as cURL (bash)** — but do this per-request into a numbered file.

Fastest path — paste this into the **DevTools Console** to dump all captured XHRs as HAR-like JSON,
then sanitize in one shot. (Console → paste → it triggers a `.har` download.)

```js
// Run in the DevTools Console on the app.undermind.ai tab.
// This uses the built-in HAR export via the Network panel is manual; instead:
// Right-click anywhere in the Network request list → "Save all as HAR with content".
// Save it to ~/um-capture-raw/undermind.har  — do NOT put it in the repo.
console.log("Use: Network panel → right-click → 'Save all as HAR with content' → ~/um-capture-raw/undermind.har");
```

- [ ] In the Network panel, right-click the request list → **Save all as HAR with content** →
      save to `~/um-capture-raw/undermind.har`.
- [ ] Confirm the `.har` is in the scratch dir, **not** in the repo. (A HAR contains full headers +
      cookies + response bodies — it is a secret until sanitized.)

---

## 4. Sanitize (the gate — nothing enters the repo without passing this)

Save this as `~/um-capture-raw/sanitize.py` and run it against the HAR. It (a) strips secret headers,
(b) redacts secret-looking values in bodies/URLs, (c) splits into per-endpoint cURL + response
fixtures, and (d) **hard-fails if any secret pattern survives** so you can't accidentally ship one.

```python
#!/usr/bin/env python3
"""Sanitize a Chrome HAR of api.undermind.ai traffic into repo-safe fixtures.

Usage:
    python sanitize.py ~/um-capture-raw/undermind.har ./out
Then copy ./out/curl/*.sh and ./out/responses/*.json into tests/fixtures/.
Exits non-zero if any secret pattern remains — do not commit if it fails.
"""
from __future__ import annotations
import json, re, sys, hashlib
from pathlib import Path

# Header names whose values are secrets — replaced wholesale.
SECRET_HEADERS = {"cookie", "authorization", "x-csrftoken", "x-companion-token", "set-cookie"}

# Value patterns that must NEVER appear in output (the commit gate).
# NOTE: the gate reuses these patterns, so it can only catch blind spots it can
# describe. Any `key=value` whose key looks sensitive has its VALUE redacted
# regardless of length — this is what catches short OAuth/magic-link query tokens
# (e.g. ?token=abc123) that the length-based net misses.
_SENSITIVE_KEY = (
    r"(?i)(sessionid|session|(?:app-)?csrftoken|csrf|authorization|auth|"
    r"bearer|token|access[_-]?token|refresh[_-]?token|id[_-]?token|"
    r"api[_-]?key|apikey|key|secret|client[_-]?secret|password|passwd|pwd|"
    r"sig|signature|code|state|nonce|companion[_-]?token)"
)
SECRET_PATTERNS = [
    re.compile(r"sessionid=[^;&\s\"']+"),
    re.compile(r"(app-)?csrftoken=[A-Za-z0-9]{8,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{12,}"),
    # any sensitive key in a query string / cookie / form body → redact the value
    re.compile(_SENSITIVE_KEY + r"=[^;&\s\"']{6,}"),
    # any sensitive key in a JSON body ("token": "abc...") → redact the value
    re.compile(_SENSITIVE_KEY + r"\"\s*:\s*\"[^\"]{6,}\""),
    re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),  # long opaque tokens even without a key
]
# Allowlist substrings that are long but NOT secret (extend as needed after review).
# Keep this tight — every entry is a hole in the gate.
ALLOW = ("application/json", "text/event-stream", "<REDACTED>")

def redact_str(s: str) -> str:
    for pat in SECRET_PATTERNS:
        s = pat.sub("<REDACTED>", s)
    return s

_SENSITIVE_KEY_RE = re.compile(_SENSITIVE_KEY + r"$")  # whole-key match for dict keys

def _key_is_sensitive(k: str) -> bool:
    return bool(_SENSITIVE_KEY_RE.match(k.strip().lower().replace("_", "").replace("-", "")
                                        )) or k.lower() in SECRET_HEADERS \
        or bool(re.search(_SENSITIVE_KEY, k))

def redact_obj(o):
    if isinstance(o, dict):
        return {k: ("<REDACTED>" if _key_is_sensitive(k) else redact_obj(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [redact_obj(x) for x in o]
    if isinstance(o, str):
        return redact_str(o)
    return o

def scrub_headers(headers: list[dict]) -> list[dict]:
    out = []
    for h in headers:
        name = h.get("name", "")
        val = "<REDACTED>" if name.lower() in SECRET_HEADERS else redact_str(h.get("value", ""))
        out.append({"name": name, "value": val})
    return out

def main() -> int:
    har_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    (out_dir / "curl").mkdir(parents=True, exist_ok=True)
    (out_dir / "responses").mkdir(parents=True, exist_ok=True)
    har = json.loads(har_path.read_text())
    entries = [e for e in har["log"]["entries"] if "api.undermind.ai" in e["request"]["url"]]
    summary = []
    for i, e in enumerate(entries, 1):
        req, resp = e["request"], e["response"]
        method, url = req["method"], redact_str(req["url"])
        # --- sanitized cURL ---
        lines = [f"curl -X {method} '{url}' \\"]
        for h in scrub_headers(req.get("headers", [])):
            if h["name"].lower() in SECRET_HEADERS:
                lines.append(f"  -H '{h['name']}: <REDACTED>' \\")
            elif h["name"].lower() in ("content-type", "accept", "referer", "origin", "user-agent"):
                lines.append(f"  -H '{h['name']}: {h['value']}' \\")
        body = (req.get("postData") or {}).get("text", "")
        if body:
            lines.append(f"  --data '{redact_str(body)}' \\")
        curl = "\n".join(lines).rstrip(" \\")
        (out_dir / "curl" / f"{i:02d}.sh").write_text(curl + "\n")
        # --- sanitized response body ---
        content = (resp.get("content") or {}).get("text", "")
        if content:
            try:
                parsed = json.loads(content)
                safe = json.dumps(redact_obj(parsed), indent=2)
            except json.JSONDecodeError:
                safe = redact_str(content)[:20000]
            (out_dir / "responses" / f"{i:02d}.json").write_text(safe + "\n")
        # find CSRF cookie name in Set-Cookie (name only, value redacted)
        setck = [h["value"] for h in resp.get("headers", []) if h["name"].lower() == "set-cookie"]
        csrf_names = sorted({m for sc in setck for m in re.findall(r"\b(app-csrftoken|csrftoken)=", sc)})
        summary.append({"n": i, "method": method,
                        "path": re.sub(r"https://api\.undermind\.ai", "", url),
                        "status": resp.get("status"),
                        "csrf_cookie_names": [c.rstrip("=") for c in csrf_names],
                        "resp_content_type": next((h["value"] for h in resp.get("headers", [])
                                                   if h["name"].lower()=="content-type"), "")})
    (out_dir / "endpoints_observed.json").write_text(json.dumps(summary, indent=2) + "\n")

    # --- THE GATE: scan all output for surviving secrets ---
    leaks = []
    for f in out_dir.rglob("*"):
        if f.is_file():
            txt = f.read_text(errors="ignore")
            for pat in SECRET_PATTERNS:
                for m in pat.finditer(txt):
                    frag = m.group(0)
                    if any(a in frag for a in ALLOW) or frag == "<REDACTED>":
                        continue
                    leaks.append((str(f), frag[:12] + "…"))
    if leaks:
        print("SECRET SCAN FAILED — do NOT commit. Offending fragments:")
        for path, frag in leaks[:50]:
            print(f"  {path}: {frag}")
        return 1
    print(f"OK — {len(entries)} endpoints sanitized into {out_dir}. Secret scan clean.")
    print(f"CSRF cookie name(s) observed: "
          f"{sorted({c for s in summary for c in s['csrf_cookie_names']}) or 'none in Set-Cookie'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Run it:
```bash
cd ~/um-capture-raw
python sanitize.py undermind.har ./out
# Only if it prints "Secret scan clean":
cat out/endpoints_observed.json   # <- answers fix #5 (CSRF name) and shows the create flow (#3)
```

- [ ] Sanitizer printed **"Secret scan clean."** (If it failed, extend `SECRET_PATTERNS`/`ALLOW` and re-run; do not proceed.)
- [ ] Reviewed `out/endpoints_observed.json` — noted the create/submit flow and the CSRF cookie name.

---

## 5. Move sanitized fixtures into the repo

- [ ] Copy only sanitized outputs:
      ```bash
      cp out/curl/*.sh        /path/to/undermind-mcp/tests/fixtures/curl/
      cp out/responses/*.json /path/to/undermind-mcp/tests/fixtures/responses/
      cp out/endpoints_observed.json /path/to/undermind-mcp/tests/fixtures/
      touch /path/to/undermind-mcp/tests/fixtures/curl/.sanitized
      ```
- [ ] Update `tests/fixtures/endpoints.md` to reflect what was actually observed (correct any drift
      from the 2026-04-23 reverse-engineering).

---

## 6. Belt-and-suspenders: pre-commit secret gate

The build plan calls for a pre-commit hook that fails on any secret under `tests/fixtures/`. Add to
`.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: no-secrets-in-fixtures
        name: no secrets in fixtures
        entry: bash -c 'if git diff --cached --name-only | grep -q "^tests/fixtures/"; then
                 if git grep -nE "sessionid=|(app-)?csrftoken=[A-Za-z0-9]{16,}|Bearer [A-Za-z0-9]{20,}" -- tests/fixtures/; then
                   echo "SECRET found in tests/fixtures — aborting commit"; exit 1; fi; fi'
        language: system
        pass_filenames: false
```

And confirm `.gitignore` ignores raw dumps in case they ever land in-tree:
```
tests/fixtures/curl/*.raw.sh
*.har
companion_token
.env
```

- [ ] Pre-commit hook added and `pre-commit run --all-files` passes.
- [ ] `.gitignore` covers `*.har`, raw cURL, `companion_token`, `.env`.

---

## 7. After capture

- [ ] Reconcile `models.py` against `tests/fixtures/responses/*.json`; add a `respx` replay test per method.
- [ ] Apply fix #3 (V1/V2 create flow) and fix #5 (CSRF cookie name) using what you observed.
- [ ] **Invalidate the captured session:** log out of the Undermind tab (or use a disposable profile),
      so the cookie you exported — even though it never hit disk unredacted — can no longer be used.
- [ ] Delete the scratch dir: `rm -rf ~/um-capture-raw` (the HAR is the last unsanitized copy).

---

### Quick reference — what must never reach the repo
`Cookie` / `sessionid` · `csrftoken` / `app-csrftoken` values · `Authorization` / `Bearer` ·
`X-CSRFToken` · `X-Companion-Token` · any raw `.har` · unredacted response bodies.
The sanitizer's secret-scan gate (Step 4) and the pre-commit hook (Step 6) are the two enforcement
points — if both are green, you're safe to commit.
