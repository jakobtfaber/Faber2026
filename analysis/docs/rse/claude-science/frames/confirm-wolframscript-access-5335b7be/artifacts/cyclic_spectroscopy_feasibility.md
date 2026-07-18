# Cyclic-spectroscopy feasibility for CHIME-band FRB scintillation

**Scope.** Assess whether cyclic spectroscopy applied to the CHIME complex baseband voltages
can convert the current CHIME scintillation-bandwidth *upper limits* into *resolved, per-burst
detections* — the one avenue Wolfram Agent One nominated as a potential signal-to-noise
wall-breaker. Verdict up front: **it is not a wall-breaker; it is a systematics tool.** The
detail below says exactly where it can and cannot help, per burst.

## 1. What the data actually are

- The 12 CHIME co-detection sightlines have **complex per-channel baseband voltages** staged as
  `singlebeam_<id>.h5` (CHIME `baseband_analysis` products; ~1 GB each). These are the raw
  voltages cyclic spectroscopy would require — they exist.
- The Faber2026 CHIME scintillation pipeline (`baseband_recovery/upchannelize_chime.py`)
  **already** operates on those voltages: it (1) coherently dedisperses at the burst DM, which
  removes the intra-channel dispersive chirp *exactly*, and (2) PFB-upchannelizes each
  0.390625 MHz coarse channel by a per-burst factor U (16–512) to expose the sub-channel
  scintle, forming a Stokes-I dynamic spectrum with a flat synthesized passband.
- **Consequence for this study:** cyclic spectroscopy would not be "using the voltages instead
  of intensity." It would have to beat a method that is *already coherent* (already de-chirped,
  already de-scalloped). That removes the two systematics — intra-channel smearing and
  PFB channel-edge response — that cyclic spectroscopy would otherwise be brought in to fix.

## 2. The physics: why cyclic spectroscopy does not add S/N for a single burst

Cyclic spectroscopy (Demorest 2011, MNRAS 416, 2821) recovers the ISM impulse response h(t)
from a **periodic** pulsar. Its leverage comes from two things a pulsar has and a single FRB
does not:

1. **Cyclic frequencies at harmonics n/P of the spin period P.** These carry the phase
   information that lets the wave field — not just its squared modulus — be measured, yielding a
   *coherently descattered* impulse response from a single snapshot. A single aperiodic burst
   has **no period and therefore no intrinsic cyclic frequencies**; the only modulation is the
   burst envelope itself.
2. **Coherent averaging over many periods**, which is what actually builds the pulsar S/N.
   A single FRB is one event.

For a single burst the total statistical budget is the **time–bandwidth product N = W·B**,
where W is the (scattering-broadened) burst width and B the processed bandwidth — and this is
the *same* budget whether the estimator is the intensity ACF or a cyclic spectrum. Both are
different projections of the same N independent samples. Confronted directly with this framing,
Agent One agreed without reservation: *no S/N gain over the ACF, no cyclic frequencies for a
single burst, delay resolution set by 1/B* — a reversal of its initial (overclaimed) "coherent
methods can recover structure below the incoherent threshold." The correction is the correct
physics; the initial claim conflated the pulsar case with the single-burst case.

## 3. Where cyclic spectroscopy *could* still help: delay-domain systematics

The one genuine benefit is not sensitivity but **separation in the delay (lag) domain**. The
diffractive bandwidth Δν_d is conjugate to a scattering delay τ ≈ 1/(2πΔν_d). The
upchannelization comb — residual coarse-channel structure at 0.390625 MHz — sits at a delay of
**2.560 μs and its harmonics**. If the scattering tail τ is well separated from that comb delay,
a delay-domain (cyclic / secondary-spectrum) representation can *isolate the astrophysical tail
from the instrumental comb* in a way the raw ACF (where both pile up at small lag) cannot. This
is a bias-control benefit, not a detection benefit.

## 4. Per-burst feasibility table

Δν_d@600 = dominant (narrower) predicted diffractive scale at 600 MHz that the pipeline sizes U
against (host scale or NE2025/NE2001 Milky-Way floor). τ@600 = 1/(2πΔν_d). Comb delay = 2.560 μs.
"delay-separable" flags whether τ sits clear of the comb delay and its first harmonics (±30%).
N_TB = W·B with B = 400 MHz and W the observed burst width at 600 MHz — the
scattering-broadened width where a τ_600 estimate exists (freya, zach, chromatica, wilhelm,
hamilton, johndoeII), otherwise the intrinsic FWHM (casey, whitney, phineas, mahi, oran, isha).
The distinction does not affect the conclusion: N_TB is 10^4–10^7 either way.

