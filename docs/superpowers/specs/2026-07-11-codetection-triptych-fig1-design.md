# Design: Fig. 1 as data | model | residual triptychs

**Date:** 2026-07-11  
**Status:** approved (owner 2026-07-11)  
**Related:** `logs/merge-fig1-triptych-design.md`, prior gallery plan `docs/rse/specs/plan-unified-12burst-figure.md`, jointmodel-pair design `docs/superpowers/specs/2026-07-07-jointmodel-pair-design.md`

## Goal

Replace the compact 4×3 `fig:codetection-gallery` with the first central manuscript figure that shows, for each co-detection, the **time–frequency data**, the **2-D joint model**, and the **whitened residuals** side by side. No overlays or contours on the data column.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Layout | Per-burst **data \| model \| resid** triptych |
| Overlays on data | **None** (`show_model_on_data=False`) |
| Pagination | **One burst per full-width `figure*[p]` page** (full structural resolution) |
| Sample order | MJD-ascending (zach … casey), including chromatica |
| Chromatica | Data-only page until an accepted joint fit exists |
| Flagged fits (whitney, hamilton, wilhelm) | **Show triptychs with †** in caption / title note |
| Residuals elsewhere | Do **not** duplicate full set in appendix; Results Whitney becomes a cross-ref |
| Trust framing | Morphology-audit panels; no quoted τ/α/β from these figures |
| Off-pulse pad | Each side ≈ total CHIME on-pulse width \(W_C\) beyond the observed union |
| Display resolution | **Fit-delivery grid from the jointmodel NPZ** (same `f_factor`/`t_factor` used for the fit); data and model share that grid. Chromatica data-only uses the gallery archival display grid. |

## Non-goals

- Contour or dashed-model overlays on the data waterfall.
- Cramming all 12×3 panels onto one page.
- Pipeline gitlink / pin bump as a side effect (prefer top-level manuscript script + existing `plot_codetection` import).
- Re-fitting or clearing Wave-1 trust reset in this lane.

## Visual recipe (per page)

Reuse `pipeline/flits/batch/codetection_plots.py::plot_codetection` with:

- `columns=("data", "model", "resid")`
- `show_model_on_data=False`
- `per_band_scale=True`, `per_band_marginals=True`
- hatched CHIME–DSA frequency gap; profile strip + spectrum marginals per column

Time window (data-driven, applied identically to data and model arrays before plot):

1. Per band, measure on-pulse span (smoothed threshold / gap-merge as in gallery `onpulse_span`, or equivalent on band-summed profiles).
2. \(W_C =\) CHIME span width.
3. Union \(U\) of CHIME and DSA spans (DSA-only structure expands \(U\)).
4. Display \(T = [U_- - P,\ U_+ + P]\) with \(P = \max(W_C,\ 1.5\,\mathrm{ms})\).
5. Clip only at product boundaries; per-burst overrides only after visual QA.

Chromatica page: `columns=("data",)` (or blank model/resid with explicit “no accepted joint fit” annotation).

## Manuscript placement

- **Observations / `sec:data`:** multi-page triptych sequence replaces `figures/codetection_gallery.pdf`.
- **Appendix `app:jointmodel-pairs`:** remove duplicate `\includegraphics` set (or leave a short pointer).
- **Results:** `fig:jointmodel-pair-whitney` → cross-ref to the Whitney page of the new Fig. 1 sequence.
- Caption language: morphology audit; † for flagged multiplicity issues; chromatica exception.

## Artifact / reproducibility

- Models from `dump_jointmodel.py` NPZs (`*data{C,D}`, `*model{C,D}`, axes, noise, valid).
- Prefer tracked `figures/jointmodel_pair/fit_artifacts/` (and promote missing scratch NPZs into that tree or `~/Data/...` before claiming REPRODUCE completeness).
- Checked-in manifest: nick → NPZ path + suffix + flag status + chromatica null.

## Success criteria

- Referee sees every co-detection’s data, model, and residual at readable structural resolution early in the paper.
- Off-pulse context ≈ one CHIME burst-width per side; bursts not drowned in empty time.
- `make` builds; labels resolve; no duplicate full triptych set in appendix.
- Data-only gallery script may remain as a diagnostic, but is not Fig. 1.

## Spec self-review

- No placeholders for the locked layout/window/trust choices.
- Scope is one figure-system change (renderer + tex wiring + artifact manifest), not a refit campaign.
- Open only if implementation discovers missing NPZs: promotion path is specified.
