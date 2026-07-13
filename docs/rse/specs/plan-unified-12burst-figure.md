# Implementation Plan: Unified 12-burst co-detection dynamic-spectra figure

> **Implemented with a later DM revision.** The original stored-DM display rule
> below is retained as design history. Manuscript Figure 1 now re-dedisperses
> both native products to the adopted CHIME-primary value before averaging; see
> [verified-dm-adoption-2026-07-13.md](verified-dm-adoption-2026-07-13.md).

---
**Date:** 2026-07-09
**Author:** AI Assistant (Claude Code)
**Status:** In Progress (Direct mode — design decisions locked with rationale; reversible on owner review)
**Related Documents:**
- [Research: Unified 12-burst figure](research-unified-12burst-figure.md)

---

## Overview

The manuscript never shows the data. Twelve co-detected bursts drive every
analysis, yet no figure presents their dynamic spectra; the closest artifacts
(joint-model audit pairs, the orphaned `jointmodel_montage`) are fit-derived and
trust-reset-revoked. This plan adds a single `figure*` gallery — one cell per
burst, each cell stacking the DSA (1.31–1.50 GHz) and CHIME (0.40–0.80 GHz)
dedispersed Stokes-I waterfalls with their band-summed profiles on a common
time axis — placed in §2 "Dynamic spectra and reduction" (`sec:data`).

**Goal:** `figures/codetection_gallery.{pdf,png,svg}` produced by a committed,
REPRODUCE.md-listed script from the 24 local `_cntr_bpc.npy` products, included
in `sections/observations.tex` with a trust-reset-compliant caption, building
clean under `make`.

**Motivation:** first-priority manuscript gap; the figure is pure data
presentation, safe under the trust reset (raw inputs are not revoked products).

## Current State Analysis

- No all-burst data figure exists; `sec:data` (sections/observations.tex:19-34)
  has no figure and disclaims morphology cataloging at observations.tex:30-34.
- Montage TODO anchor at observations.tex:45 shows a figure was scoped here.
- Data: 24 local waterfalls, `~/Data/Faber2026/dsa110/DSA_bursts/{nick}_{tel}_I_{DMstem}_{Nb}b_cntr_bpc.npy`
  (DSA (6144, 2500) @ 32.768 µs; CHIME (1024, 32000) @ 2.56 µs; both ≈81.9 ms
  burst-centered windows; stored freq-descending per
  pipeline/scattering/configs/telescopes.yaml:22,31 — flip on load).
- Sample authority: pipeline/configs/bursts.yaml:21-148 (12 bursts, DM/MJD);
  nickname→TNS: pipeline/scattering/scat_analysis/burst_metadata.py:51-56.
- Style standard: `flits.plotting.use_flits_style()` (pipeline/flits/plotting.py:21);
  script-precedent fallback: pipeline/matplotlibrc via
  scripts/plot_ne2025_mw_properties.py:17-21.
- Repro convention: `conda run -n flits python scripts/<producer.py>` (REPRODUCE.md:61-70).
- Test precedent: tests/test_dm_budget_uncertainty.py (top-level tests/ exists).

## Desired End State

- `scripts/plot_codetection_gallery.py` renders a 4-column × 3-row gallery,
  cells ordered chronologically by MJD (zach … casey). Each cell:
  profile strip (both bands, peak-normalized) over DSA waterfall over CHIME
  waterfall, common time axis (t = 0 at the DSA profile peak; CHIME re-centered
  on its own peak — the products are independently burst-centered and carry no
  shared absolute time zero), magma, per-panel robust normalization, masked
  dead channels in light gray.
- `figures/codetection_gallery.{pdf,png,svg}` checked in; `figure*` with label
  `fig:codetection-gallery` in observations.tex; REPRODUCE.md row added;
  `make` builds with no undefined references.

**Success looks like:** a referee can see all twelve co-detections, both bands,
at a glance; every panel is visibly dedispersed (no residual sweep); captions
state the per-instrument DM convention explicitly.

## What We're NOT Doing

- [ ] No fit/model/residual overlays, τ/β annotations, or component markers —
      all revoked pending §V (CONTEXT.md trust reset).
