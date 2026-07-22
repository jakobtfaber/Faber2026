# Faber2026

Manuscript: **Scattering, Scintillation, and Energetics of Fast Radio Bursts
Codetected by CHIME/FRB and DSA-110**

This repository is the compact manuscript authority synchronized with Overleaf.
Research-control material and fitting code live in pinned submodules.

## Layout

```text
main.tex          root manuscript (AASTeX631)
auth.tex          author and affiliation block
sections/         manuscript sections and parked section drafts
figures/          final embedded assets and figure catalog
bib/refs.bib      bibliography
analysis/         Faber2026-analysis submodule
pipeline/         dsa110-FLITS submodule
```

Overleaf compiles only the root TeX, bibliography, generated tables, and final
figure assets. It does not need either submodule.

## Build

```sh
make
make watch
make clean
```

## Research workspace

Clone both pins before running analysis or control tooling:

```sh
git submodule update --init --recursive
make test-science
make kb-index
```

The exact manuscript boundary is recorded in `manuscript-boundary.txt` and
enforced by `tests/test_manuscript_boundary.py`.
