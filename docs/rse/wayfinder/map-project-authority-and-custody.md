<!-- wayfinder:map -->
# Map: Establish project authority and custody before consolidation

Tickets live in [`tickets/`](tickets/). This is a planning-only map. It does
not authorize deletion, movement, branch removal, service restart, or
scientific adoption.

## Destination

Every Faber2026 code, manuscript, data, result, evidence, and operational
surface has one ratified role: authority, replica, working copy, staging area,
quarantine, preservation packet, or retired source. The evidence and owner
gates for preservation and consolidation are explicit by class, so execution
can proceed without losing science, provenance, or concurrent work.

## Notes

- Use `/wayfinder`, `/grilling`, and `/domain-modeling`; refer to every ticket
  by its linked name.
- Evidence first. Live state outranks inherited inventories. Record timestamps,
  host/path identity, Git identity, hashes or parity evidence, and access gaps.
- A preservation directory is not a Git worktree merely because its name says
  `worktree`. Classify registration, parent repository, branch, commit, dirt,
  unique files, and active ownership separately.
- Preserve all dirty or ambiguous lanes. Nothing under
  `~/Developer/scratch/2026-07/` is deletion-approved.
- `flits-joint-tf-fits` and h17 `/home/ubuntu/worktrees/joint-tf-fits` are
  directly relevant to the fitting audit and remain fail-closed.
- GitHub, the canonical Mac checkout, `pipeline/`, and the independent Overleaf
  checkout are separate truth surfaces until their relationship is ratified.
- Google Drive is the recorded processed-data authority; iacobus currently
  holds a verified 244 GB quarantine/staging copy after transfer. Reverify
  before changing either role.
- Local `results-library` currently has eight broken links. Treat the registry
  as claim-level and the library as byte-level only after live reconciliation.
- h17 has grown and drifted; h23's recorded quarantine is unexpectedly missing;
  CANFAR is presently unverifiable because its certificate expired.
- Jupyter and MkDocs are stopped. Port 8000 is closed. Their code, services,
  and future restart state are in scope for ownership; restarting them is not.
- The only stated immediate-removal candidates are empty `faber_build`
  directories. They still require fresh emptiness, process, and reference proof.

## Decisions so far

<!-- one linked gist per resolved ticket; decision detail stays in the ticket -->

## Not yet specified

- Exact source-to-destination moves, reference rewrites, and checksum receipts
  for each approved preservation class.
- Exact repair batches for the eight broken results-library links and obsolete
  CHIME paths, after their intended authorities are chosen.
- Publication path for the dirty JointTF fitting code and evidence on h17,
  after local/remote ownership and landed-commit equivalence are established.
- Final disposition of the missing h23 quarantine and the completeness claim
  for Google Drive versus iacobus, after live custody research.
- Per-worktree merge, archive, or removal actions after every unique change and
  concurrent owner has been identified.

## Out of scope

- Restarting the Jupyter kernel, MkDocs server, launch agents, or port 8000.
- Adopting component counts, rewriting manuscript science, or launching new
  JointTF fits; those remain under their scientific validation and owner gates.
- Indiscriminate worktree, scratch, branch, cache, or quarantine cleanup.
- Adjacent projects such as `gpu-ffa`, `dsa110-continuum`, Faber2024, and
  Faber2025 except where a shared directory must be excluded from this map.
