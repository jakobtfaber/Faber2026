# Assessment: ChatGPT review of the scintillation "de-combing" code

Date: 2026-07-09. Context: a ChatGPT review of the CHIME scintillation
artifact-control code in `Faber2026/pipeline` argued that the "de-combing" is
only a partial mitigation, that the harmonic mask is silently dropped in the
Lorentzian driver, and that CHIME configs carry a non-uniform mitigation stack.
This note records (a) the code audit verdict on each factual claim and (b) what
was implemented in response.

## Factual claims — all verified against the code

Every specific, checkable claim in the review holds against the actual repo:

- The three artifact controls (bandpass flat-fielding, gapped-grid
  regularization, harmonic lag mask) exist and are wired as described
  (`pipeline.py`, `freya_scintillation.py`, `analysis.py:harmonic_lag_mask`).
- The harmonic mask masks lags near k·0.390625 MHz (k≥1), default half-width
  0.05 MHz, leaving the zero-lag region to the fit window — exactly as claimed
  (`analysis.py:658`).
- The mask was wired into the generic `_fit_acf_models` path but **not** into
  the dedicated Lorentzian driver `run_dsa_lorentzian_fits.py`, which called
  `_slice_fit_window` → `compare_lorentzian_components` directly. Confirmed —
  this was a real gap and a latent `--band chime` trap (the CHIME YAML enables
  the mask, the driver ignored it). No CHIME run had been executed yet, so no
  published number was affected.
- Config non-uniformity is real: `bandpass_normalization` is present in only
  `freya_chime_hi.yaml`; `casey_chime.yaml` / `casey_chime_hi.yaml` carry the
  harmonic mask but no grid/bandpass blocks and use polynomial baseline
  subtraction.
- The freya CHIME retraction, the 35.19→42.21 kHz mask shift, and the ~37.7 kHz
  off-pulse-null median all trace to
  `experiment-freya-chime-instrumental-origin.md` (arms A/B1), which recommends
  the off-pulse null become a standing pipeline check ("Next Steps" #1).

The review is well-grounded, not hallucinated.

## Recommendations — disposition

| # | Recommendation | Disposition |
|---|---|---|
| 1 | Make harmonic masking a first-class ACF-fit mask; write removed-bin count to JSON | **Implemented.** `apply_harmonic_mask_to_fit` applied in `_fit_prepared_config` before the selector; `harmonic_mask.n_bins_removed` per sub-band. |
| 2 | Fail closed for CHIME if mitigation incomplete (grid, bandpass, harmonic, fit-window records) | **Implemented.** `chime_provenance_status` requires grid + bandpass + harmonic enabled; else `diagnostic_only`. Fit-window status is already recorded per sub-band (`fit_range_mhz`, `n_fit_points`, sub-band selection block). |
| 3 | Require an off-pulse ACF null for every CHIME measurement | **Implemented.** `_off_pulse_null_widths` + `off_pulse_null_verdict`; a failed null forces `diagnostic_only`. Verified to fire on real freya CHIME (ratio ~1.1). |
| 4 | Require low-lag excision stability | **Implemented.** `_low_lag_excision_widths` (drop first 1–3 channel lags) + `low_lag_stability_verdict`; collapse forces `diagnostic_only`. |
| 5 | Report harmonic-mask sensitivity as a systematic, not a correction | **Implemented.** `harmonic_mask_systematic` reports masked vs unmasked width + fractional band; documented as a systematic in the report prose. |
| 6 | Do not use CHIME-side de-combed values for screen attribution until they pass split-band scaling, split-time persistence, off-pulse null, and DSA consistency | **Policy — partially enforced by code, rest is manuscript discipline.** The off-pulse null and DSA-vs-CHIME contrast are now enforced automatically. Split-band ν^4.4 scaling and split-time persistence are experiment arms (D2/E3/B4) not yet promoted into the driver; screen attribution from CHIME remains gated by the manuscript's existing decision to quote the DSA-side Δν only. Recommend keeping #6 as a review checklist item, not asserting it via code alone. |

## Overall

The review's core scientific point is correct: the harmonic mask is a
lag-exclusion diagnostic, not true de-combing, and it does not prove a residual
is physical. The code now treats it that way — the mask is applied and its
sensitivity reported as a systematic, while the *decision* to trust a CHIME
number rests on the off-pulse null, low-lag stability, and provenance gate,
which is where the physics actually lives. Recommendations 1–5 are implemented
and tested; #6 is retained as manuscript-level discipline with the two enforced
sub-tests (off-pulse null, DSA consistency) now automated.
