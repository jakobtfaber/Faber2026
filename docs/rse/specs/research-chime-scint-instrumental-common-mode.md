# Research: why CHIME scintillation bandwidth estimation fails — the common-mode instrumental response

**Date:** 2026-07-14
**Scope:** internal codebase + retained freya CHIME product (direct measurement)
**Initial measurement state:** Faber2026 `main` @ `3e59e9a`, pipeline submodule pinned at `91a5120` (working tree `0da7f9` on `scint/c1-allpairs-crossgp`)

**Post-experiment correction:** checked 2026-07-15 against Faber2026 `b62282c` and pinned pipeline `1085de0`; P1 refuted the original second-stage-window attribution as described below
**Related Documents:**
[report-chime-scintillation-inventory-2026-07-14.md](report-chime-scintillation-inventory-2026-07-14.md) ·
[research-chime-scint-measurement.md](research-chime-scint-measurement.md) ·
[plan-chime-scint-corrected-products-revival.md](plan-chime-scint-corrected-products-revival.md) ·
[decision-2026-07-14-figure1-and-chime-c1.md](decision-2026-07-14-figure1-and-chime-c1.md) ·
[P1 result](../../../pipeline/analysis/chime-scintillation/experiments/p1-window-upchan/RESULT.md) ·
[P2 result](../../../pipeline/analysis/chime-scintillation/experiments/p2-routeb-voltage/RESULT.md)

## Question / Scope

Every CHIME scintillation qualification route (H0, A1, H2, H3, B3, B4, C1,
notebook replay, trigger calibration) failed for the same stated reason: at the
real burst's modulation (`m ≈ 0.15–0.17`) the Lorentzian signal is comparable
to residual structure after off-pulse template removal, and the off-pulse null
fails. **What is that residual structure, where does it come from, and is it
fundamentally separable from scintillation on the retained intensity product?**

In scope: the retained freya polarization-resolved upchannelized product, the
estimator's signal model, and a direct measurement of the off- and on-pulse
frequency cross-ACF. Out of scope: DSA-110, a full PFB simulation, and the
design of the successor product (that is planning work).

## Finding (the missing piece)

**The "residual structure" is a common-mode instrumental frequency response at
the ~35 kHz scale, present identically on- and off-pulse, that the
polarization cross-ACF cannot remove because it is correlated across
polarizations. It is not scintillation. Its effective modulation is `m ≈ 0.77`,
20–26× stronger in ACF amplitude than the nominal source-only scintillation
term (`m² ≈ 0.025`) even before accounting for the burst's 5% dilution, and its
Lorentzian width (35.4 kHz) is the same scale where the pre-P1 routes' fitted widths pin
(36–45 kHz). The retained intensity product does not contain a detectable
scintillation Lorentzian excess on top of this instrumental response.**

### Direct measurement on the retained freya product

Computed the block-demeaned (within 64-channel coarse blocks) frequency
cross-ACF between pol0 and pol1, high band 627–800 MHz, 23 064 fine channels at
6.1036 kHz, 437 time samples. Off-pulse = first 200 time samples; on-pulse =
samples 250–350.

**Off-pulse cross-ACF (pol0 × pol1), normalized by `sqrt(var0·var1)`:**

| lag (kHz) | cross-corr | auto-corr (pol0) |
|---|---|---|
| 6.10 | +0.587 | +0.759 |
| 12.21 | +0.452 | +0.514 |
| 18.31 | +0.357 | +0.352 |
| 24.41 | +0.284 | +0.245 |
| 30.52 | +0.257 | +0.192 |
| 36.62 | +0.258 | +0.191 |
| 42.73 | +0.268 | +0.208 |
| 48.83 | +0.220 | +0.177 |
| 54.93 | +0.141 | +0.113 |
| 61.04 | +0.079 | +0.059 |

This is **off-pulse** — there is no scintillation here, no burst signal, yet
the two polarizations are 59 % correlated at one fine-channel lag, decaying
over ~35 kHz. A Lorentzian fit (Wolfram, R² = 0.93) gives:

- amplitude `A = 0.586`, width `w = 35.37 kHz`, constant `c = -0.051`
- effective instrumental modulation `m_inst = sqrt(A) = 0.766`

The cross/auto ratio at lag 1 is `0.587 / 0.759 = 0.77` — most of the
frequency structure is **common-mode** (correlated across polarizations), not
independent receiver noise.

### On-pulse vs off-pulse: no scintillation excess

| lag (kHz) | ON cross-corr | OFF cross-corr | ON − OFF |
|---|---|---|---|
| 6.10 | +0.585 | +0.587 | −0.002 |
| 12.21 | +0.465 | +0.452 | +0.013 |
| 18.31 | +0.375 | +0.357 | +0.017 |
| 24.41 | +0.300 | +0.284 | +0.016 |
| 30.52 | +0.264 | +0.257 | +0.007 |
| 36.62 | +0.258 | +0.258 | −0.000 |
| 42.73 | +0.256 | +0.268 | −0.012 |
| 48.83 | +0.211 | +0.220 | −0.009 |

