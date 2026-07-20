# Validation: Latest analysis artifacts

**Date:** 2026-07-20
**Validated against:** `plan-latest-analysis-artifacts.md` and
`implement-latest-analysis-artifacts.md` on branch
`rse/jointtf-grok-harvest-revalidation`, derived from `c3e9870b`.

## Implementation Status

Automated criteria pass. The canonical directory exists and is populated.
Manual owner review of the organization remains pending.

| Phase | Status | Evidence |
|---|---|---|
| Specification/tests | Validated | Twelve unique rows; five tests. |
| Promotion/publication | Validated | Three pairs; nine fail-closed placeholders. |
| Archive lifecycle | Validated in temporary library | Change archives; identity no-ops. |
| Scientific adoption | Decision pending | Outside this implementation. |

## Automated Verification Results

- PASS — Python compilation of promoter and inventory builder.
- PASS — `python -m pytest tests/test_promote_analysis_latest.py -q`: 5 passed.
- PASS — fresh temporary-library initial and idempotent promotion.
- PASS — fresh Python 3.13.9 virtual environment, PyYAML 6.0.3.
- PASS — canonical manifest: 12 unique; 3 artifact-present; 9 not-yet-promoted.
- PASS — six copied hashes match all six tracked sources.
- PASS — canonical rerun: installed 0, unchanged 12, archived 0.
- PASS — inventory regenerated; path derives from `FABER2026_RESULTS_LIBRARY`.

## Code Review Findings

- Complete preflight prevents missing-source partial publication.
- Staging plus `os.replace` prevents half-written per-burst slots.
- Archive collisions fail closed rather than overwrite history.
- The spec never falls back to older fits for unpromoted bursts.
- Status wording honors the fit contract: no candidate is labelled PASS, and
  incomplete full diagnostic review is explicit.
- Original fit-generation reproducibility remains incomplete; promoted byte
  identity is reproducible.

## Manual Testing Required

- Open `~/Data/Faber2026/results-library/scattering/jointmodel/latest` and confirm
  that per-burst `STATUS.md` plus normalized `fit.json`/`jointmodel.npz` is the
  navigation surface you want.
- Count ratification is a separate scientific decision, not a directory test.

## Recommendations

Important:
- Use this pattern only for promoted outputs. Keep raw trials, posterior ladders,
  and unpromoted diagnostics outside `latest`.
- Promote one burst at a time through the tracked YAML; let the tool archive the
  displaced slot automatically.

Follow-up:
- Add equivalent specifications for other supersedable analyses only when they
  have a named promotion gate and a clear artifact set.

## Verdict

Validated for publication and archive lifecycle. Manual organization review and
all scientific adoption decisions remain open.

## References

- [Plan](plan-latest-analysis-artifacts.md)
- [Implementation](implement-latest-analysis-artifacts.md)
- [Research](research-latest-analysis-artifacts.md)
