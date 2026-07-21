# Validation Complete

> Validated against `plan-results-library-chime-path-repair.md` and
> `implement-results-library-chime-path-repair.md` at parent base commit
> `74b7dd6d` with pipeline commit `ded8d195` on 2026-07-20.

## Overall Status: Ready

## Summary

- Phases: 5 of 5 implemented.
- Automated checks: 8 passing, 0 unexpected failures.
- Manual testing: none required.
- Critical issues: 0.
- Important issues: 0.

## Implementation Status

### Phase 1: Exact library mechanics

**Status:** Fully implemented.

- Nested destinations, exact unique selection, broken-link handling, real-real
  conflict protection, deterministic manifests, and receipts are tested.
- Final builder dry-run covers 18 entries without writing.
- Materializer dry-run exits fail-closed on exactly the two excluded both-real
  conflicts.

### Phase 2: Parent full-resolution roots

**Status:** Fully implemented.

- All approved current parent callers expose separate CHIME/FRB and DSA-110
  roots.
- Current joint-DM runner added; historical snapshot and provenance unchanged.
- L0 regeneration produces the identical 36-row certificate file.

### Phase 3: Pipeline full-resolution roots

**Status:** Fully implemented and landed.

- Pipeline branch started at `c6111390`, passed local and GitHub checks, and
  merged through [PR #212](https://github.com/jakobtfaber/dsa110-FLITS/pull/212).
- Parent now pins merged commit `ded8d195`.
- Full pin delta includes three pre-existing Chromatica `main` commits; their
  paths were enumerated before the pin update.

### Phase 4: Stable identities and documentation

**Status:** Fully implemented.

- All 61 registry results have `library_slots`; all 18 catalog entries have
  `result_ids`; reciprocal references validate.
- Fifteen incomplete derived lineages are explicit exceptions. No stable input
  ID was invented.
- Current run and inventory documentation names separate roots and exact
  selection/receipt commands.

### Phase 5: Live repair

**Status:** Fully implemented.

- Preflight revalidated 13 link preimages, six excluded manifests, both
  external inventory preimages, scoped processes, and open files.
- Eight broken links replaced, two missing links created, and three repository
  links restored.
- All 13 resolve to their packet targets; all five manifest-bearing target
  checks pass.
- Final inventory contains the 18 catalog IDs and canonical parent/pipeline
  roots.

## Automated Verification Results

All expected checks passed:

- `pytest` parent focused suite — 67 passed, one optional SciencePlots warning.
- `pytest` pipeline focused suite — 34 passed, two pre-existing numerical/style
  warnings.
- Python compilation for `scripts/` — passed.
- TOML/YAML parsing for registry and catalogs — passed.
- Live post-repair verifier — 13 resolved links, 18 entries, six unchanged
  excluded manifests, zero errors.
- L0 certificate SHA-256 —
  `e3608a6458e8fe7075ca41395cce7a84a22cac968dbba31fd817dd212e8f184b`,
  unchanged.
- Historical joint-DM source/provenance Git diff — empty.
- `git diff --check` in parent and pipeline — passed.

Expected fail-closed result:

- Full materializer dry-run reports exactly
  `scintillation.dsa-lorentzian-2026-07-07` and
  `dispersion.pipeline-results-root` as `would-conflict-both-real`, then returns
  nonzero. No other mutation is proposed.

## Code Review Findings

### What matches the plan

- Real directories cannot be replaced by the link builder.
- Unknown/duplicate IDs fail before mutation.
- Telescope routing rejects unknown instruments rather than falling back.
- Receipt state includes Git identities, raw link payloads, resolved targets,
  and deterministic manifests.
- Current and historical joint-DM execution paths are explicitly separated.

### Deviations from the initial ticket

- Five required direct consumers were added after explicit owner approval.
- Incomplete remediation/package evidence is recorded as exceptions instead of
  receiving the initially proposed stable input IDs. This follows the accepted
  proof threshold.
- Manifest sorting and registry-section replacement defects discovered during
  validation were fixed and regression-tested.

All deviations are acceptable and preserve the approved bounded scope.

### Potential issues

No implementation issue identified. The two both-real conflicts remain
deliberately unresolved and belong to `authority-16`.

## Manual Testing Required

None. This batch changes path routing and navigation only; it makes no visual or
scientific adoption claim.

## Recommendations

### Critical

None.

### Important

None.

### Nice to Have

None for this batch.

### Follow-Up Work

- Adjudicate the two excluded both-real byte conflicts under `authority-16`.
- Complete any missing provenance needed before promoting the 15 input
  exceptions to stable input IDs.

## References

- Plan: [plan-results-library-chime-path-repair.md](plan-results-library-chime-path-repair.md)
- Implementation: [implement-results-library-chime-path-repair.md](implement-results-library-chime-path-repair.md)
- Action packet: [action-packet.json](../certificates/results-library-repair-2026-07-20/action-packet.json)
