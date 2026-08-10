# Experiment P2 (Route B): voltage-derived common-mode-immune Δν_d statistic — freya, CHIME band

---
**Date:** 2026-07-15
**Author:** Claude (Fable 5), under the owner's 2026-07-15 Route-B sanction
(research-chime-scint-successor-routes.md, "voltage-data method should be tried
already just now"; calibrator-data ask declined — in-house only)
**Status:** PREDECLARED — thresholds frozen below; no on-pulse statistic may be
computed before gates G1 and G2 pass; any gate failure is a terminal
`DOCUMENTED-FAIL` with no unblinding
**Related documents:**
- [Gate 0 detectability](../experiment/experiment-chime-scint-gate0-detectability.md) — GO with admissibility window
- [Successor-route assessment (sanctioned)](../research/research-chime-scint-successor-routes.md)
- [C1 blinded calibration](../experiment/experiment-chime-scint-c1-calibration.md) — the freeze/calibrate/null/unblind template this record follows
---

## Signal model and why this can evade the common mode

Per-polarization detected intensity on the fine grid:
`I_p(ν,t) = g(ν,t)·[ f_p·B(t)·s(ν) + N_p(ν,t) ]` where `g` is the common
instrumental response (the measured 35 kHz, A=0.586 structure — multiplies
*everything*), `s(ν)` the scintillation gain (common to both pols, multiplies
*only the source term*), `B(t)` the burst profile, `f_p` the pol flux, `N_p`
independent receiver noise. Every failed route worked on quantities in which
`g` survives. The Route-B statistic family works on quantities in which `g`
cancels **algebraically**, not by subtraction of a noisy template.

## Frozen statistic family (all three computed; selection rule below)

1. **S1 — on/off ratio cross-ACF:** per pol, `R_p(ν) = ⟨I_p⟩_on / ⟨I_p⟩_off − 1`;
   `g(ν)` cancels exactly if stable across the 437-sample frame (the measured
   on/off cross-ACF identity, ±0.017, is direct evidence of frame-scale
   stability). Then the pol0×pol1 cross-ACF of `R_p` removes pol-independent
   radiometer structure. Signal: `f_b·s(ν)` common to both pols.
2. **S2 — time-split ratio cross-ACF:** split on-pulse into two halves, form
   `R^{(1)}_p, R^{(2)}_p` against disjoint off-pulse halves, cross-ACF
   `(R^{(1)}_{p0}+R^{(1)}_{p1}) × (R^{(2)}_{p0}+R^{(2)}_{p1})`. Kills noise
   bias at all lags (independent noise between time halves) at the cost of √2
   sensitivity.
3. **S3 — voltage cross-spectral variant:** same ratio construction on
   `|V_p|²` computed from the P1 complex fine-channel voltages before Stokes
   aggregation, preserving the exact grouped-bin noise normalization from the
   P1 worker. Included because the voltage product allows exact noise-bias
   bookkeeping; expected to agree with S1 in the mean.

**Selection rule (frozen):** the statistic used for the unblinded fit is the
one with the best G1 injection-recovery calibration score; ties break S2 → S1
→ S3 (bias immunity preferred over raw sensitivity).

## Frozen gates

**G1 — injection recovery (burst-blind).** Inject synthetic scintillation
(`m ∈ {0.15, 0.17}`, `Δν_d ∈ {35 (must-fail control), 77, 127, 213, 352} kHz`,
50 realizations per cell) into real **off-pulse** frames relabeled as
synthetic on-pulse, through the full statistic + Lorentzian fit. PASS requires,
for every cell with `Δν_d ≥ 127 kHz`: median recovered Δν_d within ±30 % of
injected; amplitude pull `|z| ≤ 2`; ≥ 90 % of realizations converged. The
35 kHz control must NOT certify (its certification would prove the calibration
is broken).

**G2 — null campaign (burst-blind).** ≥ 24 disjoint off-pulse-only pseudo-on
windows through the selected statistic; PASS requires no fitted amplitude
exceeding the two-sided 3σ level after Šidák family-wise correction at 5 %.

**G3 — admissibility (applies after unblinding).** A detection claim requires
fitted `Δν_d` inside the Gate-0 ≥3σ window (≥ 77 kHz at m=0.17, ≥ 127 kHz at
m=0.15) AND fitted significance ≥ 5. Anything else is reported as the censored
exclusion: "no CHIME-band scintillation with Δν_d above the window at
m ≥ 0.15; smaller Δν_d unconstrained (radiometer-limited)."

**Unblinding rule.** The on-pulse statistic is computed exactly once, after G1
and G2 both pass, with the selected statistic and frozen fit configuration.
No threshold, window, or statistic change after first sight of on-pulse data;
a post-hoc change creates a new experiment requiring fresh owner sanction.

## Data and provenance (all in-house; no external requests)

- Input: coherently dedispersed freya baseband products on h17 under
  `/data/research/astrophysics/frbs/chime-dsa-codetections/upchan_codetections/`
  (the P1 regeneration assets, SHA-256s in the P1 validation bundle), rectangular/os2
  variant = bit-identical to the retained production product.
- Windows: on-pulse samples 250–350, off-pulse 0–200 and the post-burst
  remainder, matching the common-mode research record.
- All code lands in the FLITS repo (`scintillation/` + an
  `analysis/chime-scintillation/experiments/p2-routeb-voltage/` record with
  RESULT.md + validation.json + INVENTORY.yaml entry), then a Faber2026 pin
  bump — the C1/P1 landing pattern.

## Deliverables

1. FLITS PR: statistic implementations + G1/G2 harness + frozen-config file
   (hash-recorded), diagnostic figures for visual vetting (per the standing
   uniform-methods/visual-vetting preference).
2. Verdict: `qualified measurement` (G3 detection), `censored exclusion`
   (G3 non-detection), or `DOCUMENTED-FAIL` (G1/G2 failure) — all three are
   terminal, reportable outcomes for the manuscript.
