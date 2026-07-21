# Define authority roles and their required proof

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-human`

## Question

Which exact roles may the project assign to a surface—authority, replica,
working copy, staging area, quarantine, preservation packet, or retired
source—and what minimum evidence is required before assigning or changing each
role? Resolve precedence when Git state, filesystem bytes, host inventories,
and manuscript references disagree. Define what “verified,” “preserved,” and
“safe to consolidate” mean without treating existence or a clean status as
sufficient proof.

## Answer

Owner-ratified 2026-07-20.

### Assignment rule

A role attaches to a **scoped surface**: content class, host or repository,
path or ref, and observed revision or time. Never assign one role to a mixed
directory wholesale. Each scoped surface has exactly one role at an observation
time from this closed set: authority, replica, working copy, staging area,
quarantine, preservation packet, retired source, or unclassified.

`Unclassified` is the fail-closed default. It implies neither authority,
preservation, safety, nor permission to remove. `At risk` is a qualifier, not a
second role; it marks an authority with no independent verified recovery copy.

Every non-default assignment or role change requires a role receipt recording
the exact scope, role, owner or custodian, observation time, immutable identity
where available, evidence pointers, prior role, and reason for the change.

### Roles and minimum proof

- **Authority** — sole surface allowed to settle conflicts for its scoped
  content class. Requires explicit owner designation, live readable access, an
  immutable identity (commit, checksum manifest, or equivalent), producing
  provenance, and no unresolved competing authority claim. A replica is not
  required for designation; absence makes the authority `at risk`.
- **Replica** — verified content-equivalent copy of a named authority; never a
  conflict resolver. Requires the authority identity, completed comparison,
  file or object counts plus checksums where possible, comparison tool and
  time, and a live readability check. Partial or drifting copies are not
  replicas.
- **Working copy** — mutable descendant used for active editing. Requires a
  named authority or base identity, current owner or agent, and an inventory of
  branch/ref, dirty state, unpushed commits, and unique files. Cleanliness does
  not promote it.
- **Staging area** — bounded temporary transfer or assembly surface. Requires
  intended source and destination, exact target list, current transfer state,
  owner, and a next action or expiry. An incomplete transfer remains staging.
- **Quarantine** — isolated surface with unresolved trust, provenance, safety,
  or disposition. Requires the quarantine reason, exact inventory, known
  origin, isolation from normal consumption, owner, and release gate.
  Quarantine never implies permission to delete.
- **Preservation packet** — immutable, self-describing recovery artifact for an
  exact state. Requires source identity; manifest and checksums; Git dirt,
  untracked-file, submodule, and large-file metadata where relevant; recovery
  instructions; custody location; and an independent read or restore spot
  check.
- **Retired source** — retained surface no longer used as authority or input.
  Requires exact identity, owner ratification, a named successor or explicit
  no-successor decision, disposition of active references, and a retention or
  later-disposal policy. Retirement is not removal.
- **Unclassified** — evidence is insufficient for another role. Only the exact
  scope and observation record are required; it grants no positive inference.

### Conflict precedence

The valid authority receipt for the exact scoped identity settles content
conflicts. A stale receipt or identity mismatch is not valid. If no candidate
has a valid receipt, candidates remain unclassified or quarantined until the
owner ratifies one; no automatic winner exists.

Evidence types answer different questions and do not substitute for authority:

- Git history and status show ancestry, commits, and local changes.
- Filesystem checksums show byte equivalence.
- Host inventories show presence, counts, and custody observations.
- Manuscript references show consumption dependencies.

Newness, cleanliness, size, completeness, publication, or being referenced in
the manuscript never grants authority by itself. Contradictory evidence stops
promotion, consolidation, retirement, and removal until reconciled.

### Proof words

- **Verified** means one stated claim was checked against named live evidence,
  using a recorded method and time. It is claim-specific and expires when the
  relevant state changes. It does not imply scientific trust.
- **Preserved** means the exact scoped state has an independently readable,
  integrity-checked recovery copy, a custody receipt, and a tested recovery
  path. Existence or a started copy is insufficient. Preservation does not
  authorize removal.
- **Safe to consolidate** means an exact action and target list have ratified
  authority roles, an independent recovery and rollback path, ownership
  clearance, reference and active-process/agent checks, destination readiness,
  and post-action verification. Unresolved science, active agents, detached
  fitting evidence, or ambiguous `scratch/2026-07` content fails this test.
