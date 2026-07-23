# Freeze six redshiftless candidate identities

- Type: `wayfinder:implement`
- Status: validated; independent adversarial review pending
- Assignee: Codex
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Triage: `ready-for-human`

## Objective

Freeze source identity and no-redshift evidence for four PS1-STRM rows and two
manual AllWISE extensions. Do not adopt a redshift, change a candidate verdict
or budget flag, or promote Figure 3.

## Current evidence

dsa110-FLITS commit `c913175e567db70980e5f2745dcdf8f7f3ad9fb4`
binds the four PS1-STRM rows to their exact frozen catalog rows and the two
manual extensions to exact AllWISE rows from CDS VizieR `II/328/allwise`.
Independent live VizieR queries returned:

- Isha: `J044538.83+701843.3`
- Oran: `J211150.32+724807.8`

The independent source verifier reports 52/52 source-verified rows, no
discrepancies, no verdict changes, and no budget changes. Figure 3 remains
unpromoted pending regeneration, independent validation, and owner visual
approval.

Do not resolve this ticket until a separate reviewer adversarially checks the
identity-repair diff and records a pass.