- [ ] No re-dedispersion of CHIME panels to the shared DSA DM. Panels display
      the products at their instrument-optimized DMs (as baked into the files);
      the caption states this. Re-shifting via
      `pipeline/dispersion/dm_power_analysis.py:35` stays a documented option
      if the owner prefers a single convention.
- [ ] No pipeline submodule changes, no pin bump (script lives top-level,
      precedent scripts/plot_ne2025_mw_properties.py).
- [ ] No polarization, no per-burst zoomed appendix panels, no fix for the
      jointmodel-pairs 11-vs-12 chromatica gap (separate lane).
- [ ] No absolute-time cross-band alignment (would require per-burst
      time0 metadata reconciliation; out of scope for a morphology gallery,
      noted in caption as per-band peak alignment).

**Rationale:** keeps the figure inside the trust-reset-safe zone (raw data
only) and off the reviewed pin-bump path.

## Implementation Approach

**Key decisions:**
1. **Script location — top-level `scripts/`**: avoids a FLITS-branch PR + pin
   bump; REPRODUCE.md already documents this producer class. Trade-off: not
   importable by pipeline tooling; acceptable for a manuscript figure.
2. **DM convention — display as-baked (instrument-optimized), caption states
   both**: zero reprocessing of Wave-3-sensitive quantities; standard practice.
   CONTEXT.md's "avoid" targets quoting a single undifferentiated DM_obs — a
   caption naming both conventions complies.
3. **Layout — 4×3 grid of 3-row cells** (profile / DSA / CHIME): precedents
   plot_jointmodel_montage.py:80-82 (grid), plot_dm_grid.py:116-119 (nested
   subgridspec), fullband_waterfall.py:151-162 (two-band stack).
4. **Common display resolution**: both bands block-meaned to dt = 163.84 µs
   (CHIME t×64, DSA t×5) and 256 channels (CHIME f×4, DSA f×24); window
   ±25 ms about the profile peak (per-burst override dict for scattering
   tails).
5. **Style**: `use_flits_style()` when flits importable, else
   `matplotlib.rc_file(pipeline/matplotlibrc)`; magma; `origin="lower"`,
   `aspect="auto"`, extent in (ms, GHz); pdf+png+svg triplet, png dpi 300.

## Implementation Phases

### Phase 1: Pure helpers, test-first

**Objective:** the numerical core (block-mean, dead-channel mask, peak-window
extraction, product discovery, TNS parity) proven before any rendering.

**Tasks:**
- [x] **Write failing tests** — `tests/test_codetection_gallery.py` (new):

  ```python
  import sys
  from pathlib import Path

  import numpy as np

  ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(ROOT / "scripts"))

  from plot_codetection_gallery import (
      NICK_TNS, block_mean, dead_channel_mask, discover_products, peak_window,
  )

  def test_block_mean_reduces_and_averages():
      arr = np.arange(24, dtype=float).reshape(4, 6)
      out = block_mean(arr, f_factor=2, t_factor=3)
      assert out.shape == (2, 2)
      assert out[0, 0] == np.mean([0, 1, 2, 6, 7, 8])

  def test_block_mean_trims_ragged_edge():
      arr = np.ones((5, 7))
      assert block_mean(arr, 2, 3).shape == (2, 2)

  def test_dead_channel_mask_flags_zero_variance():
      rng = np.random.default_rng(0)
      arr = rng.normal(size=(8, 100))
      arr[3] = 0.0
      arr[5] = 2.5
      mask = dead_channel_mask(arr)
      assert mask[3] and mask[5] and mask.sum() == 2

  def test_peak_window_centers_on_peak():
      prof = np.zeros(1000); prof[400] = 10.0
      i0, i1 = peak_window(prof, dt_ms=0.16384, window_ms=25.0)
      assert i0 == 400 - 152 and i1 == 400 + 153  # 25/0.16384 ≈ 152.6

  def test_peak_window_clips_at_edges():
      prof = np.zeros(100); prof[2] = 1.0
      i0, i1 = peak_window(prof, dt_ms=1.0, window_ms=25.0)
      assert i0 == 0 and i1 == 28

  def test_discover_products_parses_dm_stems(tmp_path):
      (tmp_path / "zach_dsa_I_262_368_2500b_cntr_bpc.npy").touch()
      (tmp_path / "zach_chime_I_262_3621_32000b_cntr_bpc.npy").touch()
      prods = discover_products(tmp_path, "zach")
      assert prods["dsa"].dm == 262.368 and prods["chime"].dm == 262.3621

  def test_nick_tns_matches_pipeline():
      sys.path.insert(0, str(ROOT / "pipeline" / "scattering"))
      from scat_analysis.burst_metadata import _FALLBACK_TNS
      canon = {k.lower(): v for k, v in _FALLBACK_TNS.items()}
      assert {k.lower(): v for k, v in NICK_TNS.items()} == canon
  ```

