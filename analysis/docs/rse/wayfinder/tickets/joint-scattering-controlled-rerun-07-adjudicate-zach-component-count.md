# Adjudicate the bounded-window Zach component count

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Regenerate Zach C2D4](joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- GitHub: [Issue #205](https://github.com/jakobtfaber/Faber2026/issues/205)
- Authorization: manuscript-owner approval, 2026-07-22

## What to build

Run a new, reproducible Zach C2D3/C2D4/C2D5 comparison after the clean C2D4
morphology rerun. This is a new experiment, not recovery of job 180 and not a
substitute for the injection-calibrated sample-wide statistic in ticket 20.

Use the canonical all-exponential exponentially modified Gaussian family,
native 32.8 microsecond DSA-110 time resolution, unchanged prepared CHIME/FRB
resolution, identical masks, channels, fitted support, prior version, and a
frozen multi-seed schedule. Compare fixed gain-prior variances
`s2 = {1, 10, 100}` only within the same pulse-broadening family and sampler
contract.

## Acceptance criteria

- [ ] C2D3, C2D4, and C2D5 complete under one hash-bound controlled-run contract.
- [ ] Every fitted window contains all owner-identified candidate components.
- [ ] Every component-time prior and posterior remains inside the fitted window.
- [ ] Neighboring counts occupy the same scattering and nuisance-parameter mode.
- [ ] An evidence improvement above 5 has the same direction at every fixed gain-prior variance after numerical uncertainty.
- [ ] Added components coincide with candidate features, have bounded non-null amplitude, and improve local residuals.
- [ ] Reconstructable model products and per-band visual residual diagnostics exist for every rung.
- [ ] Owner morphology review and numerical guards agree before any fitted value or count is promoted.

Statistical failure does not promote a visibly wrong C2D3 fit. It leaves the
owner-confirmed morphology recorded while fitted parameters and count evidence
remain unaccepted. Keep `tau * delta_nu` downstream of fit acceptance.

The inner-scale power-law pulse-broadening model is a conditional sensitivity
test only, at a fixed accepted count, if the canonical fit retains tail-shaped
residuals or boundary behavior.

## Blocked by

- [Regenerate Zach C2D4](joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md)