The on- and off-pulse cross-ACFs are **identical** to within ±0.017. There is
no coherent Lorentzian excess on-pulse — the small `+0.017` bump at 12–24 kHz
is not a decaying Lorentzian (it rises then falls then goes negative). The
burst itself is only **5 % above background** (`on/off mean intensity = 1.05`),
so the instrumental structure dominates the spectrum equally on and off pulse.

### The signal-to-instrumental ratio (Wolfram)

At the real burst's modulation `m = 0.15–0.17`, the scintillation Lorentzian
amplitude is `m² = 0.023–0.029`. The instrumental amplitude is `0.586`.

| instrumental removal | residual / scintillation |
|---|---|
| 0 % (raw) | 20–26× |
| 90 % | 2.0–2.6× |
| 99 % | 0.20–0.26× |
| 99.9 % | 0.020–0.026× |

**Even 99 % removal of the instrumental response leaves a residual comparable
to the scintillation signal.** 99.9 % removal is required to get the residual
below 3 % of scintillation. Off-pulse template subtraction is non-stationary
(each realization of the instrumental response differs), so it cannot reach
99.9 %. This is why every template-subtraction / whitening / cross-ACF route
failed at `m ≈ 0.15` and passed at `m = 1.0` (where `m² = 1.0` dominates the
0.586 instrumental term).

## Why the pre-P1 estimator routes failed

The cross-ACF estimator (`pipeline/scintillation/scint_analysis/cross_acf.py:86-158`)
is built on the premise, stated in its docstring: *"Receiver noise unique to
either input has zero expectation, while frequency structure shared by both
inputs — including anything correlated at equal times — remains."* That is
correct, and it is exactly the problem. The instrumental channelization
response **is** shared by both polarizations (it is the same analog chain and
the same digital PFB/FFT), so it survives the cross-ACF. Polarization diversity
removes independent receiver noise; it cannot remove common-mode instrumental
response.

- **H0/A1/H2/H3** — post-hoc correction/whitening of a common-mode response
  estimated from the same data. A per-channel correction cannot subtract a
  response it is part of; the held-out kernel and injection gates fail because
  the "noise" is not independent across channels.
- **B3/B4/C1** — cross-ACF between polarizations or time folds. Removes
  independent noise, retains common-mode instrumental structure. The off-pulse
  null fails (`max |z| = 4.8` in C1) because the instrumental structure is
  present off-pulse; injection recovery fails at low `m` because `m² ≪ A_inst`.
- **Trigger calibration** — zero detection power because there is no
  two-component scintillation signal to find; the "second component" is the
  instrumental response, already present in both the one- and two-component
  models.
- **Notebook replay** — the archived 3.8 MHz and replayed 190 kHz "fits" were
  fitting the instrumental response at different windows; the matched-window
  falsification (24 off-pulse windows reproduce the same width family) is
  exactly the common-mode signature.

## Origin of the ~35 kHz structure — unresolved after P1

The initial code inspection identified a plausible mechanism: the retained
upchannelization
(`pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:248-266`)
uses `baseband_analysis.core.sampling._upchannel(fftsize=2*U, downfreq=2)`, an
FFT rechannelization with 2× oversampling and no explicit window. That made
second-stage spectral leakage a testable hypothesis, but not a demonstrated
cause.

P1 subsequently tested that hypothesis on freshly regenerated Freya products
from coherently dedispersed baseband. Rectangular, Hann, and Blackman--Harris
variants at oversampling 2 and 4 all retained essentially the same common mode:
lag-1 cross-ACF `0.587--0.619`, fitted amplitude `0.617--0.684`, and width
`37.4--41.4 kHz`. The predeclared gate required both lag-1 correlation and
amplitude to fall below about `0.059`; every variant failed. Therefore the
specific claim that the retained product's ~35 kHz response is created by the
unwindowed second-stage FFT is **refuted**. The response is introduced earlier
in, or remains invariant through, the shared analog/digital signal chain. Its
precise physical origin is unresolved by these experiments.

The robust finding is narrower: the ~35--40 kHz component is common to both
polarizations, appears off-pulse, and survives all tested rechannelization
windows. It is instrumental with respect to the burst measurement, but this
record does not localize the responsible hardware or processing stage.

## Successor-route adjudication through P3 Gate 0b

The later experiments separated the common-mode problem from the sensitivity
problem:

1. **P1 windowed re-upchannelization: `DOCUMENTED-FAIL`.** Changing the input
   product did not suppress the common mode, so no P1 variant was eligible for
   the blinded C1 calibration.
