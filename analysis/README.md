# Faber2026

Manuscript: **Scattering, Scintillation, and Energetics of Fast Radio Bursts Codetected by CHIME/FRB and
DSA-110.**

Per-sightline attribution of the observed DM and scattering of 12 CHIME/FRB–
DSA-110 co-detected FRBs to the responsible medium (Milky-Way ISM/halo,
intervening foreground-galaxy CGM, the cosmic IGM, and the host).

## Convention

This repo follows the `Faber<YEAR>` first-author manuscript convention: one repo
per paper, LaTeX at the root (`main.tex`), Overleaf-synced via GitHub Integration.
The niche scientific scope lives in the title/abstract, **not** the repo name —
the repo is named for the author and year, not for the pipeline that feeds it.

## Layout

```
main.tex          root manuscript (AASTeX631)
auth.tex          author / affiliation block (\input by main.tex)
sections/         \input'd section files
figures/          figures exported from dsa110-FLITS (tracked, for Overleaf)
bib/refs.bib      bibliography
pipeline/         git submodule -> dsa110-FLITS (reproducibility; see PIPELINE.md)
Makefile          latexmk build (mirrors Overleaf)
```

## Pipeline

The analysis lives in **dsa110-FLITS**, pinned as the `pipeline/` submodule rather
than vendored — the paper *references* the pipeline; the pipeline does not carry
the paper. See `PIPELINE.md`. (Overleaf ignores the submodule and compiles the
`.tex`/figures at the root.)

## Build

```sh
make          # latexmk -> main.pdf
make watch    # continuous preview
make clean
```
