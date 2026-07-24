# Implementation Plan: Horizontal RFI row component

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** Automated row candidates rejected; manual map lane in progress
**Related Documents:**
- [Research](research-rfi-horizontal-structure-capture.md)
- [Experiment](experiment-rfi-horizontal-structure-capture.md)
- [Seed-promotion experiment](experiment-rfi-offpulse-seed-promotion.md)
- [Voltage-kurtosis experiment](experiment-rfi-protected-voltage-kurtosis.md)
- [Implementation report](implementation-rfi-horizontal-row-component.md)
- [Validation report](validation-rfi-horizontal-row-component.md)
---

## Overview

Implement and test horizontal-row candidates, preserve their failure evidence,
then stop using them as bad-channel authority after owner review. Robust rows
missed contamination; the composite full-coarse mask removed far too much
support. Event-specific owner-reviewed bad-channel maps replace automated row
promotion for science analysis.

**Goal:** Preserve the automated experiments as rejected evidence and establish
owner-reviewed, exact, reusable bad-channel maps without hidden value
replacement.

## Current State Analysis

- Pixel 6 masks individual post-normalization pixels using burst-bearing data
  (`scripts/rfi_time_frequency_candidate.py:17-44`).
- The Zach review already separates training and context and performs
  non-wrapping alignment (`scripts/review_real_zach_rfi_cleaner.py:191-249,585-605`).
- The selected reference method computes off-pulse row standard deviation and
  lag-one correlation with iterative median-based spread rejection
  (`pipeline/scintillation/scint_analysis/auto_rfi_flag.py:37-83`).
- The current mask panel coarsens 64 fine rows, so it does not show exact row
  classification (`scripts/review_real_zach_rfi_cleaner.py:327-342,490-508`).

## Desired End State

- Automated candidates remain reproducible diagnostics, not science masks.
- Huge values outside training cannot change a row decision.
- The Zach script accepts historical candidates plus
  `offpulse_seed_plus_voltage_kurtosis`;
  historical failures remain reproducible.
- Candidate output records exact selected rows, feature diagnostics, burst-bright
  overlap, surviving spectra in 600–650 and 700–750 MHz, and support loss.
- Each event/instrument receives a bandpass-only fine-frequency atlas and a
  hash-bound owner-reviewed map.
- An interactive Jupyter notebook converts owner-selected frequency spans into
  exact full-resolution row ranges, previews the masked result, and writes
  drafts only.
- A standalone desktop GUI provides direct vertical click-drag selection over
  the same review panels without requiring a notebook or server.
- Two network-disabled container runs reproduce byte-for-byte.

## What We're NOT Doing

- Opening Zach validation or sealed test intervals.
- Promoting an automated Zach-tuned threshold to science use.
- Solving broadband impulse or drifting-line contamination.
- Replacing rejected values by interpolation or zero.
- Calling this component a complete or validated cleaner.

## Implementation Approach

The rejected aggressive run used a one-row seed gate and a 4.5
median-based-spread voltage cutoff. Checked-in diagnostic defaults are restored
to the earlier four-row and 5.0 cutoffs; neither configuration is science
authority.

`scripts/manual_bad_channels.py` is the science-facing boundary. It validates
the source-product and frequency-axis hashes, exact sorted row ranges, matching
frequency limits, and owner approval before producing a mask. It changes only
explicitly selected rows to `NaN`.

`scripts/manual_bad_channel_review.py` is the tested selection and draft-map
backend. `analysis/rfi/notebooks/manual_bad_channel_review.ipynb` is the
owner-facing interface. It consumes a hash-bound review bundle, displays
unmasked and proposed-masked dynamic spectra plus the time-integrated spectrum,
and converts notebook click-drag selections into sorted half-open full-resolution
row ranges. It may save only `draft` maps; approval remains outside the
notebook.

`scripts/manual_bad_channel_gui.py` is the standalone owner-facing alternative.
It uses the native Matplotlib window, applies vertical drag spans through the
same backend, navigates fixed 50-MHz review bands, and also writes drafts only.

## Implementation Phases

