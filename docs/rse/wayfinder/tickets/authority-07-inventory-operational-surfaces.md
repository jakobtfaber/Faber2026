# Inventory operational and publication surfaces

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-agent`

## Question

Which repository files, environments, processes, launch agents, ports, and
published assets define the Jupyter and MkDocs/running-notes surfaces? Confirm
their stopped state, identify their source and generated outputs, and map every
restart or deployment dependency. Include the public site only as a publication
surface. Do not start services, bind ports, deploy, or change launch agents.

## Answer

Resolved by
[`Research: Authority of operational surfaces`](../../specs/research/research-authority-operational-surfaces-2026-07-20.md).

Jupyter and MkDocs are stopped and port 8000 is closed. MkDocs source lives
under `docs/analysis/`, but its external environment is not pinned and its
default generated site is absent. No repository-owned Jupyter configuration,
kernel, environment, notebook, export, or restart chain was found; the former
kernel was ad hoc and is not reproducible from this repo.

Running Notes is a separate surface and is **not stopped**: launchd runs the
tracked standard-library server on loopback port 18765, and the installed
property list matches the tracked template. The local Cloudflare orchestrator
also runs and routes the public hostname to that origin, but public Domain Name
System, Access, authentication, and end-to-end reachability were not verified.
No runtime was changed.
