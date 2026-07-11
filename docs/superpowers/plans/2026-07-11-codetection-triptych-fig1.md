# Codetection Figure 1 grid and appendix redistribution plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Present the twelve observed joint waterfalls as a 3×4 Figure 1,
retain Zach as the representative full-fit Figure 2, and move the remaining
eleven **data | model | residual** audits to the terminal appendix.

**Architecture:** Reuse `scripts/plot_codetection_triptych.py` for the audited
per-burst artifacts and add `scripts/plot_codetection_data_grid.py` to assemble
their observed data grids into Figure 1. Split the TeX wiring between the Zach
main-text example and the remaining appendix panels. Prefer no `pipeline/`
gitlink bump.

**Tech Stack:** Python 3.12 / conda `flits`, NumPy, Matplotlib Agg, existing `BandSpectrum` + `plot_codetection`, AASTeX `figure*[p]`.

**Design spec:** [`docs/superpowers/specs/2026-07-11-codetection-triptych-fig1-design.md`](../specs/2026-07-11-codetection-triptych-fig1-design.md)

---

## File map

| File | Role |
|------|------|
| `scripts/jointmodel_triptych_manifest.yaml` | nick → NPZ path/suffix, flag, chromatica null |
| `scripts/plot_codetection_triptych.py` | producer: crop + render + write `figures/codetection_triptych/` |
| `tests/test_codetection_triptych.py` | window formula, manifest completeness, no-overlay contract |
| `figures/codetection_triptych/*_triptych.{pdf,png,svg}` | manuscript artifacts (or regenerate into `figures/jointmodel_pair/` if keeping names) |
| `scripts/plot_codetection_data_grid.py` | producer for the 3x4 observed-waterfall overview |
| `tests/test_codetection_data_grid.py` | grid roster, source-routing, and draw-contract tests |
| `figures/codetection_data_grid.{pdf,png,svg}` | manuscript Figure 1 |
| `sections/observations.tex` | Figure 1 grid plus Zach representative Figure 2 |
| `sections/codetection_triptychs_appendix.tex` / `sections/appendix.tex` | remaining eleven audits at the end of the appendix |
| `sections/results.tex` | cross-references to representative and appendix panels |
| `REPRODUCE.md`, `repro_manifest.csv` | grid and triptych producer dependencies |
| `figures/jointmodel_pair/fit_artifacts/` | promote missing jointmodel NPZs from scratch |

Reuse (do not fork physics): `pipeline/flits/batch/codetection_plots.py`, `pipeline/analysis/scattering-refit-2026-06/plot_jointmodel_pair.py` as reference for NPZ→`BandSpectrum` conversion. Prefer implementing crop in the top-level script (or a tiny shared helper under `scripts/`) rather than editing submodule crop defaults, unless a surgical `pad_ms` hook is already enough without a pin bump.

---

### Task 1: Manifest + failing tests

**Files:**
- Create: `scripts/jointmodel_triptych_manifest.yaml`
- Create: `tests/test_codetection_triptych.py`

- [ ] **Step 1: Write manifest skeleton**

Include all 12 nicknames in MJD order. For each of the 11 jointmodel bursts, record `npz` (relative to repo or absolute under `~/Data` / `fit_artifacts`), `suffix`, and `flag` (`null` or short dagger reason). Chromatica: `npz: null`.

- [ ] **Step 2: Write failing tests**

```python
def test_manifest_has_twelve_and_chromatica_null():
    ...

def test_chime_width_pad_formula():
    # synthetic CHIME/DSA on-pulse spans → P == max(W_C, 1.5)
    ...

def test_plot_kwargs_disable_model_overlay():
    # assert producer passes show_model_on_data=False (unit or contract test)
    ...
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
conda run -n flits python -m pytest tests/test_codetection_triptych.py -v
```

- [ ] **Step 4: Commit** (only when user requests / on feature branch)

```bash
git add scripts/jointmodel_triptych_manifest.yaml tests/test_codetection_triptych.py
git commit -m "test: scaffold codetection triptych Fig. 1 manifest and window tests"
```

---

### Task 2: CHIME-width crop helper + NPZ loader

**Files:**
- Create: `scripts/plot_codetection_triptych.py` (helpers first)
- Modify: `tests/test_codetection_triptych.py`

- [ ] **Step 1: Implement `chime_width_display_window(bands) -> (t0, t1)`**

