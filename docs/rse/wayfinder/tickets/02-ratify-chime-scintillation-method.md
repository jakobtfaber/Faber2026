# Ratify the CHIME-band scintillation method and unblock the full-sample campaign

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: —
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
