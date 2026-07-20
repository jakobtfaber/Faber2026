# Research: Unified 12-burst co-detection figure

> **Historical design audit.** Its stored-product DM convention was superseded
> for manuscript Figure 1 on 2026-07-13: both native waterfalls are now shifted
> to the adopted CHIME-primary DM before display averaging. See
> [verified-dm-adoption-2026-07-13.md](../notes/verified-dm-adoption-2026-07-13.md).

**Date:** 2026-07-09
**Scope:** internal codebase (data inventory, figure infrastructure, manuscript conventions); light prior-art note on FRB gallery conventions
**Codebase state:** Faber2026 `29f7a81` (main), pipeline pin `14e0d1f`
**Related Documents:** [plan-circulation-readiness.md](../plan/plan-circulation-readiness.md) (§V trust ladders), [handoff-2026-07-08-07-26-figure-resolution-font-standardization.md](../handoff/handoff-2026-07-08-07-26-figure-resolution-font-standardization.md)

## Question / Scope

The manuscript has no single figure showing the data of all twelve co-detected
DSA-110 × CHIME FRBs. What data, plotting infrastructure, and manuscript
conventions exist to build a unified all-12-burst dynamic-spectrum figure, and
what constraints (trust reset, DM conventions, style standards) govern it?

## Codebase Findings

### 1. The sample: exactly 12 bursts, authority chain verified

- In-repo source of truth: `pipeline/configs/bursts.yaml:21-148` — exactly 12
  bursts, each with `chime_id`, `dm`, `mjd`, `utc`, `ra_deg`, `dec_deg`.
  Mirrored by `pipeline/analysis/chance-coincidence/bursts.json`.
- Upstream human authority (outside git): `~/Developer/scratch/2026-06/_downloads-import/text-corpus/DSA-110_CHIME Codetections - DSA-CHIME Burst Properties.csv`
  — 16 candidate rows with CHIME event IDs; 12 pass `Processed baseband? = Yes`
  on both instruments.
- Nickname → TNS map: `pipeline/scattering/scat_analysis/burst_metadata.py:51-56`
  (`_FALLBACK_TNS`). The 12: zach=FRB 20220207C, whitney=20220310F,
  oran=20220506D, isha=20221113A, wilhelm=20221203A, phineas=20230307A,
  freya=20230325A, johndoeII=20230814B, hamilton=20230913A, mahi=20240122A,
  chromatica=20240203A, casey=20240229A.
- The 4 exclusions are all data-availability (per
  `~/Data/Faber2026/dsa110/catalog/dsa110_frb_catalog_README.md:40-54`):
  gertrude (CHIME baseband has no signal), pingu (CHIME baseband+intensity
  missing), FRB20220912A2 (repeater, ambiguous CHIME event ID), benjy (no DSA
  voltage data).
- **Hazard:** derived sheets `DSA_CHIME_BurstProps.csv`,
  `DSA110_CHIME_Codetection_BurstProperties_Short.csv`, and
  `chimedsa_burst_specs.csv` carry a rotated-MJD defect and mislabel mahi as
  FRB 20240119A. Do not consume them; use `bursts.yaml` + `_FALLBACK_TNS`.

### 2. Data: both bands, all 12 bursts, fully local

All physical data under `~/Data/Faber2026/dsa110/` (symlinked into
`pipeline/data/`). Per burst:

- **DSA** dedispersed bandpass-corrected Stokes-I waterfall:
  `~/Data/Faber2026/dsa110/DSA_bursts/{nick}_dsa_I_{DM}_{tag}_2500b_cntr_bpc.npy`,
  shape (6144, 2500) — 6144 chans × 2500 × 32.768 µs ≈ 81.9 ms window,
  burst-centered. Present for all 12.
- **CHIME** dedispersed ("dmphase") bandpass-corrected Stokes-I waterfall:
  `~/Data/Faber2026/dsa110/DSA_bursts/{nick}_chime_I_{DM}_{tag}_32000b_cntr_bpc.npy`,
  shape (1024, 32000) — 32000 × 2.56 µs ≈ 81.9 ms window. Present for all 12.
- Per-burst run configs (DM, f/t decimation, data path):
  `pipeline/scattering/configs/bursts/{dsa,chime}/{nick}_{tel}.yaml` — DSA
  `dm_init` = optimized DM; CHIME `dm_init: 0.0` (already dedispersed).
- Band geometry: `pipeline/scattering/configs/telescopes.yaml` — DSA
  1311.25–1498.75 MHz (df 0.0305 MHz, dt 32.768 µs, stored freq-descending);
  CHIME 400.19–800.19 MHz (df 0.390625 MHz, dt 2.56 µs).
