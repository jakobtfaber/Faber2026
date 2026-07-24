# Owner review artifact: trust-ledger row audit

Date: 2026-07-22

**Disposition update — 2026-07-24:** retained as historical review evidence.
The owner rejected the host-DM trust promotion recommended below; that row
remains pending. The current authority is the row-level registry and resolved
Wayfinder ticket 13. Verdi source-event identifiers are authoritative; any
`A`-suffix event label retained below is a legacy registry key, not the current
event identity.

Abbreviations used here: CHIME/FRB = Canadian Hydrogen Intensity Mapping
Experiment Fast Radio Burst project; DSA-110 = Deep Synoptic Array 110; DM =
dispersion measure; ACF = autocorrelation function.

Wayfinder ticket: `docs/rse/wayfinder/tickets/13-overhaul-trust-assessment.md`

Mode: review only. No registry edit. No ticket resolution. No scientific trust promotion.

## Verdict

At review time, the registry was a usable review surface but did not yet
supersede the `CONTEXT.md` trust-reset block. `origin/main` commit `6972689` already
demoted `sample.gallery_fig1` to `pending`, resolving the non-current trusted-row
ambiguity found during this review. The historical recommendation was:

1. `budget.host_dm_posteriors`: retain `pending`. The review proposed promotion
   after an owner-approved registry patch, but the owner rejected that promotion
   on 2026-07-24.
2. All other `trust` values: no trust-state change.

Additional non-trust registry fixes recommended:

- Association rows with `VERIFY` notes should keep trust but fill generator and
  artifact paths.
- `scint.chime_gate_table` should stay `pending`; consider `current=false` once
  a replacement campaign row exists, because the current input lineage failed.
- `scattering.beta_table` should remain `revoked,current=false`; any 2026-07-18
  joint time-frequency campaign products need new pending rows, not reuse of
  the revoked legacy row.
- The 36 input-certificate rows should stay `pending` until builder identity,
  stable masks, and final remediated byte provenance are complete.

## Evidence Base Read

- `CONTEXT.md` trust-reset block: waves 1-3 revoked fits, census/budget,
  association, and dispersion-measure products; later restored association,
  foreground census, and dispersion budget; still revoked scattering,
  scintillation, energies, and FRB 20230913G intervening attribution (legacy
  registry key: `attribution.frb20230913a_intervening`).
- `docs/rse/control/results-registry.toml`: 61 result rows and 15 input
  exceptions.
- `docs/rse/control/BOARD.md`: ticket 13 is the active trust-overhaul gate;
  both-band scintillation remains blocked by input remediation.
- `docs/rse/specs/validation-trust-reset-revalidation-phase6.md`: association
  and per-telescope dispersion-measure provenance passed Phase 6.
- `docs/rse/wayfinder/tickets/06-adjudicate-phineas-halo-mass-prescriptions.md`:
  Phineas uses probabilistic crossing; binary radius conflict resolved.
- `docs/rse/wayfinder/tickets/07-sign-off-budget-priors-and-host-dm-headline.md`:
  dispersion-budget priors and headline accepted.
- `docs/rse/specs/notes/owner-data-review-findings-2026-07-18.md`: CHIME/DSA
  scintillation inputs fail due radio-frequency interference, over-dedispersion,
  and dispersion-measure inconsistency; method ratification blocked.
- `docs/rse/wayfinder/tickets/14-free-alpha-diagnostic-reporting.md`:
  free-alpha fit is diagnostic only, excluded from physical result tables and
  headline claims.
- `docs/rse/wayfinder/tickets/16-build-verified-zach-chime-preprocessing-baseline.md`:
  Zach preprocessing baseline is accepted as fail-closed; no science fit or
  claim admitted.

Plain term: a 1-sigma interval means the middle expected range for repeated
measurements under the stated uncertainty model; it is not owner approval.

## Row Audit

