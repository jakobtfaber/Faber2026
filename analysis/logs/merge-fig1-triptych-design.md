# Design: Fig. 1 as data | model | residual triptychs

**Date:** 2026-07-11  
**Status:** approved 2026-07-11 (flagged fits: show with †)  
**Canonical spec:** `docs/superpowers/specs/2026-07-11-codetection-triptych-fig1-design.md`  
**Plan:** `docs/superpowers/plans/2026-07-11-codetection-triptych-fig1.md`  
**Supersedes:** overlay/contour recommendation in `logs/merge-fig1-jointmodel-synthesis.md`

## Owner lock

- No overlays or contours on the data waterfall.
- Each burst: **time–frequency data | 2-D model | residuals** side by side.
- Full structural resolution; off-pulse pad each side ≈ CHIME burst width \(W_C\).

## Layout

**One burst per full-width `figure*[p]` page**, MJD-ordered, continued under one conceptual figure number (or `fig:codetection-gallery` + sub-labels `…-zach`, etc.).

This is the existing `plot_codetection` / `jointmodel_pair` layout, promoted from appendix to the early Observations slot that currently holds the compact 4×3 gallery. Cramming 12×3 waterfalls into one page would violate the resolution constraint.

Per page (reuse `pipeline/flits/batch/codetection_plots.py::plot_codetection`):

| Column | Content |
|--------|---------|
| **Data** | CHIME+DSA on one frequency axis, hatched gap; profile strip + spectrum marginal; **no** model curve overlaid (`show_model_on_data=False`) |
| **Model** | Same geometry, best-fit 2-D model waterfall + its marginals |
| **Residual** | Whitened residual (existing RdBu_r / σ clip) |

## Window & resolution (unchanged consensus)

- On-pulse union of both bands via current `onpulse_span`; pad \(P=\max(W_C, 1.5\,\mathrm{ms})\) beyond that union; DSA-only structure expands the union first (Zach).
- Display grid: DSA native 32.768 µs; CHIME ×13 ≈ 33 µs; 512 ch/band; ~600 dpi raster for waterfalls, vectors for axes.

## Manuscript placement

- **Replace** `figures/codetection_gallery.pdf` as the opening sample figure in `sections/observations.tex`.
- **Retire or thin** the appendix `app:jointmodel-pairs` duplication (same panels must not appear twice). Prefer: front-load all accepted triptychs; appendix keeps only notes / flagged commentary, or disappears.
- **Results Whitney exemplar:** become a cross-ref to the Whitney page of Fig. 1, not a second include.
- **Chromatica:** data-only single-column page (or data with blank model/resid marked “no accepted joint fit”) until a fit exists — still in the sequence so the sample is complete.
- **Caption:** morphology-audit framing; no quoted τ/α/β from these panels under trust reset (same language as current jointmodel-pair captions).

## Implementation sketch

1. Apply CHIME-width crop + display resolution when building/staging the band dicts that feed `plot_codetection` (today’s jointmodel_pair crops may differ).
2. Regenerate `figures/jointmodel_pair/*` (or a new `figures/codetection_triptych/`) with `show_model_on_data=False` and the new window rule.
3. Swap Observations include from gallery PDF → multi-page triptych includes (mirror `sections/jointmodel_pairs.tex` macro).
4. Remove duplicate appendix includes; update Results Whitney paragraph.
5. Manifest of exact NPZ/JSON artifacts; promote scratch fits into tracked `fit_artifacts/` for REPRODUCE.md.
6. Keep optional `--data-only` gallery script for diagnostics, but it is no longer Fig. 1.

## Open (minor)

- Flagged fits (Whitney/Hamilton/Wilhelm): still show full triptych with a caption dagger, or hold those pages until refit?
- Exact label scheme: one `\label{fig:codetection-gallery}` with continued captions vs twelve numbered subfigures.
