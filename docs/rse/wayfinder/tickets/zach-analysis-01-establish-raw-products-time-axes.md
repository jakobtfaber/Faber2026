# Establish Zach's original products, metadata, and time axes

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Define the CHIME RFI-cleaning acceptance contract](rfi-validation-01-define-acceptance-contract.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner direction, 2026-07-22

## Question

What exactly are Zach's original DSA-110 filterbank (`.fil`) and CHIME/FRB
singlebeam (`.h5`) products, and what physical time and frequency coordinates do
their samples represent?

Start from the original files, not derived NumPy or NPZ products. For each file:

1. resolve its authoritative path, size, SHA-256, observation/event identity,
   producing system, and available header or dataset metadata;
2. record whether coherent dedispersion, incoherent dedispersion, both, or
   neither has already been applied, including the exact recorded dispersion
   measure and reference frequency when present;
3. establish the time coordinate: epoch, time standard, sample-reference
   convention, channel-dependent offsets, FPGA or packet counters, cadence,
   gaps, and the conversion to a common arrival-time convention;
4. establish channel identifiers, order, center-frequency convention, nominal
   and measured frequency resolutions, missing/excised channels, and usable
   bandwidth; and
5. record every ambiguity rather than filling it from a derived product.

DSA-110's recorded incoherent dedispersion is irreversible; coherent
dedispersion must not be claimed. CHIME/FRB dedispersion state must be read from
the Zach H5 evidence, not inferred from a filename.

Resolution requires a checksummed machine-readable metadata packet, a concise
human table, exact extraction commands, and an owner-review figure showing both
native grids and time-axis conventions. No dispersion-measure fit, burst model,
ACF, or science claim may be produced here.

On pass, unblock
[Fit and adopt Zach's dual-band dispersion measures](zach-analysis-02-fit-dual-band-dm.md).

