# Overhaul the trust assessment — re-audit what is trusted and what is not

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

The trust-reset ledger (three revocation waves of 2026-07-06, recorded in
`CONTEXT.md` and enforced through the plan's re-validation ladders) was drawn
under maximum caution; the owner now judges it misaligned with the actual
epistemic state (2026-07-18: "we need to overhaul our assessment of what is
trusted and what's not"). Re-audit the ledger lane by lane:

- **What has changed since the reset** — census, budget, and
  association/DM-provenance lanes already re-cleared; working scintillation
  methods now exist in both bands; the β-campaign artifacts, injection
  machinery, and provenance audits all postdate the revocation.
- **Per revoked lane** (joint scattering fits, sub-band profile fits,
  scintillation ACF fits, spectral amplitudes/energies, and any residual
  association/DM doubts): does the revocation still serve, or can it be
  cleared outright, or downgraded to a *targeted* check (e.g. verify input
  lineage only) instead of the full five-term contract (lineage + injection
  recovery + rail test + posterior-predictive check + independent
  cross-check)?
- **The re-entry bar itself**: is the five-term contract the right bar
  everywhere, or proportionate per lane?

**Phase 1 (owner decision 2026-07-18): the results registry.** Before
adjudication, populate `docs/rse/results-registry.toml` (BOARD.md §0) — every
manuscript-facing result with its producing script, pipeline pin,
external-source provenance, and current trust state seeded from `CONTEXT.md`.
The overhaul grilling then walks the registry row-by-row.

Resolution = a revised trust ledger that supersedes the `CONTEXT.md`
trust-reset block, plus revised re-validation requirements per lane. This
sets the evidence bar the re-fit and scintillation campaigns run against;
the contract-ratification ticket then ratifies whatever bar emerges (and may
be absorbed here if the overhaul settles it).
