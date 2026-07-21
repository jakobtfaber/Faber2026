# Validation Complete

> Validated against `docs/rse/specs/plan-h17-source-data-layout.md` /
> `docs/rse/specs/implement-h17-source-data-layout.md` at implementation commit
> `7d2528d` on 2026-07-21.

## Overall Status: Ready

## Summary

- Phases: 4 of 4 implemented.
- Automated checks: 10 passing, 0 failing.
- Manual testing: 1 owner science-trust review remains.
- Critical issues: 0.
- Important issues: 1 future-reuse guardrail.

## Implementation Status

### Phase 1: Freeze the allowlist and preflight

**Status:** Fully implemented

- Twelve unique project records and 24 unique typed paths are tested.
- Read-only preflight proved 24 sources, zero targets, device 2049, zero open
  handles, and complete hashes before mutation.

### Phase 2: Move and verify bytes

**Status:** Fully implemented

- Exactly 24 allowlisted files were renamed on the same filesystem.
- The receipt contains matching pre/post size, SHA-256, device, inode, and
  modification time for every file.
- Three excluded files remain unchanged.
- `/data` mount semantics prevent the planned per-directory ownership/mode;
  this is documented and does not affect byte identity.

### Phase 3: Update authorities and consumers

**Status:** Fully implemented

- Parent certificates and paired manifest use project-scoped paths.
- Pipeline PRs #214 and #215 are merged; the parent pins merged commit
  `d0d1e278766de4ac97af0765b7d7c58fa0fbdfbc`.
- Primary and all nineteen promoted worker/diagnostic consumers use the new
  source tree.
- Historical evidence retains the paths used when produced.

### Phase 4: Closeout

**Status:** Fully implemented

- Zach metadata-only reads succeeded for DSA-110 and CHIME/FRB.
- Final h17 verification, knowledge-base refresh, both closeout gates, and the
  task-scoped implementation commit completed.

## Automated Verification Results

### Passing checks

- `python3 scripts/h17_source_data_layout.py verify ...` — 24/24 verified,
  zero old canonical paths, 3/3 exclusions preserved.
- Parent `pytest -q tests/test_h17_source_data_layout.py` — 7 passed.
- Pipeline `pytest -q tests/test_h17_source_data_layout.py tests/test_data_manifest.py`
  — 5 passed.
- `python3 -m compileall -q scripts/h17_codetections` — passed.
- Receipt/paired-manifest invariant check — passed.
- `git check-ignore -v data/test.fil` — `.gitignore:20:/data/`.
- Fail-closed active-reference search — no retired flat source root found.
- Pipeline PR #214 Python 3.12 and Socket checks — passed.
- Pipeline PR #215 Python 3.12 and Socket checks — passed.
- `make kb-index` — full build completed; final incremental pass embedded
  48/48 changed chunks.
- Parent and pipeline `agent-closeout-check` — passed.

No automated verification check failed.

## Code Review Findings

### What matches the plan

- Hardcoded allowlist, collision checks, open-handle checks, same-device guard,
  no-clobber renames, rollback, post-hash verification, exclusions, manifests,
  burst-scoped consumers, tests, and documentation are present.
- `.gitignore` remains unchanged because the existing rule is sufficient.
- No compatibility symlink or derived-product move was introduced.

### Deviations from plan

1. The `fuseblk` mount reports fixed `root:root 0777`; requested
   `ubuntu:ubuntu 2775` metadata is not representable. Acceptable for this move;
   documented in the implementation and metadata receipt.
2. Pre-move hashes were held in memory and embedded in the final verified
   receipt, not persisted as a separate file before rename. Custody is closed
   by repeated post-move verification, but this is a future-reuse weakness.
3. The broad search found nineteen additional promoted workers after the first
   pipeline PR. A second focused PR updated and tested all of them. Acceptable;
   the desired final state is met.

### Potential issues

- `scripts/h17_source_data_layout.py`: a future migration run should persist
  its preflight hash payload before the first rename. Do not reuse the mutation
  path until that guardrail is added.

## Manual Testing Required

1. **Owner source-layer spot-check**
   - Review `source-manifest.json` and `zach-metadata-readability.json`.
   - Confirm the twelve directory names and the observed Zach header fields.
   - Expected outcome: owner accepts custody evidence while leaving applied
     DSA dispersion measure, CHIME voltage processing history, and exact time
     axis pending the square-one producer audit.

## Recommendations

### Critical

- None.

### Important

- Before any future data move with this tool, persist the preflight hashes to a
  durable local and remote manifest before mutation.

### Nice to have

- None for this bounded migration.

### Follow-up work

- Perform the owner spot-check.
- Continue the square-one Zach audit: applied DSA dispersion measure, CHIME
  voltage processing history, time-axis semantics, and source resolutions.
- Only then begin dispersion-measure fitting and later analyses.

## References

- Plan: [plan-h17-source-data-layout.md](plan-h17-source-data-layout.md)
- Implementation: [implement-h17-source-data-layout.md](implement-h17-source-data-layout.md)

Would you like me to fix the future-reuse guardrail, provide more detail on a
finding, or run an additional verification check?