2. **P2 ratio statistic: common-mode gate passed, sensitivity gate failed.**
   The on/off ratio suppressed the measured amplitude from `0.586` to at most
   about `0.006` in all 24 off-pulse nulls. Width recovery nevertheless failed
   in every admissible low-modulation cell because the burst fraction is only
   about 5%; this demonstrated that common-mode cancellation alone is
   insufficient.
3. **P3 frozen Gate 0b failed; P3-prime was subsequently sanctioned.** The frozen
   block-demeaned estimator forecasts only `1.24 sigma` at 213 kHz. A diagnostic
   without block demeaning restores a `3.0--4.5 sigma` window over 127--352 kHz,
   and the owner sanctioned a new P3-prime specification with global-mean-only
   removal, a frozen `k >= 11` envelope cut, and null-mean-subtracted scores.
   Implementation is in progress; the realistic target remains a calibrated
   upper-limit product, not a likely 5-sigma detection.

The original 5%-burst-fraction arithmetic remains the central scale argument:
at `m ≈ 0.15`, scintillation imprints only about `0.15 × 0.05 ≈ 0.75%` on total
intensity. P2 shows the 59% common mode can be cancelled algebraically, but the
remaining radiometer/self-noise still prevents the inherited lag-space fit
from recovering the width. Any further route must be judged against that
measured sensitivity ceiling, not against the now-refuted window hypothesis.

## Codebase anchors

- `pipeline/scintillation/scint_analysis/cross_acf.py:86-158` —
  `blockwise_cross_acf_pairs`; the common-mode retention premise is in the
  docstring at `:96-103`.
- `pipeline/scintillation/scint_analysis/cross_acf.py:237-259` —
  `_block_demeaned_model_acf`; the block-demeaning high-pass (removes coarse
  comb, not intra-coarse response).
- `pipeline/scintillation/scint_analysis/cross_acf.py:262-392` —
  `fit_cross_lorentzian`; the Lorentzian + constant model fitted to the
  common-mode structure.
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:248-266`
  — `_waterfall`; the unwindowed FFT upchannelization that motivated P1 but was
  not shown to cause the common mode.
- `pipeline/analysis/chime-scintillation/experiments/p1-window-upchan/RESULT.md`
  — direct falsification of the second-stage-window hypothesis.
- `pipeline/analysis/chime-scintillation/experiments/p2-routeb-voltage/RESULT.md`
  — common-mode cancellation PASS separated from width-recovery FAIL.
- `pipeline/analysis/chime-scintillation/INVENTORY.yaml` — the 0/qualified
  inventory; every route's `decisive_failures` trace to the common-mode term.
- Data: `~/Data/Faber2026/dsa110/upchan_codetections/crossacf-2026-07-14/`
  (freya pol0/pol1/intensity npy, 57024 × 437, sha256-pinned in
  `DATA_MANIFEST.yaml`).

## Reproducibility

- Environment: conda `py312` (numpy); Wolfram Local kernel for the Lorentzian
  fit and SNR algebra.
- Code version: pipeline `0da7f9` (working tree, branch
  `scint/c1-allpairs-crossgp`); parent `3e59e9a`.
- Later causal adjudication: pipeline `1085de0` (P1/P2 results); parent
  `b62282c` (P3 Gate-0b result and owner-decision state).
- Data: freya cross-ACF products, sha256 in
  `pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml` (entries
  `freya-crossacf-pol0/pol1/frequencies/metadata`).
- Commands: the two inline `python3 -c` scripts in this session's shell history
  (block-demeaned pol0×pol1 cross-ACF, off-pulse and on-pulse windows); the
  Wolfram `NonlinearModelFit` on the 16 measured lag/correlation pairs.
- No clean-room reproduction run yet — the measurement is deterministic
  (mean spectra, fixed windows) and the data is pinned; a minimal reproduction
  is one `python3` invocation against the pinned npy files.

## Synthesis

The retained detected-intensity product contains a common-mode instrumental
frequency response at the target scale, 20--26× stronger in ACF amplitude than
the nominal source-only scintillation term even before burst-fraction dilution,
that polarization diversity cannot remove.
That observational diagnosis survives. The original causal attribution does
not: P1 shows the response is not removed by windowing or greater oversampling,
so its location in the shared signal chain remains unresolved. P2 then proves
that cancelling the common mode is possible but does not overcome the burst's
radiometer/self-noise ceiling. The publishable negative result is therefore
two-part: the historical estimators were common-mode-confounded, and after that
confounder is cancelled the retained product is still sensitivity-limited for
the inherited width fit. P3-prime is an owner-sanctioned upper-limit route now
in implementation, not evidence that a CHIME bandwidth has been recovered.
