# Set the Figure 3 regeneration and promotion gate

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Codex
- Blocked by: [Set the stellar-mass, halo-mass, and radius authority](expanded-foreground-catalog-repair-03-set-physics-authority.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Triage: `ready-for-agent`

## Question

What exact versioned input and review receipt are required before corrected
foreground geometry may replace the installed Figure 3 bytes?

## Acceptance decision

Build a checked-in figure-input CSV from the census verdicts plus corrected
mass/radius product. Declare it in `figures/catalog.yaml`; remove the home-directory
default from the generator. Render only to `figure_review/staging/fig3_halo_grid`,
register a `fig3-halo-grid` approval slot, and require independent validation
plus manuscript-owner visual approval before byte-identical promotion.
