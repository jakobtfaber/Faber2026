# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific and visual decisions. Silence leaves every item blocked._

## 1. Figure 3 installed-bytes approval

**Decision:** Approve the installed Figure 3 bytes (figures/sightline_halo_grid.pdf), or return needs_revision with the presentation changes required?

**Recommended:** `approve` — The analysis-only validation recomputes every census input behind the figure and passes with mutation coverage; the remaining judgment is presentation only, and the nine-panel layout follows the fail-closed rule for the three sightlines without an established host redshift.

**Choose:**

- `approve` — Approve the installed bytes and record the exact-hash decision.
- `needs-revision` — Return needs_revision, naming the presentation changes required.

**Context:**

- Nine of twelve sightlines are drawn; three are omitted because no established host redshift exists, and each omission is checked against the data rather than trusted.
- The candidate is byte-identical to the installed figures/sightline_halo_grid.pdf and to the owner-review.json review binding (SHA-256 281e4bf4…).
- Correctness is established by six recomputing checks with mutation tests; this call judges only whether the figure reads well for the paper.

**Evidence:**

- [Candidate bytes (installed Figure 3)](figure_review/artifacts/batches/2026-07-31-fig3-installed-approval/candidates/fig3-halo-grid.pdf) — `281e4bf4…`
- [Analysis-only validation receipt](docs/rse/specs/receipt-foreground-census-analysis-only-2026-07-29.md) — `c13404f8…`
- [Owner-review byte binding](docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/owner-review.json) — `32887fda…`

**Effect:** Closes the last owner call on the Figure 3 independent-validation-gate ticket and unblocks exact-byte promotion of the installed figure.

**Record:** `figure_review/artifacts/batches/2026-07-31-fig3-installed-approval/manifest.json` — python3 scripts/figure_review.py decide 2026-07-31-fig3-installed-approval fig3-halo-grid approved|needs_revision --reviewer <owner> --note <note>

## 2. WHL J115048.0+714428 identity

**Decision:** How should WHL J115048.0+714428 be treated while its relationship to J115120.4+714435 and its model-compatible mass and radius remain unresolved?

**Recommended:** `exclude-pending-source` — Preserve the confirmed catalog entry but exclude it from the quantitative budget until primary-source identity, M500, R500, and crossmatch evidence are adjudicated.

**Choose:**

- `distinct-halo` — Treat as a distinct halo after source evidence establishes a separate system and supplies model-compatible M500 and R500.
- `duplicate-fragment` — Treat as a catalog duplicate or fragment of J115120.4+714435 after primary-source crossmatch adjudication.
- `exclude-pending-source` — Preserve the entry but exclude it pending source adjudication; exclude after adjudication if model eligibility is not established.

**Context:**

- WHL12 identifies the entry at photometric redshift 0.1893 with N200=12 and catalog r200=0.92 Mpc; the sightline impact is 614.3 kpc.
- The budgeted Wen--Han entry is at spectroscopic redshift 0.2000 with adopted M500=1.48e14 Msun and R500=0.729 Mpc.
- No primary-source evidence in the current packet establishes distinctness or duplication, and no model-compatible M500 and R500 are adopted for WHL J115048.0+714428.

**Evidence:**

- [Frozen WHL12 source payload](foregrounds/census/data/candidate_redshift_source_payloads_2026-07-22.json) — `81484524…`
- [Frozen census registry](foregrounds/census/data/intervening_census_registry.csv) — `96bfd323…`
- [Census-gap source assessment](docs/rse/specs/research-v4-census-gap-extension.md) — `83f2a559…`

**Effect:** Records whether the entry remains excluded, is reconciled as a duplicate, or proceeds as a distinct halo requiring a new reviewed column; it does not admit a cluster budget.

**Record:** `docs/rse/wayfinder/tickets/owner-decision-whl-j115048-identity.md` — Record the owner or source-expert choice and cite the adjudicating source receipt; do not change the budget until the stated evidence exists.

## 3. TNG calibration authority

**Decision:** What evidence must govern the IllustrisTNG intergalactic dispersion calibration used by the host-dispersion calculation?

**Recommended:** `published-binary` — Accept the immutable first-party artifact only as a fixed calibration input, while preserving explicit limits: its fit was not reproduced and no host-dispersion result is admitted without separate local and intervening receipts.

**Choose:**

- `published-binary` — Accept Connor repository revision c8ca7cccc22828270291b039963a316b5e35d04f and src/tng_params_new.npy SHA-256 e4e1aa68ae4367bb698df5ca1cc93d9eaaeba23f73bef2435f4aee0ef5674625 as the calibration authority. This permits a reviewed receipt to bind the fixed grid and a diagnostic rerun. It forbids claiming that the TNG fit was reproduced, that its producing environment is known, or that any host-dispersion result is admitted.
- `original-fit` — Require the original TNG fit inputs, producer command or code revision, and producing environment before accepting the calibration. Until those exist and reproduce the binary within an owner-defined tolerance, this forbids using the grid as an admitted calibration or rerunning it for an admissible result.
- `replace` — Reject this calibration and select a replacement. This forbids using the Connor binary beyond historical comparison; a replacement requires its own immutable source, fit inputs, producer, environment, scientific validation, and downstream rerun receipt.

**Context:**

