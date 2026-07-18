# PR-192 estimator — independent validation evidence

**Scope:** dsa110-FLITS PR #192 ("CHIME window-tuning campaign: injection-validated
matched estimator"). The PR *references* an injection harness and a
`window_campaign_2L/` results table but **commits neither** — the evidence lives only
in code comments. Below is an independent reproduction: (A) injection-recovery on the
fitter, (B) the real estimator run end-to-end on our sample.

## A. Injection-recovery on known-truth synthetic ACFs (`inject_recover.py`)
Synthetic ACFs on a 6.1 kHz lag grid; ACF amplitude = m^2 (pipeline norm).

- **T1 gamma recovery, isolated scintle (m=0.7):** ratio = 1.00 at every truth in
  {0.02,0.05,0.1,0.3,1.0,3.0} MHz; 100% resolved. No low-gamma floor.
- **T2 scintle under a broad envelope (gamma_n=0.08, m_n=0.6; envelope m_b=0.7):**
  single-Lorentzian FAILS to resolve the scintle (railed/gated, NaN) for gamma_b in
  {1,2,5} MHz; the 2-component model recovers gamma to ratio 1.00 and is adopted 100%.
  This is the zach-622 / whitney censoring failure the PR targets.
- **T3 false-positive rate of the dBIC>=6 2-comp gate:** 0/150 on envelope-only,
  0/150 on pure noise. The gate does not manufacture scintles.
- **T4 modulation-index recovery (2-comp):** ratio 1.00 at m=0.6 and m=0.9.

**Verdict A:** the two-component fitter, dBIC gate, and physicality caps are unbiased
on known truth. This half of the PR is validated and independently reproduced.

## B. Real-sample run (`run_real.py`, `isolate.py`)
Estimator = window_optimize.select_windows -> window_refit.refit(time_weights=).

### chromatica (the sample's one clean detection)
| window | source | alpha | gamma ladder (hi->lo, MHz) | note |
|---|---|---|---|---|
| [184,198] | MANUAL (validated) | **+1.87 +- 0.25** | 0.102/0.080/0.042/0.043 | all resolved, m<1, monotonic |
| [184,198] + matched wts | MANUAL | **+1.70 +- 0.22** | 0.095/0.071/0.054/0.043 | all resolved, m<1 |
| [177,223] | AUTO select_windows | **-0.05 +- 0.48** | 0.002/0.059/0.050/0.071 | top subband m=3.16 unphysical |

The PR-192 **fitter reproduces the manual chromatica detection** (+1.87, consistent
with the prior +2.03+-0.23). The PR-192 **automated window** (burst 46 bins vs the
correct 14) is ~3x too wide, ingests scattering tail/adjacent structure, and destroys
the detection.

### zach / whitney (auto windows)
- zach auto burst=[220,277] off=[0,163]: 4/4 subbands "resolved" 2L but alpha=-0.32+-0.46,
  non-monotonic (g 0.055/0.139/0.164/0.036) — same over-wide-window signature.
- whitney auto burst=[1014,1062]: mixed 1L/2L, two subbands m>1.2 (censored), alpha n/a.

**Verdict B:** the estimator RUNS end-to-end on the real sample, but its automated
window-selection half does not yet match the hand-tuned windows — it selects
over-wide burst windows that break the one unambiguous detection (chromatica) and
produce non-physical ladders on zach/whitney.

## Bottom line
- Fitter (2-comp + gates): **validated**, keep.
- Automated window selection: **not yet trustworthy** on this sample — needs the
  burst-window width tightened (it should not exceed the scintle-bearing core) and
  re-checked against chromatica's known-good ladder before it can be the primary path.
- Keep window_tuning.ipynb (merged #191) as the trusted fallback, as agreed.