### Phase 1: Lock robust row semantics

**Objective:** Add a tested shared implementation.

**Status:** Complete. Focused test first failed on the absent module; all four
row-component tests now pass.

1. Add `tests/test_rfi_offpulse_row_candidate.py` with analytic assertions:

   ```python
   def test_decisions_ignore_every_value_outside_training():
       time = np.tile([-1.0, 1.0], 8)
       base = np.vstack([scale * time for scale in np.linspace(0.8, 1.2, 12)])
       changed = base.copy()
       changed[:, 8:] = 1e6
       first, _ = robust_offpulse_row_mask(base, np.ones(12, bool), (0, 8))
       second, _ = robust_offpulse_row_mask(changed, np.ones(12, bool), (0, 8))
       np.testing.assert_array_equal(first, second)

   def test_obvious_variable_row_is_flagged_but_noise_rows_are_retained():
       time = np.tile([-1.0, 1.0], 8)
       rows = np.vstack(
           [scale * time for scale in np.linspace(0.8, 1.2, 11)] + [8.0 * time]
       )
       result, _ = robust_offpulse_row_mask(rows, np.ones(12, bool), (0, 16))
       assert result.sum() == 1 and result[-1]
   ```

2. Run
   `/Users/jakobfaber/.conda/envs/py312/bin/python -m pytest tests/test_rfi_offpulse_row_candidate.py -q`
   and require failure because the module does not exist.
3. Add `scripts/rfi_offpulse_row_candidate.py` with `_mad_z()`,
   `offpulse_channel_stats()`, `robust_offpulse_row_mask()`, and
   `apply_row_mask()`. Validate two-dimensional shape, row support, finite
   positive threshold, positive iterations, and a non-empty in-bounds training
   interval. Masked values become `NaN`; retained values remain exact.
4. Re-run the focused test and require all assertions to pass.

### Phase 2: Add candidate dispatch and diagnostic output

**Objective:** Apply either historical Pixel 6 or frozen robust rows through the
same verified timing and window path.

**Status:** Complete. Dispatch, claim-safe labels, exact-row output, both marked
interval summaries, and focused tests are implemented; the final focused suite
contains 25 passing tests.

1. Add failing tests to `tests/test_review_real_zach_rfi_cleaner.py` asserting:
   robust labels say “component” rather than “cleaner”; exact added row masks are
   broadcast only after off-pulse learning; and both owner-marked intervals are
   summarized without influencing decisions.
2. Extend `scripts/review_real_zach_rfi_cleaner.py:191-249` with
   `candidate_method`. For `robust_rows`, call:

   ```python
   added_rows, diagnostics = robust_offpulse_row_mask(
       combined, final_valid, compact_training, sigma=5.0, iterations=6
   )
   candidate, added_mask = apply_row_mask(combined, added_rows)
   ```

3. Extend `scripts/review_real_zach_rfi_cleaner.py:371-537` so labels, warning,
   mask panel, and JSON identify the selected candidate. Save
   `additional_candidate_rows.npy` and both shared-module hashes.
4. Add `--candidate` with choices `pixel6` and `robust_rows`; default remains
   `pixel6` for historical reproduction.
5. Run the three focused test files and require all to pass.

### Phase 3: Frozen Zach application

**Objective:** Produce a reproducible diagnostic without tuning.

**Status:** Superseded after execution. The robust candidate was byte-stable
but selected seven rows and left both strongest marked-band residuals
unchanged.

1. Copy exact scripts to
   `/data/Faber2026/evidence/rfi-horizontal-row-candidate-20260721/code/` and
   record SHA-256 hashes before execution.
2. Run twice in the pinned, network-disabled container with
   `--candidate robust_rows`, writing `zach-1` and `zach-2`.
3. Require byte-identical manifests. Record, without changing configuration:
   selected row count; selected rows in 600–650 and 700–750 MHz; pre/post
   outlier scores; burst-bright overlap; retained row fraction; and profile-peak
   change.
4. Copy only SVG, JSON, and checksums into
   `docs/rse/verify/rfi-horizontal-row-candidate-20260721/`.
