# Faber2026-analysis

Research-control workspace for the Faber2026 manuscript.

This repository owns analysis products, scientific tests, figure-generation
sources, provenance, review material, and operational documentation. It is
mounted as the public `analysis/` submodule of
[`jakobtfaber/Faber2026`](https://github.com/jakobtfaber/Faber2026).

## Expected checkout

```text
Faber2026/
├── main.tex             manuscript authority
├── figures/             final embedded assets
├── pipeline/            dsa110-FLITS submodule
└── analysis/            this repository
```

The parent pins the exact analysis and pipeline commits used by the manuscript.
Overleaf synchronizes the parent but does not need either submodule to compile.

## Start here

Read the
[repository and provenance map](docs/rse/ops/repository-map.md)
for the three-repository structure, data chain, authority roles, and recipes
for tracing a manuscript claim, figure, table, or fit back to its sources.

## Layout

- `docs/` — research control, decisions, verification, and handoffs.
- `dm-joint-phase-v2/` and related top-level directories — analysis products.
- `scripts/` — manuscript analysis and control tooling.
- `tests/` — scientific and provenance checks.
- `figure_review/` — fail-closed figure review state.
- `figures/` — noncompiled sources, diagnostics, and historical assets.

Final manuscript TeX, generated tables, and embedded figures remain in the
parent repository.

## Commands

From the parent checkout:

```sh
make test-science
make figures
make kb-index
```

Or from this submodule:

```sh
make test MANUSCRIPT_ROOT=..
make kb-index
```
