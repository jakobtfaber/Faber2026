# Set the Figure 3 regeneration and promotion gate

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: Codex
- Blocked by: [Set the stellar-mass, halo-mass, and radius authority](expanded-foreground-catalog-repair-03-set-physics-authority.md), [Repeat source-level redshift verification](expanded-foreground-catalog-repair-09-repeat-redshift-source-verification.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `resolved`

## Question

What exact versioned input and review receipt are required before corrected
foreground geometry may replace the installed Figure 3 bytes?

## Acceptance decision

Build a checked-in figure-input CSV from the census verdicts plus corrected
mass/radius product. Declare it in `figures/catalog.yaml`; remove the home-directory
default from the generator. Render only to
`figure_review/artifacts/staging/fig3_halo_grid`,
register a `fig3-halo-grid` approval slot, and require independent validation
plus manuscript-owner visual approval before byte-identical promotion.

## Resolution

Resolved 2026-07-24 under the standing delegated decision authority. The
analysis-owned `figures/catalog.yaml` now declares `sightline_halo_grid` with
the versioned analysis input
`foregrounds/census/data/sightline_halo_grid.csv`, passes that input
explicitly via `--halo-csv`, and renders only to
`analysis/figure_review/artifacts/staging/fig3_halo_grid/figures/`.

The default figure-flow catalog now comes from the analysis repository. The
Figure 3 node is not `clone_ok`, has manuscript target
`figures/sightline_halo_grid.pdf`, and is tied to the existing
`fig3-halo-grid` approval slot. The installed manuscript Figure 3 bytes were
not changed. Promotion remains impossible without a verified reproduction
receipt, independent validation, byte-identical approval receipt, and
manuscript-owner visual approval.
