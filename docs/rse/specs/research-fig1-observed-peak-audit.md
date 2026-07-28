# Research: Figure 1 observed-peak and provenance audit

Date: 2026-07-17

## Scope

Reconcile the owner review of Figure 1 without touching the protected manuscript
target until exact candidate bytes are approved. The audit covers the time
anchor, adopted-DM rendering, input hashes, raw frequency headers, channel order,
and residual frequency-time drift for all 12 bursts and both instruments.

## Current implementation

- `scripts/plot_codetection_data_grid.py` renders all 12 rows from the 24 archival
  `_cntr_bpc.npy` products through `bands_archival`.
- Before this change, `load_row_bands` added a joint-fit scattering correction.
  That contradicted the owner's observed-peak-only instruction and introduced an
  unnecessary dependency on the model-ToA result family.
- `bands_archival` already re-dedisperses each filename-stem DM to the adopted
  CHIME phase-coherence DM, puts the measured DSA peak at zero, and positions
  CHIME using the recorded measured peak offset. Passing no extra shift therefore
  implements the requested convention directly.

## Data and header evidence

- The review branch is rebased on parent revision `26e37e4e`; its inherited
  pipeline revision is `17d9d26675702e9f8917da655621bef3231f0ddb`.
- All 24 local archival products match the byte counts and SHA-256 values in the
  pinned pipeline `data-manifest.csv`.
- Live reads of the 12 DSA filterbank headers on `iacobus` agree with the tracked
  reproduction fixture: 6144 channels, `fch1=1498.75 MHz`,
  `foff=-0.03051757812 MHz`, and `tsamp=32.768 us`. Raw channels descend.
- Live reads of the 12 CHIME single-beam HDF5 files on `h17` agree with the local
  extracted metadata: channels descend from roughly 800 to 400 MHz and
  `delta_time=2.56 us`.
- The display loader flips stored descending-frequency arrays before plotting,
  so the rendered vertical axis increases upward for both instruments. The final
  `_cntr_bpc.npy` builder is no longer available, so this mapping is supported by
  the raw-header snapshots, tracked checksum lineage, and loader behavior rather
  than a rerun of the lost builder.

## Residual-drift finding

Two estimators were tested on all 24 adopted-DM products: a subband profile-peak
regression and a scattering-aware exponentially modified Gaussian arrival-time
regression. The simple peak estimator is visibly biased by scattering and
profile evolution. The morphology-aware estimator is better motivated, but
several panels remain more than two standard deviations from zero and several
CHIME fits are unconstrained. Therefore the requested all-panel zero-drift gate
is not met and must not be reported as met.

## Implementation consequence

The producer can be corrected and an exact observed-peak candidate can be
staged with complete provenance. The candidate must remain unpromoted until the
manuscript owner both resolves the drift-gate interpretation and approves the
exact candidate hash. `sections/results.tex` and `sections/toa.tex` are outside
this workstream; the protected Figure 1 target and caption also remain unchanged
in this candidate-only PR.
