# Build Zach's standardized dynamic spectra and validate the burst models

- Type: `wayfinder:task` (HITL)
- Status: open
- Assignee: —
- Blocked by: [Fit and adopt Zach's dual-band dispersion measures](zach-analysis-02-fit-dual-band-dm.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner direction, 2026-07-22

## Question

Do provenance-bound, correctly dedispersed Zach dynamic spectra support stable
two-dimensional burst models in both bands?

Build standardized DSA-110 and CHIME/FRB dynamic spectra from the verified
original products, adopted band-specific dispersion measures, and established
time axes. Preserve native resolution metadata. For CHIME/FRB, restore the
nominal 1,024-channel grid while keeping the 153 absent channels explicitly
missing; never zero-fill them. Keep bandpass correction, padding, and RFI masks
as separately named and hashed transformations.

Before fitting, validate band-specific burst windows and complete both manual
bad-channel reviews. Reconfirm that Zach's approved CHIME/FRB row map remains
appropriate on the final dedispersed product; create and approve Zach's DSA-110
map. Retained values must remain unchanged.

Fit the predeclared two-dimensional component models from the complete
first-to-last-component interval. Record model multiplicity, likelihood,
uncertainties, residuals, posterior checks, failure modes, and sensitivity to
reasonable window perturbations. The owner reviews full triptychs and concise
residual diagnostics before model adoption.

Resolution requires exact input/output hashes, code and environment identities,
rerun commands, approved masks, and an explicit model-adoption verdict for each
band. No ACF, scintillation fit, foreground interpretation, or manuscript claim
may be promoted here.

On pass, unblock
[Validate the approved Zach manual map in ACF preprocessing](rfi-validation-02a-validate-zach-manual-map-acf.md).
