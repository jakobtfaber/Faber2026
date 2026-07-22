# Fit and adopt Zach's dual-band dispersion measures

- Type: `wayfinder:task` (HITL)
- Status: open
- Assignee: —
- Blocked by: [Establish Zach's original products, metadata, and time axes](zach-analysis-01-establish-raw-products-time-axes.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner direction, 2026-07-22

## Question

What dispersion measure should be adopted for Zach in each instrument, and are
the CHIME/FRB and DSA-110 measurements consistent under a common arrival-time
convention?

Use only provenance-bound products derived from the verified original files and
their established time axes. Account explicitly for dedispersion already
applied in each source product. Use band-specific on-pulse envelopes with
off-pulse padding; for a multi-component burst, span the first through last
component rather than only the brightest component. Visually review every crop
before fitting.

Report the CHIME/FRB and DSA-110 dispersion measures separately with uncertainty,
fit objective, reference frequency, covariance or equivalent uncertainty
evidence, sensitivity to window and component choices, and the measured
cross-band difference. Record any adopted shared reference value as a separate
decision; do not silently force agreement.

Resolution requires reproducible fit inputs and commands, checksummed outputs,
diagnostic dispersion-measure curves and dedispersed dynamic spectra, validated
time-of-arrival conventions, and owner approval. No two-dimensional burst model,
scattering fit, ACF, or scintillation result may be promoted here.

On pass, unblock
[Build Zach's standardized dynamic spectra and validate the burst models](zach-analysis-03-build-dynamic-spectra-fit-burst.md).