5. Update the Wayfinder ticket. Keep it open because time-local contamination
   remains unresolved.

### Phase 4: Saturated-row revision

**Objective:** Capture the owner-marked saturated rows without using burst
pixels or converting broadband impulses to row vetoes.

**Status:** Rejected by owner after real-event review. The four-row gate left
visible saturated channels in 700–750 MHz.

1. Add protected off-pulse seed promotion and fail-closed tests.
2. Preserve the broadband-failure and five-row-gate failure outputs.
3. Require complete recovery on three saturated-row known-truth seeds and an
   exact fresh-container repeat.
4. Apply the frozen four-row rule twice to Zach in the pinned,
   network-disabled container.
5. Preserve both exact Zach outputs as `zach-seed-1` and `zach-seed-2`.

### Phase 5: Isolated strong rows plus protected raw-voltage tails

**Objective:** Capture the owner-observed misses without consulting the burst
window or hard-coding a frequency.

**Status:** Rejected by owner as far too aggressive.

1. Admit an isolated six-standard-deviation off-pulse row seed after excluding
   simultaneous broadband columns. Known truth recovers 84/84 injected rows on
   three seeds, leaves no injected intensity, selects 0–1 clean-control row,
   and removes 0.52–0.53% of injected burst support.
2. Add the protected raw-voltage amplitude-kurtosis component at a frozen 4.5
   median-based-spread cutoff. Known truth recovers 28/28 contaminated coarse
   channels on three seeds, selects no clean or broadband controls, and is
   invariant to every protected value.
3. Apply the union twice to Zach in the pinned, network-disabled container.
   Runs `zach-voltage-7` and `zach-voltage-8` have byte-identical manifests.
4. Render a dedicated 700–750 MHz review without dropping fully masked coarse
   coordinates. The output erased broad blocks around 718–745 MHz and is
   preserved only as rejected evidence.

### Phase 6: Owner-reviewed manual bad-channel maps

**Objective:** Make exact event-specific row decisions reviewable, durable,
and reusable without automatic promotion.

**Status:** Infrastructure implemented; Zach CHIME/FRB atlas ready; all maps
pending owner selection.

1. Bind every map to the exact frequency-axis SHA-256 and row count.
2. Store sorted half-open row ranges, matching frequencies, reason, evidence,
   reviewer, and review time.
3. Fail closed unless map status is `owner_approved`.
4. Apply approved rows only as explicit `NaN`; retain every other value exactly.
5. Track all twelve events for CHIME/FRB and DSA-110. Start with Zach
   CHIME/FRB from bandpass-only measured support.
6. Keep diagonal and time-local interference separate: a one-dimensional bad-
   channel map cannot remove it without erasing the entire swept band.

### Phase 7: Notebook-based manual flagging

**Objective:** Let the owner select, inspect, revise, and save exact bad-channel
ranges without editing JSON by hand or granting approval implicitly.

**Status:** Automated implementation complete; owner interaction pending.

1. Add `tests/test_manual_bad_channel_review.py` with failing tests for exact
   span-to-row conversion, contiguous-range merging, descending frequency axes,
   hash mismatch rejection, draft-only saving, undo, and retained-value
   invariance.
2. Add `scripts/manual_bad_channel_review.py` with pure selection, draft-map,
   and before/after plotting functions. The backend has no desktop GUI or
   persistent service.
3. Extend `scripts/manual_bad_channel_atlas.py` with `--output-bundle`. Store the
   full-resolution frequency axis, review-valid rows, aligned display data,
   off-pulse row measures, on-pulse spectrum, time axis, and exact source/frequency
   hashes in a compressed NumPy bundle.
4. Add `scripts/manual_bad_channel_notebook.py` and
   `analysis/rfi/notebooks/manual_bad_channel_review.ipynb`. Notebook controls
   select the visible frequency window and proposed span; buttons flag, unflag,
   undo, clear, refresh, and save a draft.
