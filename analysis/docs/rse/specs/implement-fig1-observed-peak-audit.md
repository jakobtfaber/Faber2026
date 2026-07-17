# Implementation: Figure 1 observed-peak audit

Date: 2026-07-17

## Delivered

- Figure 1 no longer imports or applies model-ToA scattering corrections. Both
  fitted and data-only rows use the observed-profile peak convention already
  implemented by `bands_archival`.
- The focused review CLI can stage one or more named candidates and freezes only
  evidence required by the selected families.
- `scripts/audit_fig1_frequency_axes.py` verifies all 24 local product hashes and
  sizes against the current pipeline manifest and records per-burst raw-header
  band edges, sampling, and channel order for DSA-110 and CHIME/FRB.
- `scripts/audit_fig1_residual_drift.py` reproduces the profile-peak and
  morphology-aware EMG drift estimates and classifies unconstrained results
  separately from zero-consistent results.
- `figure_review/batches/2026-07-17-fig1-observed-peak-audit/` contains exactly
  one hash-pinned candidate, its preview, frozen DM/catalog evidence, the 24
  input/header records, the 24 drift records, and only the prior Figure 1 owner
  decision metadata.

## Deliberately not delivered

The candidate was not copied to `figures/codetection_data_grid.pdf`; the prior
approval receipt and manuscript caption were not changed. The all-panel drift
gate failed (8 consistent with zero, 7 nonzero, 9 unconstrained under the EMG
estimator), and the new exact bytes have not been approved by the manuscript
owner. Promotion remains a separate follow-up after the science gate is resolved
and the candidate hash is explicitly approved.
