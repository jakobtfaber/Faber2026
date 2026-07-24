# Implementation: Protected horizontal RFI row components

**Date:** 2026-07-22
**Status:** Automated candidates rejected; manual-map transition active
**Plan:** [Horizontal RFI row component](plan-rfi-horizontal-row-component.md)

## Delivered

- `scripts/rfi_offpulse_row_candidate.py`: historical robust-row option,
  protected strong off-pulse row seeds, broadband-time exclusion, and explicit
  whole-row missing-data masks.
- `scripts/rfi_voltage_kurtosis_candidate.py`: protected raw-voltage amplitude
  kurtosis, broadband-time exclusion, one-sided iterative selection, and
  coarse-to-fine mapping.
- `scripts/review_real_zach_rfi_cleaner.py`: composite dispatch, raw-H5
  provenance, exact selected-row arrays, common-support equality checks, full
  review figure, and corrected 700–750 MHz review figure.
- `scripts/manual_bad_channel_review.py`: exact span selection, unflagging,
  undo, clear, before/after plotting, integrated spectrum, hash binding, and
  draft-only save.
- `scripts/manual_bad_channel_notebook.py` and
  `analysis/rfi/notebooks/manual_bad_channel_review.ipynb`: Jupyter controls for
  frequency-window selection, flag/unflag spans, refresh, and draft save.
- `scripts/manual_bad_channel_gui.py`: native desktop click-drag review with
  flag/unflag modes, 50-MHz navigation, undo, clear, refresh, and draft save.
- `scripts/manual_bad_channel_atlas.py`: optional full-resolution compressed
  review bundle carrying aligned display data, row measures, time/frequency
  axes, and exact source bindings.
- Unit tests for protected-value invariance, known analytic decisions, missing
  support, invalid inputs, exact row mapping, and plot-coordinate preservation.

## Preserved failures

- `zach-1`, `zach-2`: robust row statistics; insufficient.
- `zach-seed-1`, `zach-seed-2`: four-row seed gate; owner rejected for visible
  700–750 MHz misses.
- `zach-voltage-3` through `zach-voltage-6`: intermediate composite and review
  axis correction; diagnostic history only.

The current real output is `zach-voltage-7`, repeated exactly as
`zach-voltage-8`.

## Verification

- Focused local suite: 53 passed.
- Python compilation: passed.
- The real Zach notebook executed end to end with the dedicated
  `Faber2026 (Python 3)` kernel; its controls render without changing the map.
- Notebook refresh clears only its figure output. A first version used the
  global output clear and erased the controls; a regression test now prevents
  recurrence.
- The standalone GUI builds against the real Zach bundle with zero selected
  rows; every drag panel remains locked to the active frequency band.
- Strong-row known truth: 84/84 recovered on each of three seeds; 0–1 clean
  control row; protected values excluded; exact repeat.
- Raw-voltage known truth: 28/28 recovered on each of three seeds; zero clean
  and broadband-control selections; protected values invariant; exact repeat.
- Zach: two byte-identical manifests; retained values exactly equal on common
  support; dedicated frequency axis retains fully masked coarse channels.
- Manual editor: ascending and descending axes, selection, unflagging, undo,
  clearing, hash drift, approved-map immutability, draft save, retained-value
  invariance, notebook controls, and headless figure rendering are tested.
- Real Zach bundle: 65,536 rows by 108 time bins, 55,744 measured rows,
  SHA-256 `40eaf83f7a9c3da74f0edc8a570ad76514e56178d9d7411340e02abe65ad49a6`.
- A test-only 41-row draft validated against the live h17 source and frequency
  hashes with `--allow-draft`; default consumption rejected it as unapproved.

## Open gate

The owner rejected the final composite as far too aggressive. These modules are
preserved diagnostics only. Science support now requires an owner-approved,
event-specific map validated by `scripts/manual_bad_channels.py`. Drifting and
time-local broadband interference remain separate unresolved work.

The standalone GUI is ready for owner interaction. No Zach rows have been
selected in the repository map, and the map remains a draft.
