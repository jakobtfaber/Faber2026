# Brief for Claude Code — P0 keychain security fixes ONLY

> Paste everything below this line into Claude Code, running in the `undermind-mcp` repo root.

---

**Scope.** Fix exactly two security bugs in this repo. Do **not** touch endpoint capture, the V1/V2
create flow, the CSRF cookie name, `models.py`, or the companion extension — those are separate work.
If you find yourself editing any file other than `src/undermind_mcp/server.py` and
`src/undermind_mcp/cli.py` (plus their tests), stop and ask.

**Context.** Two bugs make session credentials persist to the OS keychain against the project's own
stated policy (`project-outline.md` §5: "Do not persist credentials to the keychain by default";
§3 Step 3: "Persistence is opt-in. Default is in-memory only").

---

## Bug 1 — keychain persistence is hardcoded ON

**File:** `src/undermind_mcp/server.py`, module level.
**Current:** `auth_store = AuthStore(use_keychain=True)` — runs on every `serve()`, unconditionally.
The `init --use-keychain` flag in `cli.py` is never threaded here, so it's cosmetic.

**Required behavior:**
- Default must be **in-memory only** (`use_keychain=False`).
- Keychain persistence is enabled **only** when the user explicitly opted in at `init` time.

**Implementation (persist the choice at init, read it at serve):**
1. In `cli.py` `_cmd_init`, when `args.use_keychain` is True, write a marker file:
   ```python
   from undermind_mcp.http_receiver import _CONFIG_DIR
   _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
   (_CONFIG_DIR / "keychain_enabled").write_text("1")
   ```
   When False, ensure the marker is absent (`missing_ok=True` unlink).
2. In `server.py`, replace the hardcoded instantiation. Move it into `serve()` (or a factory) so it
   reads the marker at startup rather than at import time:
   ```python
   def _build_auth_store() -> AuthStore:
       from undermind_mcp.http_receiver import _CONFIG_DIR
       use_kc = (_CONFIG_DIR / "keychain_enabled").exists()
       return AuthStore(use_keychain=use_kc)
   ```
   Use it inside `serve()`; keep the module importable without side effects. If the module-level
   `client = UndermindClient(auth_store, ...)` wiring makes this awkward, refactor the globals into a
   small `build_server()` factory called by `serve()` — but keep the public `mcp` tool functions and
   their names unchanged.
3. `load_from_keychain()` should only be awaited when `use_keychain` is True (it already guards on
   `self._use_keychain`, so this is automatic).

**Do not** add a `serve --use-keychain` flag as the *primary* mechanism — the init marker is the
source of truth so the running server and the user's earlier choice can't disagree. (A `serve`
override flag is acceptable as an optional extra, defaulting to the marker.)

## Bug 2 — `reset` does not purge the keychain it wrote

**File:** `src/undermind_mcp/cli.py`, `_cmd_reset`.
**Current:** `store = AuthStore()` (keychain OFF) → `store.clear()` skips `_delete_from_keychain()`,
so the persisted session survives "reset." Only the companion-token file is removed.

**Required behavior:** `reset` must remove the keychain entry regardless of the current mode, so a
user can always fully wipe their session.

**Implementation:**
```python
store = AuthStore(use_keychain=True)   # force clear() to also purge the keychain
asyncio.run(store.clear())
```
Also delete the `keychain_enabled` marker from Bug 1 during reset:
```python
from undermind_mcp.http_receiver import _CONFIG_DIR
(_CONFIG_DIR / "keychain_enabled").unlink(missing_ok=True)
```
Keep the existing companion-token unlink. `AuthStore._delete_from_keychain()` already swallows
`PasswordDeleteError` when there's no entry, so calling it when nothing was stored is safe.

---

## Tests (add/adjust — no network, no real keychain)

Put these in `tests/test_server.py` / `tests/test_cli.py`. Mock the keychain (`keyring` set/get/delete)
so nothing touches the real OS store.

1. **Default is in-memory:** with no `keychain_enabled` marker, the store built by `serve()`'s factory
   has `use_keychain is False`.
2. **Opt-in works:** after `_cmd_init` with `--use-keychain`, the marker exists and the factory builds
   `use_keychain is True`.
3. **init without flag leaves no marker** (and removes a stale one).
4. **reset purges keychain:** patch `keyring.delete_password`; assert `_cmd_reset` calls it (or that a
   `clear()` on a keychain-enabled store does), and that the marker + companion-token file are gone.
5. Existing tests still pass; `ruff` clean; `pyright` strict clean on `src/`.

## Acceptance
- `undermind-mcp init` (no flag) → run `serve` → session is NOT written to keychain.
- `undermind-mcp init --use-keychain` → run `serve` → session IS written to keychain.
- `undermind-mcp reset` → keychain entry, marker, and companion token all gone; prints an accurate
  "credentials cleared" message.
- Commit as two commits: `"fix: keychain persistence off by default (opt-in via init marker)"` and
  `"fix: reset now purges keychain entry and marker"`.

**Reminder:** scope is these two bugs. Nothing else in the repo changes.
