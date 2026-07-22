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

- **Standing delegation (owner, 2026-07-20):** [delegated decision authority](standing-delegation-2026-07-20.md)
  covers only tickets recorded open at `main` commit `33e9e1ce3570`; it permits
  evidence-backed recommendations to be accepted by default. Covered
  away-from-keyboard tickets may resolve after validation without another owner
  response; human-in-the-loop tickets still require live exchange. The grant
  does not waive explicit scientific, visual-review, or one-way action gates.
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
  language contracts), [`technical_review_triage_2026-07-15.md`](../../technical_review_triage_2026-07-15.md),
  [`referee_response_status_2026-07-09.md`](../claude-science/frames/resolve-dsa-110-trial-count-denominator-27fa6148/artifacts/referee_response_status_2026-07-09.md).
  Skills: `/grilling`, `/domain-modeling` for HITL tickets.
- **Both-band scintillation campaign stands as a circulation gate** (owner,
  reaffirmed 2026-07-18): methods now exist for CHIME and DSA bands; the
  qualifying CHIME route postdates the 2026-07-15 docs and must be named and
  ratified (see its ticket).

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- [Reconcile the end-of-July target with the remaining science gates](tickets/01-reconcile-deadline-with-science-gates.md)
  — premise rejected (owner, 2026-07-18): the target is achievable and timing
  is not a sequencing driver; scope follows scientific need. Superseded as
  head of the map by
  [Overhaul the trust assessment](tickets/13-overhaul-trust-assessment.md).
- [Correct the census-aperture description to match the pipeline](tickets/08-correct-census-aperture-description.md)
  — describe the frozen census as built: eligible rows span 101.7–242.7 kpc,
  the retained envelope reaches 281.4 kpc, and eligibility is provenance-based.
- [Replace letter+number stage names with descriptive names in the planning docs](tickets/12-retire-letter-number-stage-names.md)
  — active planning now uses descriptive names; a validated glossary preserves
  historical-code traceability without rewriting closed records.
- [Build the verified Zach CHIME preprocessing baseline](tickets/16-build-verified-zach-chime-preprocessing-baseline.md)
  — explicit-mask channel restoration and migration preflight pass; the owner
  clarified that the accepted diagnostic precedes the bad-channel mask,
  current radio-frequency-interference cleaning is rejected, and science
  remains fail-closed pending the linked validation and input-remediation route.
- [Obtain the exact DSA-110 detection denominator](tickets/09-obtain-dsa-trigger-denominator.md)
  — use the 64 FRB detections with finite MJD in `59611 <= MJD < 60370`;
  candidate-name parity is coincidental, and the manuscript must say
  “detections,” not raw “triggers.”
- [Sign off the dispersion-budget priors and host-DM headline](tickets/07-sign-off-budget-priors-and-host-dm-headline.md)
  — retain the current Walker/Connor diffuse-gas continuation and remaining
  nuisance priors; a `pyhesdm` plus continuous-TNG low-redshift benchmark leaves
  the interpretation unchanged. Only FRB 20220310F has P(host DM < 0) above
  one half, and the central shift is primarily the lower fitted
  $f_{\rm IGM}$, not a generic skew correction.
- [Decide how the free-α diagnostic is reported in the paper](tickets/14-free-alpha-diagnostic-reporting.md)
  — methods/appendix mismatch diagnostic only; excluded from physical tables,
  screen inference, abstract, conclusions, and headline claims.
- [Adjudicate the conflicting halo-mass prescriptions on the phineas sightline](tickets/06-adjudicate-phineas-halo-mass-prescriptions.md)
  — adopt a probabilistic crossing mixture tied to the modified-NFW gas
  truncation radius; retain `R200c` crossing as a reported geometry sensitivity.
- [Ratify the fit re-trust validation contract](tickets/03-ratify-fit-retrust-contract.md)
  — owner ratified the four-term checklist; synthetic-injection recovery is not a
  standalone re-trust step, but known-truth injection remains required for new
  estimators, changed likelihoods/forward models, model-selection procedures, and
  component-count-setting statistics.
- [Decide whether the profile-component-count statistic blocks submission](tickets/05-profile-component-statistic-blocker-decision.md)
  — the statistic is not a circulation blocker for this submission; visual/heuristic
  vetting with the temporary neighbor-count guard from ticket 15 suffices.
- [Adopt count-audit remediation as standing method](tickets/15-count-audit-remediation-standing-method.md)
  — the neighbor-count comparison is a temporary validation guard, not a count setter;
  none of the proposed component-count changes are adopted.

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
- **Injection-calibrated profile-component-count statistic** — chartered as a
  non-blocking successor to the resolved tickets 05 and 15 decisions; required
  before the statistic itself may set manuscript component counts in a future
  campaign. [Develop an injection-calibrated profile-component-count statistic](tickets/20-develop-injection-calibrated-profile-component-count-statistic.md)

## Out of scope

- **Companion polarization paper** (`codetections_polarization/`) — owner
  decision 2026-07-06: parked as companion-paper materials; not on this route.
- **Post-submission work** — response to the actual ApJ referee, proofs,
  press. A fresh effort if/when it arrives.
