# Referee-Style Review — Faber et al. (2026 draft)

**Manuscript:** "Scattering, Scintillation, and Energetics of Fast Radio Bursts Codetected by CHIME/FRB and DSA-110"
**Review date:** 2026-07-07
**Scope note:** The scattering, scintillation, turbulence, and energy sections are to-be-added; the author confirms they will be included and contextualized by the per-sightline analysis. This report therefore treats the present draft as the completed paper's skeleton: it reviews the association, foreground-census, and dispersion-budget material as near-final, and gives design-level feedback on the pending sections rather than objecting to their absence.

**Recommendation (current material):** Major revision — primarily uncertainty quantification, not structure or method.

---

## Overall assessment

The core idea is strong and publishable: a 12-burst CHIME/FRB–DSA-110 co-detection sample with a ~1 GHz lever arm, a physically self-consistent β-based scattering closure (co-modeling PBF shape and α through the turbulence spectral index rather than fitting a fixed PBF with α free), and a careful sightline-by-sightline foreground census. The methods are unusually rigorous: the gain-marginalized likelihood, the matched-grid evidence comparison for component multiplicity, and the explicit distinction between "unconstrained" and "zero" foreground terms are all commendable and should be preserved verbatim in spirit.

The single most important revision across all present material: **no quantity in the draft currently carries an uncertainty.** The association, census, and budget sections are otherwise close to publishable.

---

## Blocking items (independent of the pending sections)

### B1. Uncertainties in the dispersion budget (Table `tab:budget`)
DM_host is a residual of four terms, each with substantial error:

- Macquart-mean cosmic variance: σ(DM_cosmic) is ~40–100% of the mean at z ≲ 0.5;
- NE2025 disk model uncertainty;
- the 40 pc cm⁻³ MW-halo prior spans at least a factor ~2 in the literature (Yamasaki & Totani 2020 vs. Keating & Pen 2020; Cook et al. 2023);
- the two-phase mNFW intervening model (mass, f_gas, cool-phase clumping).

Reporting DM_host = 45, 30, 17… as point estimates invites over-interpretation; "host residuals are modest" is not defensible without error bars. The table comment references a "prior-predictive sensitivity analysis" quantifying P(DM_host < 0) — that analysis must appear in the paper, not be alluded to.

Preferably, follow the now-standard forward-modeling approach: subtracting the *mean* of the highly skewed P(DM_cosmic|z) biases every residual, not just the two negative ones. Report host posteriors from the full distribution (Macquart et al. 2020; James et al. 2022) rather than arithmetic residuals. The current prose treatment of the negative residuals (bounding scatter about the cosmological mean) is correct in words; make it probabilistic.

### B2. Uncertainty on the intracluster column (~160 pc cm⁻³)
The FRB 20230307A cluster contribution appears in the abstract, results, and conclusions as a bare "of order 160 pc cm⁻³." The mNFW extrapolation to cluster scale, the richness-based M_500 from Wen & Han (2024), f_gas, and the cool component each carry factor-level uncertainties — quote a range or error bar. Additionally, mNFW profiles calibrated on ~L* halos (Prochaska & Zheng 2019) are not obviously valid at log M_500 = 14.1; cross-check against an X-ray/SZ-calibrated ICM profile (e.g., GNFW; Arnaud et al. 2010) or a β-model as a systematic.

### B3. P_cc trials factor
Eq. for μ_i conditions on the CHIME background rate against fixed DSA events, and Σμ_i is summed over the 12 pairs. That is correct only if the 12 DSA bursts are the full trial set. State explicitly the number of DSA-110 detections searched over the two-year overlap (the denominator); if hundreds of DSA bursts were scanned against the CHIME stream, the look-elsewhere correction belongs in Σμ.

### B4. Timing residuals lack errors and a criterion
Table `tab:sample` gives Δt to ±0.01 ms with no per-burst uncertainty and no stated acceptance threshold; residuals reach +8.41 ms (FRB 20220506D). What residual would have *failed*? A residual column without errors and a criterion is not a test. Also state the sign convention and the expected geometric-delay range for the CHIME–OVRO baseline (|τ_geo| ≲ 11 ms) so readers can judge the residuals.

### B5. Non-citable internal materials
Load-bearing claims are deferred to "internal validation materials" / "companion software archive" (per-telescope DM agreement, §Obs; association cross-checks, §ToA; data provenance, §Data). ApJ policy and reproducibility require these in the manuscript, an appendix, or a citable archival product. Plan the Zenodo release path now — the Data Availability TODO already anticipates it — and replace every internal-materials reference with a pointer to that section.

---

## Design decisions for the incoming scattering/scintillation sections

These are choices best made *before* the sections are written, because the per-sightline attribution ledger inherits them.

### D1. Galactic-vs-extragalactic α inconsistency
The screen-attribution logic (Discussion scaffold) first asks whether the Galactic contribution explains the scattering, using NE2025 τ predictions scaled with a *fixed* Kolmogorov α = 4.4 — while the paper's central methodological thesis is that fixing a scattering family with an assumed α biases inference. Decide now: is the Galactic comparison done at fixed α = 4.4, or propagated over the fitted β posterior? Otherwise every per-sightline verdict inherits an inconsistency a referee will find. At minimum, acknowledge the asymmetry explicitly in §Obs-MW.

