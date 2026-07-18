# Implementation Summary: Outdated science-result quarantine

---
**Date:** 2026-07-17
**Author:** Codex
**Status:** Complete
**Plan Reference:** [plan-outdated-science-quarantine-2026-07-17.md](plan-outdated-science-quarantine-2026-07-17.md)
---

## Overview

Obsolete or superseded numerical products were moved, without byte changes, to
dated quarantine trees in Faber2026 and dsa110-FLITS. Active manuscript and
navigation surfaces now fail closed instead of presenting those products as
current science. Historical generators remain executable but default to a
`quarantine/.../regenerated/` destination.

No quarantined product was deleted. Scientific rehabilitation or removal is a
separate owner decision.

## Plan Adherence

The implementation followed the approved plan with one evidence-driven
deviation: the frozen foreground-attribution CSV no longer reproduces byte for
byte from current registry inputs. Its Wilhelm-coherence and DM-budget cells
have drifted. The historical CSV is therefore tested as a preserved, schema-valid
snapshot rather than as a currently reproducible output. This strengthens the
reason for quarantining it and does not alter the snapshot.

The pipeline merge was allowed after comprehensive local validation while its
non-required GitHub merge-commit workflow was still running. That workflow is
tracked as a final publication check.

## Phases Completed

### Phase 1: Pipeline quarantine

- Merged dsa110-FLITS PR [#202](https://github.com/jakobtfaber/dsa110-FLITS/pull/202)
  at `23fbd295a25aaa80e352ecf0c08287ba4f60a885`.
- Preserved the beta two-screen JSON/Markdown, joint summary, foreground
  attribution matrix, and legacy CHIME inventory/README beneath
  `quarantine/2026-07-17-outdated-science/`.
- Replaced the active joint-summary path with a tombstone and the CHIME README
  with a pointer to the finalized window-tuning campaign.
- Redirected all three historical generators and added quarantine regression
  tests.

### Phase 2: Parent manuscript quarantine

- Preserved the three provisional TeX tables and full propagation ledger beneath
  `quarantine/2026-07-17-outdated-science/`.
- Removed their active TeX inputs and event-specific foreground/scattering
  readings from the manuscript.
- Retained the active fail-closed two-screen table and a screen-readiness-only
  ledger.
- Updated the reproduction manifest, results catalog, generator, and regression
  tests.

### Phase 3: Pipeline integration

- Advanced the parent gitlink from `17d9d266` to merged pipeline commit
  `23fbd295` after an ancestry and full-range audit.
- The range contains the quarantine changes plus two already-reviewed upstream
  updates: `crossmatching/toa_crossmatch.py` (fail-closed model-ToA correction)
  and `analysis/RESULTS_LIBRARY.md` (finalized campaign indexing).
- Re-ran parent tests, consistency audit, and the LaTeX build at the new pin.

## Preserved Artifacts

The quarantine indexes contain the original path, reason, review prerequisite,
and SHA-256 record for each moved artifact. Representative exact-byte hashes are:

- Parent joint-fit provisional table:
  `c83b4f0cc24374d866172484b6b9a779544b2cbed7ea5bbdcd15ab8e301bd68f`
- Parent full provisional-propagation ledger:
  `e16a57b43bef1988864c99a5296aec94879cb630faa9c6b9d82ea7729e875388`
- Pipeline beta two-screen JSON:
  `477e5836c531402847c4e360cb816b7b458a9d1d7a53b46b2fcd5194c17d5e66`
- Pipeline foreground-attribution CSV:
  `1bd29845235c928c750baf006fb78927be9171bd3f25f00aafd923b833aca0f6`

## Verification Results

- Parent: `PYTHONPATH=. python3 -m pytest -q tests` — 151 passed, 1 xfailed.
- Parent: `python3 scripts/consistency_audit.py` — clean.
- Parent: `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex` —
  succeeded, 37 pages.
- Parent: `main.fls` contains only `twoscreen_provisional_table.tex` among the
  four provisional table families.
- Pipeline focused suite — 15 passed.
- Pipeline full frozen-uv suite — 788 passed, 8 skipped, 1 xfailed; nine tests
  could not collect only because that local Python 3.13 environment lacks
  `dynesty`.
- The same nine dynesty-dependent tests in clean Conda `flits` — 9 passed with
  dynesty 3.0.0.
- `git diff --check` passed in both repositories.

Running plain `python3 -m pytest -q` from the parent root is not the canonical
parent test surface because it recursively collects nested pipeline analysis
scripts. The repository's `tests/` suite is the validated parent surface.

## Files and Reachability

No result bytes were deleted. The active manuscript no longer reaches:

- `joint_fit_provisional_table.tex`
- `dsa_scint_provisional_table.tex`
- `foreground_propagation_provisional_table.tex`

The fail-closed `twoscreen_provisional_table.tex` remains active. Current prose
states that only the qualified Oran DSA and Chromatica CHIME measurements are
promoted; other DSA and foreground-attribution claims await certified refits.

## Remaining Work

- Owner review later decides whether each quarantined family is removed,
  rehabilitated with new science, or retained indefinitely.
- Parent delivery is published for review as Faber2026 PR
  [#131](https://github.com/jakobtfaber/Faber2026/pull/131).

## References

- [Research](research-outdated-science-quarantine-2026-07-17.md)
- [Plan](plan-outdated-science-quarantine-2026-07-17.md)
- [Pipeline PR #202](https://github.com/jakobtfaber/dsa110-FLITS/pull/202)
- [Parent PR #131](https://github.com/jakobtfaber/Faber2026/pull/131)
