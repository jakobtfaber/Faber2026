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

## Start here

After initializing the submodules, read the
[repository and provenance map](analysis/docs/rse/ops/repository-map.md).
It explains the three repositories, scientific data chain, authority roles,
and how to trace a manuscript claim, figure, table, or fit to its sources.

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
