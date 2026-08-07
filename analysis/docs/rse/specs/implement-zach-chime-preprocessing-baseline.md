# Implementation Summary: Zach CHIME preprocessing baseline

**Date:** 2026-07-21
**Status:** Implemented; RFI method decision pending
**Plan:** [plan-zach-chime-preprocessing-baseline.md](plan-zach-chime-preprocessing-baseline.md)

## Outcome

Future source migrations now persist and verify complete local/remote preflight
evidence before mutation. The Zach baseband worker now emits a nominal
1,024-coarse-channel grid with explicit missing-data masks and both nominal and
package frequency coordinates. A live factor-64 run and held-out off-pulse audit
completed on h17.

The grid contract passed. Bandpass correction was necessary. The current RFI
routine/order failed stability and held-out-improvement gates, so no science fit
or result promotion occurred.

## Changes

### Parent repository

- `scripts/h17_source_data_layout.py` — attempt-specific atomic preflight
  packets, matching local/remote SHA-256 gate, source re-stat, journal binding.
- `tests/test_h17_source_data_layout.py` — 51-path completeness, ordering,
  mismatch, and fail-before-migrate tests.
- Research, plan, validation, Wayfinder, and evidence records.

### Pipeline submodule

- `analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py` —
  authoritative fine identifiers, exact nominal grid, package coordinate,
  `NaN` padding, validity mask, always-on provenance metadata.
- `analysis/scattering-refit-2026-06/baseband_recovery/audit_chime_preprocessing.py`
  — off-pulse training/validation audit and ordering controls.
- Focused unit tests for restoration and audit invariants.
- Pipeline PR [#216](https://github.com/jakobtfaber/dsa110-FLITS/pull/216)
  merged as `ab6af1f713496abd2ff2d71bf11edf4100871e94`; the parent pin advances
  only to that merged commit.

## Verification

- Parent focused tests: 12 passed.
- Pipeline focused tests: 15 passed; audit-only repeat: 3 passed.
- Python compilation and `git diff --check`: passed.
- Live grid invariant: 65,536 total, 55,744 measured, 9,792 missing, 437 time bins.
- Missing rows: no finite values; mask=false.
- Source hash before/after: unchanged.
- Live baseband and both diagnostic runs: completed; audit exits recorded as 0.

Full evidence and scientific boundaries are in
[validation-zach-chime-preprocessing-baseline.md](validation-zach-chime-preprocessing-baseline.md).

## Remaining work

- Owner review of the diagnostic figure and no-go verdict.
- A separate RFI-method ticket with a stable bandpass model and held-out
  stationarity gates.
- Dispersion-measure and exact time-axis validation before any Zach science run.
