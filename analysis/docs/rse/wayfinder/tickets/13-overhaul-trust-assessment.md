# Overhaul the trust assessment — re-audit what is trusted and what is not

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: Codex
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
adjudication, populate `docs/rse/control/results-registry.toml` (BOARD.md §0) — every
manuscript-facing result with its producing script, pipeline pin,
external-source provenance, and current trust state seeded from `CONTEXT.md`.
The overhaul grilling then walks the registry row-by-row.

Resolution = a revised trust ledger that supersedes the `CONTEXT.md`
trust-reset block, plus revised re-validation requirements per lane. This
sets the evidence bar the re-fit and scintillation campaigns run against;
the contract-ratification ticket then ratifies whatever bar emerges (and may
be absorbed here if the overhaul settles it).

## Resolution

The owner accepted exact commit
`5292337ffc6c0bb918a763860d70c0575530ae61` as the authority baseline on
2026-07-23. This integration preserves its fail-closed dispositions:
`association.toa_offset_figure`, `budget.cluster_column`, and
`budget.host_dm_posteriors` remain pending under their row-specific gates.
The closed row audit at `75b9d5f` remains supporting evidence; its older host
release condition and cluster snapshot are superseded.

Independent review rejected the initial product-only closure. Later reviews
found source-wide numeric ownership, incomplete TeX graph discovery, permissive
row/pin validation, and semantic cross-assignment risks. Those defects are
closed: all 586 number-bearing lines have an independently fixed owner or
substantive exclusion; the active graph covers `\input`, `\include`, nested
tables, figure wrappers, and fresh recorder files; and the exact canonical 62
rows pass strict schema and repository-specific commit checks. New or changed
registered number-bearing claims, rows, keys, and unregistered artifacts fail
closed. Qualitative scientific claims remain subject to manuscript review; this
registry does not claim to discover them. No scientific result was promoted by
this audit. The TOA-offset figure remains `pending`: no explicit
authority or exact-byte review cleared it.

### Revised ledger

- **Trusted, within named boundaries:** association/sample results tied to the
  V6 artifacts and shared DSA-DM convention; the remediated foreground census;
  and the unchanged, receipted V5 budget outputs. A row-specific open decision
  or provenance gap limits only that row or field. It does not revoke the
  cleared lane wholesale.
- **Pending:** Figure 1 exact bytes, host-DM posterior headline, the CHIME gate
  table as a science result, the probabilistic Phineas budget update, and the
  remediated two-band scintillation campaign. The stale Phineas value and pin
  were replaced by the current 255 (+67/-52) intervening-DM and 62 host-DM
  values, but the row remains non-quotable until its analysis and manuscript
  commits are integrated and re-receipted. Other pending products likewise stay
  non-quotable until their named gate closes. The owner accepts the Zach visual
  diagnostic as pre-bad-channel-mask diagnostic evidence, not as a cleared
  measurement or validated preprocessing product.
- **Revoked:** legacy joint and sub-band scattering fits, DSA-only ACF fits,
  the two-screen composite, spectral amplitudes/energies, the multiplicity
  demonstration, and FRB 20230913A attribution. Their tracked artifacts are
  provenance records, not citable sky measurements.
- The JointTF v2 packet audited on held branch
  `rse/jointtf-grok-harvest-revalidation` (preserved on main while this ticket
  was active) contributes three independently harvested, byte-reproducible
  candidate figures. It does not
  supply a complete twelve-burst roster, exact rerun provenance, component-count
  adoption, or manuscript promotion. Those candidates remain pending/revoked.

### Proportionate re-entry requirements

1. **Deterministic catalog, association, and budget products:** named source
   inputs; producing code and exact pin; byte-exact replay; units/sign/convention
   tests; and one independent calculation, invariant, or source check. Synthetic
   injections and posterior-predictive checks are required only when the row
   makes a fit, detection-efficiency, or uncertainty-coverage claim.
