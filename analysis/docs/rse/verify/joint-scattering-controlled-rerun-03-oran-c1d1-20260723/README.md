# Oran C1D1 controlled-rerun verification

Status: reproduction verified; scientific and visual review pending.

The h17 v4 bundle was independently checked against its contract. The source
worktree is clean at pipeline revision `fba755ad`; the frozen morphology is
C1D1 and the seed is `20220506`. Both runs pass preflight,
post-preparation reverification, and complete-output gates. JSON and SVG files
match exactly; NumPy scientific arrays match canonically.

The diagnostics contain prior-edge, residual-morphology, component, fitted
window, and crop-configuration records. Their presence and hashes were
verified; their fitted values were not interpreted or trusted.

The prior Oran triptych PDF (`490d297f…`) and preview (`2328c64b…`) are
superseded and cannot satisfy the new source, contract, output-role, or panel
hash bindings.

The receipt deliberately keeps:

- `scientific_trust: pending`
- `panel_review_eligible: false`
- `panel_approved: false`

Next gate: ticket 6 admission to independent scientific and visual review. No
manuscript figure is promoted.
