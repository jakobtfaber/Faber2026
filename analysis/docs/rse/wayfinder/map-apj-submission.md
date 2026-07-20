<!-- wayfinder:map -->
# Map: ApJ submission of the CHIME/FRB–DSA-110 co-detection manuscript

Tickets live in [`tickets/`](tickets/). A ticket is claimed by writing an
assignee into its header; blocking uses the `Blocked by:` header line (local
markdown tracker — no native dependency links). The frontier = open tickets
with no open blockers and no assignee.

## Destination

Every decision required to submit the manuscript to the Astrophysical Journal
is made and recorded: scope under the deadline is settled, the analysis
re-validation contracts are ratified, the open author calls (priors, census
wording, prescription conflicts, review dispositions, co-authors) are closed,
and execution of the remaining campaigns and writing is fully specified in the
existing lane system. The map does not carry the execution itself.

## Notes

- **Target: submit by 2026-07-31** — owner judges it more than achievable
  with the resources at hand (2026-07-18). Timing is **not** a sequencing
  driver: decisions are made on scientific need ("worry about what needs
  doing"), and the date is context, not a constraint that forces descoping.
- **Planning-only map** (owner choice, 2026-07-18): tickets resolve decisions;
  execution lives on the manuscript-aligned board, [`BOARD.md`](../control/BOARD.md)
  (canonical as of 2026-07-18 — organized abstract→appendices with one
  cross-cutting campaigns lane). The map sits *above* the board.
  `plan-circulation-readiness.md` and the `program-state.toml` lane views are
  archived/frozen history.
- **Naming convention (owner preference, 2026-07-18):** descriptive names
  everywhere; the plan's letter+number stage codes (V1, B7, S12, P3…) are
  being retired — see the renaming ticket. When a ticket must reference a
  legacy code for traceability, it gives the description first, code in
  parentheses.
- **Standing context:** [`CONTEXT.md`](../../../CONTEXT.md) (trust-reset state,
  language contracts), [`ops/review-status.md`](../ops/review-status.md)
  (open review items; root referee/triage docs deleted 2026-07-19).
  Skills: `/grilling`, `/domain-modeling` for HITL tickets.
- **Both-band scintillation campaign stands as a circulation gate** (owner,
  reaffirmed 2026-07-18): methods now exist for CHIME and DSA bands; the
  qualifying CHIME route postdates the 2026-07-15 docs and must be named and
  ratified (see its ticket).
- **Raw CHIME data (owner, 2026-07-19):** only the twelve singlebeam voltage
  `.h5` files on h17
  (`…/chime_singlebeam/singlebeam_<id>.h5`). Full stop. Full-resolution and
  upchannelized `.npy` products are derived, not raw. Canonical note:
  [`../specs/notes/definition-raw-chime-data-2026-07-19.md`](../specs/notes/definition-raw-chime-data-2026-07-19.md).

## Resume pointer (2026-07-19 — raw CHIME = voltages)

**Ticket 17 reopened** under the corrected raw-data definition. Chain:

1. [Certify the raw data layer](tickets/17-certify-raw-data-layer.md) ← **start here**
   — certify the twelve CHIME singlebeam `.h5` files on h17; do not call
   intensity cubes “raw”
2. [Redo the DM analysis on certified bytes](tickets/18-redo-dm-analysis-certified.md)
   — show `docs/rse/decks/dm/casey-dm-calibration-2026-07-19/casey_dm_strip_CORRECTED.png`
   full-size before asking; read handoff
   `docs/rse/specs/handoff/handoff-2026-07-19-14-56-scint-input-remediation-casey-dm-calibration.md`
3. [Redo the TOA analysis on certified DMs](tickets/19-redo-toa-analysis-certified.md)
4. [Rebuild the upchannelized products + data cards](tickets/20-rebuild-upchannelized-products.md)
5. [Redo the scattering analysis on certified inputs](tickets/21-redo-scattering-certified.md) (folds tickets 14/15)
6. [Redo the scintillation campaign on certified inputs](tickets/22-redo-scintillation-certified.md) → [CHIME-method ratification](tickets/02-ratify-chime-scintillation-method.md)

Master resume doc:
`docs/rse/specs/handoff/handoff-2026-07-19-stratified-restart.md`. Strata tickets
may carry HITL execution where owner calibration is intrinsic (owner
amendment to the planning-only rule). Downstream decision tickets
(priors 07, phineas 06, census wording 08, trust overhaul 13, etc.) remain
open and re-anchor to certified strata as they land; ticket 16 closed as
superseded into 18.

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- [Reconcile the end-of-July target with the remaining science gates](tickets/01-reconcile-deadline-with-science-gates.md)
  — premise rejected (owner, 2026-07-18): the target is achievable and timing
  is not a sequencing driver; scope follows scientific need. Superseded as
  head of the map by
  [Overhaul the trust assessment](tickets/13-overhaul-trust-assessment.md).
- [Certify the raw data layer](tickets/17-certify-raw-data-layer.md)
  — Raw Data (12 singlebeam HDF5 voltage files on h17 with CANFAR lineage)
  certified; intensity cubes are Input Data Products, not Raw Data.
  (Ticket reopened under that definition — see resume pointer.)
## Not yet specified

Fog toward the destination — sharpens as the frontier advances:

- **Post-refit presentation calls** — what the scattering table finally quotes
  per sightline (geometry class, turbulence index or descriptive statement),
  and the restored measured-vs-predicted scattering overlay. Ticketable only
  after the re-fit campaign reports.
- **Synthesis framing** — propagation-vs-intrinsic attribution per sightline,
  the role of each foreground medium class; graduates after the sightline
  analysis exists.
- **Final reconciliation decisions** — abstract headline claims, conclusions
  rewrite, opening-prose consistency with whatever the filled slots actually
  state; post-synthesis.
- **Figure-set finalization** — which wishlist figures ship; Figure 1
  hash-bound byte approval (contract already locked 2026-07-14 — the approval
  is execution QA, not a new decision).
- **Submission mechanics** — Zenodo archive scope + DOI mint, abstract slot
  fills, NE2025 publication-status check, software/facility citations sweep.

## Out of scope

- **Companion polarization paper** (`codetections_polarization/`) — owner
  decision 2026-07-06: parked as companion-paper materials; not on this route.
- **Post-submission work** — response to the actual ApJ referee, proofs,
  press. A fresh effort if/when it arrives.
