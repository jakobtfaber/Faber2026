# Research: trust-reset re-validation surfaces (V1–V5)

---
**Date:** 2026-07-06
**Author:** AI Assistant (five parallel read-only explorations of the pinned pipeline)
**Status:** Complete
**Scope:** dsa110-FLITS @ pin `7e77437` + manuscript tree, mapping the five §V
re-validation surfaces of [plan-circulation-readiness.md](plan-circulation-readiness.md).
All `path:line` references are relative to `pipeline/` unless absolute.
---

## V1 — existing validation machinery

**Synthetic injection / known truth**
- `simulation/engine.py:84` FRBScintillator (geometric two-screen MW+host);
  `calculate_theoretical_observables()` `:766` returns injected τ and ν_s truth
  per screen (`:782-789`). Intrinsic pulse delta|gauss only (`:79`).
- `simulation/sim_fit_bridge.py:48` `simulate_scattered_burst` — the
  simulate half of the M2 simulate→fit roundtrip; narrow-band rescale
  caveat `:112-118`.
- `simulation/recovery_campaign.py:9-24` (module docstring; entry points
  `recovery_curve` `:76`, `dnu_recovery_curve` `:146`) — **recovery is
  LINEAR, not absolute**: recovered/injected τ ratio ≈ 2.47–2.50 across an
  ~80× range (Δν_d ratio ≈ 0.29); `tests/test_recovery_campaign.py:38,54`
  deliberately assert linearity (std/mean < 0.15), never ratio==1.
- `analysis/beta_campaign/sim_gate.py:47-52` — 3-point injection gate
  (interior 3.7 / interior 3.3 / rail 4.0) through the production joint-fit
  path; all passed. No injection coverage for extended-medium kernels,
  multi-component fits, or the two-screen different-screens regime.

**Gates**
- `scattering/scat_analysis/burstfit.py:1464` classify_fit_quality; constants
  `:81-86` (PASS 0.3–1.5, MARGINAL to 10, FAIL >10; χ²-only, R²/normality
  informational `:1470-1479`).
- `flits/fitting/VALIDATION_THRESHOLDS.py` — partially superseded
  (`CHI_SQ_RED_MARGINAL_MAX=3.0` at `:30` is dead).
- `analysis/scattering-refit-2026-06/gate_joint_committed.py:40` 3-level joint
  gate; rail-pinned or τ·Δν_d-unevaluable ⇒ capped MARGINAL (`:93-100`);
  joint fits never certify PASS.

**Rail detection — three incompatible definitions, no SSOT**
- `analysis/beta_campaign/grade_beta_campaign.py:65` — 3σ-proximity OR
  ≥30% edge mass within an **absolute** 0.05-wide window at the bound
  (`EDGE_MASS_WIDTH`, `:61-62,77-82`; equals 5% only because the campaign
  β prior is unit-width).
- `analysis/beta_campaign/sim_gate.py:72` — 3σ only.
- `gate_joint_committed.py:47-55` — proximity < 0.1 only.

**"PPC" is not a PPC**: `analysis/scattering-refit-2026-06/joint_ppc_multi.py:54`
is a per-band OLS-gain reduced-χ² statistic — no replicated-data discrepancy
distribution, no Bayesian p-value.

**Adversarial verification gap**: `.claude/workflows/fit-verify.js` globs
`**/*_fit_results.json`; the joint gate writes `*_joint_gate.json`
(`gate_joint_committed.py:8-10`) — **the joint fits were never covered**.
Stale line refs in `fit-validation.md`/`fit-verify.js` (cite burstfit.py:1342
vs actual :1464).

**Fleet state**: `analysis/beta_campaign/fleet_status.json` shows 10/12 ok;
whitney_fine and phineas rc=−15 (killed ~18 min) — reconcile against the
"campaign complete" narrative.

**Rung gap summary**: (1) input lineage — greenfield; (2) injection recovery —
strong thin-screen core, linear-only, no geometry breadth; (3) rail-as-
rejection — machinery exists, needs SSOT; (4) true PPC — greenfield;
(5) independent cross-checks — real (two_screen.py, freya regression
FREYA_REF=3.6838±0.05 `run_fleet.py:54-55`) but joint fits outside discovery.

## V2 — scattering-fit inputs & defect lineage

