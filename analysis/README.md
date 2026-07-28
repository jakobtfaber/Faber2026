# Faber2026 analysis

Scientific analysis and research-control workspace for the Faber2026
manuscript. The parent manuscript repository mounts this repository at
`analysis/` and pins one exact commit. Shared fitting code is supplied by the
exact FLITS dependency recorded in `pyproject.toml` and `uv.lock`.

## Scientific subjects

| Directory | Manuscript subject |
|---|---|
| `observations/` | data products, calibration, recovery, and integrity |
| `associations/` | event association, timing comparison, and chance coincidence |
| `dispersion/` | dispersion measure and arrival-time alignment |
| `scattering/` | pulse broadening, model comparison, and joint fits |
| `scintillation/` | scintillation measurement and interpretation |
| `foregrounds/` | foreground systems, hosts, and propagation budgets |
| `energetics/` | flux calibration, fluence, and burst energy |
| `polarization/` | polarization and rotation-measure interpretation |

Every subject presents the same small interface:

```text
subject/
├── README.md
├── data/
├── methods/
├── results/
├── figures/
├── tests/
└── studies/
```

The first five directories hold current canonical material. `studies/` hides
dated, focused, or superseded investigations without making their names part of
the repository’s top-level interface.

## Shared repository machinery

- `docs/` — scientific narratives, research control, decisions, and protocols.
- `scripts/` — shared producers, renderers, audits, and control tools.
- `tests/` — repository-wide scientific, provenance, and contract checks.
- `figure_review/` — fail-closed figure review records.
- `figures/` — shared diagnostic and historical figure material.
- `config/` — shared configuration.
- `schemas/` — structured-record schemas.
- `.archive/` — preserved material that is not part of the active interface.

Final manuscript TeX and embedded figure bytes remain in the parent repository.
Large scientific data remain external and are referenced through manifests and
provenance records.

## Start here

1. Read `CONTEXT.md` for current science and custody state.
2. Read `docs/rse/ops/repository-map.md` for authority and provenance.
3. Search before reconstructing history:

   ```sh
   python3 scripts/kb search "<topic>"
   ```

4. Run the repository gate:

   ```sh
   make test MANUSCRIPT_ROOT=..
   ```
