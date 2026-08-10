# Receipt: Phase 4 — Preservation-Artifact Termination (2026-07-25)

**Objective/phase:** Phase 4 of
`plan-scattered-work-integration-and-retirement.md`.
**Decision:** terminal home = `~/Data/Faber2026/preservation/` (plan
option (a)), chosen by Codex recommendation under the owner's standing
follow-Codex directive for phases 2–4. Layout-rule amendment recorded in
project memory (`faber2026-consolidation-target-layout`): the
subtree holds immutable preservation material only — bundles, manifests,
checksums, receipts, rescue captures; never working checkouts or routine
analysis output.

## Examination of the previously unexamined directory

`Faber2026-science-gates-20260722` (780 MB) is **self-provenanced and
verified**, not opaque: its own `PROVENANCE.md` records a 2026-07-22
science-gates worktree preservation (parent `ms/science-gates-g1a-20260715`
@ `6889effc`, pipeline `ms/g1a-july-morphology-parity` @ `11403e6c`, two
nested agent branches, four remote rescue refs) and its `SHA256SUMS`
verifies 7/7 OK. Classification: preservation artifact, moved as-is.

## Bundle re-verification (from inside source repos)

- FLITS `unreferenced-commits.bundle`: `git bundle verify` — complete
  history; sha256
  `3933b486184b08675a20a7a3f7d1b5468c0953b8a5b1ee232b73ba979060a8a6`
  (exact match to the handoff record).
- Overleaf `overleaf-comprehensive-preservation.bundle`: `git bundle
  verify` from `~/Developer/overleaf/Faber2026` — OK (one prerequisite,
  present in that repo); size 78,223,987 bytes (exact match); sha256
  **established this session**:
  `ae6fa3a0d7fbf49688488542838dc2e9ac6ee500eb40089e3ee5ad8ea669e376`.

## Moves (manifest-first, atomic, originals untouched)

Method: per source — sorted sha256 manifest of every regular file +
symlink inventory → `rsync -a` to `<dest>.partial` → destination manifest
→ `diff` (must be empty) → atomic `mv`. Free-space preflight: 66 GiB free
vs ~10.6 GB moved. All six passed with empty manifest diffs:

| Source | Files | Destination |
|---|---|---|
| `~/Developer/scratch/preservation/dsa110-FLITS-unreferenced-20260725` | 11 | `~/Data/Faber2026/preservation/…` |
| `~/Developer/scratch/preservation/Faber2026-overleaf-20260725` | 107 | 〃 |
| `~/Developer/scratch/preservation/Faber2026-science-gates-20260722` | 8 | 〃 |
| `/Volumes/ArtifexBackupDrive/Faber2026-preserved-bundles` | 138 | 〃 |
| `/Volumes/ArtifexBackupDrive/Faber2026-preserved-bags` | 21 | 〃 |
| `/Volumes/ArtifexBackupDrive/Faber2026-rescue-20260725-v2` | 221 | 〃 |

All src/dst manifests preserved at
`~/Data/Faber2026/preservation/_manifests-20260725/` (24 files). Both
bundles re-hashed **at the destination** post-move: identical to the
source hashes above.

**Originals are untouched** at their source paths — their removal is
Phase 5 Track B, per candidate, with owner approval naming each path.

## Scope notes

- Live registered worktrees and working checkouts were not copied as
  preservation material. The
  preserved-checkouts tree's disposition belongs to Phase 5 Track A after
  reconciliation assigns authority statuses.
- The 10 known-empty slots inside `Faber2026-preserved-bundles` moved
  as-is; their recovery map lives in the worktree-inventory banner.
