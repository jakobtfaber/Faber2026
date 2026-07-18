# Brief for Claude Code — Batch 2 (stacked on `fix/keychain-persistence-p0`)

> Paste into Claude Code at the `undermind-mcp` repo root. **Branch off the existing
> `fix/keychain-persistence-p0` branch** (not `main`) so this stacks on the P0 fixes / PR #1.
> Suggested branch name: `fix/config-constants-and-create-flow`.

This brief has **two parts**. **Part A is ready to run now.** **Part B waits for endpoint-capture
evidence** — do Part A, commit it, then stop and confirm capture has produced
`tests/fixtures/endpoints_observed.json` before starting Part B. If those fixtures don't exist yet,
do Part A only and say so.

---

# PART A — cleanup (run now)

Two things: promote the two private constants in `http_receiver.py` to public so the four
`# pyright: ignore[reportPrivateUsage]` suppressions can go, and close a resource leak introduced by
the P0 refactor.

## A1 — Promote `_CONFIG_DIR` / `_TOKEN_FILE` to public

**Why:** PR #1 reaches into `http_receiver`'s private names from `cli.py` and `server.py`, forcing
four `reportPrivateUsage` suppressions. These are module-level config paths legitimately shared across
modules — they should be public.

**Reference map (every occurrence at branch head — change all of them):**

| File | Lines | Role |
|------|-------|------|
| `src/undermind_mcp/http_receiver.py` | 40–41 (defs), 94–97, 107–108 (uses) | canonical definitions + internal uses |
| `src/undermind_mcp/cli.py` | 46, 48, 49, 93, 94, 103, 104, 105 | `_cmd_init`, `_cmd_reset` (3 of the 4 suppressions here) |
| `src/undermind_mcp/server.py` | 40, 42 | `_build_auth_store` (the 4th suppression) |
| `tests/test_cli.py` | 13, 14 | `monkeypatch.setattr(http_receiver, "_CONFIG_DIR"/"_TOKEN_FILE", ...)` |
| `tests/test_server.py` | 13, 20 | `monkeypatch.setattr(http_receiver, "_CONFIG_DIR", ...)` |

**Do it as a rename, not an alias:**
1. In `http_receiver.py`: rename `_CONFIG_DIR` → `CONFIG_DIR` and `_TOKEN_FILE` → `TOKEN_FILE` at the
   definitions (lines 40–41) and all internal uses (94–97, 107–108).
2. In `cli.py` and `server.py`: update the imports to the public names and **delete all four
   `# pyright: ignore[reportPrivateUsage]` comments** (they become unnecessary and pyright will now
   flag them as unused-ignore under strict, so they must go).
3. In both test files: update the `monkeypatch.setattr(http_receiver, "CONFIG_DIR"/"TOKEN_FILE", ...)`
   target strings to the new public names.
4. Grep to confirm zero remaining references to `_CONFIG_DIR` / `_TOKEN_FILE` **and** zero remaining
   `pyright: ignore[reportPrivateUsage]` anywhere in the repo.
5. **Do not** leave backward-compat aliases (`_CONFIG_DIR = CONFIG_DIR`) — this is a private,
   single-consumer codebase; a clean rename is correct.

Optional (only if trivial): the literal `"keychain_enabled"` marker name now appears in `cli.py`
(×2), `server.py`, and both test files. Promoting it to a `KEYCHAIN_MARKER = "keychain_enabled"`
constant in `http_receiver.py` (or a small shared spot) would de-duplicate it. Nice-to-have, not
required — skip if it widens the change surface.

## A2 — Close the orphaned httpx client from the P0 refactor

**Why:** After PR #1, `server.py` creates an `httpx.AsyncClient` at import time
(`client = UndermindClient(auth_store, rate_limiter)`), and `build_server()` creates a **second**
`UndermindClient` — orphaning the first without closing it. Harmless functionally (GC reclaims it) but
httpx may emit an "Unclosed client" ResourceWarning, and it's sloppy.

**Fix (pick the smaller diff):**
- **Preferred:** in `build_server()`, close the existing client before replacing it:
  ```python
  global auth_store, client
  old = client
  auth_store = _build_auth_store()
  client = UndermindClient(auth_store, rate_limiter)
  with contextlib.suppress(Exception):
      asyncio.get_event_loop().run_until_complete(old.close())  # or schedule close; see note
  ```
  `UndermindClient.close()` is async (`await self._http.aclose()`), and `build_server()` is sync and
  called from `serve()` *before* `asyncio.run(...)`. Simplest correct form: since nothing has used the
  import-time client yet at `serve()` time, close it synchronously via
  `asyncio.run(old.close())` **only if** no loop is running — or avoid the problem entirely with the
  alternative below.
- **Alternative (cleaner, preferred if it typechecks):** make the module-level `client` lazy — don't
  construct a `UndermindClient` at import time at all. Keep `auth_store = AuthStore(use_keychain=False)`
  for the default, set `client = None` at module scope with a proper type
  (`client: UndermindClient | None = None`), and construct it only in `build_server()`. Update the
  tool functions' access if needed (they reference `client` as a global; add an assert-not-None or a
  small accessor). This removes the orphan by never creating it.

Use judgment: if the lazy approach ripples into many tool functions, do the close-on-rebuild version
instead. Either is acceptable; the test below pins the behavior.

