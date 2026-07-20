# Ratify the CHIME-band scintillation method and unblock the full-sample campaign

- Type: `wayfinder:grilling` (HITL)
- Status: open — **BLOCKED 2026-07-18 by owner data review** (input defects;
  see `docs/rse/specs/owner-data-review-findings-2026-07-18.md`): RFI
  unexcised in CHIME upchan + DSA central channel; over-dedispersion in ≥9
  upchan products; per-burst DM inconsistency between CHIME products
  (up to ±0.13 pc cm⁻³ ≈ 2.6 ms sweep). Ratification resumes only after
  remediation + campaign re-run + fresh input/ACF review. Grilling decisions
  already recorded: bar = campaign's own predeclared gates with five-term
  contract mapping (owner choice (a)); τ·Δν_d excluded from any ratification.
- **Re-wired 2026-07-19 (stratified restructure):** Blocked by
  [22](22-redo-scintillation-certified.md) — the campaign re-run on
  certified inputs. Resumes as the last step of stratum 6.
- Assignee: claude (cowork session, with owner)
- Blocked by: [22](22-redo-scintillation-certified.md)
- Scope expanded 2026-07-18: also covers the **2L scint table ratification**
  (owner-decision item from handoff-2026-07-18-14-51) — same conversation.
- Blocked by: [22](22-redo-scintillation-certified.md)
- Map: [ApJ submission](../map-apj-submission.md)

## Question

The owner states (2026-07-18) that working scintillation-analysis methods now
exist for both the CHIME and DSA bands — postdating the documented record, in
which three CHIME qualification routes closed DOCUMENTED-FAIL and the
delay-domain optimal-estimator + envelope-model pair ended with a calibrated
estimator but no separable detection. Which method is the qualifying CHIME
route? Name it descriptively, point at its artifacts/PRs, and state the
qualification evidence (calibration, gates passed) that ratifies it.

**Concrete candidate identified 2026-07-18 (claude-science lane,
proj_55f9c893cfe1):** the R5/R6 two-band campaign — FLITS #201 merged at
`666306d1` (`window_refit.py` with per-subband null, campaign driver,
two-band scripts); Faber2026 PR #140 stages the pin bump + five finalized
figures. Pinned science: chromatica detection (+1.72, n=4), zach detection
(+3.03, n=3), hamilton diagnostic_only, freya non_detection;
τ·Δν_d = 26.7/61.0/386.7/1.3. Ratification should name this campaign, cite
its calibration/null evidence, and record what supersedes the earlier
PR #192 chromatica_hi/oran picture. Registry row:
`scint.two_band_campaign`. On
ratification, record that the freya-qualification blockade is lifted so the
full-sample campaign (burst configs for the four unconfigured sightlines,
regeneration for the six never-generated co-detections, ACF/decorrelation-
bandwidth measurements across the sample, two-screen rebuild on joint
CHIME+DSA products) can execute in the lane system — under the re-trust
validation contract, since the existing DSA-band fits are also revoked.
