# Freeze six redshiftless candidate identities

- Type: `wayfinder:implement`
- Status: resolved (2026-07-23) — independent adversarial review passed
- Assignee: —
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

## Independent adversarial review — 2026-07-23

The separate review passed. It did not trust the producing replay:

- all four PS1-STRM identities and native rows were compared directly with the
  pinned frozen STRM catalog;
- both AllWISE designations and coordinates were checked against the pinned
  query rows and fresh official CDS VizieR `II/328/allwise` responses;
- source-row and query-response hashes were recomputed;
- all six registry redshifts remain blank, verdicts remain inconclusive, and
  budget flags remain false; and
- the registry, expanded-catalog input, and checked-in Figure 3 grid are
  byte-identical to the pre-repair revision. None of the six inconclusive rows
  enters the confirmed-only Figure 3 grid.

The machine-readable
[review receipt](../../specs/evidence/foreground-source-verification-2026-07-22/adversarial-review.json)
records the six row-level identities, coordinate separations, and source
hashes. This resolves only the identity ticket. Figure 3 regeneration,
independent figure validation, owner visual approval, and promotion remain
blocked later gates.