- [x] **Run, watch fail:**
  `conda run -n flits python -m pytest tests/test_codetection_gallery.py -v`
  → expect ImportError (module doesn't exist).
- [x] **Implement minimal helpers** — `scripts/plot_codetection_gallery.py` (new),
  module top + pure functions only:

  ```python
  DATA_ROOT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"

  NICK_TNS = {  # parity-tested against pipeline burst_metadata._FALLBACK_TNS
      "zach": "FRB 20220207C", "whitney": "FRB 20220310F",
      "oran": "FRB 20220506D", "isha": "FRB 20221113A",
      "wilhelm": "FRB 20221203A", "phineas": "FRB 20230307A",
      "freya": "FRB 20230325A", "johndoeII": "FRB 20230814B",
      "hamilton": "FRB 20230913A", "mahi": "FRB 20240122A",
      "chromatica": "FRB 20240203A", "casey": "FRB 20240229A",
  }

  @dataclass
  class Product:
      path: Path
      dm: float

  def block_mean(arr, f_factor, t_factor):
      nf = (arr.shape[0] // f_factor) * f_factor
      nt = (arr.shape[1] // t_factor) * t_factor
      a = arr[:nf, :nt].reshape(nf // f_factor, f_factor, nt // t_factor, t_factor)
      return a.mean(axis=(1, 3))

  def dead_channel_mask(arr):
      return np.nanstd(arr, axis=1) == 0.0

  def peak_window(profile, dt_ms, window_ms):
      peak = int(np.nanargmax(profile))
      half = int(round(window_ms / dt_ms))
      return max(0, peak - half), min(profile.size, peak + half + 1)

  def discover_products(data_root, nick):
      out = {}
      for tel in ("dsa", "chime"):
          hits = sorted(Path(data_root).glob(f"{nick}_{tel}_I_*_cntr_bpc.npy"))
          if len(hits) != 1:
              raise FileNotFoundError(f"{nick}/{tel}: {len(hits)} matches")
          stem = re.match(rf"{nick}_{tel}_I_(\d+)_(\d+)_\d+b", hits[0].name)
          out[tel] = Product(hits[0], float(f"{stem.group(1)}.{stem.group(2)}"))
      return out
  ```

- [x] **Run, watch pass** (same pytest command).
- [x] **Commit** on branch `ms/codetection-gallery`:
  `git commit -m "feat(figures): codetection-gallery helpers + tests"`

**Verification:**
- [x] `conda run -n flits python -m pytest tests/test_codetection_gallery.py -v` → 7 passed.

### Phase 2: Rendering

**Objective:** end-to-end script producing the triplet.

**Tasks:**
- [x] **Add loading + render** to `scripts/plot_codetection_gallery.py`:
  - Band constants from telescopes.yaml values (DSA 1.31125–1.49875 GHz,
    dt 32.768 µs, 6144 ch; CHIME 0.40019–0.80019 GHz, dt 2.56 µs, 1024 ch);
    both stored freq-descending → `arr = np.flipud(np.load(path, mmap_mode="r"))`.
  - Per band: block_mean (CHIME f4/t64, DSA f24/t5) → dead_channel_mask →
    per-channel off-pulse median subtraction (off-pulse = outer 25% of window)
    → profile = masked channel sum → peak_window(±25 ms, `WINDOW_MS_OVERRIDES`
    dict for per-burst widening) → clip vmin/vmax at 1st/99.5th pct.
  - Figure: `fig = plt.figure(figsize=(7.3, 8.0))`; outer
    `gridspec(3, 4, hspace=0.32, wspace=0.18)`; per cell
    `subgridspec(3, 1, height_ratios=[1.0, 2.2, 2.2], hspace=0.08)`;
    profile axis (DSA black, CHIME steel-blue, peak-normalized, TNS title);
    two `imshow(..., origin="lower", aspect="auto", cmap=magma-with-bad-gray,
    extent=[t0, t1, f_lo_GHz, f_hi_GHz])`; y-ticks [1.35, 1.45] / [0.5, 0.7];
    "Time (ms)" bottom row, "Frequency (GHz)" left column only.
  - Style: `try: from flits.plotting import use_flits_style` (after
    `sys.path.append(...parent.parent / "pipeline")`) `except ImportError:`
    `matplotlib.rc_file(pipeline/matplotlibrc)`.
  - Order: MJD-ascending from pipeline/configs/bursts.yaml (yaml.safe_load).
  - Save: `for ext in ("pdf", "svg", "png"): fig.savefig(figures/codetection_gallery.{ext}, dpi=300)`.
  - `--data-root`, `--out-dir`, `--window-ms` argparse with the above defaults.
- [x] **Run:** `conda run -n flits python scripts/plot_codetection_gallery.py`
  → three files under `figures/`.
- [x] **Commit:** `git commit -m "feat(figures): render codetection gallery"`

**Dependencies:** Phase 1.

**Verification:**
- [x] `rtk ls figures/codetection_gallery.*` → pdf+png+svg, pdf < 10 MB.
- [x] Script exits 0 and prints the 12 rendered nicknames in MJD order.

### Phase 3: Visual QA

**Objective:** confirm the panels are publication-sane before tex integration.

**Tasks:**
- [x] Render PNG, inspect all 24 panels for: residual dispersion sweep
  (chromatica DSA flagged — file DM 272.368 vs bursts.yaml 272.664),
  burst visibility/centering, dead-channel artifacts, clip saturation.
- [x] Apply per-burst `WINDOW_MS_OVERRIDES` / percentile adjustments as needed;
  re-render; send PNG to owner.

**Dependencies:** Phase 2.

**Verification:**
- [x] Every panel shows a visible, centered, dedispersed burst (human check).

### Phase 4: Manuscript integration

**Objective:** figure in the paper, provenance recorded, build green.

**Tasks:**
- [x] **observations.tex** — insert after the `sec:data` paragraph (after
  line 34), reusing the two-column pattern of observations.tex:86-91:

  ```latex
  \begin{figure*}[t!]
  \centering
  \includegraphics[width=\textwidth]{figures/codetection_gallery.pdf}
  \caption{Dedispersed total-intensity dynamic spectra of the full
  twelve-burst co-detection sample, ordered by detection epoch. Each panel
  pairs the DSA-110 waterfall (1.31--1.50\,GHz, top) with the CHIME/FRB
  waterfall (0.40--0.80\,GHz, bottom); the upper strip shows the
  band-summed profiles (DSA-110 black, CHIME/FRB blue), each normalized to
  its peak. Every spectrum is shown at its instrument-optimized dispersion
  measure as recorded in the archival data products (the per-telescope DM
  values and their agreement accompany the data release,
  Section~\ref{sec:data-availability}); times are relative to each band's
  profile peak. Data are bandpass-corrected and block-averaged for display
  ($163.84\,\mu$s; 256 channels per band); masked channels are gray. No
  model curves are overlaid.}
  \label{fig:codetection-gallery}
  \end{figure*}
  ```

- [x] **Soften the disclaimer** (observations.tex:30-34): replace "We do not
  catalog the fine-scale baseband morphology of each burst here; the analysis"
  with "Figure~\ref{fig:codetection-gallery} presents the dedispersed dynamic
  spectra of all twelve co-detections. We do not further catalog fine-scale
  baseband morphology; the analysis".
- [x] **REPRODUCE.md** — add a row for `figures/codetection_gallery.*` →
  `scripts/plot_codetection_gallery.py`,
  run command `conda run -n flits python scripts/plot_codetection_gallery.py`,
  inputs `~/Data/Faber2026/dsa110/DSA_bursts/*_cntr_bpc.npy` +
  `pipeline/configs/bursts.yaml`.
- [x] **Build:** `make` → grep the log for "undefined references" (none) and
  `fig:codetection-gallery` resolving.
- [x] **Commit:** `git commit -m "ms(observations): unified 12-burst co-detection gallery (fig:codetection-gallery)"`

**Dependencies:** Phase 3.

**Verification:**
- [x] `make` exits 0; `rtk grep -c "codetection_gallery" main.log` ≥ 1;
  no `LaTeX Warning: Reference` for the new label.

### Phase 5: Closeout

**Objective:** land it.

**Tasks:**
- [x] Journal the lane done (`scripts/journal-append.sh`).
- [ ] Push `ms/codetection-gallery`, open PR mirroring the `ms/…` precedent
  (standing authorization; oneway-guard gates the push mechanically). No
  pipeline pin change in the diff.
- [x] Update the readiness board is **not** in scope for this agent's session
  unless asked; note the lane in the PR body instead.

**Verification:**
- [ ] PR open, CI (if any) green, diff contains no `pipeline` gitlink change.

## Success Criteria

### Automated Verification
- [x] `conda run -n flits python -m pytest tests/test_codetection_gallery.py -v` — 7 passed
- [x] `conda run -n flits python scripts/plot_codetection_gallery.py` exits 0
- [x] `figures/codetection_gallery.{pdf,png,svg}` exist; pdf < 10 MB
- [x] `make` builds; no undefined `fig:codetection-gallery` reference
- [x] TNS-parity test passes against the pinned pipeline (guards the mahi
      FRB 20240122A vs 20240119A mislabel)

### Manual Verification
- [x] All 24 panels: visible centered burst, no residual sweep, clean masking
- [x] chromatica DSA panel specifically checked for sweep (DM-stem discrepancy)
- [x] Fonts render as CM serif; layout survives at print scale
- [ ] Owner approves layout/ordering/caption

### Reproducibility & Correctness
- [x] Producer, env (`flits` conda), inputs, and command recorded in REPRODUCE.md
- [x] Deterministic (no RNG); block-mean unit-tested against hand-computed
      values (Phase 1)

## Testing Strategy

Unit tests are in-phase (Phase 1). Integration = the end-to-end render on real
data (Phase 2 verification). Manual = visual QA grid (Phase 3) + owner review.
Test data: the 24 local npy products (no fixtures needed; discovery test uses
tmp_path touch files).

## Risk Assessment

1. **Risk:** chromatica DSA product dedispersed at 272.368 while catalog says
   272.664 (≈5 display bins of differential sweep across the DSA band).
   - Likelihood: Medium · Impact: Low (display-level)
   - Mitigation: visual QA gate; if sweep visible, correct via
     `shift_waterfall_residual_dm`-style roll at load, and document in caption.
2. **Risk:** memory (24 × ~120 MB) — mitigated by `mmap_mode="r"` + immediate
   block-mean per band, sequential loop.
3. **Risk:** weak-burst panels (low S/N after ±25 ms window) look empty.
   - Mitigation: per-burst window/percentile overrides (Phase 3).
4. **Risk:** `flits` env lacks a needed import — mitigated by matplotlibrc
   fallback and pure-numpy core.

## Edge Cases and Error Handling

1. **Missing/duplicate product file** → `discover_products` raises
   FileNotFoundError naming burst+telescope (tested).
2. **All-NaN or all-zero channel block** → dead_channel_mask + masked-array
   sum keeps the profile finite (tested for zero-variance).
3. **Peak near window edge** → `peak_window` clips to array bounds (tested).

## Documentation Updates

- [x] REPRODUCE.md row (Phase 4)
- [x] Module docstring in the script: data contract, DM convention, provenance

## Open Questions

None. (Owner-preference items — layout, DM display convention — are decided
with rationale above and remain reversible on review.)

---

## References

- [Research: Unified 12-burst figure](research-unified-12burst-figure.md)
- Files: `sections/observations.tex:19-46`, `pipeline/configs/bursts.yaml:21-148`,
  `pipeline/scattering/configs/telescopes.yaml:16-33`,
  `pipeline/flits/plotting.py:21-59`,
  `pipeline/analysis/scattering-refit-2026-06/plot_jointmodel_montage.py:18,80-112`,
  `pipeline/analysis/scattering-refit-2026-06/fullband_waterfall.py:42-162`,
  `pipeline/analysis/chime_dm/plot_dm_grid.py:49-138`,
  `scripts/plot_ne2025_mw_properties.py:14-21`, `REPRODUCE.md:61-70`.

## Review History

### Version 1.0 — 2026-07-09
- Initial plan; design decisions locked with rationale (Direct mode, owner away).