| Registry row | Current trust | Recommended trust | Evidence and required gate |
|---|---:|---:|---|
| `association.sample_roster` | trusted | trusted | Keep. Phase 6 restored 12/12 association under the shared DSA dispersion-measure convention. Fill producer/artifact `VERIFY` fields, but no trust change. |
| `association.sample_table` | trusted | trusted | Keep. Phase 6 plus timing-budget update. Fill generator path. |
| `association.pcc_sum` | trusted | trusted | Keep. Association arithmetic restored. Ticket 09 fixed denominator wording; value remains approximate in prose. |
| `association.cards_figures` | trusted | trusted | Keep. Phase 6 restored association figures. Fill generator/hash receipt before final freeze. |
| `association.dm_measurements_table` | trusted | trusted | Keep. Phase 6 documented per-telescope provenance and CHIME-DSA agreement. Fill generator and V6 artifact link. |
| `sample.gallery_fig1` | pending | pending | Keep. `current=false` and owner figure-review promotion is still pending; the prior non-current trusted-row ambiguity is already fixed on current `origin/main`. |
| `mw.foreground_characterization` | trusted | trusted | Keep. Cleared by dispersion-budget re-validation. Submission-time NE2025 publication check remains non-trust follow-up. |
| `mw.disk_halo_values` | trusted | trusted | Keep. Priors accepted in ticket 07; no new change needed beyond updating notes. |
| `census.foreground_table` | trusted | trusted | Keep. Census restored by V4 plus 2026-07-15 remediation. Query-date `VERIFY` is documentation debt, not a trust blocker. |
| `census.counts` | trusted | trusted | Keep. Counts match deduplicated 28-system / 9+1 confirmed state. |
| `census.halo_grid_figure` | trusted | trusted | Keep. Caption/panel-count fix remains presentation work. |
| `census.clusters_icm_figure` | trusted | trusted | Keep. Restored by census remediation. |
| `budget.budget_table` | trusted | trusted | Keep. Ticket 06 changed Phineas modeling details, but the row should stay trusted after registry text is updated to the probabilistic route. |
| `budget.dm_int_nonzero` | trusted | trusted | Keep. Update value text to Phineas probabilistic percentiles in a later registry patch; do not demote for the already-resolved route. |
| `budget.cluster_column` | trusted | trusted | Keep. Cluster geometry systematic is recorded and not material against column uncertainty. |
| `budget.host_dm_posteriors` | pending | pending | The review proposed later owner-approved promotion; the owner rejected that promotion on 2026-07-24. |
| `scattering.beta_table` | revoked | revoked | Keep revoked. 2026-07-18 joint time-frequency outputs are not yet manuscript-facing; validation and owner ratification still pending. |
| `scattering.jointmodel_figures` | revoked | revoked | Keep revoked. Old joint-model montage lineage remains wave-1 revoked. |
| `scattering.multiplicity_demo` | revoked | revoked | Keep revoked. Profile-bias claim still rides on re-fit/count decisions. |
| `scint.dsa_acf_figures` | revoked | revoked | Keep revoked. DSA ACF fits must be rerun under remediated inputs and ratified contract. |
| `scint.chime_gate_table` | pending | pending | Keep pending. It is a campaign-quality table, not a sky claim; current source inputs failed owner review. |
| `scint.twoscreen_table` | revoked | revoked | Keep revoked. Requires both valid decorrelation bandwidth and scattering-fit inputs. |
| `energies.burst_energies_table` | revoked | revoked | Keep revoked. Depends on old spectral amplitudes and energy chain; re-validation still open. |
| `attribution.frb20230913a_intervening` (legacy key; FRB 20230913G) | revoked | revoked | Keep revoked. Both supporting diagnostics still sit on revoked scintillation/scattering strands. |
| `scint.two_band_campaign` | pending | pending | Keep pending. Owner data review blocks science use until radio-frequency-interference cleaning, dispersion-measure reconciliation, byte provenance, and rerun. |
| `l0.casey.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.casey.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.casey.chime_upchan` | pending | pending | Keep pending. Upchannelized products are in the failed scintillation-input class until remediation. |
| `l0.chromatica.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.chromatica.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.chromatica.chime_upchan` | pending | pending | Keep pending. Owner found over-dedispersion and input-lineage failure. |
| `l0.freya.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.freya.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.freya.chime_upchan` | pending | pending | Keep pending. Upchannelized provenance and remediated masks incomplete. |
| `l0.hamilton.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.hamilton.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.hamilton.chime_upchan` | pending | pending | Keep pending. Upchannelized provenance and remediated masks incomplete. |
| `l0.isha.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.isha.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.isha.chime_upchan` | pending | pending | Keep pending. Owner found over-dedispersion and large product dispersion-measure mismatch. |
| `l0.johndoeII.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.johndoeII.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.johndoeII.chime_upchan` | pending | pending | Keep pending. Owner found over-dedispersion and input-lineage failure. |
| `l0.mahi.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.mahi.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.mahi.chime_upchan` | pending | pending | Keep pending. Owner found over-dedispersion and input-lineage failure. |
| `l0.oran.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.oran.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.oran.chime_upchan` | pending | pending | Keep pending. Owner found over-dedispersion and large product dispersion-measure mismatch. |
| `l0.phineas.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.phineas.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.phineas.chime_upchan` | pending | pending | Keep pending. Owner found over-dedispersion and input-lineage failure. |
| `l0.whitney.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.whitney.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.whitney.chime_upchan` | pending | pending | Keep pending. Owner found over-dedispersion and input-lineage failure. |
| `l0.wilhelm.chime_full` | pending | pending | Keep pending. Builder identity not verified; final science mask not approved. |
| `l0.wilhelm.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.wilhelm.chime_upchan` | pending | pending | Keep pending. Owner found over-dedispersion and input-lineage failure. |
| `l0.zach.chime_full` | pending | pending | Keep pending. Zach baseline is accepted only as fail-closed preprocessing evidence; no final science input approval. |
| `l0.zach.dsa` | pending | pending | Keep pending. Builder identity not verified. |
| `l0.zach.chime_upchan` | pending | pending | Keep pending. Zach route still requires cleaning-boundary ratification and complete remediation. |