| burst | kind | U | Δν_d@600 (MHz) | τ@600 (μs) | τ / comb (2.56 μs) | delay-separable from comb | W_obs (ms) | N_TB=W·B | recover |
|---|---|---|---|---|---|---|---|---|---|
| casey | host-dominated | 16 | 0.1870 | 0.85 | 0.33 | yes | 0.180 | 7.2e+04 | Y |
| whitney | MW-floor | 16 | 0.1400 | 1.14 | 0.44 | yes | 0.486 | 1.9e+05 | Y |
| phineas | MW-floor | 16 | 0.2060 | 0.77 | 0.30 | yes | 2.989 | 1.2e+06 | Y |
| mahi | MW-floor | 512 | 0.0036 | 44.21 | 17.27 | yes | 24.286 | 9.7e+06 | Y |
| freya | MW-floor | 64 | 0.0388 | 4.10 | 1.60 | NO (τ≈comb harmonic) | 1.070 | 4.3e+05 | Y |
| zach | MW-floor | 64 | 0.0360 | 4.42 | 1.73 | NO (τ≈comb harmonic) | 2.100 | 8.4e+05 | Y |
| chromatica | MW-floor | 64 | 0.0353 | 4.51 | 1.76 | NO (τ≈comb harmonic) | 0.530 | 2.1e+05 | Y |
| wilhelm | MW-floor | 64 | 0.0259 | 6.14 | 2.40 | NO (τ≈comb harmonic) | 1.040 | 4.2e+05 | Y |
| oran | MW-floor | 128 | 0.0239 | 6.66 | 2.60 | NO (τ≈comb harmonic) | 74.200 | 3e+07 | Y |
| hamilton | single-block | 64 | 0.0386 | 4.12 | 1.61 | NO (τ≈comb harmonic) | 0.110 | 4.4e+04 | n |
| johndoeII | single-block | 512 | 0.0058 | 27.44 | 10.72 | yes | 1.700 | 6.8e+05 | n |
| isha | unresolvable | 256 | railed | — | — | — | 1.805 | 7.2e+05 | n |

**Reading the table.**
- **"delay-separable = yes" (casey, whitney, phineas, mahi, johndoeII):** here τ sits clear of
  the 2.56 μs comb and its low harmonics, so a delay-domain method has a real systematics
  advantage — it can quarantine the comb. casey/whitney/phineas have τ *below* the comb delay
  (broad host/MW scintle); mahi/johndoeII have τ far *above* it (very narrow scintle).
- **"delay-separable = NO" (freya, zach, chromatica, wilhelm, oran, hamilton):** τ@600 lands at
  1.6–2.6× the comb delay — i.e. squarely on the 2nd/3rd comb harmonics. For exactly these
  finely-upchannelized (U≥64) bursts, delay-domain separation offers **no clean advantage**,
  because the astrophysical tail and the comb harmonics overlap in the delay domain. This is the
  same population where multiplicative and covariance-space de-comb already failed.
- **N_TB is large for all bursts (10^4–10^7)** yet CHIME still yields zero robust detections.
  That is the signature of an **S/N-per-sample / noise-correlation** limit, not a
  sample-count or resolution limit — consistent with the established injection-recovery result
  (the estimator recovers an injected scintle down to ~0.02 MHz; the wall is real-noise S/N).
  Because cyclic spectroscopy does not change N or the per-sample S/N, it cannot move these
  bursts across the detection threshold.

## 5. Verdict and recommendation

1. **Cyclic spectroscopy is not a viable route to per-burst CHIME scintillation-bandwidth
   detections for this dataset.** It carries no S/N advantage over the ACF for single aperiodic
   bursts (budget = W·B, identical), and the pipeline already applies the coherent de-chirp and
   PFB de-scallop that would otherwise be its motivation. The current decision — report CHIME as
   censored upper limits, let DSA carry the scintillation science and the α fit — stands.
2. **Its only defensible use here is as a delay-domain bias check on the ~5 bursts whose τ is
   clear of the comb** (casey, whitney, phineas, mahi, johndoeII): a secondary-spectrum /
   cyclic representation could confirm that no residual comb harmonic is contaminating the ACF
   small-lag region. This validates the *limits*; it does not produce detections. For the six
   U≥64 bursts whose τ coincides with comb harmonics it adds nothing new.
3. **The genuinely fundamental statement:** the CHIME scintle is expected at ~0.02–0.04 MHz
   (host/MW floors), barely above the 0.02 MHz recovery floor, and the limit is correlated-noise
   S/N per burst. No re-projection of the same W·B samples — ACF, cyclic spectrum, or secondary
   spectrum — can extract signal that the per-sample S/N does not contain. Sensitivity-limited,
   not method-limited.

## Provenance

- Complex baseband existence, coherent-dedispersion + PFB upchannelization method, and per-burst
  U / DM / FWHM / recoverable flags: `dsa110-FLITS/analysis/scattering-refit-2026-06/`
  `baseband_recovery/upchannelize_chime.py` (read in-repo this session).
- DSA diffractive-bandwidth / τ / α context: `dsa110-FLITS/results/consistency.csv` and the
  per-burst DSA Lorentzian fits under `analysis/scintillation-dsa-lorentzian-2026-07-07/`.
- Cyclic-spectroscopy physics anchor: Demorest 2011, MNRAS 416, 2821 (cyclic spectral analysis
  of radio pulsars — measures wave phases / ISM impulse response from a single snapshot of a
  *periodic* source).
- Scaling and delay/time-bandwidth arithmetic independently computed in numpy (reproduced Agent
  One's ν^α scaling exactly); cyclostationarity assessment cross-checked against Agent One, whose
  corrected answer agrees with the independent physics.
- Agent One is a reasoning agent over Wolfram tools, not a bare kernel; every quantitative claim
  above was verified independently before being recorded here (per project convention).
