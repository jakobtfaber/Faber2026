# Ratify preservation gates and the consolidation sequence

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: [Classify worktrees, scratch clones, and preservation packets](authority-03-classify-worktrees-and-preservation-packets.md), [Choose the code and manuscript authority policy](authority-08-choose-code-manuscript-authority.md), [Choose the data and results authority policy](authority-09-choose-data-results-authority.md), [Choose operational ownership for paused services](authority-10-choose-operational-ownership.md)
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-human`

## Question

What evidence packet, rollback path, ownership clearance, and authority receipt
must exist before each class may be preserved, merged, relinked, moved,
archived, retired, or removed? Choose the class order and concurrency rules.
Require exact target lists and exclude unresolved science, active agents,
detached fitting evidence, and all ambiguous `scratch/2026-07` content.

## Answer

Owner-ratified 2026-07-20.

### Universal action packet

Every preservation or consolidation action requires one immutable packet tied
to its exact target list and operation. The packet records:

- exact source and destination paths, hosts, repositories, refs, roles, and
  observation time;
- complete target and exclusion lists;
- source identity: commits and Git dirt, untracked/ignored files, submodules,
  or byte manifests and checksums;
- named owner/custodian plus fresh agent, process, scheduler, mount, and
  open-file checks;
- destination authority receipt and readiness proof;
- independent recovery copy and tested restore path;
- current code, manuscript, link, service, and external-consumer references;
- exact proposed commands, dry-run evidence, expected changes, and blast radius;
- exact rollback procedure and rollback verification;
- post-action counts, hashes, Git state, references, runtime state, and summary;
  and
- explicit stops for drift, unexpected content, ownership change, failed
  parity, or concurrent activity.

The packet authorizes only its named action and scope. Everything else remains
excluded.

### Action-specific gates

- **Preserve:** leave the source untouched; complete manifest and checksums;
  independent custody; successful read or restore spot-check.
- **Merge:** known base and owner; focused reviewed pull request; required
  tests/build/visual checks; no unrelated paths or implicit pipeline-pin
  change; resulting merge receipt.
- **Relink:** stable authority/result ID; exact old/new targets; dry run; every
  target resolves; consumers pass; reversible link manifest retained.
- **Move:** copy first; verify full parity; switch references; verify consumers;
  then quarantine the former source. Never destructively move across authority
  boundaries.
- **Archive:** immutable manifest, checksums, provenance, recovery instructions,
  custodian, retention rule, and restore spot-check.
- **Retire:** named successor or explicit no-successor decision; active
  references removed; owner ratification; retention and restoration policy.
- **Remove:** separate explicit owner approval after all other gates; fresh
  no-agent/process/reference proof; verified recovery; exact deletion list;
  recoverable removal where possible; post-removal verification.
- **Restart/redeploy:** use the separately ratified restart receipt. Never
  combine operational changes with file consolidation.
- **Scientific adoption:** use claim promotion. Never bundle scientific trust
  with byte movement or code merging.

### Consolidation sequence

1. **Refresh control evidence:** inventories, owners, active work, authority
   identities, and exact packets. No mutations.
2. **Preserve at-risk states:** copy-only preservation of unique dirty
   worktrees, detached evidence, raw HDF5 files, ambiguous scratch content, and
   active handoffs; verify recovery.
3. **Return code/manuscript work to authority:** focused reviewed merges,
   pipeline-pin decisions, and Overleaf reconciliation. Scientifically
   unresolved JointTF material remains preserved and unmerged.
4. **Repair data/results navigation:** execute the separately approved
   results-library and current CHIME-path repair; establish stable IDs, Drive
   byte authority, and verified local replicas.
5. **Archive or retire superseded sources:** only after references point to
   verified successors and restoration succeeds.
6. **Remove approved remnants:** smallest, lowest-risk targets first, beginning
   only with freshly proven empty build directories; every removal remains
   separately owner-approved.

Operational service changes and scientific adoption remain outside this
sequence.

### Concurrency and stop rules

One writer may hold an exact authority ref, directory tree, result scope,
Overleaf reconciliation, or service state. Read-only inventories and reviews
may run in parallel. Copy-only preservation may run concurrently only for
disjoint sources, destinations, owners, and resource budgets. Merge, relink,
move, archive, retire, remove, restart, and rollback actions are exclusive
within their affected scope.

No mutation may run while an agent, process, scheduler job, notebook, service,
mount, or collaborator owns the target. Each sequence stage has a barrier: all
manifests, verification, receipts, and exceptions close before the next stage.
Any changed checksum, count, Git identity, ownership, reference set, or runtime
state invalidates the packet and stops execution.

Partial failure leaves both copies intact, freezes reference changes, and
places the target in quarantine or unclassified status. JointTF, detached
fitting evidence, dirty scientific lanes, and ambiguous `scratch/2026-07`
content remain fail-closed. Force-push, shared-history rewrite, blanket cleanup,
wildcard removal, and concurrent forward/rollback execution are forbidden.