- At immutable first-party revision c8ca7cccc22828270291b039963a316b5e35d04f, src/tng_params_new.npy has SHA-256 e4e1aa68ae4367bb698df5ca1cc93d9eaaeba23f73bef2435f4aee0ef5674625; all 12 redshifts match local ordering, mean and scatter columns agree within 5e-9, and the f_IGM baseline 0.797 matches.
- The first-party repository does not identify the original inputs, command, or producing environment for tng_params_new.npy; proc_TNG.py writes a differently named artifact. The semantic match therefore establishes transcription, not reproduction of the fit.
- The local host_dm_receipt.json remains fail_closed and independently requires an admitted calibration receipt, a rerun bound to producer and environment, cluster/intervening closure for FRB 20230307A, and owner admission review.

**Evidence:**

- [First-party Connor reproduction repository at the inspected immutable revision](https://github.com/liamconnor/frb_baryon_connor2024/tree/c8ca7cccc22828270291b039963a316b5e35d04f/src)
- [Remaining-science research note](docs/rse/specs/research/research-remaining-science-questions-2026-07-31.md) — `06154034…`
- [Current fail-closed host-dispersion receipt](foregrounds/results/propagation/host_dm_receipt.json) — `ea279131…`

**Effect:** The choice determines whether the immutable published binary may serve as a fixed calibration input, whether full fit-production provenance is mandatory, or whether the calibration must be replaced. No choice alone admits a host-dispersion result.

**Record:** `docs/rse/wayfinder/tickets/owner-decision-tng-calibration-authority.md` — Record the owner choice, its permitted claim boundary, and any required follow-up receipts; then resolve this ticket without changing scientific trust.

## 4. Choose energetics comparison and roster

**Decision:** What scientific comparison, if any, should the band-energy analysis test, and what exact event roster is required before execution?

**Recommended:** `methods-only` — No accepted event-band receipt exists, so keeping the section method-only avoids inventing a population question or minimum roster before the owner defines one.

**Choose:**

- `complete-paired-roster` — Compare paired CHIME/FRB and DSA-110 band energies for every redshift-eligible event; require every paired event-band receipt.
- `predeclared-subset` — Use an owner-named comparison and exact named subset; record the minimum event count and exclusions before any calibration work.
- `methods-only` — Run no population comparison; retain only the measurement method until a later owner decision.

**Context:**

- The candidate table has 24 event-band rows, seven failed window gates, and no accepted row.
- The builder fails closed unless window, calibration, correlated-noise, and owner-review gates pass.
- No current authority defines the population comparison or the minimum acceptable roster.

**Evidence:**

- [Fit-independent energetics workflow and admission rules](energetics/studies/burst-energies/README.md) — `79035b11…`
- [Remaining-science evidence probe](docs/rse/specs/research/research-remaining-science-questions-2026-07-31.md) — `06154034…`

**Effect:** Defines whether energetics remains method-only or may begin a predeclared comparison, and fixes the roster gate that measurement receipts must satisfy.

**Record:** `docs/rse/wayfinder/tickets/owner-decision-energetics-comparison-roster.md` — Record the selected comparison; for a population comparison, also record the exact named roster, minimum count, and exclusions. For methods-only, record roster none, minimum count 0, and exclusions not applicable.

## 5. Choose the historical FRB 20230307A cluster model

**Decision:** Which fully specified historical model, if any, should govern the FRB 20230307A intervening-dispersion result?

**Recommended:** `defer` — The arithmetic lineage is known, but no historical state has both the required producer/environment receipt and independent scientific acceptance of its cluster prescription.

**Choose:**

- `ticket-06-model` — Adopt the ticket-06 probabilistic-crossing model. Only 203/255/322 pc cm^-3 may become quotable, and only after its exact producer/environment receipt and scientific review are accepted.
- `corrected-historical-model` — Adopt the later equal-weight modified-NFW/beta mixture, revised beta calculation, and c200=4 NFW M500c-to-M200c conversion together. Only 217/281/354 pc cm^-3 may become quotable, and only after its exact producer/environment receipt and scientific review are accepted.
- `defer` — Quote no historical cluster-budget result pending source-expert review and complete receipts.

**Context:**

- Ticket 06 records 203/255/322 pc cm^-3 at commit be2131b76771d6291dfd18784eaa1c3f08636272.
- The later profile-mixture and beta revision, before the mass-conversion correction, yields 202/260/329 pc cm^-3; this is a version-lineage checkpoint, not an accepted result and is not quotable under any offered choice.
- Commit c8ec78ceeeb37505b5343aeb0ad0a51671658640 changes the cluster point from 183.674227906529 to 224.719617368599 pc cm^-3 under a c200=4 NFW M500c-to-M200c conversion; 9890aa8 restores the producing artifacts without changing the resulting 217/281/354 row.

**Evidence:**

- [Resolved probabilistic-crossing ticket](docs/rse/wayfinder/tickets/06-adjudicate-phineas-halo-mass-prescriptions.md) — `fc077afb…`
- [Historical 217/281/354 output at 9890aa8](https://github.com/jakobtfaber/Faber2026-analysis/blob/9890aa8cc299fc2696348327a1c2efe14c80fdbe/scripts/dm_budget_uncertainty.csv)
- [Evidence probe and version reconciliation](docs/rse/specs/research/research-remaining-science-questions-2026-07-31.md) — `06154034…`

**Effect:** Selects a model state for later receipt construction and scientific review; the decision alone admits no number.

**Record:** `docs/rse/wayfinder/tickets/owner-decision-historical-cluster-model.md` — Record the chosen model, source-expert rationale, accepted profile mixture, beta revision, mass-conversion prescription, and receipt identity; resolve only when every admission blocker is discharged.
