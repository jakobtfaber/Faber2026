# Experiment: Figure 1 residual-drift audit

Date: 2026-07-17

## Question

At each adopted CHIME phase-coherence DM, is the residual arrival-time slope
consistent with zero for every Figure 1 panel and both instruments?

## Approaches

### A. Subband profile-peak regression

The dedispersed waterfall was divided into frequency subbands, a peak arrival
time was measured from each band-summed profile, and arrival time was regressed
against `nu^-2`. This is simple but conflates dispersive drift with scattering,
frequency-dependent morphology, and noisy component switching.

### B. Morphology-aware EMG regression

The same subbands were fit with the pipeline's exponentially modified Gaussian
arrival-time estimator before the `nu^-2` regression. A slope passed only when
its absolute value was at most two fitted standard deviations and at least three
subbands constrained the fit.

## Result

Neither approach establishes the requested universal zero-drift statement.
The profile-peak result is systematically morphology-sensitive. The EMG result
has several greater-than-two-sigma residuals (including both bands for Zach,
DSA for Wilhelm, Phineas, Freya, and Casey, and CHIME for Chromatica) and leaves
multiple CHIME panels unconstrained. Representative strong discrepancies are
Phineas DSA at 10.65 sigma and Chromatica CHIME at 7.10 sigma.

## Decision

Do not certify the all-panel gate and do not promote a new Figure 1. Preserve
the full machine-readable measurements with the review candidate. The observed-
peak render remains useful and removes the revoked model-ToA dependency, but a
science decision is required: either revise the gate to one tied to the adopted
phase-coherence statistic or establish a validated morphology model that makes
the residual-slope test interpretable for every panel.
