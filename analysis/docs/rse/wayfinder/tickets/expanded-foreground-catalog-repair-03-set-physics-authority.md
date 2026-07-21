# Set the stellar-mass, halo-mass, and radius authority

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Codex
- Blocked by: [Set the catalog crossmatch and quality contract](expanded-foreground-catalog-repair-02-set-crossmatch-contract.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Triage: `ready-for-agent`

## Question

Which measurements govern each object type, and when must a derived mass or
radius remain null rather than be produced from an inapplicable relation?

## Acceptance decision

The adjudicated census table and overrides govern adopted galaxy stellar mass.
Recompute halo `M200c` with the redshift-dependent Moster relation and `R200c`
from `M200c` and critical density; do not reuse its known-bad legacy radius
columns. A fresh Cluver value is diagnostic only and remains null unless
rest-frame W1-W2, valid photometric flags, and uncertainties are available.
Cluster rows retain their catalog `M500` and `R500`; any `M200c` conversion must
name and test a separate cluster model. Unknown uncertainty stays null with an
explicit status. No numerical fallback is allowed.
