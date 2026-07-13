# Joint CHIME/DSA DM-phase reproducibility package

This directory is the manuscript-repository copy of the validated custom
DM-phase campaign. It contains the complete code snapshot, tests, numerical
results, provenance, held-out injection validation, and visual diagnostics for
all 12 CHIME+DSA events.

## Manuscript adoption policy

The manuscript adopts the CHIME/FRB fit for every event and uses DSA-110 as an
independent cross-check. The previously generated inverse-variance and
random-effects joint values remain useful sensitivity tests, but are not the
primary DMs because the CHIME curves are consistently narrower and the
400--800 MHz band has about 34 times the cold-plasma DM leverage of the
1311--1499 MHz DSA band. The authoritative adopted-value surface is
[`manuscript_dm_catalog.csv`](manuscript_dm_catalog.csv); the full reasoning is
recorded in `docs/rse/specs/verified-dm-adoption-2026-07-13.md`.

Do not use the earlier adaptive-arrival or DM-phase v1 `UNCONSTRAINED` statuses
as measurement-quality evidence. Those statuses came from an incorrect
application-level gate, not from invisible bursts. This v2 package fits every
band independently and then produces one joint DM per event.

## Start here

- [`results/diagnostics/all_events_contact_sheet.jpg`](results/diagnostics/all_events_contact_sheet.jpg): all-event visual audit.
- [`results/diagnostics/summary.md`](results/diagnostics/summary.md): manuscript-facing DM table.
- [`manuscript_dm_catalog.csv`](manuscript_dm_catalog.csv): adopted CHIME-primary DMs and both band measurements.
- [`results/diagnostics/`](results/diagnostics/): one full diagnostic figure per event.
- [`results/validation/injection_recovery.png`](results/validation/injection_recovery.png): held-out recovery matrix.
- [`results/fits.json`](results/fits.json): complete curves, jackknifes, cutoff studies, resolution studies, and joint fits.
- [`results/run_provenance.json`](results/run_provenance.json): SHA-256 fingerprints for all 24 raw products and the implementation used for the run.
- [`code/`](code/): exact source and test snapshot.
- [`PIPELINE_RUNBOOK.md`](PIPELINE_RUNBOOK.md): detailed algorithm and acceptance-gate description.

## Source of record

The analysis was developed and executed in `dsa110-FLITS` commit
`c07f1f1660ee0736459eead04ebf69eaa82aebc4` on branch
`agent/dm-phase-v2`. The code under `code/` is an exact copy of that commit's
campaign implementation. The FLITS branch remains the executable upstream
source; this directory makes the full evidence durable beside the manuscript.

## Re-run from this repository

The snapshot uses the scientific support modules and vendored released
`DM_phase` implementation in the `pipeline/` submodule. From the top-level
`Faber2026` directory, with the same FLITS source checked out, run:

```bash
git submodule update --init pipeline
export PYTHONPATH="$PWD/analysis/dm-joint-phase-v2/code:$PWD/pipeline"

python analysis/dm-joint-phase-v2/code/scripts/run_joint_dm_phase.py \
  --manifest pipeline/data-manifest.csv \
  --output analysis/dm-joint-phase-v2/results/fits.json

python analysis/dm-joint-phase-v2/code/scripts/validate_joint_dm_phase.py \
  --output analysis/dm-joint-phase-v2/results/validation

python analysis/dm-joint-phase-v2/code/scripts/render_joint_dm_diagnostics.py \
  --results analysis/dm-joint-phase-v2/results/fits.json \
  --output analysis/dm-joint-phase-v2/results/diagnostics

python analysis/dm-joint-phase-v2/code/scripts/write_joint_dm_provenance.py \
  --results analysis/dm-joint-phase-v2/results/fits.json \
  --output analysis/dm-joint-phase-v2/results/run_provenance.json

pytest -q \
  analysis/dm-joint-phase-v2/code/tests/test_dm_joint_phase.py \
  analysis/dm-joint-phase-v2/code/tests/test_dmphase_recovery.py
```

The raw `.npy` products are intentionally not copied into the manuscript repo.
Their absolute paths, shapes, sizes, exact filename DMs, modification times, and
SHA-256 fingerprints are recorded in `results/run_provenance.json`.

## Validated outcome

- 12/12 events have constrained CHIME, DSA, and joint fits.
- All 24 band fits selected native frequency and time resolution.
- All selected maxima are interior to their final search grids.
- The paired held-out injection matrix has joint RMSE
  `0.0028 pc cm^-3` and maximum absolute error `0.0062 pc cm^-3`.
- `PASS_SYSTEMATIC` denotes a constrained joint fit whose uncertainty includes
  measured between-band scatter; it is not an unconstrained or failed fit.
