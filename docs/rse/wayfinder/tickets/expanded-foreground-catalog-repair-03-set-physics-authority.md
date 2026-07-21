# Set the stellar-mass, halo-mass, and radius authority

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: Codex
- Blocked by: [Set the catalog crossmatch and quality contract](expanded-foreground-catalog-repair-02-set-crossmatch-contract.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
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

## Resolution

Implemented in dsa110-FLITS PR #213, merge
`3e466c1a180fb169ad09845312348cf539b82632`. Independent replay found zero
classification differences; the 25 finite halo rows pass the Moster inversion,
`R200c` enclosed-mass, published Dutton–Macciò `h=0.671`, and scale-radius
checks. Cluver is correctly Equation 2 and remains null without rest-frame
color.