- Loader `scattering/scat_analysis/pipeline/io.py:16` (BurstDataset): reads
  pre-de-chirped `(n_freq,n_time)` `.npy`; **no dedispersion in-pipeline**.
  CHIME configs assert `dm_init: 0.0` ("coherently dedispersed",
  `analysis/scattering-refit-2026-06/local_runs/configs/freya_chime_run.yaml:6`).
- Scattering CHIME inputs = native 1024-ch `*_32000b_cntr_bpc.npy`
  (`data/CHIME_bursts/dmphase/`), a **different lineage** from the defective
  up-channelized scint npz (24.4 kHz, `upchannelize_chime.py`,
  `scintillation/DATA_PROVENANCE.md:78-79,242-252`). The gen-1 wrap defect is
  documented only in the scint lineage; the scattering cubes' wide 32000-bin
  centered windows are structurally protective against wraps.
- **BUT**: (a) no in-repo builder exists for the scattering cubes (no
  `np.save` of `cntr_bpc` anywhere) — off-repo h17/arc step, `time_shift`
  handling unauditable at the pin; (b) `data-manifest.csv` sha256/bytes are
  ALL `PENDING` (24 rows) — inputs unpinned; (c) `DATA_SOURCES.md:90-111`
  (pipeline repo root) is an OPEN reconciliation failure ("stored scintillation does not reproduce
  from the current arc files + committed joint fits"; suspected re-generated/
  re-centered arc files); (d) joint plotting re-aligns CHIME→DSA by measured
  TOA because "crop-relative fit t0 can misalign bands by ~10 ms"
  (`plot_jointmodel_prototypes.py:83-96`).
- Shared footgun: `coherent_dedisp(time_shift=True)` per-channel circular
  roll; safe convention is `time_shift=False` + explicit roll
  (`crossmatching/chime_singlebeam.py:111`).
- Verdict: defect not confirmed in scattering cubes, not ruled out; the
  builder audit + checksum fill is the concrete forensic gap.

## V3 — energies

- Export: `analysis/calculate_burst_energies.py` (`compute` `:225`, band
  integral `:112-120`, writes `analysis/burst_energies/*` `:543-547`).
- c₀,γ source: `analysis/scattering-refit-2026-06/joint_json/*_joint_fit.json`
  (`JOINT_DIR` `:66`) — the **old mixed-legacy generation**, not the β
  campaign. N=8 roster.
- **γ hard prior bound (−5, 5)**: `scattering/scat_analysis/burstfit.py:1403`,
  inherited verbatim by the joint fit (`burstfit_joint.py:396-409`). Five of
  eight emitted γ_D within 0.15 of −5; chromatica pinned (lower CI −4.994).
  A relaxation harness exists: `analysis/burst_energies/refit_calibrated.py`
  (`GAMMA_FLOOR=-10` `:61`, RAILED list `:57` = chromatica, oran, phineas,
  zach, freya; no CLI — bare `main()`, outputs hardwired to
  `analysis/burst_energies/`). The mixed-legacy `*_joint_fit.json` are
  summary files (medians/percentiles) — no posterior samples for this
  generation exist in-tree or in the local runs store.
- **Energies are quality-ungated by design**: `load_joint_params()`
  `:182-190` drops only non-physical c₀/γ; quality_flag informational
  (self-check `:464-482` asserts FAIL-α fits with valid c₀/γ are retained).
  Real criterion: spec-z (`:237-239`, placeholder z==1.0) + both-band
  fluxcal (`:248,269`) + physical amplitudes. "spec-provisional" redshifts
  (chromatica, hamilton) pass.
- **Three-way chromatica inconsistency**: committed
  `chromatica_joint_gate.json` = MARGINAL (χ²=null); manuscript prose + β
  campaign say gate-FAIL χ²ᵣ≈11.6/9.3; energies table includes it. The two
  manuscript tables (energies vs tab:beta) are fed by different fit
  generations with different gate verdicts.
- Flux scale: CHIME SEFD 34.5 Jy (`analysis/chime_beam.py:77,118-120`);
  `BAND_SYS_DEX={"C":0.25,"D":0.20}` (`calculate_burst_energies.py:77`,
  folded `:279-288`). The DSA per-element figure (8016.2 Jy / 48 antennas)
  appears in docs/reports only — no analysis-code anchor at the pin; the
  V3 flux-scale audit (plan P5.4) pins its provenance.

## V4 — foreground census