5. Generate the Zach CHIME/FRB bundle in the pinned network-disabled container,
   copy it to the local review directory, and open the notebook against
   `analysis/rfi/manual-bad-channels/chime-frb/zach.json`.
6. Require the focused tests, headless figure smoke test, bundle/map binding
   check, executed-notebook smoke test, Python compilation, and
   `git diff --check` to pass before requesting owner interaction.

### Phase 8: Desktop click-drag manual flagging

**Objective:** Provide direct frequency-row selection in a standalone desktop
window without notebook widget lifecycle or server state.

**Status:** Automated implementation complete; owner interaction pending.

1. Add `tests/test_manual_bad_channel_gui.py` first. Cover flag and unflag drag
   dispatch, exact row selection, 50-MHz band navigation, undo, clear,
   draft-only save, approved-map immutability, and headless figure construction.
2. Add `scripts/manual_bad_channel_gui.py` using the native Matplotlib backend.
   Vertical drags on the before, after, or spectrum panel apply the selected
   frequency span in the active `Flag` or `Unflag` mode.
3. Keep before/after dynamic spectra and the time-integrated spectrum visible.
   Highlight proposed rows and report the exact selected count and retained
   measured-row fraction.
4. Add previous/next 50-MHz controls plus undo, clear, refresh, save-draft, and
   quit controls. Saving must remain `draft` and must clear reviewer/time.
5. Launch the real Zach CHIME/FRB GUI against the existing hash-bound bundle and
   empty draft map. Do not preselect or save any row automatically.
6. Require the full focused suite, Python compilation, `git diff --check`, live
   process/window verification, and owner drag/save review before closure.

## Success Criteria

### Automated Verification

- Focused tests pass.
- Draft maps are rejected by the default consumer.
- Source-product or frequency-axis drift is rejected.
- Row ranges must be sorted, non-overlapping, in bounds, and frequency-bound.
- Applying a reviewed mask changes only selected rows to `NaN`.
- Every Zach atlas segment records exact inputs, code, and container hashes.
- The interactive notebook rejects bundle/map hash drift and cannot emit an
  owner-approved map.
- The standalone GUI rejects bundle/map hash drift and cannot emit an
  owner-approved map.
- Drag selections produce exact sorted, non-overlapping full-resolution row
  ranges on ascending or descending frequency axes.
- Undo, clear, and draft save preserve all unselected values exactly.
- JSON parsing, local checksums, Python compilation, and `git diff --check` pass.

### Manual Verification

- Owner selects exact Zach rows across the eight 50-MHz atlas segments.
- Owner can set the view and exact selection spans, flag, unflag, undo, clear,
  and inspect the before/after view in the notebook.
- Owner can drag directly across frequency rows in the desktop GUI, navigate
  50-MHz bands, and inspect the updated before/after view without losing controls.
- A before/after figure is reviewed before the map becomes `owner_approved`.
- The same review is repeated for every event and instrument.

### Reproducibility and Correctness

- Input, container, code, configuration, commands, output hashes, and selected
  rows are recorded.
- The full-band atlas is split into eight checksummed 50-MHz segments.
- An approved map cannot silently transfer to a changed source or frequency
  axis.

## Testing Strategy

Unit tests cover analytic feature values, decision invariance, iteration,
missing data, invalid inputs, immutability, and exact row broadcasting. The
container integration covers the real 65,536-row timing/alignment path. Manual
review covers scientific ambiguity that Zach cannot resolve without truth.

## Risks

- Whole-row vetoes remove real burst support at selected frequencies. Report
  support loss and burst-bright overlap explicitly.
- Robust row capture does not solve time-local broadband or drifting RFI. Keep
  the complete-chain verdict fail-closed.
- Coarse plotting can conceal fine-row behavior. Save and summarize exact row
  decisions separately.

## References

- [Research](research-rfi-horizontal-structure-capture.md)
- [Experiment](experiment-rfi-horizontal-structure-capture.md)
- `pipeline/scintillation/scint_analysis/auto_rfi_flag.py`
- `scripts/review_real_zach_rfi_cleaner.py`
- `tests/test_review_real_zach_rfi_cleaner.py`
