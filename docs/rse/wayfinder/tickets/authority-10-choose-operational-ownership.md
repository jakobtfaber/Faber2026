# Choose operational ownership for paused services

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: [Define authority roles and their required proof](authority-01-define-authority-roles-and-proof.md), [Inventory operational and publication surfaces](authority-07-inventory-operational-surfaces.md)
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-human`

## Question

Which repo files and environments own the Jupyter and MkDocs/running-notes
surfaces, which generated outputs are preserved, and what explicit evidence is
required before an agent may restart, redeploy, or retire them? Record the
current stopped state without treating it as abandonment or cleanup approval.

## Answer

Owner-ratified 2026-07-20. All recommendations were accepted together.

### Observed state

Read-only verification at `2026-07-20T19:31:09-07:00` found:

- Jupyter stopped; no process or port-8000 listener; no executable in the
  current agent environment.
- MkDocs stopped; no process or port-8000 listener; no executable in the
  current agent environment.
- Running Notes running under launchd at `127.0.0.1:18765`, PID 1015; the
  installed property list was byte-identical to the tracked template.
- The Cloudflare orchestrator tunnel running separately, PID 1040.
- `claude` absent from the current agent environment; submission health remains
  unverified even though the local HTTP origin is live.

This observation grants no restart, deployment, retirement, or cleanup
authorization.

### Default operating state

Jupyter and MkDocs remain stopped-by-default and may run only for bounded work.
Running Notes is the intended persistent launch-agent service. Cloudflare is a
separate publication dependency. A stopped service is paused, not abandoned.

### Jupyter

The former ad hoc Jupyter runtime is unclassified, not retired. The repository
currently owns no Jupyter environment, lock, kernel, notebook, output policy,
port, or restart command. Agents must not reconstruct it from shell history.

Any future Jupyter surface requires a repository-owned definition naming the
environment and lock, kernel specification, notebooks, data mounts,
generated-output policy, bind address and port, start/stop commands, owner, and
recovery procedure. Admission requires a local kernel smoke test.

### MkDocs

Faber2026 GitHub `main` under `docs/analysis/` owns MkDocs source. The external
MkDocs/Material environment is unclassified and currently blocks reproducible
restart. The absent default `site/` directory is rebuildable output, not
preserved authority.

Restart requires source identity, pinned MkDocs/Material dependencies,
executable and version proof, port-availability check, explicit bind address,
successful clean build, local page smoke test, and generated-output
disposition. Starting a preview never authorizes public deployment.

### Running Notes

Faber2026 GitHub `main` owns `scripts/running_notes.py`, `index.html`,
`pulse.json`, the launch-agent template, and the state-file policy. A matching
installed property list is a replica. The process and listener are operational
state, not authority.

Inbox notes, Claude logs, and `status.json` are local working state. Non-empty
pending or error state must be preserved before disruptive restart or
retirement. Dispositions become authoritative only after reviewed Git merge.
`.gitignore` never establishes disposability.

Submission must use Claude Code subscription authentication through headless
`claude -p` with standard input closed. An Anthropic API workflow is forbidden
as a substitute. Health requires executable resolution, subscription
authentication, and a harmless live dry-run; HTTP origin health alone is
insufficient.

### Public edge

Faber2026 owns only the public-hostname-to-local-origin contract.
Maistro/dotfiles owns tunnel configuration; Cloudflare owns Domain Name System
and Access policy. A local-origin restart must not mutate the tunnel. Public
redeployment requires explicit outward authorization plus live hostname,
authentication, and access-denial checks.

### Restart, redeployment, and retirement proof

Every change requires a restart receipt containing:

- exact source commit and configuration hashes;
- environment and tool versions;
- mutable-state inventory and preservation;
- executor, owner authorization, and time;
- pre/post process and port state;
- local health test;
- submission handshake when applicable;
- public-edge test when applicable;
- rollback command and rollback verification.

Retirement additionally requires preserved state, reference removal,
launch-agent and tunnel disposition, verified shutdown, and a tested restoration
path. Retirement never implies deletion.