- Loader convention (`pipeline/CLAUDE.md` "Data & metadata"): frequency flipped
  to ascending on load.
- CHIME baseband (raw voltages) and DSA full-Stokes are NOT local (CANFAR arc /
  host iacobus) — not needed for a Stokes-I gallery.

### 3. Figure infrastructure: strong precedents, no existing gallery

- **No committed all-bursts raw-waterfall gallery exists.** The
  `dm-power-h17-manifest-dynamic-spectra-sheet.png` in specs was an ad-hoc h17
  QA diagnostic; its generator was never committed.
- **Premier reusable engine:** `pipeline/flits/batch/codetection_plots.py` —
  `BandSpectrum` dataclass (:97), `plot_codetection()` (:593), multi-band
  stacking with time regridding (`_regrid_bands` :179), magma waterfalls with
  masked-gap colormap (`_cmap_with_bad` :244), per-band independent
  normalization (:661, :716), `imshow(origin="lower", aspect="auto",
  extent=[t0,t1,fmin,fmax])` (:718-725). Design tests:
  `pipeline/tests/test_codetection_plots_design.py`.
- **Two-band joint single-burst precedent:**
  `pipeline/analysis/scattering-refit-2026-06/fullband_waterfall.py` — CHIME+DSA
  stack with blank inter-band gap (`cmap.set_bad("0.85")` :152-153), per-block
  99.5-pct normalization (:61), `BurstDataset` loading with f/t decimation (:42-58).
- **12-panel grid precedents:** `plot_jointmodel_montage.py` (4-col ×
  ceil(n/4)-row, `ORDER` list of 12 nicknames :18, layout :80-82, 1/99-pct clip
  :34-52, pdf/svg/png triplet save :110-112);
  `pipeline/analysis/chime_dm/plot_dm_grid.py` (nested subgridspec per cell
  :116-119, z-scored waterfalls :49-62, rasterized=True).
- **Style standard:** `pipeline/flits/plotting.py:21` `use_flits_style()` —
  scienceplots base + Computer Modern serif (cmr10), mathtext=cm, no usetex;
  declared the repo-wide standard in the 2026-07-08 handoff. Manuscript figures
  emitted as pdf+png+svg triplets.
- **Provenance conventions:** every manuscript figure maps to a producer script
  + command in `REPRODUCE.md`; pipeline figure scripts call
  `pipeline/tools/figure_manifest.py:write_manifest`.

### 4. Manuscript conventions and insertion point

- `main.tex:6` — `\documentclass[twocolumn]{aastex631}`; `\graphicspath{{figures/}}`
  (main.tex:11). Every existing figure is a two-column `figure*` with
  `width=\textwidth`.