2. **Joint scattering measurements:** certified L1 inputs; exact code/config/
   seed manifest; synthetic recovery; explicit rejection of boundary/rail and
   mode-jump solutions; posterior-predictive residual check; independent
   re-derivation; and simulation-based calibration when posterior intervals are
   quoted. Owner component-count and figure review remain required.
3. **Sub-band profile diagnostics:** input lineage, pin/config, window support,
   boundary and residual checks suffice while they stay diagnostic-only. Any
   promotion to a sky measurement inherits the full joint-fit bar.
4. **Scintillation ACF measurements:** certified DM, mask, axes, burst envelope,
   and off-pulse inputs; injection recovery including resolution/censoring;
   window/mask stability; off-pulse/null and residual checks; and an independent
   ACF estimate. Use an identifiability/support test instead of an irrelevant
   parameter-rail test. Owner review of the data cards and ACF panels remains.
5. **Spectral amplitudes and energies:** calibrated input lineage; exact
   selection rule; spectral-index boundary diagnosis; synthetic parameter
   recovery; residual check; and an independent units/calibration calculation.
   Scattering-fit validation is not required unless a stated energy result
   consumes scattering parameters.
6. **Composites and attributions:** every upstream row must already be trusted;
   then replay the composite and independently recompute it. Do not repeat an
   upstream injection battery unless the composite introduces a new fitted
   estimator.

`revoked` may move only to `pending` when its automated evidence packet is
complete. `pending` may move to `trusted` only through its named independent
validation and any required owner visual or scientific sign-off.

### Registry completion

- `docs/rse/control/results-registry.toml` now separates scientific `trust`
  from `provenance_state` for all 62 rows, including the 36 input certificates;
  resolves producers/pins/inputs/artifacts where live evidence exists; and
  names every remaining provenance gap. A `complete` row cannot contain an
  inferred/unconfirmed pin or a missing producing, input, or artifact path.
  Every producer, input, and artifact has its own declared repository and
  commit; complete-row commits are full 40-hex identities verified in that
  repository, and each declared path must exist in that exact commit.
  Analysis-local producers cannot borrow a pipeline commit.
- `docs/rse/control/results-registry-claim-owners.toml` is the independent
  semantic ownership review. Validation compares every source, fingerprint,
  duplicate occurrence, owner, and exclusion against it; changing a claim to a
  different known result is rejected. TOA delay/dispersion definitions,
  chance-coincidence claims, and residual diagnostics therefore have distinct
  owners. Exact ledger keys and types are enforced before lookup construction;
  duplicate source blocks or claim identities cannot be hidden by dictionary
  collapse.
- `scripts/render_results_registry.py` deterministically generates `RESULTS.md`.
  Tests enforce every required key and type on every row, unique rows, allowed
  states, explicit pending reasons, anchored pipeline pins that exist in the
  pipeline repository, strict complete-provenance rules, full compiled-graph
  coverage, and byte equality of the generated view. The exact row roster and
  row keys are fixed. Mutation tests prove that a new number, figure, included
  file, wrapper, nested table, row, or key fails closed. A recorder file is used
  only when newer than every source it discovers, including recorder-only
  wrappers. The trusted association-card row covers only the twelve appendix
  cards; the TOA decomposition and its `sections/toa.tex` consumer belong solely
  to the pending TOA row. Exact nested schemas cover prose sources and claims,
  artifact ownership, and the canonical fifteen input-lineage exceptions.
- `make check-state` now runs both registry validation and the generated
  `RESULTS.md` byte-drift check after the existing control-state gate.
- `scripts/generate_results_coverage.py` preserves reviewed per-claim owners;
  every newly discovered claim receives the rejected `__SELECT_OWNER__`
  sentinel until a row owner is explicitly selected.
- `CONTEXT.md` now marks the 2026-07-06 blanket reset as historical and names
  this row-level registry as current authority.
- Exactly fifteen derived-input exceptions remain explicitly incomplete: twelve
  remediation packets lack producing Git identity and SHA-256 manifests; three
  Freya package manifests lack producing Git identity and separate receipts.
  They were not silently promoted.
