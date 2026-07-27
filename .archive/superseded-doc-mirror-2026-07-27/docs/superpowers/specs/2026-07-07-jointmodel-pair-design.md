# Jointmodel Data-Model Pair Figure Design

## Goal

Generate prototype dynamic-spectrum figures for the 11 manuscript/citable
2D burst-model rows. Each output shows observed CHIME+DSA data, the recovered
best-fit 2D model, and the whitened residual in the same visual grammar as the
codetection preview: top time profile, shared-frequency waterfall with hatched
CHIME-DSA gap, and right-side spectrum.

## Scope

- Include only rows from `pipeline/analysis/beta_campaign/beta_campaign_verdicts.json`
  whose `final` is not `FAIL`.
- Exclude `chromatica` for this pass.
- Save one figure per citable burst under `figures/prototypes/jointmodel_pair/`.
- Emit PNG, PDF, and SVG.

## Approach

Use existing model reconstruction artifacts instead of reimplementing the
likelihood. The renderer consumes `*_jointmodel*.npz` files created by
`pipeline/analysis/scattering-refit-2026-06/dump_jointmodel.py`. Each NPZ
contains per-band `dataC/modelC` and `dataD/modelD`, frequency/time axes,
noise vectors, validity masks, and fit summary values.

The new script converts those arrays into `flits.batch.codetection_plots.BandSpectrum`
instances and calls the existing `plot_codetection` renderer once per burst
with `data`, `model`, and `resid` columns. All panels share the same style
choices: per-band scaling, no "no coverage" text in the hatched gap, no
in-gap telescope labels, and no column subtitles.

## Outputs

For each citable burst:

- `<burst>_jointmodel_pair.png`
- `<burst>_jointmodel_pair.pdf`
- `<burst>_jointmodel_pair.svg`

The script prints the list of rendered bursts and fails if any expected citable
row lacks a corresponding jointmodel NPZ.
