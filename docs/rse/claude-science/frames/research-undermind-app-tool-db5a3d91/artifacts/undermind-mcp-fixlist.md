# undermind-mcp — Correction Punch-List

Repo: `jakobtfaber/undermind-mcp` @ `main` (reviewed 2026-07-08). Status: Phase 1.
Ordered by priority. Each item = **where** → **what's wrong** → **why it matters** → **fix**.
Line references are by function/symbol since the tree may have moved.

---

## P0 — Security / correctness (fix before running locally)

### 1. Keychain persistence is ON by default (violates the project's own rule)
- **Where:** `src/undermind_mcp/server.py`, module-level: `auth_store = AuthStore(use_keychain=True)`.
- **What's wrong:** `serve()` unconditionally persists session cookies + CSRF to the OS keychain
  (`keyring` service `"undermind-mcp"`, key `"session"`). The `init --use-keychain` flag in `cli.py`
  is never threaded into this instantiation — it only prints a message. So the flag is cosmetic and
  the default is the opposite of what's documented.
- **Why it matters:** Directly violates `project-outline.md` §5 ("Do not persist credentials to the
  keychain by default") and §3 Step 3 ("Persistence is opt-in. Default is in-memory only"). Your
  session outlives the process and sits in the keychain until explicitly cleared — a larger
  credential blast radius than a user reading the docs would expect.
- **Fix:**
  - Read persistence intent from config/env, defaulting OFF. E.g. write a flag to
    `~/.config/undermind-mcp/config.json` (or a `keychain` marker file) at `init` time when
    `--use-keychain` is passed, and read it in `serve()`:
    ```python
    from undermind_mcp.http_receiver import _CONFIG_DIR
    use_kc = (_CONFIG_DIR / "keychain_enabled").exists()   # written by `init --use-keychain`
    auth_store = AuthStore(use_keychain=use_kc)
    ```
  - Or accept `undermind-mcp serve --use-keychain` and pass it through `_cmd_serve`.
  - Either way: default must be `use_keychain=False`.

### 2. `reset` does not delete the keychain entry it wrote
- **Where:** `src/undermind_mcp/cli.py`, `_cmd_reset`: `store = AuthStore()` (i.e. `use_keychain=False`),
  then `store.clear()`.
- **What's wrong:** `AuthStore.clear()` only touches the keychain when `self._use_keychain` is True.
  A reset store is created with keychain OFF, so `clear()` skips `_delete_from_keychain()` — the
  persisted session (written by bug #1) is left behind. `reset` only removes the companion token file.
- **Why it matters:** "Reset complete: credentials cleared" is false — the actual session credentials
  remain in the keychain. Combined with #1, a user who thinks they've wiped their session hasn't.
- **Fix:** In `_cmd_reset`, force keychain deletion regardless of flag:
  ```python
  store = AuthStore(use_keychain=True)   # so clear() also purges keychain
  asyncio.run(store.clear())
  ```
  Or call `keyring.delete_password("undermind-mcp", "session")` directly with a
  `PasswordDeleteError` guard. Keep the companion-token unlink.

---

## P1 — Functional bugs (tool won't work end-to-end as written)

### 3. `create_search` mixes V1 and V2 — the create→status→results pipeline is broken
- **Where:** `src/undermind_mcp/server.py` `undermind_create_search`; `client.py` `submit_search`
  (V1 `/search/submit/`), `get_job` / `list_papers` (V2 `/projects/{id}/...`).
- **What's wrong:**
  1. `undermind_create_search` creates a **V2** project (`create_project` → `/api/v2/projects/`),
  2. then calls `client.submit_search({"query": ...})` which POSTs to **V1**
     `/api/v1/search/submit/` (the "classic search"), unrelated to the project just created,
  3. and returns that V1 response's `id` as `job_id`.
  - But `undermind_get_status` → `get_job()` reads **V2** `/projects/{id}/jobs/{job_id}/`, and
    `undermind_get_results` reads **V2** `/projects/{id}/papers/`. A V1 classic-search id will not
    resolve as a V2 job, and classic results are not attached to the V2 project.
- **Why it matters:** The headline workflow (start a search, poll it, read papers) can't complete.
  This is almost certainly why it's still Phase 1.
- **Fix:** Pick one API surface and wire it through. The V2 project/job flow is the one the rest of
  the client already speaks, so:
  - In `undermind_create_search`: after `create_project`, create + submit a **V2 job** on that
    project rather than calling `submit_search`. `client.py` already has `submit_job(project_id, job_id)`
    (POST `/projects/{id}/jobs/{job_id}/submit/`). You need the job-creation call that yields the
    `job_id` first — capture the real "New Research Project → submit first step" request (see #6) to
    learn whether a job is created via `POST /projects/{id}/jobs/` or is auto-created by the project,
    then return `{project_id, job_id, status}` all in the V2 namespace.
  - Keep `submit_search` (V1 classic) only if you deliberately expose a separate
    `undermind_classic_search` tool; don't cross the two.

### 4. `doctor` can never see a live session (always reports "missing or expired")
- **Where:** `src/undermind_mcp/cli.py` `_cmd_doctor`: `store = AuthStore()` then `store.is_fresh()`.
- **What's wrong:** `doctor` creates a fresh in-process `AuthStore` with keychain OFF and never calls
  `load_from_keychain()`. It has no connection to the running `serve()` process's in-memory store and
  loads nothing, so `is_fresh()` is always False and it returns before ever contacting Undermind.
- **Why it matters:** The documented end-to-end verification step (`project-outline.md` Step 11 /
  INSTALL.md step 7) can never pass, even with a healthy session.
- **Fix:** Make `doctor` query the running server the same way the extension does — hit the loopback
  receiver instead of constructing an `AuthStore`:
  ```python
  import httpx
  from undermind_mcp.http_receiver import load_companion_token
  token = load_companion_token()
  r = httpx.get("http://127.0.0.1:8787/auth/status",
                headers={"X-Companion-Token": token or ""})
  status = r.json()   # {connected, age_seconds, ...}
  ```
  Report from `status`. (Listing projects from `doctor` would need the server's authed client; simplest
  is to add a `GET /auth/whoami`-style diagnostic route on the receiver that proxies `get_profile()`,
  or accept that `doctor` only reports session freshness.) If you keep the `AuthStore` path, it must
  be constructed with `use_keychain=True` and `await store.load_from_keychain()` first — but that only
  works when bug #1's keychain persistence is enabled, so the receiver-ping approach is cleaner.

### 5. CSRF cookie-name mismatch — rotation logic misses `app-csrftoken`
- **Where:** `src/undermind_mcp/auth_store.py` `update_from_set_cookie`: `if morsel_name == "csrftoken":`.
  Compare with `tests/fixtures/endpoints.md`, which states the CSRF cookie is **`app-csrftoken`**
  (header `X-CSRFToken`), and `background.js`, which reads `csrftoken` **or** `app-csrftoken`.
- **What's wrong:** If the real cookie is `app-csrftoken` (per the reverse-engineered notes), then
  when Django rotates it via `Set-Cookie`, `update_from_set_cookie` won't recognize the name and won't
  update `creds.csrftoken`. The next mutating request sends a stale `X-CSRFToken` → 403 → `SessionExpired`.
- **Why it matters:** Silent, intermittent auth failures on state-changing calls (create project,
  submit job, send message) after the first token rotation.
- **Fix:** Accept both names in `update_from_set_cookie`:
  ```python
  if morsel_name in ("csrftoken", "app-csrftoken"):
      new_csrf = morsel.value
  ```
  Confirm the real cookie name during endpoint capture (#6) and make the client's `X-CSRFToken`
  source match. Add a `test_cookie_jar.py` case for `app-csrftoken` rotation.

---

## P2 — Validation & known gaps (do before trusting output)

### 6. Endpoint models are unvalidated — run Step 6 ("STOP AND ASK: endpoint capture")
- **Where:** `tests/fixtures/curl/` and `tests/fixtures/responses/` contain only `.gitkeep`.
  `models.py` / `client.py` were inferred from the SPA bundle (`endpoints.md`, dated **2026-04-23**),
  not validated against live responses.
- **Why it matters:** Pydantic models may not match real payloads (field names, nesting, pagination
  envelope vs. bare list, `relevance_score` presence). The API is ~3 months past the capture date and
  may have drifted. This is the single highest-value next step and is explicitly gated in your own plan.
- **Fix:** Do the capture the outline describes — log in to `app.undermind.ai`, DevTools → Network
  (Preserve log, Disable cache), exercise: reload projects, open a project, start+abandon a New
  Research Project, send one chat message, visit updates + settings. "Copy all as cURL" for every
  `api.undermind.ai` request; "Copy response" on the key ones. Sanitize (strip `Cookie`,
  `Authorization`, `X-CSRFToken`), save to `tests/fixtures/curl|responses/`, then reconcile
  `models.py`, the V1/V2 flow (#3), and the CSRF name (#5). Add `respx` replay tests per method.

### 7. Bundle-hash drift check is specified but not implemented
- **Where:** `project-outline.md` Step 10 / §6 describe a `doctor`-time bundle-hash comparison; not
  present in `_cmd_doctor`, and `bundle_hash` is never populated (companion `background.js` doesn't
  send it; `AuthRefreshRequest.bundle_hash` stays `None`).
- **Why it matters:** No early warning when Undermind ships a new SPA build and the reverse-engineered
  endpoints change under you — failures will look like random auth/parse errors instead.
- **Fix (optional, low effort):** In the companion, fetch `https://app.undermind.ai/`, extract the
  hashed JS bundle filename, include it as `bundle_hash` in the refresh payload. In `doctor`, compare
  against the value stored at capture time and warn on mismatch.

### 8. `wait_for` cap is shorter than a real deep search
- **Where:** `server.py` `undermind_wait_for`, `timeout_seconds` capped at 120s, polls every 5s.
- **What's wrong (UX, not a bug):** Undermind deep searches routinely run several minutes, so
  `wait_for` will usually return `{"status": "timeout"}` and the agent must loop.
- **Fix:** Document this in the tool description (the caller should poll `get_status` in a loop), and
  consider emitting MCP progress notifications if the SDK build supports them. Don't raise the cap
  past ~120s — long-held MCP calls are fragile.

---

## Not bugs — keep these (they're done right)
- Companion token: `secrets.token_urlsafe(32)`, chmod 600, `secrets.compare_digest`.
- Receiver bound strictly to `127.0.0.1:8787`; CORS locked to `app.undermind.ai` + `chrome-extension://`.
- Secret redaction in logs + `__repr__` (with tests); MCP tools never return raw auth material.
- Undermind free-text wrapped `{"source":"undermind","untrusted":true}`; snippets truncated to 200 chars.
- Conservative rate limits; explicit refusal to automate login or defeat bot detection.

## Standing risks the code can't remove (accept knowingly)
- **ToS:** reverse-engineered private endpoints + lifted browser session ≈ what SaaS ToS prohibit;
  realistic downside is account suspension. (The `init` "I understand" gate is there for this reason.)
- **Bot detection:** `BotChallenge` handling is correct, but repeated triggering is what flags accounts.
- **Maintenance:** endpoint drift will require re-capture periodically.
- **Better path:** a sanctioned Undermind API key (their enterprise API is real — cf. the GSK
  deployment) removes the ToS, Cloudflare-fragility, and drift burden at once, and would be cleanly
  connectable from a hosted agent environment too.