Use band-summed profiles; CHIME width \(W_C\); union of spans; \(P=\max(W_C, 1.5)\). Apply with existing `crop_band_dict` / equivalent so data and model stay aligned.

- [ ] **Step 2: Implement NPZ → `BandSpectrum` pair**

Mirror `plot_jointmodel_pair._band` / `_aligned_bands` TOA shift behavior when metadata exists; then apply the new crop (do **not** rely on fixed `SUBBURST_PAD_MS` alone).

- [ ] **Step 3: Make window tests PASS**

```bash
conda run -n flits python -m pytest tests/test_codetection_triptych.py -v
```

---

### Task 3: Renderer + artifact inventory

**Files:**
- Modify: `scripts/plot_codetection_triptych.py`
- Create/Update: `figures/codetection_triptych/` (or regenerate `figures/jointmodel_pair/`)
- Possibly copy NPZs into `figures/jointmodel_pair/fit_artifacts/`

- [ ] **Step 1: Inventory NPZs**

```bash
ls figures/jointmodel_pair/fit_artifacts/*jointmodel*.npz
ls ~/Developer/scratch/flits-local-runs/data/joint/*jointmodel*.npz
```

Promote any of the six (or however many) scratch-only NPZs needed for the 11-burst set into tracked `fit_artifacts/` (or document `~/Data` paths in REPRODUCE if too large — prefer tracked small NPZs).

- [ ] **Step 2: Implement render loop**

For each manifest row with an NPZ:

```python
fig = plot_codetection(
    bands,
    columns=("data", "model", "resid"),
    show_model_on_data=False,
    per_band_scale=True,
    gap_label=False,
    band_labels=False,
    show_column_titles=True,  # Data / Model / Residual
    per_band_marginals=True,
    title=tns_title_with_optional_dagger,
)
# save pdf/png/svg at dpi>=300 (prefer 600 for waterfalls if API allows)
```

Chromatica: load gallery `_cntr_bpc.npy` products (reuse gallery loaders) and call `plot_codetection(..., columns=("data",), show_model_on_data=False)` with the same window rule.

- [ ] **Step 3: Run producer**

```bash
conda run -n flits python scripts/plot_codetection_triptych.py
```

Expected: 12 stems written; chromatica data-only.

- [ ] **Step 4: Visual QA**

Open zach, whitney (†), phineas (scatter), chromatica. Check: no model curves on data column; pad ≈ CHIME width; structure readable; residual column present for 11.

---

### Task 4: Manuscript wiring

**Files:**
- Modify: `sections/observations.tex`
- Modify: `sections/jointmodel_pairs.tex` and/or `sections/appendix.tex`
- Modify: `sections/results.tex`
- Modify: `REPRODUCE.md`, `repro_manifest.csv`

- [ ] **Step 1: Observations**

Replace the single `codetection_gallery.pdf` include with the 3x4 observed-waterfall grid. Follow it with the Zach triptych as the representative Figure 2. State that the remaining audits are collected at the end of the appendix.

- [ ] **Step 2: Appendix**

Move the remaining eleven triptychs to a dedicated include at the terminal end of the appendix. Do not duplicate Zach there; retain Chromatica as the data-only exception.

- [ ] **Step 3: Results**

Cross-reference Zach as the representative fit and Whitney as an appendix audit.

- [ ] **Step 4: REPRODUCE**

Document `scripts/plot_codetection_triptych.py`, data/NPZ dependencies, and that the old gallery is optional/diagnostic.

- [ ] **Step 5: Build check**

```bash
make
```

Expected: exit 0; no undefined references; the data grid is Figure 1, Zach is Figure 2, and the other eleven audits follow the appendix science content.

---

### Task 5: Closeout

- [ ] **Step 1: Confirm tests + producer + make green**
- [ ] **Step 2: Branch + PR** (standing push/PR auth applies): e.g. `ms/codetection-triptych-fig1`
- [ ] **Step 3: Do not bump `pipeline/` gitlink** unless a submodule edit was unavoidable and separately reviewed

---

## Risks / stop points

1. Missing jointmodel NPZs outside tracked tree → promote or block REPRODUCE claim.
2. Current `crop_bands_to_subburst_window` uses fixed pad + trail cap — must not silently keep that if it violates CHIME-width rule.
3. Live/dirty main tree — implement on a focused branch; do not sweep unrelated dirty lanes into the PR.
4. Flagged fits remain scientifically imperfect; † is honest, not a fix.
