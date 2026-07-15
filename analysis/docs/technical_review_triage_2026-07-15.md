# Triage of technical review (2026-07-15) — Faber2026_CHIME_DSA_Codetections

**Review:** `technical-review-report.pdf` (20 suggestions, run on the docx export) · **Verified against:** working tree @ 2026-07-15 (`sections/*.tex`, `*_table.tex`, `pipeline/galaxies/foreground/` data products) · **Prior report:** `docs/referee_report_2026-07-07.md` + status matrix

**Bottom line:** 16 of 20 suggestions are valid against the *current* tex, not just the reviewed docx. One (S9/S10) exposes a genuine data-integrity bug in the DM budget that must be fixed before submission. Two complaints (S9 first half, S10 fragments) are docx-conversion artifacts. S18 restates the already-tracked V/A/C re-validation blocker.

## P0 — Correctness bugs (fix before anything else)

**S9 (part 2) + S10 — DM_int provenance broken for three sightlines. VALID, CONFIRMED IN DATA.**
Table 4 (`budget_table.tex`) reports nonzero DM_int for sightlines that have **no confirmed foreground system in any census product**:

| Sightline | Table 4 DM_int | Census (registry + `foreground_table_data.json`, frozen_census) |
|---|---|---|
| FRB 20221113A | 41, regime CGM, mass **measured** | **no rows at all** |
| FRB 20230814B | 70, interior (b≈4.6 kpc) | **no rows at all** |
| FRB 20230325A | 10, CGM assumed | two candidates, both *inconclusive* (host-z-unknown, `budget_eligible=False`) |

This directly violates the "confirmed foreground only" rule of §2.5/§3.3 and cannot be regenerated from `intervening_census_registry.csv`. The values in `budget_table_data.json` appear to be stale (pre-trust-reset campaign?). Additionally, `foreground_table.tex` (Table 3) omits 20221113A, 20230814B, and 20240122A entirely — including the "interior" case discussed in Results. Action: audit `budget_table_data.json` generation end-to-end; either restore the confirming systems with provenance or zero/flag these DM_int entries; add an explicit Table 3 row for every sightline (even "no relevant candidates"); add a per-sightline contributor breakdown (supplementary) as the review suggests. Note this propagates: DM_int enters the host-DM posteriors (Table 4/6 and Appendix C) for 20221113A.

**S9 (part 1) — Table 6 shows redshifts in the DM_host column. ARTIFACT (probably).**
`tab:host-forward-model` in `sections/appendix.tex` is correct in tex (z and DM_host are separate columns). Almost certainly a docx-conversion column collapse. Action: fix the docx export path; no tex change.

**S15 (cross-ref) — VALID, TRIVIAL.**
`budget.tex` ~line 33: "integrated to 30 kpc (consistent with the Galactic characterization of Section \ref{sec:obs-fg})" — should be `\ref{sec:obs-mw}`. One-line fix.

**S2 — P_cc units. VALID (wording, not arithmetic).**
Eq. `pcc_mu` defines R "per unit solid angle per unit time" but the numbers use R = 10³ sky⁻¹ day⁻¹ with Ω_win in deg². The computation is correct with sky-fraction normalization: 10³ × (0.785/41253) × (2/86400) = 4.4×10⁻⁷ ✓ (matches Table 1). Action: define R as the all-sky rate and write μ = R·(Ω_win/Ω_sky)·(2Δt)·f_DM, stating the deg²↔sky conversion. Low effort, high referee value.

## P1 — Low-cost robustness additions (do before submission)

**S4 — Positive residual bias. VALID, quantitatively supported.**
9/12 residuals positive; unweighted mean +2.42 ms (+2.13 ms excluding the two wide-σ bursts), ≈2.4σ from zero against the naive error on the mean — consistent with the O(1 ms) clock systematic but worth reporting. Action: quote sample mean ± uncertainty, optionally fit a constant offset, confirm verdicts unchanged after subtraction. Data already in `toa_crossmatch_results.json`.

