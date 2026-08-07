# Validation: JointTF v2 artifact harvest, jobs 169–182

> Evidence-only preservation extracted from Faber2026 pull request 152 and
> independently re-harvested from h17 on 2026-07-22. This record does not select,
> adopt, or approve any component count, result roster, figure, or manuscript
> change.

## Status

**Diagnostic evidence only. Not science-ready. Not manuscript-facing.**

The checked manifest and a fresh read-only re-harvest were identical after
removing the generation timestamp. Their canonical JSON SHA-256 was
`363c8589868c32cebd260b403aaea3d4b5567bef1007745709079d5106ad6b56`.

Fresh mechanical checks:

- 14 of 14 endpoint logs report return code zero.
- 14 of 14 result JSON and sample-archive pairs are present.
- 56 job artifacts, six configurations, six inputs, six executed-code files,
  and two diagnostic figures are SHA-256 bound.
- Every reported component-time median and central interval lies inside its
  logged fit window.

These checks establish artifact presence and internal consistency only. They do
not establish a physical component count or publication readiness.

## Preserved evidence

- `manifest.json`: hashes, job metadata, fit summaries, numerical comparisons,
  fit-window checks, environment metadata, and explicit provenance warnings.
- `../../../../scripts/revalidate_jointtf_v2_harvest.py`: read-only
  re-harvester used for the fresh check.

The figures are not duplicated here. Their remote paths, sizes, modification
times, and hashes remain in the manifest.

## Reproducibility boundary

The artifact harvest is reproducible from the surviving h17 files. The original
fits are not exactly reproducible:

- no sampler seed was recorded;
- the executed pipeline checkout was at `d292f4b91ef02dfd120a816c015fbb67cb15261f`;
- two executed files were modified and one was untracked at revalidation;
- hashes captured during revalidation cannot prove those uncommitted bytes were
  unchanged since execution.

A rerun would therefore be a new stochastic experiment, not exact reproduction
of jobs 169–182.

## Excluded from preservation

- owner-pending component-count choices;
- any latest-result or manuscript-facing selection;
- candidate fit JSON or NumPy archives;
- triptychs, vet images, and PDF, PNG, or SVG duplication;
- result-promotion code, catalogs, and promotion tests;
- production-table or time-of-arrival changes;
- authorization for another fit rung.

## Remaining human gates

1. Owner review and hash-bound approval of any exact candidate bytes.
2. Separate owner decision on component-count adoption.
3. Version and review the executed fitting code; add recorded sampler seeds
   before new production fitting.
4. Separate authorization for any later fit rung.

## Verification commands

```bash
python3 -m py_compile scripts/revalidate_jointtf_v2_harvest.py
python3 scripts/revalidate_jointtf_v2_harvest.py \
  --output /tmp/jointtf-v2-harvest-fresh.json
jq -S 'del(.generated_utc)' /tmp/jointtf-v2-harvest-fresh.json | shasum -a 256
jq -S 'del(.generated_utc)' \
  docs/rse/specs/validation/evidence/jointtf-v2-harvest-2026-07-19/manifest.json \
  | shasum -a 256
```

## References

- Original draft: <https://github.com/jakobtfaber/Faber2026/pull/152>
- Recovery handoff:
  `../handoff/handoff-2026-07-19-23-24-jointtf-grok-harvest-revalidation.md`
- Evidence manifest:
  `evidence/jointtf-v2-harvest-2026-07-19/manifest.json`
