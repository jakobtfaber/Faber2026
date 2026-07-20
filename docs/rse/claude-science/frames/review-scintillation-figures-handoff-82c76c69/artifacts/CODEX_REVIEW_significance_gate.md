# Codex gpt-5.5 (xhigh) review — on-vs-off ACF significance gate
Date: 2026-07-09

## Verdict: NOT sound enough for ApJ as-is. Treat the 9 as candidates, not measurements.

1. NORMALIZATION (risky): normalizing both ACFs by their own lag-0 makes the statistic a
   difference of correlation COEFFICIENTS, not excess correlated POWER. On-pulse lag-0
   self-noise/intrinsic variance suppresses the finite-lag on-pulse ACF by construction,
   can manufacture large negative excess. Fix: model C_on(lag) = a*C_off(lag) + scint + nuisance,
   exclude lag 0 from the detection fit.

2. LAG-BIN BOOTSTRAP (INVALID — highest priority): resampling ACF lag bins treats correlated,
   overlapping bins as independent -> sigma badly overcounted. With effective independent scale
   = measured off-pulse correlation length (tens-hundreds of kHz), mahi 16-18sigma -> ~1.4-2.2sigma,
   zach sb3 -> ~1-1.5sigma. Fix: resample the DATA before the ACF (frequency-domain block bootstrap,
   block >= off-pulse correlation/comb scale) OR pass phase-randomized off-pulse surrogates through
   the full gate to build a per-subband null. Also correct for 48 trials.

3. POSITIVE EXCESS (necessary, not specific): on-pulse-only intrinsic burst spectral structure,
   band-limited envelope, residual bandpass coupling, drift, RFI can all give positive excess.
   Fix: require Lorentzian central lobe + fitted dnu + cross-band Galactic scaling consistency +
   time/pol stability + negative controls (inject smooth/band-limited intrinsic spectra into real
   off-pulse noise, confirm they do NOT pass).

4. FIXED [10,200] kHz BAND (biased): MW dnu scales ~nu^4 (7 kHz@400 -> 138 kHz@800), so the fixed
   band captures more of the high-freq lobe -> biases detections toward high-freq sub-bands.
   Fix: frequency-dependent matched band, or full-ACF likelihood with a dnu prior per sub-band.

5. ORAN/MAHI vs CASEY (red flag): not S/N-driven (MEASURE mean S/N 1.93 vs non-detect 2.03; casey
   sb1/sb2 S/N 5.6/5.0 are upper limits). But of the 9 MEASURE only mahi sb2 + oran sb1 are also
   real:YES in the independence width test. oran sb2 formally 49.8sigma but width-ratio only 1.14,
   real:no -> statistic/error-model artifact, not a 50sigma physical detection.

6. OVERALL: not sound yet. Fix bootstrap null, lag-0/normalization, freq-dependent/fitted detection,
   intrinsic false-positive controls, multiple-testing. Most defensible starting candidates after
   fixes: mahi sb2, oran sb1. Rest must re-earn detection.

## My verification of Codex's central quantitative claim (effective-DOF correction)
Re-scaled sigma by sqrt(n_independent/n_bins) using each sub-band's measured off-pulse correlation
length as the block size. Result: 9 MEASURE -> 6 survive a crude correction (mahi sb2, oran sb0/1/2,
phineas sb1, zach sb3); mahi sb0/sb1 and oran sb3 drop to marginal/upper-limit. Codex's direction
is confirmed: the lag-bin bootstrap inflated sigma. A crude 1/sqrt(corr_ch) correction is itself
approximate (phineas sb1 corr_ch=1 is a low-S/N artifact, not a real independence scale), so even
the surviving 6 need the proper data-level block-bootstrap null before any can be called a detection.
The honest count of robust CHIME detections is AT MOST 2 (mahi sb2, oran sb1) pending the full fix.