**S5 — Declination-conditioned CHIME rate. VALID.**
The +70°–74° strip has enhanced CHIME exposure (near-circumpolar, two transits/day); the ×2 conservatism (525→1000 sky⁻¹day⁻¹) may not cover the local rate enhancement. Action: one sensitivity sentence ("a factor-X higher local rate leaves ΣP_cc ≪ 1") — with Σμ ≈ 1.8×10⁻⁶ there is enormous headroom, so this is cheap and decisive.

**S6 — Repeater/clustering robustness. VALID.**
Not addressed anywhere. Action: state whether any of the 64 DSA triggers / CHIME counterparts are known repeaters; optionally a time-scramble background test. Low effort.

**S7 — Jackknife/masking specification. VALID, EASY.**
`observations.tex` §2.2 says "robust per-channel normalization and masking" and "twelve leave-one-channel-block-out jackknifes" without block width/contiguity/ordering relative to masking. Action: 3–4 sentences + a mask-threshold stability statement.

**S13 — R_500 sensitivity. VALID.**
Appendix B itself documents the near-miss (J115128.2+713637, b/R_500 = 1.25, ~95 pc cm⁻³ — would be the sample's second-largest intervening column). Action: keep R_500 as fiducial aperture, add a recompute at 1.5·R_500 / R_200 with an envelope. Machinery exists (`clusters_icm` profiles).

**S14 — τ_int microphysics. VALID.**
Table 4 carries τ_int with no documented DM→SM→τ mapping (turbulence normalization, outer/inner scales, cool-clump vs hot-phase weighting, screen geometry). Action: either document the mapping with priors in an appendix, or drop the column until the scattering framework (§sec:scattering results) lands. Given the V-gate, dropping/deferring is the cheaper consistent choice.

**S16 — Modulation gate vs two-screen √3. VALID, logical inconsistency confirmed.**
Results enforces m ≤ 1.5; Appendix E.3 (Eq. `eq:sqrt3`) allows m_tot = √3 ≈ 1.73 unresolved two-screen. Six of twelve CHIME rejections cite "modulation physicality," so the gate is doing real work. Action: reframe as "inconsistent with any plausible propagation+instrument model for this data product" or raise the bound to be two-screen-consistent and re-run the gate matrix (the `chime-scint-artifact-guards` driver covers this); report whether any Table 5 verdict changes.

**S15 (benchmark) — NE2025 vs NE2001/YMW16 per-sightline table. VALID.**
Only qualitative "retained as cross-checks" in `budget.tex`; no per-sightline comparison found in pipeline products. Would justify the 30% disk-DM prior in Appendix C. `pygedm` is already a dependency; ~half-day.

## P2 — Moderate-effort strengthening (worth doing, schedule against V/A/C)

**S1 — Deterministic trial set + operational crossmatch. VALID, PARTIAL.**
B3 (prior report) fixed the denominator (64, with the 64/12 scaling in `toa.tex`), but there is still no deterministic generating rule (time range + trigger class + required products) nor a description of the *actual* pipeline association windows (vs the conservative bounding windows). Action: add the rule + machine-readable trigger list as supplementary material; the review is right that referees will ask.

**S3 — TOA estimator + time standards. VALID.**
`toa.tex` defines the sign convention, GCRS vectors, and |τ_geo| ≤ 4.5 ms, but never states the per-pipeline TOA estimator (peak vs matched-filter vs model t₀), the time scale (UTC vs TDB/TT), topocentric vs barycentered inputs, or the software path for τ_geo. Residuals are few-ms, i.e. same order as convention differences. Action: one paragraph + reproduce the −2.30…−2.03 ms τ_geo range numerically.

**S8 — Coverage-calibrated DM uncertainties. VALID.**
Held-out injections exist (RMS 0.0028, max 0.0062) but no coverage diagnostic and no scattered/multi-component injections into real off-pulse waterfalls. Action: end-to-end injection campaign + 68%-coverage fraction per instrument. Fits the existing "max-of-variations" rule as a validation, not a change.

**S11 — Completeness / missing-halo systematic. VALID.**
Note u is qualitative. Action: per-footprint-class limiting magnitude → stellar/halo-mass completeness vs z → order-of-magnitude P(missed group-scale halo) per corridor. Moderate effort; makes "small on the rest" defensible.

**S12 — Probabilistic b/R_vir. VALID, aligns with existing machinery.**
Note m already flags mass-conditionality of the two zeros (20240203A, 20240229A). Action: Monte-Carlo M_halo (SHMR + photo-z scatter) → P(b < R_vir) → mixture DM_int in the Appendix C forward model, which is already sampling-based. Prevents "0" being read as a measurement.

**S19 — β∈[3,4] prior and δDM ±50. VALID, PARTIAL.**
The α ≥ 4 restriction is deliberate (thin-screen inertial branch) and the β=4 pile-up is handled by the D2 `endpoint-degenerate` label — but the review is right that no *effective-α* sensitivity variant exists (the parked EMG appendix is the natural vehicle). The δDM prior (±50 pc cm⁻³) is ~10⁴× broader than the measured DM uncertainties (~0.005); the bounding rationale is stated but posterior-concentration evidence is not. Action: add a sensitivity fit + either tighten δDM to the measured posteriors or show δDM posteriors hug zero. Schedule with the V-ladder re-fits.

## P3 — Already tracked / blocked on core science

**S18 — Missing scattering results/diagnostics. VALID but KNOWN.**
This is the declared V/A/B/C/D re-validation blocker (status matrix "core pending science"). The asks (per-burst τ/β/regime table, representative panels, per-event audit bundle) match what `tab:beta` / Fig 2 / Appendix F slots already anticipate. No new action beyond the existing ladder; treat the review as confirming the fill-list.

**S17 — CHIME scintillation positive control. VALID, PARTIAL.**
Injection-recovery calibration and the 20230325A template-subtraction experiment already function as partial positive/negative controls, but no known scintillator (pulsar) has been pushed through the same upchannelization + mitigation chain. Real effort (new data product); would upgrade "no certified Δν_d" from analysis choice to demonstrated instrument limit. Decide whether the sample's conclusions need it or whether the injection battery suffices with clearer framing.

**S20 — Energy definitions + calibration budget. VALID, DEFERRED BY DESIGN.**
F_X(ν) ambiguity (fluence vs flux density — the 1 Jy ms Hz conversion implies fluence density but the text says "spectral amplitude"), time-integration/masking handling, and SEFD/beam systematics are all real gaps — and the section is explicitly TODO-gated (D5 lock, V3). Action: fold the review's checklist (explicit units, unmasked-bandwidth integration, coupled-vs-separate fit statement, SEFD/beam prior budget) into the energy re-validation spec so it's satisfied at fill time.

## Suggested execution order

1. **S9/S10 audit** (data integrity; touches budget table, host posteriors, Results text)
2. **S15 cross-ref + S2 units + S7 jackknife spec** (same editing pass, < 1 day total)
3. **S4 + S5 + S6** (association robustness paragraph; one script + a few sentences)
4. **S13 + S14** (aperture sensitivity; defer τ_int column)
5. **S16 gate reframe** (+ re-run guard matrix)
6. **S1 + S3** (reproducibility supplement + TOA conventions)
7. **S8, S11, S12, S15-benchmark, S19** (moderate campaigns, schedule against V/A/C)
8. **S17, S18, S20** (ride the existing re-validation ladder)

*Verification notes: P_cc arithmetic reproduced (4.4×10⁻⁷); residual mean computed from `sample_table.tex`; census absences confirmed in `intervening_census_registry.csv`, `foreground_table_data.json`, and `data/frozen_census/*`; √3 vs 1.5 gate confirmed in `results.tex` / `twoscreen_formalism.tex`; cross-ref slip confirmed at `budget.tex` §sec:dm.*
