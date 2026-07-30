# Adjudicate the bounded-window Zach component count

- Type: `wayfinder:task`
- Status: open
- Assignee: Orchestrator
- Blocked by: [Regenerate Zach C2D4](joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- GitHub: [Issue #205](https://github.com/jakobtfaber/Faber2026/issues/205)
- Authorization: manuscript-owner approval, 2026-07-22

## Owner decision

- Decision: keep every native 32.768-microsecond DSA-110 sample for all 27
  controlled component-count fits. Choice `native` on card
  `zach-time-resolution`.
- Recorded: manuscript owner, 2026-07-30.
- Basis: a like-for-like comparison of the same archival product at time
  factors 1 and 2, holding the loader, the 12-channel frequency averaging, the
  window and the zero residual dispersion measure identical. Averaging adjacent
  samples to 65.536 microseconds destroys two components that exceed five
  standard deviations at native resolution — one at +2.195 milliseconds from
  the peak at 5.8 standard deviations, one at +2.785 milliseconds at 8.1 — each
  by merging it into a neighbour 0.13 to 0.26 milliseconds away. Six components
  above five standard deviations survive at native resolution; four survive
  after averaging. Averaging therefore changes the count of resolvable
  components in the very burst whose count this ticket adjudicates.
- Evidence: `docs/rse/verify/zach-dsa-resolution-comparison-20260730/`
  (`zach_dsa_resolution_comparison.json`, the figure, and the script that
  regenerates both).
- Input: `zach_dsa_I_262_368_2500b_cntr_bpc.npy`, SHA-256
  `be917e94d89134f699c456b9185422e8cfdbf3d935bbcf4d8b2e798d0ea12b01`.
- Effect: the time sampling is fixed at 32.768 microseconds and is no longer an
  owner decision. It does **not** unblock technical execution on its own: the
  preparation code still delivers 65.5 microseconds because `_build_model`
  re-applies the `MAX_TIME_BINS` cap of 512 after band reconciliation, and no
  band configuration setting overrides that. Delivering this decision requires
  raising the cap to 1024, at roughly double the DSA-110 sample count and a
  corresponding increase in fit time. That code change is the remaining work on
  this ticket.
- Supersedes: the decision recorded on 2026-07-29 selecting 65.536 microseconds,
  which the owner did not make. See
  [Retract the unsupported Zach sampling decision](unsupported-zach-sampling-decision.md).
  The present ratification reaches the opposite conclusion on evidence that now
  exists.

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
