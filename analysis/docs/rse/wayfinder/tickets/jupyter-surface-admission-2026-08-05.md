# Ratify the Jupyter surface against the authority-10 admission bar

- Type: `wayfinder:grilling` (HITL)
- Status: resolved — ratified 2026-08-07 by the owner (jakobtfaber):
  choice `ratify` on the decision card. The kernel-only Jupyter surface is
  ADMITTED as a repository-owned operational surface under its own start,
  stop, and recovery instructions. Receipts:
  [admission receipts](jupyter-surface-admission-receipts-20260806.md).
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `done`

## Owner decision card

```json
{
  "id": "ratify-jupyter-surface",
  "kind": "operational",
  "title": "Ratify the Jupyter surface",
  "decision": "Is the kernel-only Jupyter surface admitted as a repository-owned operational surface? (Admission presupposes the authority-10 bar is satisfied; the choices distinguish a technical rejection from a deferred authorization.)",
  "recommended": {
    "choice": "ratify",
    "reason": "All four promotion conditions hold as of 2026-08-06: the definition and locked notebook group are merged (#256), make test-notebook passed locally (2 passed, exit 0, Python 3.12.13, ipykernel 7.3.0, machine jakob), and an owner-run workbench session selected the checkout .venv and executed a cell. Receipts attached to this ticket."
  },
  "choices": [
    {
      "id": "ratify",
      "label": "The admission bar is satisfied; admit the surface under its own start, stop, and recovery instructions."
    },
    {
      "id": "defer-authorization",
      "label": "The admission bar is satisfied, but authorization is deferred; the surface stays unadmitted for now."
    },
    {
      "id": "reject-bar-unmet",
      "label": "The admission bar is not satisfied; the surface stays unadmitted and authority-10's finding stays in force."
    }
  ],
  "context": [
    "The definition, dependency group, lock entries, and smoke test are merged on main (pull request #256).",
    "The surface is kernel-only: no server, no exposed port, no user-level kernel specification.",
    "The 2026-08-06 pilot first hit a stale anaconda-pointing user kernelspec (since quarantined, editor settings hardened), then succeeded on the checkout .venv through the author's own picker path."
  ],
  "evidence": [
    {
      "label": "Surface definition",
      "path": "docs/rse/ops/jupyter-surface.md",
      "sha256": "dbaef59f2fba72638ce22f98a3cb8ebeac65e39047c70d4a4bb52cb3d81865b4"
    },
    {
      "label": "Admission receipts: smoke test and workbench pilot, 2026-08-06",
      "path": "docs/rse/wayfinder/tickets/jupyter-surface-admission-receipts-20260806.md",
      "sha256": "d33038b8a2887e3e22435b0328f0d4432b180349c123dff077049646ce0c0e42"
    }
  ],
  "effect": "Ratification lets agents start and stop a kernel for bounded local work under the definition; rejection leaves the surface unadmitted.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/jupyter-surface-admission-2026-08-05.md",
    "action": "Record the decision and its receipt on this ticket and update the ticket status. On ratify only, also update the standing admission state in AGENTS.md and CLAUDE.md (the 'defined, not yet owner-ratified' lines) in the same change, or the granted kernel-start permission stays inert; on defer or reject, leave the standing state unchanged."
  },
  "priority": 40
}
```

## Question

[Choose operational ownership for paused services](authority-10-choose-operational-ownership.md)
was ratified on 2026-07-20 and found that this repository owns no Jupyter
environment, lock, kernel, notebook, output policy, port, or restart command.
It set the admission bar for any future Jupyter surface, requiring a
repository-owned definition that names the environment and lock, the kernel
specification, the notebooks, the data mounts, the generated-output policy, the
bind address and port, the start and stop commands, the owner, and the recovery
procedure, and requiring a local kernel smoke test before admission. This
ticket exists to satisfy that admission bar. It is governed by authority-10; it
does not wait on it.

The owner is asked to decide two things once the evidence below exists.

First, does the proposed material satisfy the admission bar in full? Every
element listed above must be named in the repository rather than inferred, and
the smoke test must be a real kernel round trip rather than an import check.

Second, if it does, is the Jupyter surface thereby admitted as a
repository-owned operational surface, so that agents may start and stop a
kernel for bounded local work under the definition's own start, stop, and
recovery instructions?

The surface being proposed is **kernel-only**. There is no persistent Jupyter
server, no externally exposed browser port, and no user-level kernel
specification installed outside the repository. An editor or workbench selects
the worktree's own interpreter directly, and each kernel launch allocates its
own loopback ZeroMQ ports. That is how a kernel-only surface answers
authority-10's "bind address and port" element, and it is deliberately narrower
than what that finding anticipated. A JupyterLab or notebook server, which
would bind a fixed port and could be exposed, is a separate and later
admission that this ticket neither requests nor grants.

