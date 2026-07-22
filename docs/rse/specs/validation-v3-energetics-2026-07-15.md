# V3 — Energies re-validation: contract, audit, and disposition

> Session 2026-07-15. Owner decisions this session: (1) re-base the energy
> table on the **data-driven** per-channel fluence estimator; (2) author this
> **energies-scoped validation contract** now (to be folded into the V1 ADR
> when authored); (3) keep wilhelm/hamilton/chromatica **footnoted
> provisional-z** rows (8 rows); (4) **skip** the D5 fixed rest-frame-band
> variant.
> Independent recomputation code: `analysis/v3_energetics/recompute_energies.py`
> (manuscript repo — deliberately outside the pinned `pipeline/` submodule).

## 1. Energies-scoped validation contract (V1 principles applied)

A burst-energy row is citable only when ALL of the following hold:

- **E1 (input lineage).** Every input is provenance-pinned: host redshift with
  named published source (or explicit provisional flag), SEFD and beam
  response with acquisition record, fluence inputs sha256-stamped
  (`burst_energies.provenance.json` pattern).
- **E2 (estimator independence).** The fluence estimator does not consume any
  trust-revoked fit product. Adopted route: the per-channel on-pulse data
  integral (`flux_cal.dsa_band_fluence_jy_ms_hz` and a CHIME analog), which
  uses no fitted parameters — only calibration (SEFD, beam) and the on-pulse
  window.
- **E3 (prior-rail disposition).** Any prior-railed parameter that could
  shape the estimate is either absent from the estimator (E2 satisfies this)
  or shown quantitatively not to move the result beyond stated systematics.
- **E4 (independent cross-check).** A second estimator route or external
  anchor agrees within the stated systematic (catalog anchors; model-vs-data
  comparison below).
- **E5 (explicit inclusion rule).** The row-selection rule is stated in the
  table caption and matches the code gate exactly.

## 2. Input-lineage audit (E1) — findings

**Redshifts.** The repo `TARGETS` values match **Connor et al. 2024
(arXiv:2409.16952) Table 1** exactly for zach (0.0430), whitney (0.4790),
oran (0.3005), isha (0.2505), phineas (0.2710). Sharma et al. 2024
(arXiv:2409.16964, Extended Data Table 1) quotes slightly different values
(zach 0.0433, whitney 0.4780, phineas 0.2706): Δz ≤ 0.001, ≤0.5% in D_L,
negligible against the 0.20–0.25 dex scale systematics. **Adopted source
should be cited as Connor+2024 Table 1** (or the difference footnoted).

- **DISPOSITION (owner, 2026-07-15): wilhelm (FRB 20221203A) z = 0.5100 is
  retained as a provisional internal value.** It appears in NEITHER
  Sharma+2024 Extended Data Table 1 NOR Connor+2024 (v2) Table 1/2 — the
  attribution "Connor+2024 Keck/MOSFIRE" in
  `research-energetics-followups.md` could not be confirmed against the
  posted paper. No additional redshift measurement or external source is
  expected; the available project value is what this analysis has. The row
  therefore remains in the eight-row roster with an explicit provisional
  footnote, and redshift-source acquisition is no longer a V3 blocker.
  The same qualifier is propagated to the compiled DM-budget, host-DM
  appendix, results, and conclusions surfaces so the value is never presented
  as a published measurement elsewhere in the manuscript.
- hamilton (FRB 20230913A) and chromatica (FRB 20240203A): spec-provisional
  (no published host paper), footnoted per owner decision. Unchanged.

**Calibration inputs.** DSA SEFD (per-element dashboard / 48 = coherent-beam
167 Jy), measured beam cube, CHIME documented cylinder beam + derived SEFD
(`chime_sefd.csv`): acquisition records in `CALIBRATION_REVIEW.md`. Absolute
scale is catalog-anchored for zach (1.27×), whitney (2.15×), oran (0.99×)
against Law+2024 Table 1 only; anchor cannot be widened (structural — no
later published fluence catalog). Non-anchored sightlines are model-trusted;
this is stated in the table systematics, not hidden.

**Fit-product inputs (legacy route).** `burst_energies.json` @ git 4c4dbd2
(clean tree), 22 input JSONs sha256-stamped. These are wave-1-revoked
products; under E2 they are demoted to cross-check inputs only.

## 3. Independent legacy-table recomputation (all PASS, 2026-07-15)

