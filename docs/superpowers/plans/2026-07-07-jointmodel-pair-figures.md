# Jointmodel Data-Model Pair Figures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a prototype renderer that creates codetection-style data/model/residual figures for the 11 citable 2D burst-model rows.

**Architecture:** Add one focused script beside the existing jointmodel dump/plot scripts. The script reads committed beta-campaign verdicts, loads existing jointmodel NPZ artifacts, converts arrays into `BandSpectrum` objects, and delegates data/model/residual rendering to the existing codetection plotting function.

**Tech Stack:** Python 3.12, NumPy, Matplotlib Agg, existing FLITS plotting helpers.

---

### Task 1: Add Triptych Renderer

**Files:**
- Create: `pipeline/analysis/scattering-refit-2026-06/plot_jointmodel_pair.py`

- [ ] **Step 1: Implement citable-row discovery**

Read `pipeline/analysis/beta_campaign/beta_campaign_verdicts.json`, skip rows with `final == "FAIL"`, and preserve campaign order.

- [ ] **Step 2: Implement NPZ selection**

For each row, load `<runs>/data/joint/<burst>_jointmodel<suffix>.npz`. If it is missing, fail with a message telling the operator to run `dump_jointmodel.py <burst> <suffix>`.

- [ ] **Step 3: Implement `BandSpectrum` conversion**

Construct CHIME and DSA `BandSpectrum` objects for either `data` or `model` display using `freqC/freqD * 1e3`, `timeC/timeD`, `dataC/dataD`, `modelC/modelD`, `noiseC/noiseD`, and `validC/validD`.

- [ ] **Step 4: Implement side-by-side figure**

Call `plot_codetection(..., columns=("data", "model", "resid"), per_band_scale=True, gap_label=False, band_labels=False, show_column_titles=False, per_band_marginals=True)` once per burst.

- [ ] **Step 5: Save outputs**

Save PNG, PDF, and SVG to `figures/prototypes/jointmodel_pair/` by default.

### Task 2: Render And Verify

**Files:**
- Output: `figures/prototypes/jointmodel_pair/*_jointmodel_pair.{png,pdf,svg}`

- [ ] **Step 1: Run renderer**

Run:

```bash
env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" /opt/anaconda3/bin/conda run -n flits python pipeline/analysis/scattering-refit-2026-06/plot_jointmodel_pair.py
```

Expected: 11 rendered bursts, no `chromatica`.

- [ ] **Step 2: Inspect output inventory**

Run:

```bash
find figures/prototypes/jointmodel_pair -maxdepth 1 -type f | sort
```

Expected: 33 files, three extensions for each of the 11 bursts.

- [ ] **Step 3: Visual spot-check one output**

Open `casey_jointmodel_pair.png` with the local image viewer and verify it has left data and right model panels with CHIME/DSA bands, hatched gap, top profiles, and right spectra.
