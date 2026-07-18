# Codex gpt-5.5 (xhigh) review — CHIME de-comb reasoning
Date: 2026-07-09

## Verdict summary
1. Covariance-vs-mean argument: PLAUSIBLE, but the "U=64 → only 2-3 independent samples"
   claim is NOT established and is physically wrong as stated. CHIME upchannelization is
   real voltage-domain channelization (collect successive complex-baseband voltage samples,
   FFT, then form Stokes-I) — NOT interpolation of intensity channels. So fine channels DO
   carry independent information. U alone is not an independence metric. Need measured
   off-pulse covariance / effective rank, or injection through the real channelizer.
2. casey is MOSTLY UNRESOLVED. sb0-2 have HWHM ≈ 1 fine channel (29.8/29.78, 27.4/27.45,
   35.8/35.82) — a resolution floor, not a resolved scintle. These are UPPER LIMITS, not
   clean measurements. casey sb3 (172 kHz = 5 channels, hwhm/coarse=0.44) is intermediate,
   needs individual scrutiny. => "casey is our clean CHIME anchor" is WRONG.
3. hwhm_over_subbw > 0.15 threshold: physically motivated (reject envelope-dominated lobes:
   freya sb0-2, hamilton sb3) but the specific value is arbitrary without injection/recovery
   or stability tests. Also partially circular: gating on comb-on (pre-decomb) central_hwhm.
4. Covariance-space de-comb dismissed too early. Real recovery paths: subtract/model off-pulse
   covariance/ACF; fit ACF = Lorentzian + comb-template nuisance; prewhiten with measured
   channel covariance; split by time/pol to suppress additive-noise covariance; rechannelize
   baseband with different window/bin-phase to test stability. Not guaranteed (off-pulse
   subtraction won't remove multiplicative burst-bandpass coupling; unconstrained comb
   template can absorb real scintillation) but worth trying for broad/intermediate cases.
5. Landing "DSA clean + CHIME measure/upper-limit/reject" is right framing ONLY IF CHIME is
   handled with CENSORED LIKELIHOODS (upper limits), not point estimates. Classification from
   the 4-burst JSON is too optimistic. Only 4/12 bursts here — cannot justify a full-sample
   rule yet.

## Codex's per-subband classification (from the 4-burst comb-on data)
- Reject (envelope): freya sb0-2, hamilton sb3
- Possible measurements after covariance validation: zach sb1, hamilton sb2
- Marginal: casey sb3, zach sb0, hamilton sb0-1
- Upper limits: casey sb0-2, zach sb2-3, freya sb3

## Actionable corrections
- Do NOT call casey clean; do NOT infer independence from U.
- Validate independence with measured off-pulse covariance / effective rank + injection tests
  BEFORE fitting alpha.
- Handle CHIME with censored (upper-limit) likelihoods, not point estimates.
- Re-derive keep/reject on DE-COMBED (not comb-on) ACFs to avoid circularity.
