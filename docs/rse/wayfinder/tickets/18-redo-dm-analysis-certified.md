# Stratum 2 — Redo the DM analysis on certified bytes (L1/L2)

- Type: `wayfinder:grilling` (HITL — figure-driven, casey-first calibration)
- Status: open
- Assignee: —
- Blocked by: [17](17-certify-raw-data-layer.md)
- Blocks: [19](19-redo-toa-analysis-certified.md), [20](20-rebuild-upchannelized-products.md), [21](21-redo-scattering-certified.md)
- Map: [ApJ submission](../map-apj-submission.md)
- **Carries forward ticket 16 (superseded) + its handoff:**
  `docs/rse/specs/handoff-2026-07-19-14-56-scint-input-remediation-casey-dm-calibration.md`
  — corrected-sign transform, sign-test recipe, disqualified peak-S/N metric,
  casey state (pick pending: 491.148 vs 491.178 vs finer strip;
  decision figure `docs/rse/decks/casey-dm-calibration-2026-07-19/casey_dm_strip_CORRECTED.png`).

## Question

Re-derive per-burst DMs with declared authorities. (a) casey calibration
first: owner picks from the corrected-sign strip; codify the structure/onset
metric that reproduces the pick blind. (b) Run that metric on all 12 (both
telescopes' products), producing per-burst: fit DM (catalog, with σ),
structure-aligned DM, the scattering-bias gap, and an owner-reviewed strip.
(c) Adjudicate the **input-authority table**: which DM serves which purpose
(measurement tables vs product alignment vs TOA reference). Fit DMs are
scattering-biased high (marker-dependence); the manuscript DM catalog is not
rewritten here — its role is scoped. Output: authority table in the registry
+ per-burst DM certificates.