- Natural home: §2 "Dynamic spectra and reduction" (`sections/observations.tex:19`,
  `\label{sec:data}`) — currently has NO figure and explicitly declines
  morphology cataloging at observations.tex:31-32 ("We do not catalog the
  fine-scale baseband morphology of each burst here" — needs softening).
  A montage TODO anchor already exists at observations.tex:45
  (`% TODO(obs-scattering): Reinsert any joint-fit montage only after ... re-validation`).
- Caption naming: TNS designations only (`FRB~20220207C`); nicknames are
  filename stems, never reader-facing. Per-burst appendix macros
  (`sections/jointmodel_pairs.tex:4-19`, `sections/dsa_scint_acf.tex`) take
  nickname (path) + TNS (caption) arguments.
- Existing per-burst appendix panels: association cards (12), joint-model
  audits (11 — chromatica omitted), DSA scint ACFs (12). None is a raw
  dynamic-spectrum gallery of both bands.
- Orphaned asset: `figures/jointmodel_montage.{pdf,png,svg}` exists but is not
  included anywhere — pulled during the trust reset (fit-derived).

### 5. Trust-reset constraints (CONTEXT.md)

- Raw observational inputs are inputs, not revoked products (CONTEXT.md:55-59):
  a data-only gallery is safe manuscript territory — **no fit/model overlays**
  (joint-fit models, τ, β annotations all revoked pending §V).
- DM_obs was Wave-3 revoked; V6 restored association/DM under the **shared
  DSA-DM reference convention** (CONTEXT.md:35-39). **Verified against the
  actual filenames (2026-07-09): the two bands are NOT at a shared DM.** Each
  CHIME `_cntr_bpc` product is dedispersed at a CHIME-optimized DM that
  differs from the DSA DM at the 0.01–0.15 pc cm⁻³ level (e.g. oran CHIME
  397.0153 vs DSA 396.882; zach 262.3621 vs 262.368). Two DSA filenames also
  deviate from `bursts.yaml`: chromatica 272.368 vs 272.664 (0.3 pc cm⁻³ —
  ~5 DSA time bins of differential sweep, worth a provenance check) and casey
  491.211 vs 491.207 (negligible). Display options for planning: (a) show
  each panel at its instrument-optimized DM and say so in the caption
  (standard practice, zero reprocessing — CONTEXT.md's "avoid" is about
  quoting a single undifferentiated DM_obs, which a caption stating both
  conventions does not do); (b) re-shift CHIME panels to the DSA reference DM
  via `pipeline/dispersion/dm_power_analysis.py:35`
  (`shift_waterfall_residual_dm`). The caption must state whichever convention
  is used, per the trust-reset documentation rule.
- Per-section sample rule (CONTEXT.md:163-165): the caption must state the
  sample is the full twelve-burst co-detection set.

## Prior Art

Light note (domain memory, not a fresh sweep): multi-burst waterfall galleries
are the standard presentation for FRB sample papers — e.g. CHIME/FRB catalog
papers and DSA-110 host-galaxy papers show per-burst dedispersed dynamic
spectra with summed time profiles in a grid. A two-band (co-detection) gallery
showing CHIME and DSA panels per burst with a common time axis is the natural
extension; no external tooling is needed beyond matplotlib infrastructure
already in the repo.

## Synthesis

Everything needed exists locally; the figure is net-new but well-precedented.

- **Data path is clear:** 24 local npy waterfalls (12 bursts × 2 bands),
  dedispersed and bandpass-corrected, 81.9 ms burst-centered windows, with
  per-burst decimation hints in the scattering configs.
- **Design skeleton suggested by precedent:** per burst, a CHIME panel
  (400–800 MHz) and DSA panel (1311–1499 MHz) sharing a common ms-scale time
  axis (fullband_waterfall precedent), tiled 4×3 or 3×4
  (jointmodel_montage precedent), magma, per-band 1–99 pct normalization,
  `use_flits_style()`, pdf+png+svg triplet, `figure*` at `\textwidth` in
  `sec:data`.
- **Open design decisions for planning:** grid arrangement (4×3 vs 3×4 vs
  2×6); whether to add summed time-profile marginals per panel; time-window
  width per burst (fixed ±20–40 ms vs per-burst adaptive); frequency
  downsampling factors for print resolution; burst ordering (chronological =
  `bursts.yaml` order vs `ORDER` list); where the producer script lives —
  pipeline submodule (clean provenance, but requires FLITS-branch PR + pin
  bump) vs top-level `scripts/` (lighter precedent:
  `scripts/plot_ne2025_mw_properties.py`).
- **Gaps/hazards:** corrupted derived sheets (mahi TNS mislabel) must not be
  consumed; jointmodel appendix's 11-vs-12 chromatica gap is an adjacent
  inconsistency this figure would *not* inherit (chromatica's raw data exists);
  the observations.tex:31-32 disclaimer sentence needs a wording pass when the
  figure lands.

## References / Sources

- Code: `pipeline/configs/bursts.yaml:21-148`;
  `pipeline/scattering/scat_analysis/burst_metadata.py:51-56`;
  `pipeline/scattering/configs/telescopes.yaml`;
  `pipeline/flits/batch/codetection_plots.py:97,159,179,244,593,661,687-725`;
  `pipeline/analysis/scattering-refit-2026-06/fullband_waterfall.py:42-162`;
  `pipeline/analysis/scattering-refit-2026-06/plot_jointmodel_montage.py:18,34-52,80-112`;
  `pipeline/analysis/chime_dm/plot_dm_grid.py:49-138`;
  `pipeline/flits/plotting.py:21-59`; `pipeline/tools/figure_manifest.py`;
  `pipeline/tools/sync_figures.py`; `main.tex:6-21`;
  `sections/observations.tex:19-45`; `sections/jointmodel_pairs.tex:4-31`.
- Data: `~/Data/Faber2026/dsa110/DSA_bursts/` (24 `_cntr_bpc.npy` waterfalls);
  `~/Data/Faber2026/dsa110/catalog/dsa110_frb_catalog_README.md:35-54`;
  `~/Data/Faber2026/dsa110/upchan_codetections/{nick}_time0_metadata.json`.
- Manuscript state docs: `CONTEXT.md` (trust reset, V6 convention);
  `REPRODUCE.md`; `docs/rse/specs/handoff/handoff-2026-07-08-07-26-figure-resolution-font-standardization.md`.
