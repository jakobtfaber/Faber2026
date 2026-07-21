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
- Google Drive is the recorded processed-data authority; iacobus holds a dated
  recovery copy. Full MD5 comparison passes for all 5,437 project-data paths.
  Strict object parity still fails because Drive has one identical same-name
  duplicate and iacobus has one local recovery receipt.
- CANFAR is authority for the 24 derived fit-input cubes. The twelve raw CHIME
  HDF5 files on h17 remain unclassified pending a checksum-manifested archive.
- GitHub `main` governs result claims; Drive governs receipted bulk result
  bytes. The local `results-library` becomes their replica/navigation view only
  after its eight broken links and other inventory conflicts are repaired.
- h17 has grown and drifted; h23's recorded quarantine is unexpectedly missing;
  CANFAR read-only VOSpace access is live and verified through 2026-08-20.
- Jupyter and MkDocs are stopped and port 8000 is closed. Running Notes is a
  separate launchd service and remains live on loopback port 18765; its public
  edge is unverified. Ownership is in scope; runtime changes are not.
- The only stated immediate-removal candidates are empty `faber_build`
  directories. They still require fresh emptiness, process, and reference proof.

## Decisions so far

<!-- one linked gist per resolved ticket; decision detail stays in the ticket -->

- [Define authority roles and their required proof](tickets/authority-01-define-authority-roles-and-proof.md)
  — roles attach singly to exact scoped surfaces; authority requires an
  owner-ratified immutable identity, all uncertainty fails closed, and
  verification, preservation, and consolidation safety have distinct proofs.
- [Choose the code and manuscript authority policy](tickets/authority-08-choose-code-manuscript-authority.md)
  — GitHub `main` governs manuscript history and the reproducibility pin,
  FLITS fork `main` governs fitting code, and every working-copy return requires
  a scoped reviewed receipt; Overleaf and dirty fitting lanes remain fail-closed.
- [Choose operational ownership for paused services](tickets/authority-10-choose-operational-ownership.md)
  — Jupyter remains unclassified, MkDocs source is repository-owned but its
  environment is not, and persistent Running Notes has separate source,
  mutable-state, submission, and public-edge gates with explicit receipts.
- [Restore CANFAR read-only verification access](tickets/authority-05-restore-canfar-read-access.md)
  — a renewed CADC certificate passed a live, authenticated, non-recursive
  listing of the project VOSpace root and remains valid through 2026-08-20.
- [Reconcile local data and results custody](tickets/authority-04-reconcile-local-data-and-results.md)
  — local instrument custody is split correctly, but the registry/library
  relationship is unreconciled; eight stale worktree links and current CHIME
  path authorities require a gated repair rather than data recovery.
- [Classify worktrees, scratch clones, and preservation packets](tickets/authority-03-classify-worktrees-and-preservation-packets.md)
  — the estate mixes registered worktrees, bare rewrite repositories,
  preservation packets, and ordinary directories; most carry unique or
  unverified material, and none is deletion-approved.
- [Reconcile the code and manuscript truth surfaces](tickets/authority-02-reconcile-code-and-manuscript-surfaces.md)
  — GitHub commit and manuscript pin authority were precise at observation,
  but distributed dirt/commits remain; Overleaf is a clean, history-orphaned
  content source with 89 changed common paths, not a behind replica.
- [Reverify remote and institutional custody](tickets/authority-06-reverify-remote-custody.md)
  — Drive and the dated iacobus recovery quarantine agree in size/count and a
  sentinel but lack current full parity; h17 growth is compute drift, HPCC is
  intact, h23's recorded quarantine is missing, and CANFAR is unverified.
- [Inventory operational and publication surfaces](tickets/authority-07-inventory-operational-surfaces.md)
  — Jupyter and MkDocs are stopped and lack pinned/reproducible runtime
  ownership; Running Notes remains live on port 18765 under its tracked launch
  agent, while the public Cloudflare edge remains unverified.
- [Trace the missing h23 quarantine](tickets/authority-14-trace-missing-h23-quarantine.md)
  — last verified July 6, then absent without a move/deletion receipt; migrated
  classes largely survive downstream, but exact-byte custody of the vanished
  137 GB tree remains unproved.
- [Complete Drive-to-iacobus parity and duplicate adjudication](tickets/authority-15-complete-drive-iacobus-parity.md)
  — all 5,437 project-data paths match by MD5; the local recovery receipt and
  byte-identical duplicate Drive object explain why content parity passes while
  strict one-to-one object parity fails.
- [Choose the data and results authority policy](tickets/authority-09-choose-data-results-authority.md)
  — Git governs claims, Drive governs receipted bulk bytes, CANFAR governs the
  24 fit-input cubes, and local/h17 surfaces remain replicas, working copies,
  staging, or unclassified until explicit promotion gates pass.
- [Ratify preservation gates and the consolidation sequence](tickets/authority-11-ratify-preservation-and-consolidation-gates.md)
  — every action requires an exact packet, recovery and rollback proof, an
  exclusive scope lock, and a verified phase barrier; preserve at-risk states
  before merging, relinking, retiring, or separately approved removal.

## Not yet specified

- Exact source-to-destination moves, reference rewrites, and checksum receipts
  for each approved preservation class.
- Publication path for the dirty JointTF fitting code and evidence on h17,
  after local/remote ownership and landed-commit equivalence are established.
- Per-worktree merge, archive, or removal actions after every unique change and
  concurrent owner has been identified.

## Out of scope

- Restarting the Jupyter kernel, MkDocs server, launch agents, or port 8000.
- Adopting component counts, rewriting manuscript science, or launching new
  JointTF fits; those remain under their scientific validation and owner gates.
- Indiscriminate worktree, scratch, branch, cache, or quarantine cleanup.
- Adjacent projects such as `gpu-ffa`, `dsa110-continuum`, Faber2024, and
  Faber2025 except where a shared directory must be excluded from this map.
