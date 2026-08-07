# Subject directory migration

Date: 2026-07-28

## Decision

The active analysis interface is organized by manuscript subject:

- `observations/`
- `associations/`
- `dispersion/`
- `scattering/`
- `scintillation/`
- `foregrounds/`
- `energetics/`
- `polarization/`

Each subject documents the same interface: `data/`, `methods/`, `results/`,
`figures/`, `tests/`, and `studies/`. Git records only populated directories.
Focused, dated, legacy, or exploratory work is contained below `studies/`.

## Retired top-level names

| Previous location | Canonical subject |
|---|---|
| `campaigns/codetections/`, cube and CHIME calibration work | `observations/studies/` |
| association and crossmatching campaigns | `associations/studies/` |
| `dm-joint-phase-v2/` and dispersion-measure campaigns | `dispersion/` |
| scattering campaigns and fit generations | `scattering/` |
| `scintillation-summary/` and scintillation campaigns | `scintillation/` |
| `provisional_propagation/` and foreground census work | `foregrounds/` |
| `v3_energetics/` and burst-energy campaigns | `energetics/` |
| `codetections_polarization/` | `polarization/studies/codetections/` |

The generic `campaigns/` root is retired. Its obsolete analysis-manuscript
prototype is preserved under `.archive/legacy-analysis-manuscript/`.
Single-submodule migration tools are preserved under
`.archive/single-submodule-migration/`.

Two overlapping scattering-refit trees were reconciled. The complete recovered
snapshot, identified by its migration provenance, is canonical at
`scattering/studies/joint-refits/`. The older duplicate is preserved under
`.archive/superseded-joint-refits/`.

## Boundary

Shared fitting code comes from the exact FLITS dependency in `pyproject.toml`
and `uv.lock`. Project-specific scientific material belongs to one subject.
Repository-wide control, rendering, provenance, and contract machinery remains
under `docs/`, `scripts/`, `figure_review/`, `config/`, and `tests/`.

Historical receipts, handoffs, certificates, and archived evidence retain the
paths they recorded at creation. Active code and configuration use canonical
subject paths.

## Verification

`tests/test_subject_structure.py` fails if a retired root returns or a subject
loses its documented interface. The full test suite and an exhaustive active
path search are required before the parent repository updates its analysis pin.