### D2. β = 4 degeneracy with the inner-scale regime
The α = 2β/(β−2) closure assumes a thin screen with the diffractive scale inside the inertial range. When the diffractive scale falls below the inner scale, α → 4 regardless of β (Cordes et al. 2016; Cordes 2025), so the square-law point β = 4 and the inner-scale-dominated regime are observationally degenerate. Do not report β = 4 as a turbulence-spectrum measurement; bake a "closure regime" column into the eventual results table rather than retrofitting the caveat in prose.

### D3. Sub-band validation uses the parametrization the joint fit rejects
§Subband fits an EMG (exponential PBF) per sub-band — the family the paper argues biases α. As a slope cross-check this is defensible *if* the shape-mismatch bias in per-sub-band τ largely cancels in the slope; but that cancellation holds only when the mismatch is frequency-independent, which it is not in general. Make the argument explicitly, and label the sub-band slopes as a validation diagnostic, not a turbulence constraint.

### D4. Scintillation double-use
The gain marginalization absorbs the scintillation pattern into the per-channel gain; scintillation later returns as an observable (§Results-scintillation). State, the first time the marginalization is introduced, that scintillation products come from a separate analysis path, and address whether the gain prior width interacts with the τ posterior at low S/N (a fully free per-channel gain can absorb scattering-induced spectral smearing in the low-τ limit).

### D5. Energetics comparability
The band-restricted two-band E_iso is a reasonable choice but is not comparable to literature values computed over a fixed rest-frame band. Either provide a fixed rest-frame-band variant or state prominently that these energies cannot be placed on standard luminosity functions. Eq. `eq:eiso` applies a single (1+z) k-correction to a two-band sum with different spectral indices — write out the per-band rest-frame intervals actually sampled.

---

## Association (§ToA) — non-blocking

1. **"Fewer than one in ten million" understates the quoted bound.** P_cc < 10⁻⁸ is one in a hundred million. Fix prose (abstract, §Results-association, §ToA) or the threshold.
2. **DM window treatment per association class.** ΔDM = ±5 pc cm⁻³ is called chance-maximizing, yet four bursts lack constraining CHIME DMs. For those, was f_DM set to 1? If not, the quoted P_cc for position-only associations is inconsistent with their verdict. Clarify per-class.
3. The Monte-Carlo cross-check (0.3% agreement) is good; keep it.

---

## Milky Way foreground (§Obs-MW) — non-blocking

4. **NE2025 citation (Ocker 2026):** ensure published/on arXiv by submission.
5. **Text–table inconsistency:** §Obs-MW quotes DM_MW up to ≈95 pc cm⁻³ while Table `tab:budget` lists 74–137. The table includes the +40 halo term and the text apparently does not — reconcile and say so explicitly.

---

## Foreground census (§Obs-FG) — non-blocking but important

6. **Photo-z misclassification budget.** "Confirmed foreground" at z_phot + 1σ < z_host tolerates ~16% per-object misclassification under Gaussian errors; over 15 confirmed systems that is ~1–2 expected mistakes before catastrophic-outlier rates (a few percent for Legacy DR9). Quantify how many confirmed systems rest on photometry alone and propagate an outlier rate into the DM_int systematic.
7. **Aperture values.** "A fixed proper impact parameter" (galaxies) and "several R_500" (clusters) must be stated numerically — they set the census completeness.
8. **Fallback mass prescription (note m).** Zeros for FRB 20240203A/20240229A are conditional on an unspecified "fallback mass." One sentence: what mass, from what relation, and is it a lower bound (conservative zero) or a median guess (sign could flip)?

---

## Minor

9. Remove all draft-status / re-validation language from reader-facing text (Introduction closing paragraph, Results and Conclusions openings). Process, not science.
10. Remove internal nicknames (*zach, whitney, …*) from Table `tab:sample`; TNS names suffice. Note the leftover comment in `methods.tex` (line ~207) naming the "validating clean case" — name it properly in the text or delete.
11. `\software{}`: add pygedm, the reduction/fitting pipeline (Zenodo DOI), and cite astropy properly.
12. Keywords: consider adding "Radio bursts (1339)".
13. Parked EMG appendix (`emg_alpha4_appendix.tex`): ensure no dangling `\ref` at submission.
14. Table `tab:budget`: FRB 20230814B is out of chronological order.
15. Fig. `fig:sightline_halo_grid` caption: state how many panels are shown, since three sightlines lack spectroscopic host redshifts and are omitted.
16. Abstract slot for the cluster column should carry the uncertainty from B2 when filled.

---

## Summary

Association and census methodology: sound. Dispersion budget: sound in structure, unpublishable without uncertainties (B1–B2). The β-closure scattering framework is the paper's strongest contribution; the design decisions D1–D4 should be locked before those sections are written so the per-sightline ledger is internally consistent. Highest-leverage single fix: propagate uncertainties through Table `tab:budget` and report DM_host as posteriors.
