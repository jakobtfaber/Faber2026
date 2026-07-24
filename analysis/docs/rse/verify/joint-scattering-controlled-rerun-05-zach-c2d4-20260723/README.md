# Zach C2D4 controlled-rerun verification

Status: reproduction verified; scientific and visual review pending.

The h17 v4 bundle was independently checked against its contract. The source
worktree is clean at pipeline revision `fba755ad`; the frozen morphology is
C2D4 and the seed is `20220207`. Both runs pass preflight,
post-preparation reverification, and complete-output gates. JSON and SVG files
match exactly; NumPy scientific arrays match canonically.

The diagnostics record the required arrival, width, fluence, support, mode,
residual, prior-edge, component, window, and crop guards. Their presence and
hashes were verified; their fitted values and component-count evidence were
not interpreted or trusted.

Every recorded job-180 fit, model-grid, sample, and log hash is explicitly
superseded and cannot satisfy the v4 source, contract, or output-role bindings.

The receipt deliberately keeps:

- `scientific_trust: pending`
- `component_count_evidence_trust: pending`
- `panel_review_eligible: false`
- `panel_approved: false`

Next gate: ticket 6 admission to independent scientific and visual review. No
manuscript figure is promoted.
