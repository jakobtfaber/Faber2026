# Technical-review robustness dispositions

**Date:** 2026-07-22
**Status:** owner accepted 2026-07-23
**Scope:** ApJ Wayfinder ticket 10 only
**Analysis base:** `dfcd1d5e76c48642a3cb83dc7dd7cbd6ca26fc15`

## Decision

The owner accepted the dispositions below as one batch on 2026-07-23. They
preserve the trusted association, foreground-census, and dispersion-budget
lanes; they do not promote any revoked fit or scintillation result.

`In` means required for this submission. `Out` means remove the unsupported
surface instead of building new machinery. `Defer` means the submission may
proceed without the work only with the stated limitation.

| Review item | Disposition | Evidence | Execution consequence |
|---|---|---|---|
| S14: intervening-scattering column | **Out** | The dispersion budget is trusted, but the scattering fits and attribution products remain revoked. The review found no documented dispersion-to-scattering mapping, turbulence normalization, scale priors, or screen geometry. | Drop the intervening-scattering column and dependent prose. Do not invent an appendix mapping before the scattering framework is trusted. Reintroduce only from a separately validated physical model. |
| S16: modulation-index limit versus the two-screen square-root-of-three limit | **Defer into tickets 17 and 02** | The old `m <= 1.5` matrix is a pending campaign-quality product, not a sky claim. Current CHIME products require radio-frequency-interference remediation and a complete rerun; ticket 17 is blocked on the cleaning-boundary gate. The two-screen formalism permits modulation up to about 1.73 in its unresolved limit. | Do not rerun the old matrix or quote its six historical rejections. The remediated campaign must replace the fixed 1.5 rule with a model- and product-specific limit, then report every changed verdict before ticket 02 ratification. |
| S17: pulsar positive control through the complete CHIME chain | **Defer** | Existing injections test estimator recovery, but no known scintillator tests the complete acquisition and upchannelization chain. The manuscript no longer has a qualified sample-wide CHIME non-detection claim, and ticket 17 already requires rebuilt inputs plus fresh owner review. | State that injections validate the estimator, not the complete instrument chain. A pulsar product does not block this submission unless the paper revives a sample-wide instrument-limit or non-detection claim. |
| S13: cluster-aperture sensitivity | **In** | The cluster lane and dispersion budget are trusted. The documented object at `1.25 R500` would add about `95 pc cm^-3`, the sample's second-largest intervening column. This is a result-scale sensitivity, not cosmetic robustness. | Recompute the complete sample at `1.5 R500` and `R200`, preserve `R500` as fiducial, and report an envelope. Propagate any contributor or host-dispersion change before freezing the budget. |
| S4: positive timing-residual mean | **In** | Association arithmetic is trusted; the review recomputed a mean near `+2.4 ms`, about 2.4 standard errors from zero. The residual scale is comparable to the stated clock systematic. | Add the mean with its uncertainty and repeat the association verdicts after subtracting a fitted common offset. Report stability; do not call the offset astrophysical. |
| S5: declination-conditioned CHIME rate | **In** | The exact 64-detection trial set is resolved in ticket 09. Even the review's conservative summed chance expectation near `1.8e-6` leaves large rate headroom. | Add one predeclared rate-multiplier sensitivity using the high-declination exposure. Quote the resulting summed chance expectation and whether any association class changes. |
| S6: repeater and clustering statement | **In, wording-level** | Ticket 09 establishes detections, not statistically independent sources, as the trial unit. The frozen catalog includes a known repeater detection, so silence about clustering leaves the denominator easy to misread. | State the detection-level trial rule and known repeater status. Do not add a time-scramble campaign unless the classification shows that repeated detections materially change the bound. |
| S7: jackknife and masking specification | **In** | The adopted dispersion-measure record already uses channel-block jackknifes and a maximum-of-variations uncertainty, but the manuscript does not define block width, contiguity, masking order, or mask-threshold stability. | Add the exact frozen settings and ordering. Add a threshold-variation sentence from existing products; if that evidence is absent, run only this bounded variation. |
| S8: coverage-calibrated dispersion-measure uncertainties | **Defer with caveat** | The adopted campaign has a held-out injection root-mean-square error of `0.0028 pc cm^-3`, maximum error `0.0062 pc cm^-3`, interior maxima for all 24 fits, and conservative maximum-of-variations errors. It does not establish nominal 68-percent coverage on realistic scattered bursts. | Keep the existing uncertainties, describe them as conservative validation envelopes rather than calibrated confidence intervals, and do not make coverage claims. Require the real-off-pulse coverage campaign before precision population inference, not before this submission. |
| S11: completeness and missing-halo systematic | **In, through the expanded-catalog repair** | The frozen census is trusted for its stored rows, but the expanded-catalog map says authority remains open pending a frozen nine-sightline corpus and independent replay. Absence of a stored candidate is therefore not yet a quantified absence of a group-scale halo. | After the expanded corpus and replay close, use their footprint and depth receipts to bound a missed group-scale halo per sightline. Until then, prohibit the claim that intervening dispersion is small on every otherwise empty sightline. Do not launch a second catalog search. |
| S15b: per-sightline Galactic disk-model comparison | **In** | The budget lane already treats NE2001 and YMW16 as cross-checks, and the trust-reset plan specifies a direct 12-sightline comparison. Ticket 07 accepted the 30-percent disk prior but did not supply the missing transparent comparison. | Emit a compact appendix table for NE2025, NE2001, and YMW16 from the existing validated path. State whether the 30-percent prior covers the model spread; reopen the prior only if it does not. |
| S19a: effective-index sensitivity variant | **Out** | Ticket 14 restricts free-alpha fits to model-mismatch diagnostics and forbids physical interpretation. A separate two-screen forward-model lane owns the surviving physical question. Reviving the parked exponential-tail appendix would duplicate those decisions without resolving geometry. | Do not revive the parked appendix or add effective-index values to result tables. Preserve only the ticket-14 diagnostic framing; route physical chromaticity through the two-screen lane. |
| S19b: broad delta-dispersion-measure prior | **In, at the next trusted refit** | The current `+/-50 pc cm^-3` prior is orders of magnitude wider than measured dispersion uncertainties. Current fit products are revoked, so a standalone audit of their posteriors cannot support the paper. | In the first fit admitted by tickets 13 and 03, compare the current bound with a measurement-informed prior and show posterior concentration. This is a required fit-systematics check, not a reason to rerun revoked products now. |