**Test (add to `tests/test_server.py`):**
- `build_server()` called twice does not leave an unclosed client — assert the current `client` is the
  most recently built one and (close-on-rebuild variant) that the prior client's `close()` was
  awaited, or (lazy variant) that no client exists until `build_server()` runs.

## Part A acceptance
- `ruff` clean, `pyright --strict src/` 0 errors, **0** `reportPrivateUsage` ignores in the repo.
- All existing tests pass (the P0 suite must stay green; you're renaming symbols it references).
- Commit as: `"refactor: promote CONFIG_DIR/TOKEN_FILE to public, drop pyright suppressions"` and
  `"fix: close orphaned httpx client on server rebuild"`.
- **Stop here and report.** Confirm whether `tests/fixtures/endpoints_observed.json` exists. If not,
  Part B is blocked — do not attempt it.

---

# PART B — fixes #3 and #5 (apply ONLY after endpoint capture exists)

> ⛔ Prerequisite: `tests/fixtures/endpoints_observed.json` and the sanitized
> `tests/fixtures/curl/*.sh` + `responses/*.json` from the capture workflow must be present. These
> supply the ground truth for the two open questions below. If they're absent, stop — the fixes below
> are guesses without them.

## B1 — Fix #5: CSRF cookie name (`csrftoken` vs `app-csrftoken`)

**The question the capture answers:** `endpoints_observed.json` has a `csrf_cookie_names` field and the
sanitized cURLs show the request `X-CSRFToken` header source. Determine the **real** cookie name.

**What to fix once known** (`src/undermind_mcp/auth_store.py`, `update_from_set_cookie`, ~line with
`if morsel_name == "csrftoken":`):
- Accept both names so rotation is never missed:
  ```python
  if morsel_name in ("csrftoken", "app-csrftoken"):
      new_csrf = morsel.value
  ```
- Verify the client's outgoing `X-CSRFToken` is sourced from whichever cookie the capture shows
  (`client.py` `_build_headers`, the `csrftoken` field). If the real cookie is `app-csrftoken`, make
  sure `SessionCredentials.csrftoken` is populated from it end-to-end (companion `background.js`
  already reads either name; confirm the receiver → auth_store path preserves it).
- **Test:** add a `test_cookie_jar.py` (or extend `test_auth_store.py`) case that rotates
  `app-csrftoken` via `Set-Cookie` and asserts `creds.csrftoken` updates. Include a `respx` replay of a
  captured mutating request asserting the correct `X-CSRFToken` is sent.

## B2 — Fix #3: unify the V1/V2 create→status→results flow

**The bug (confirmed by code read):** `undermind_create_search` creates a **V2** project, then calls
`client.submit_search()` → **V1** `/search/submit/` (unrelated to the project) and returns that V1 id
as `job_id`; but `undermind_get_status`/`get_results` read **V2** `/projects/{id}/jobs/{job_id}/` and
`/papers/`. The ids don't line up and the pipeline can't complete.

**The question the capture answers:** in `endpoints_observed.json` / the cURLs from the "New Research
Project → submit first step" action, find how a search is really launched in V2:
- Is a job created by `POST /projects/{id}/jobs/` (returns a `job_id`), then launched by
  `POST /projects/{id}/jobs/{job_id}/submit/`?
- Or is the job auto-created with the project?
- What is the exact request body and the response shape (esp. the id field and `status` values)?

**What to fix once known** (`src/undermind_mcp/server.py` `undermind_create_search`, and add the
missing primitive to `client.py` if capture shows a `POST /projects/{id}/jobs/` create call):
- Wire the whole flow through **V2**: after `create_project`, create + submit a V2 job on that
  project, and return `{project_id, job_id, status}` all in the V2 namespace so `get_status` /
  `get_results` resolve. `client.py` already has `submit_job(project_id, job_id)`; add the
  job-creation call if the capture shows one.
- Keep `submit_search` (V1 classic) **only** if you deliberately expose a separate
  `undermind_classic_search` tool. Do not cross the two APIs in one tool.
- The `E501` on `server.py:119` (pre-existing, in this function) will be rewritten here — fix it as
  part of the change; no separate commit needed.
- **Test:** `respx` replays of the captured create + submit + status + papers sequence, asserting the
  ids thread through and a terminal `status` is reached. Use the sanitized `responses/*.json` as
  fixture payloads so the models are validated against real shapes (this also closes fix #6 for these
  endpoints).

## Part B acceptance
- `ruff` + `pyright --strict` clean; new `respx` tests green against captured fixtures.
- `undermind_create_search` → `undermind_get_status` → `undermind_get_results` resolve end-to-end in
  the replay tests (ids consistent, papers returned).
- Commits: `"fix: accept app-csrftoken in CSRF rotation (#5)"` and
  `"fix: unify create_search on the V2 job flow (#3)"`.

---

## Order of operations recap
1. Branch off `fix/keychain-persistence-p0`.
2. Do **Part A** (A1 rename + drop 4 suppressions, A2 close orphaned client), commit, report.
3. Confirm capture fixtures exist. If yes → **Part B** (#5 then #3). If no → stop, report that B is
   blocked pending capture.
4. Do not merge to `main`; keep stacking on the branch for one combined review.
