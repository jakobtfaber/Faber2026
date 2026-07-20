# Adjudicate the scint-input DM authority (calibrated on casey)

- Type: `wayfinder:grilling` (HITL — figure-driven; session must display PNGs full-size)
- Status: **closed 2026-07-19 — SUPERSEDED by the stratified restructure.**
  Its content (casey calibration, DM-authority adjudication) is carried by
  [ticket 18](18-redo-dm-analysis-certified.md) within the data-integrity
  data chain (verification-protocol). No decision was reached here.
- Assignee: —
- Blocked by: —
- Blocks: remediation rollout to 11 bursts → scint campaign re-run → [02](02-ratify-chime-scintillation-method.md)
- Map: [ApJ submission](../map-apj-submission.md)
- **Resume context (read FIRST):**
  `docs/rse/specs/handoff/handoff-2026-07-19-14-56-scint-input-remediation-casey-dm-calibration.md`
- **Decision figure:** `docs/rse/decks/dm/casey-dm-calibration-2026-07-19/casey_dm_strip_CORRECTED.png`
  (the SUPERSEDED-signbug-* files beside it have mirrored labels — history only)

## Question

The measured fit DMs (chime_dm catalog) are scattering-biased high and
visibly over-dedisperse the scattered bursts; structure-alignment optima sit
below the catalog per burst. Which DM aligns the scintillation input
products, and by what rule? Concretely, calibrated on casey first:

1. **casey's pick** from the corrected-sign DM strip: 491.148 (−0.06),
   491.178 (−0.03), or a finer strip between — owner's eye decides.
2. **The codified metric** that reproduces that pick blind (structure/onset
   alignment with the corrected-sign transform; peak-S/N is disqualified —
   scattering-biased high).
3. **The rule for the other eleven**: metric-derived structure DM per burst,
   each validated by an owner-reviewed strip; catalog DMs remain the
   manuscript *measurement* — this adjudication governs only the scint-input
   alignment (and the ACF windowing built on it).
4. Then: aggressive RFI recipe sign-off (casey before/after), rollout,
   campaign re-run, and back to the blocked ratification (ticket 02).
