# Stratum 1 — Certify the raw data layer (stratum 0)

- Type: `wayfinder:task` (agent-driven build + owner spot-check)
- Status: **closed** (2026-07-19)
- Assignee: Antigravity
- Blocked by: —
- Blocks: [18](18-redo-dm-analysis-certified.md)
- Map: [ApJ submission](../map-apj-submission.md)
- **Binding definition:**
  [`../../specs/notes/definition-raw-chime-data-2026-07-19.md`](../../specs/notes/definition-raw-chime-data-2026-07-19.md)

## Question

Certify the **true** raw CHIME layer: the twelve singlebeam voltage files on
h17 at
`/data/research/astrophysics/frbs/chime-dsa-codetections/chime_singlebeam/singlebeam_<id>.h5`
(checksums, lineage, host path; upstream CANFAR path recorded). Owner
spot-check only.

Full-resolution `.npy` cubes and upchannelized products are **not** raw —
they are derived inputs (stratum 1). Any inventory of those products
(including the draft `l0.*` registry rows / `l0-certificates.json` from the
2026-07-19 mis-scoped pass) must be relabeled as derived-product
certificates, with applied dispersion measure and build provenance, not as
raw-layer certification.

## Resolution

Certified true Stratum 0 (L0) raw CHIME layer: 12 singlebeam HDF5 voltage files on h17 (`/data/research/astrophysics/frbs/chime-dsa-codetections/chime_singlebeam/singlebeam_<event_id>.h5`) with recorded CANFAR upstream paths. Generator: [`scripts/build_raw_voltage_certificates.py`](../../../scripts/build_raw_voltage_certificates.py); output: [`docs/rse/certificates/l0-raw-voltage-certificates.json`](../../certificates/l0-raw-voltage-certificates.json). Intensity `.npy` cubes and upchannelized products categorized as Stratum 1 derived inputs.

## Prior mis-scope (do not treat as resolution)

A 2026-07-19 pass inventoried 36 intensity products (full-resolution CHIME,
DSA-110, upchannelized) as if they were raw. Owner decision the same day:
those are not raw. Keep the mechanical inventory if useful under a derived
label; do not close this ticket on that work.