## Dependency-aware execution order

1. Drop S14; execute S4, S5, S6, S7, and S15b from trusted products.
2. Run S13 and propagate any budget change.
3. Complete the expanded-catalog corpus and replay, then execute S11 from their
   coverage receipts.
4. Carry S16 into the ticket-17 rerun and ticket-02 ratification. Carry S19b
   into the first fit admitted by tickets 13 and 03.
5. Preserve the explicit S8 and S17 caveats; do not start those campaigns for
   this submission. Do not revive S19a.

## Trust and blocker reconciliation

- Trusted now: association/sample, Milky Way foreground, frozen foreground
  census, and dispersion-budget lanes in `results-registry.toml`.
- Pending or revoked: CHIME gate matrix, scattering fits, decorrelation-
  bandwidth products, and two-screen attribution. No disposition above treats
  them as science-ready.
- Ticket 06's probabilistic Phineas crossing and ticket 07's budget-prior
  decision are preserved. Neither answers cluster-aperture sensitivity or
  survey completeness.
- Ticket 09 closes the trial-set denominator and rule, enabling S5 and S6.
- Ticket 14 already closes the reporting boundary that makes S19a unnecessary.
- Ticket 17 and the radio-frequency-interference validation chain own the
  product corrections required before S16 can be tested honestly.

## Decision receipt

Owner accepted the table as a batch on 2026-07-23, as recorded in
[`10-disposition-technical-review-robustness-items.md`](../wayfinder/tickets/10-disposition-technical-review-robustness-items.md).
Execution remains in the lane system and does not itself promote science claims.

## Evidence checked

- `docs/technical_review_triage_2026-07-15.md`
- `docs/rse/control/results-registry.toml`
- `docs/rse/control/BOARD.md`
- tickets 02, 03, 06--10, 13, 14, 17, and the radio-frequency-interference
  cleaning-boundary ticket
- `docs/rse/wayfinder/map-expanded-foreground-catalog-repair.md`
- `docs/rse/specs/verified-dm-adoption-2026-07-13.md`
- `docs/rse/specs/v6-association-dm-report-2026-07-07.md`
- `docs/rse/specs/research-chime-scint-measurement.md`
- `docs/rse/specs/research-phineas-probabilistic-crossing-model.md`