- Two halves: frozen adjudication (scripts REMOVED from main by `9096a60`;
  survive in worktrees `~/Developer/scratch/worktrees/flits-rerun/scratch/
  codetection/` + `flits-acf-lag-selector`; four frozen CSVs byte-match the
  reproducibility doc SHA-256s) and tracked artifact half
  (`galaxies/foreground/`).
- Verdict logic: `validate_foreground.py:169-192` (1σ straddle; priority DESI
  spec-z → LS-DR9 z_spec → z_phot±std → NED; placeholder host-z ⇒
  inconclusive); `ps1_strm_adjudicate.py:34-47` (UNSURE/extrapolated ⇒
  inconclusive); `merge_final.py:32-58` with hard assert 49/29/7/13
  (`:88-96`).
- Registry: `galaxies/foreground/data/intervening_census_registry.csv`
  (49 rows; 34 halos/15 clusters; budget_eligible=15 via
  `census_registry.py:76-82` — confirmed + cluster b/R500≤1).
- Impact params: `utils.py:18-35`; b/R_vir `build_unified.py:277-282`;
  cluster b/R500 frozen (`census_registry.py:111-113`). Mass ladder
  `build_unified.py:117-154` (assumed logM*=10.0 fallback `:154`;
  MEASURED/PREDICTED flag `:415`); cluster override M200=1.3·M500
  (`:430-460`).
- `foreground_table.tex` auto-generated by `make_catalog_table.py`
  (worktree-only, not in main).
- Reproducibility runbook with pinned input/output hashes:
  `docs/rse/specs/reproducibility-foreground-galaxies.md` (pipeline-side).
- **Re-derivation**: Tier 1 — restore frozen CSVs, replay deterministic tail
  (census_registry → build_artifacts → sightline_budget → systems_figures),
  diff tracked artifacts; zero network, minutes. Tier 2 — re-run adjudication
  live (NOIRLab TAP ls_dr9/desi_dr1, NED, SIMBAD) scoped to flippable rows
  (photo-z 1σ-straddlers, STRM-UNSURE); full live re-search is discovery
  cross-check only, historically not fully repeatable (PS1-STRM HLSP strips).

## V5 — DM budget

- Chain (`galaxies/foreground/sightline_budget.py`): pygedm pass-through
  `galactic_dm_tau` `:265-285` (both NE2001/YMW16); halo prior 40 pc cm⁻³
  `:90-92`; Macquart `dm_cosmic_macquart` `:130-151` (F_IGM=0.84 `:97`,
  CHI_E=0.875 `:98`, Planck18 `config.py:6`); interior cap 0.1 R_vir
  `:73-77` applied `:592-614`; residual `:666-675`.
- mNFW: `scattering_predict.py:369-440` (α=2, y0=2, c=7.67, f_hot=0.75);
  cool phase `:64-90` (k_eff=0.3); τ prediction `tau_scat_ms` `:163-194`
  (A=1e-6 ms lump), leverage `g_scatt` `:132-160`, two-phase `:208-243`
  (COOL_CLUMP_BOOST=10).
- Sensitivity (negative-residual claim): `sightline_sensitivity.py` whole
  module; P(DM_host<0) `:277,306-308`.
- **Export gap**: pipeline emits markdown/CSV only
  (`format_budget_table:836-876`); root `budget_table.tex` is a hand
  transcription with a false "regenerate, not by hand" header — no parity
  check exists.
- External oracles available: mNFW hard oracle 350.875 pc cm⁻³
  (`test_scattering_predict.py:183-187`); pygedm live bound test
  (`test_sightline_budget.py:359-368`); τ∝(1+z)⁻³ test
  (`test_scattering_predict.py:86-96`).
  **Missing**: any test pinning `dm_cosmic_macquart` to a published/analytic
  Macquart-curve point. Internal priors (halo 40, A=1e-6, boost 10, k_eff,
  caps) are audit-only by design.

## Cross-cutting themes

1. **Provenance is the systemic hole**: unpinned inputs, off-repo builders,
   removed census scripts, hand-transcribed tex, two fit generations feeding
   different manuscript tables.
2. **Prior rails are systemic** (β at 4, γ at −5) and rail *detection* is
   fragmented across three definitions.
3. **Existing machinery is real but fragmented** — consolidate (rail SSOT,
   fit-verify glob, gate constants) rather than reinvent.
4. **Absolute calibration of τ recovery was never asserted** — only
   linearity. Any re-fit campaign must add an absolute-recovery criterion.