## Revoked Lane Recommendations

| Lane | Recommendation | Proportionate re-entry bar |
|---|---|---|
| Joint scattering fits | Keep revoked. Create new pending rows for the 2026-07-18 production mass-refit only after leakage, count adoption, validation, and owner ratification. | Full five-term contract: lineage, injection recovery, rail test, posterior-predictive check, independent cross-check. |
| Sub-band profile fits | Keep revoked where they support scattering or component-count claims. | Targeted lineage + injection/count robustness first; full five-term bar if used as physical evidence. |
| Scintillation ACF fits | Keep revoked for old DSA ACFs and pending for current CHIME/two-band campaign. | Full input-lineage and remediated-input rerun are mandatory; posterior-predictive check may be replaced by predeclared ACF null/injection gates if ticket 02 ratifies that exact method. |
| Spectral amplitudes and energies | Keep revoked. | Full re-validation of amplitude lineage, spectral-index rail behavior, selection rule, calibration budget, and independent table parity. |
| Association and observed dispersion measures | Keep trusted. | Targeted maintenance only: fill generator/artifact `VERIFY` fields, spot-check h17 CHIME extraction when practical, preserve shared DSA dispersion-measure convention. |
| Foreground census and dispersion budget | Keep trusted. | Targeted maintenance only: update Phineas probabilistic-crossing text, preserve ticket 07 prior caveat, fill external query-date documentation. |

## Closeout

This is the completed owner review artifact requested by the task. It is not a
trust promotion, registry patch, ticket resolution, Figure 3 action, foreground
redshift re-adjudication, budget re-adjudication, or manuscript submission.