A negative answer on either part leaves the surface unadmitted and leaves
authority-10's finding in force unchanged.

## Evidence

The artifacts the owner is being asked to judge are these.

- [`docs/rse/ops/jupyter-surface.md`](../../ops/jupyter-surface.md) — the
  repository-owned surface definition, which is where every element authority-10
  requires must be named.
- The `notebook` dependency group in
  [`pyproject.toml`](../../../../pyproject.toml), supplying `ipykernel`,
  `jupyter-client`, and `jupytext`, together with its resolved entries in
  [`uv.lock`](../../../../uv.lock) — the environment and lock half of the
  requirement.
- [`tests/test_jupyter_surface.py`](../../../../tests/test_jupyter_surface.py)
  — the local kernel smoke test, run through `make test-notebook`, which starts
  a kernel from the declared specification, executes a cell, and reads the
  result back.
- [`docs/rse/ops/live-analysis.md`](../../ops/live-analysis.md) — the
  interactive analysis workflow the surface exists to serve, which is the
  reason to admit a kernel at all rather than continue without one.

All four artifacts are on `main` (merged in the minimal live-analysis surface
consolidation, pull request #256), so the links above resolve and promotion
conditions 1 and 2 below hold. Conditions 3 and 4 were discharged on
2026-08-06 under the bounded pre-admission pilot authorized below; the machine,
versions, commands, exit status, and the owner-run workbench cell (including
the first attempt's stale-kernelspec failure and its repair) are recorded in
[the attached admission receipts](jupyter-surface-admission-receipts-20260806.md).

## Promotion condition

This ticket moves to `Status: open` and `Triage: ready-for-human`, and the
owner's decision becomes live, only when all four of the following hold.

1. The `notebook` dependency group — `ipykernel`, `jupyter-client`, and
   `jupytext` — is merged and resolved in `uv.lock`.
2. `docs/rse/ops/jupyter-surface.md` is merged.
3. `make test-notebook` has been run locally and its output attached to this
   ticket, naming the machine, the Python and `ipykernel` versions, the
   command, and its exit status.
4. At least one real workbench session has selected the checkout interpreter
   and run a cell against it, confirming that the kernel is reachable the way
   an author would actually reach it and not only from the test harness.
   (Clarified 2026-08-06: "worktree interpreter" in earlier wording means the
   interpreter of the checkout the session runs against — the canonical
   checkout's `.venv` here, since the surface definition uses "worktree" for
   whichever checkout hosts the session, and per-session git worktrees with
   their own environments arrive only with the launcher this ticket's sibling
   pull request introduces. The attached receipt records the canonical
   checkout's interpreter.)

Conditions 3 and 4 are hereby explicitly authorized as a bounded
pre-admission pilot: the owner, or an agent acting on the owner's direct
instruction in an interactive session, may run `make test-notebook` and one
workbench cell against the checkout interpreter solely to produce these
receipts. This is a narrow, single-purpose exception to the prohibition in
"Until this is resolved" below; it grants no other kernel use, and its scope
ends when the receipts are recorded on this ticket.

Only then does the owner ratify or reject. Until all four hold, this ticket is
agent work, not an owner decision, and it should not be surfaced on the owner
queue.

Promotion was completed on 2026-08-06: all four conditions hold, the receipts
are attached, and the decision card above was refreshed in the same change
(recommendation, context, and evidence, within the validator's three-entry
evidence limit). The card now reflects the post-promotion state; no further
promotion handling applies. What remains is solely the owner's decision,
recorded per the card's recorder instructions.

## What is not being asked

- This ticket does not amend, reopen, or reinterpret authority-10. That ticket
  is resolved and owner-ratified, and its findings on MkDocs, Running Notes,
  the public edge, and the restart, redeployment, and retirement receipts are
  untouched by whatever is decided here.
- It does not authorize any public deployment. Kernel transports are loopback
  and per-launch, and no browser-facing port is opened. Publishing any Jupyter
  surface outward remains governed by authority-10's separate
  outward-authorization requirement.
- It does not change the notebook-tracking policy. Whether notebooks are
  tracked as `.ipynb`, as paired text through `jupytext`, or not tracked at
  all, is decided in its own separate change and is not bundled into this
  admission.
- It does not advance the parent manuscript repository's `analysis/` submodule
  pointer. A pin change is a separately scoped, verified step and never a side
  effect of admitting an operational surface.

## Resolution state

Ratified 2026-08-07. Authority-10's admission bar is satisfied and the
kernel-only surface is admitted: agents may start and stop a kernel for
bounded local work under `docs/rse/ops/jupyter-surface.md`'s own start, stop,
and recovery instructions. The standing admission state in `AGENTS.md`,
`CLAUDE.md`, and the surface definition's Status section was updated in the
same change, per the card's recorder instructions. A JupyterLab or notebook
server remains a separate, later admission.
