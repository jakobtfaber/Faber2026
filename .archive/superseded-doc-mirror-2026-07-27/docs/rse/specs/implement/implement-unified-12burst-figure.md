# Implementation Summary: Unified 12-burst co-detection dynamic-spectra figure

---
**Date:** 2026-07-09
**Author:** AI Assistant (Claude Code)
**Status:** Complete (pending owner layout/caption review)
**Plan Reference:** [plan-unified-12burst-figure.md](../plan/plan-unified-12burst-figure.md)

---

## Overview

`fig:codetection-gallery` now exists: a 4×3 gallery of all twelve co-detected
bursts, each cell stacking band-summed profiles, the DSA-110 waterfall
(1.31–1.50 GHz), and the CHIME/FRB waterfall (0.40–0.80 GHz) on a ±25 ms
relative-time axis, rendered from the 24 local `_cntr_bpc.npy` products (raw
data only — no fit products touched). Embedded in §2 `sec:data` as Figure 1;
builds clean.

**Final Status:** ✅ Complete (one manual criterion open: owner approval)

## Plan Adherence

Deviations:

- **`np.asarray` → explicit copy** (`scripts/plot_codetection_gallery.py:167`):
  memmap-backed arrays are read-only; dead-channel NaN assignment needs a copy.
- **Thin-space glyph bug found in QA:** an accidental U+2009 in the panel-title
  string rendered as tofu under cmr10; removed (titles now plain
  "FRB YYYYMMDDX").
- **No `WINDOW_MS_OVERRIDES` needed:** the planned per-burst widening was
  unnecessary — a 5σ emission-span check on all 24 products bounded every
  burst within ±16 ms of its peak (widest: zach CHIME tail +15.4 ms), inside
  the ±25 ms window.
- **8 tests, not 7:** added `test_discover_products_raises_on_missing`.

## Phases Completed

1. **Pure helpers, test-first** — ✅ 8 tests (block-mean, dead-channel mask,
   peak window, DM-stem parsing, missing-product error, nickname→TNS parity
   against the pinned pipeline's `_FALLBACK_TNS`).
2. **Rendering** — ✅ `scripts/plot_codetection_gallery.py` produces the
   pdf/svg/png triplet; 12 bursts MJD-ascending from `pipeline/configs/bursts.yaml`.
3. **Visual QA** — ✅ all 24 panels show a visible, centered, dedispersed burst;
   **chromatica DSA shows no residual sweep** at the baked 272.368 DM (the
   catalog's 272.664 in `bursts.yaml` vs the file stem remains a provenance
   footnote, not a display defect); CHIME RFI-zapped bands render as gray masks.
4. **Manuscript integration** — ✅ `figure*` in `sections/observations.tex`
   (sec:data), disclaimer sentence softened, REPRODUCE.md + repro_manifest.csv
   rows added, `make` green.
5. **Closeout** — branch `ms/codetection-gallery`, PR per standing
   authorization (see Commits below).

## Files Modified

**Created:**
- `scripts/plot_codetection_gallery.py` — producer (data contract + DM
  convention documented in the module docstring)
- `tests/test_codetection_gallery.py` — 8 unit tests
- `figures/codetection_gallery.{pdf,png,svg}` — the figure (pdf 2.8 MB)
- `docs/rse/specs/research/research-unified-12burst-figure.md`, `plan-…`, this doc

**Modified:**
- `sections/observations.tex` — figure environment + softened morphology
  disclaimer (sec:data)
- `REPRODUCE.md` — embedded-count prose (25→26 tracked, 9→10 embedded)
- `repro_manifest.csv` — new row (`writer_verified=yes`,
  `clone_verified=blocked_external_data`: needs `~/Data/Faber2026/dsa110/DSA_bursts`)

## Verification Results

### Automated
- ✅ `conda run -n flits python -m pytest tests/test_codetection_gallery.py -v` — 8 passed
- ✅ `conda run -n flits python scripts/plot_codetection_gallery.py` — exit 0,
  "rendered 12 bursts (MJD order): zach whitney oran isha wilhelm phineas
  freya johndoeii hamilton mahi chromatica casey"
- ✅ triplet exists; pdf 2.8 MB (< 10 MB)
- ✅ `make` exit 0; `codetection_gallery` ×5 in main.log; no
  `LaTeX Warning: Reference` lines; figure typesets as Figure 1 (page 4)
- ✅ TNS parity test guards the mahi 20240119A mislabel

### Manual
- ✅ 24/24 panels QA'd on the rendered PNG and the typeset PDF page
- ✅ chromatica DSA sweep check: none visible
- ✅ CM-serif fonts; no tofu glyphs after the thin-space fix
- ⬜ **Owner approval of layout/ordering/caption — open**

## Issues Encountered

1. read-only memmap (fixed: copy); 2. U+2009 tofu (fixed: plain space);
3. `conda run` does not forward heredoc stdin — QA scripts run from files
   instead (scratchpad).

## Remaining Work

- [ ] Owner review: layout, MJD ordering, ±25 ms window, caption wording
  (esp. the instrument-optimized-DM sentence), and whether CHIME panels
  should instead be re-shifted to the shared DSA reference DM
  (`shift_waterfall_residual_dm`) — documented option, not implemented.
- [ ] Optional follow-up: chromatica DSA file-stem DM (272.368) vs
  `bursts.yaml` (272.664) provenance note upstream.

## Next Steps

Validate against plan (done inline above), PR review, merge. Journal lane
closes with the PR.

## References

- [Plan](../plan/plan-unified-12burst-figure.md) · [Research](../research/research-unified-12burst-figure.md)
- Commits: `3258195` (helpers+tests+docs), `c2643a3` (render), + tex/repro/closeout commit(s) on `ms/codetection-gallery`

---

**Implementation completed by AI Assistant on 2026-07-09**