Re-derived from the legacy table's stored calibrated band integrals with independent code
(astropy Planck18): D_L (8/8), E_iso per band and total (8/8, <1e-9
relative), k-correction identity (8/8), error propagation from joint-JSON c0
posterior widths + BAND_SYS_DEX quadrature (8/8), closed-form band integral
vs dense quadrature incl. γ=−9.9 (PASS). The arithmetic of the existing
table is fully reproducible; what was wrong with it was trust, not math.

## 4. γ_D ≈ −5 pile-up — resolved (E3)

- **It is a prior bound.** 7 of 11 joint fits sit at the −5 floor
  (chromatica, freya, hamilton, johndoeII, oran, phineas, zach); isha
  (+0.95), whitney (+2.91), wilhelm (−1.99), mahi (−0.17) do not rail.
- **The rail is real steepness, not calibration.** `refit_calibrated.py`
  (floor opened to −10): S/N-fit γ_D runs −6 to −9.9; flux-calibration
  relaxes off-axis bursts by the analytic beam-slope amount (freya +2.2) but
  the steep DSA falloff survives on-axis (phineas pinned at −9.9). Per the
  V-contract rail principle, the −5 rail is model-family rejection (the
  spectral index is NOT quotable from these fits), never a limit.
- **The energy does not care.** Analytic: with the amplitude anchored
  mid-band, the DSA band-shape factor moves 6.1% for γ −5 → −10, vs the 58%
  (0.20 dex) scale systematic. Empirical (E4): model-based vs data-driven
  DSA fluence ratio median 1.00, range 0.59–1.13 across the 8 rows — all
  within ~1σ of the scale systematic (zach 0.59 and isha 0.62 are marginal,
  0.21–0.23 dex; both become moot on the data-driven route, which we adopt).
- **Disposition:** γ_D is removed from the energy pipeline's load-bearing
  path (E2) and from the table columns; per-band spectral indices await the
  C1 re-fit campaign. No γ from the revoked fits appears in prose or tables.

## 5. Selection-rule contradiction — resolved (E5)

The old caption language implied a "quality-passing" criterion while
gate-FAIL FRB 20240203A (chromatica) was tabulated. The rule the code
actually applies (ADR-0003/0004) is correct — E_iso is independent of the
shared-α scattering verdict — the caption was wrong. **The explicit rule:**

> A burst appears in the energy table iff (i) it has a spectroscopic host
> redshift (published, or flagged provisional), and (ii) both bands carry a
> validated absolute flux calibration at the burst position. Scattering-fit
> quality verdicts do not enter: on the data-driven route the energy consumes
> no fit product. Excluded: freya, mahi, johndoeii (no host redshift);
> casey (photometric redshift only).

Note the casey point: the old 8-row set was defined by "has a joint c0/γ
fit". Under the data-driven estimator that criterion vanishes, and casey
(z=0.2870, published in Connor+2024 Table 2 as FRB 20240229A — verify
whether that z is photometric: the table footnote †-flags 20240229A) must be
explicitly re-adjudicated rather than silently omitted. **Resolved this
session:** Connor+2024 Table 1 †-flags 20240229A's z = 0.2870 as
**photometric** (verified against the posted v2 PDF), so casey stays out
under rule (i), and the exclusion reason is "no spectroscopic z", not "no
fit". The caption must say so.

## 6. Adopted estimator switch (E2) and CHIME-side runbook

**Decision (owner, 2026-07-15):** the table value becomes
E_iso = 4πD_L²/(1+z) · [I_C^data + I_D^data] · 10⁻²⁹ J m⁻² per Jy·ms·Hz,
I_X^data = ∫ σ_S,X(ν) · Δt · Σ_onpulse(S/N)(ν) dν over each band's valid
channels. The legacy model-based values are retained as the E4 cross-check
column in the validation artifact (not the manuscript table).

DSA side: exists (`dsa_fluences.csv`, `dsa_band_fluence_jy_ms_hz`).
CHIME side (compute host, data staged):

1. Stage the 8 CHIME .npy under `pipeline/data/chime/` (h17/iacobus per
   `DATA_LOCATIONS.md`); verify gen-2 lineage + md5 against
   `scintillation/DATA_PROVENANCE.md` conventions (V2 cross-cut: confirm the
   energies inputs do NOT share the gen-1 de-chirp defect lineage — the
   fluence integral is broadband and insensitive to intra-channel de-chirp
   structure, but record the lineage anyway).
2. Implement `chime_band_fluence_jy_ms_hz(nick)` mirroring the DSA function:
   loader with the burst config's f/t binning, per-channel on-pulse S/N sum,
   σ_S from `chime_sefd.csv` with G=1 (baseband beamformed at source),
   trapezoid over valid channels. Emit `chime_fluences.csv` (same schema).
