# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific, visual, and operational-authority decisions. Silence leaves every item blocked._

## 1. Ratify the Jupyter surface

**Decision:** Is the kernel-only Jupyter surface admitted as a repository-owned operational surface? (Admission presupposes the authority-10 bar is satisfied; the choices distinguish a technical rejection from a deferred authorization.)

**Recommended:** `ratify` — All four promotion conditions hold as of 2026-08-06: the definition and locked notebook group are merged (#256), make test-notebook passed locally (2 passed, exit 0, Python 3.12.13, ipykernel 7.3.0, machine jakob), and an owner-run workbench session selected the checkout .venv and executed a cell. Receipts attached to this ticket.

**Choose:**

- `ratify` — The admission bar is satisfied; admit the surface under its own start, stop, and recovery instructions.
- `defer-authorization` — The admission bar is satisfied, but authorization is deferred; the surface stays unadmitted for now.
- `reject-bar-unmet` — The admission bar is not satisfied; the surface stays unadmitted and authority-10's finding stays in force.

**Context:**

- The definition, dependency group, lock entries, and smoke test are merged on main (pull request #256).
- The surface is kernel-only: no server, no exposed port, no user-level kernel specification.
- The 2026-08-06 pilot first hit a stale anaconda-pointing user kernelspec (since quarantined, editor settings hardened), then succeeded on the checkout .venv through the author's own picker path.

**Evidence:**

- [Surface definition](docs/rse/ops/jupyter-surface.md) — `dbaef59f…`
- [Admission receipts: smoke test and workbench pilot, 2026-08-06](docs/rse/wayfinder/tickets/jupyter-surface-admission-receipts-20260806.md) — `d33038b8…`

**Effect:** Ratification lets agents start and stop a kernel for bounded local work under the definition; rejection leaves the surface unadmitted.

**Record:** `docs/rse/wayfinder/tickets/jupyter-surface-admission-2026-08-05.md` — Record the decision and its receipt on this ticket and update the ticket status. On ratify only, also update the standing admission state in AGENTS.md and CLAUDE.md (the 'defined, not yet owner-ratified' lines) in the same change, or the granted kernel-start permission stays inert; on defer or reject, leave the standing state unchanged.