3. On-pulse window sensitivity check (the one free choice the data route
   has): recompute with onpulse_thresh varied (2.5/3.0/3.5σ) and pad factor
   varied; require <~10% spread or widen the stated systematic.
4. Regenerate `burst_energies.json` with both bands data-driven; re-stamp
   provenance (new gate_policy text = §5 rule); keep model-based values as
   cross-check columns; regenerate `burst_energies.tex`.
5. Add a data-driven verifier (or extend
   `analysis/v3_energetics/recompute_energies.py` with a schema-selected
   data-driven mode) that independently recomputes the table from the
   regenerated fluence and statistical-error fields, checks its provenance,
   and fails if any adopted value or uncertainty depends on joint-fit
   `c0`/`gamma`. The current script intentionally accepts only the
   mixed-legacy artifact and is retained as the E4 arithmetic cross-check.
6. Encode the §2 owner disposition in the regenerated provenance and table:
   wilhelm uses the available $z=0.5100$ as a provisional internal value;
   casey remains excluded per §5 because its redshift is photometric.

## 7. V3 status after this session

| Contract item | Status |
|---|---|
| E1 input lineage | **PASS with explicit provisional flags** for wilhelm/hamilton/chromatica; casey is photometric and excluded |
| E2 estimator independence | **PENDING**: DSA done; CHIME run pending (runbook §6) |
| E3 prior-rail disposition | **RESOLVED** (this document §4) |
| E4 independent cross-check | PASS (model-vs-data median 1.00; catalog anchors ×3) |
| E5 explicit inclusion rule | **RESOLVED** (this document §5; caption updated) |

V3 is **not** yet clearable: the CHIME-side data-driven run, its independent
data-driven verification, regenerated-table review, and owner sign-off remain.
The redshift roster is closed with the three provisional flags above; no new
redshift acquisition is expected or required.

## 8. Publication validation

Validated against the V3 implementation at commit `2cb2323` on 2026-07-15.

### Implementation status

- The estimator definition, validation contract, legacy arithmetic audit,
  explicit selection rule, and owner-view state are implemented.
- The Results table and its interpretation prose remain source-gated and do
  not compile before V3 clearance.
- V3 itself remains pending on the CHIME-side computation, independent
  verification, regenerated-table review, and owner sign-off; landing this
  contract does not mark the science lane complete.

### Automated verification results

- **PASS:** `analysis/v3_energetics/recompute_energies.py` — all legacy-table
  arithmetic and robustness checks passed; the script rejects non-legacy
  provenance rather than masquerading as the future data-driven verifier.
- **PASS:** `make` — manuscript compiled with no undefined references and no
  overflow from the energy-estimator equation.
- **PASS:** `make test-science` — 76 passed, 1 expected xfail; figure-approval
  and journal tests passed.
- **PASS:** `python3 scripts/sync_state.py --check` — all three generated views
  matched their canonical sources; lane/ledger rules passed.
- **PASS:** `git diff --check`.

### Code review findings

- Codex GPT-5.5/medium identified premature compiled-result claims, ambiguity
  between the legacy audit and future data-driven verifier, and a stale Casey
  exclusion reason. All were corrected.
- Antigravity identified an orphaned compiled Discussion lead-in and internal
  gate/future-tense leakage. The Results and Discussion drafts are now gated
  together in source comments; Methods uses publication-ready present tense.
- Claude Opus 4.8/xhigh could not run because the local Claude CLI session was
  not authenticated. No Claude review is claimed.

### Manual testing required

No manual test remains for landing this contract. The CHIME-side computation,
independent data-driven verification, regenerated artifact review, and owner
sign-off are follow-up science gates, not completed work in this change.

### Recommendations

- **Critical for this contract:** none.
- **Follow-up:** complete §6, implement the data-driven verifier, preserve the
  three provisional-redshift flags in provenance and the table, review the
  regenerated table, then uncomment and fill the gated Results and Discussion
  prose only after owner V3 clearance.

## References

- [D2--D5 scattering design locks](decision-d2-d5-scattering-design-locks.md)
- [Legacy arithmetic audit](../../../analysis/v3_energetics/recompute_energies.py)
- [Energy estimator](../../../sections/methods.tex)
- [Gated energy results draft](../../../sections/results.tex)
- [Gated energy interpretation draft](../../../sections/discussion.tex)
