# Handoff: provisional joint fits, DSA scintillation, and two-screen follow-through

---
**Date:** 2026-07-15 16:49 PDT

**Author:** AI Assistant

**Status:** Manuscript integration merged; scientific verification and fixed-index refits pending

**Branch:** `main`

**Commit:** `0f96f1d37e25cd349991130e089fb2f4db79c8b0` at handoff creation
---

## Task(s)

Audit the joint scattering fits and DSA scintillation fits, identify the best-so-far figures and
stored values, integrate appropriately qualified figures and tables into the manuscript, implement a
policy-correct two-screen analysis, and compare the resulting propagation constraints with the
foreground halo/cluster census without overstating causality.

| Task | Status | Notes |
|---|---|---|
| Audit joint-fit status, saved figures, and stored values | Complete | Twelve adjudication rows: 7 `accepted_physical`, 3 `morphology_only`, 2 `rejected`; 11 retained fit summaries/PPCs |
| Add best-so-far joint-fit figures and values | Complete | Merged as explicitly provisional diagnostics; not promoted to robustly verified measurements |
| Add DSA bandwidth figures and values | Complete | Forty-one internally unflagged fit components shown provisionally; only Oran at 1328.24 MHz is certified |
| Implement two-screen analysis with accepted dual-tau policy | Diagnosed / pending refits | The generator fail-closes all seven eligible rows until alpha-fixed `tau_consistency` refits exist |
| Compare propagation with foreground halo/cluster census | Complete as descriptive analysis | Twelve-sightline ledger merged; no causal or sample-wide correlation claim is supported |
| Robustly verify scattering/scintillation values | Pending | Full posterior covariance/samples and most component-level DSA certification are absent |

**Current Workflow Phase:** Experiment. The manuscript/provenance integration is validated and
merged, but the next scientific step is to execute and validate the seven fixed-index consistency
refits before any two-screen products are interpreted.

## Workflow Artifacts

- Research: [`research-provisional-joint-scint-twoscreen.md`](research-provisional-joint-scint-twoscreen.md)
- Foreground research: [`research-foreground-propagation-alignment.md`](research-foreground-propagation-alignment.md)
- Implementation plan: [`plan-provisional-joint-scint-twoscreen.md`](plan-provisional-joint-scint-twoscreen.md)
- Validation: [`validation-provisional-joint-scint-twoscreen.md`](validation-provisional-joint-scint-twoscreen.md)
- Closeout inventory: [`closeout-provisional-joint-scint-twoscreen.json`](closeout-provisional-joint-scint-twoscreen.json)
- Machine-readable ledger: [`../../../analysis/provisional_propagation/results.json`](../../../analysis/provisional_propagation/results.json)

## Critical References

Read these first:

- [`../../../pipeline/CONTEXT.md`](../../../pipeline/CONTEXT.md), especially the accepted dual-tau
  policy: screen consistency uses alpha-fixed `tau_consistency`, never the free-alpha joint-fit tau.
- [`../../../pipeline/analysis/scattering-dm-locked-2026-07-14/results/fit_adjudication.csv`](../../../pipeline/analysis/scattering-dm-locked-2026-07-14/results/fit_adjudication.csv)
  for the frozen twelve-row fit adjudication and retained artifact paths.
- [`../../../pipeline/galaxies/foreground/data/tau_consistency_catalog.csv`](../../../pipeline/galaxies/foreground/data/tau_consistency_catalog.csv)
  for the authoritative consistency-refit roster. Every eligible row is currently pending.
- [`../../../pipeline/galaxies/foreground/run_tau_consistency_refits.py`](../../../pipeline/galaxies/foreground/run_tau_consistency_refits.py)
  for the present alpha=4 driver. Verify morphology/component parity before production use.
- [`../../../scripts/build_provisional_propagation_tables.py`](../../../scripts/build_provisional_propagation_tables.py)
  for the fail-closed screen-product logic and reproducible table generation.

## Recent Changes

- PR [#97](https://github.com/jakobtfaber/Faber2026/pull/97), reviewed head
  `a660e442a58d926d7e192190f199d2df4cd6d415`, merged the provisional joint/DSA figures and tables,
  policy-correct pending two-screen table, complete foreground ledger, tests, research notes, and
  validation report. Merge commit: `53f4e402dd2e987b5cb88bf745c25c9972b082e2`.
- Independent review corrected three substantive issues before merge: free-alpha joint tau was
  removed from the two-screen consistency track; 41 DSA values were relabeled as fit components;
  and the Oran aggregate row was prevented from implying certification of every component.
- PR [#99](https://github.com/jakobtfaber/Faber2026/pull/99) reconciled the exact-byte figure approval
  provenance after #97. It was independently reviewed and merged at
  `0f96f1d37e25cd349991130e089fb2f4db79c8b0`.
- The `pipeline/` pin is `af78543d` in the current tree. The approved figure receipts retain their
  original production provenance; #99 makes owner approval and clone-verification status distinct.

## Scientific State and Trust Boundaries

### Joint scattering fits

- The frozen adjudication contains 7 physically accepted fits, 3 morphology-only fits, and 2
  rejected fits. Chromatica is rejected without a retained fit; the other 11 have fit-summary and
  posterior-predictive-check artifacts.
- The retained `fit_summaries/*.json` files store marginal medians and intervals. They are sufficient
  for the provisional table, but they do not preserve full posterior samples or parameter covariance.
- No saved corner plots or posterior-chain/sample files were found for the July DM-locked result
  tree. Generic corner/posterior plotting code exists elsewhere, but it cannot reconstruct missing
  covariance from marginal summaries.
- Therefore the manuscript figures are citable as owner-approved, explicitly provisional diagnostic
  bytes. The numerical fits are not yet robustly certified astrophysical measurements.

### DSA scintillation bandwidths

- Forty-one internally unflagged ACF fit components are available and appear in the provisional
  products.
- Only Oran / FRB 20220506D at 1328.24 MHz is certified:
  `gamma = 0.446^{+0.239}_{-0.250} MHz`.
- Every other DSA width remains diagnostic/provisional until the component-level certification
  ladder is completed.

### Two-screen readiness

- `analysis/provisional_propagation/results.json` records
  `screen_analysis_status = PENDING_ALPHA4_CONSISTENCY_REFITS`.
- All seven eligible accepted-physical sightlines are pending fixed-index refits; there are currently
  no policy-compliant screen products, verdicts, screen distances, or medium assignments.
- Do not resurrect the earlier “six favored” result. It paired DSA bandwidths with the wrong
  free-alpha tau track and was explicitly superseded by the accepted dual-tau policy.

### Foreground alignment

- Phineas / FRB 20230307A intersects confirmed cluster J115120.4+714435 at `b/R500 = 0.83` and has
  three budget-eligible galaxy halos. The foreground budget is about 22% of the provisional joint
  tau, so a partial contribution is plausible but not causal evidence.
- Whitney has a confirmed halo at roughly 101 kpc, but its foreground budget is only about 0.5% of
  the provisional joint tau; a dominant foreground role is disfavored.
- Isha and Freya have close inconclusive candidates at about 16 and 60 kpc; redshift validation is
  required before association claims.
- Casey has a foreground prediction around eleven times its retained morphology-only tau. Treat this
  as a fit-budget tension, not a detection or causal association.
- Coverage censoring, fit availability, and the absent fixed-index screen results prevent a defensible
  sample-wide correlation claim.

## Reproducibility & Data State

- Generated products:
  - `joint_fit_provisional_table.tex`
  - `dsa_scint_provisional_table.tex`
  - `twoscreen_provisional_table.tex`
  - `foreground_propagation_provisional_table.tex`
  - `analysis/provisional_propagation/results.json`
- Rebuild command: `python3 scripts/build_provisional_propagation_tables.py`.
- The generator is standard-library-only and deterministic; input SHA-256 hashes are recorded in the
  result ledger. The broader science suite uses the frozen pipeline environment:
  `uv run --project pipeline --frozen ...`.
- The fixed-index runner defaults to `nlive=600`, `nproc=8`, and expects the full joint-fit output
  under `${FLITS_RUNS:-/central/scratch/jfaber/flits-runs}/data/joint`. No fixed-index refit was run
  in this lane, and no long-running job is currently in flight.
- Before launching production refits, confirm that `run_tau_consistency_refits.py` selects the exact
  accepted July morphology/component variants rather than falling back to an older default topology.
- Manuscript figure approval covers 26 protected bytes: the scintillation summary, Whitney
  triptych, qualified Oran calibration, 12 DSA ACF panels, and 11 retained joint panels. Approval is
  not equivalent to scientific certification.

## Verification State / Known-Broken

- `make test-science`: 83 passed, 1 expected xfail.
- Documented xfail:
  `tests/test_association_diagnostics.py::test_committed_report_has_eight_dm_filtered_and_four_position_time_rows`;
  the rewritten FLITS pin lacks the class-aware association lane, and re-landing it remains an owner
  decision.
- `python3 scripts/consistency_audit.py`: clean.
- `python3 scripts/figure_review.py verify`: passed.
- Clean temporary Python 3.13 venv: generator and five focused tests passed.
- Forced `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex`: passed; the subsequently
  updated current manuscript is 54 pages.
- Manual PDF inspection: screen-readiness and foreground tables were readable without clipping.
- `agent-closeout-check`: passed for the merged propagation lane.
- Known incomplete science: fixed-index consistency refits, posterior/covariance preservation,
  component-level DSA certification, and final two-screen/foreground causal interpretation.
- Before this document's own publication commit, the unrelated untracked
  `handoff-2026-07-15-16-44-dm-host-budget-clarify.md` is present in the shared checkout. It belongs
  to another lane and must not be swept into this handoff commit.

## Learnings

- “Not citable” was not merely “we have not looked at it.” The exact figures have now been reviewed
  and approved for provisional use, but scientific citation strength is limited by missing posterior
  covariance, incomplete DSA certification, and the need for fixed-index consistency refits.
- The free-alpha joint tau is appropriate for the provisional joint-fit morphology table. It is not
  interchangeable with the alpha-fixed consistency tau required by the two-screen calculation.
- A foreground object on a sightline is not, by itself, evidence that it caused the propagation
  signature. Coverage, redshift confidence, impact parameter, scattering budget, and fit trust must
  all be carried together.
- Generated pending rows are a successful fail-closed result, not a failed analysis: they prevent a
  numerically polished but policy-invalid screen inference from entering the manuscript.

## Action Items & Next Steps

1. [ ] Inspect the fixed-index runner against all seven accepted July fit variants; add or update
   tests so each burst's component count and PBF morphology are explicit inputs, not ambient defaults.
2. [ ] Run production alpha=4 `tau_consistency` refits for Whitney, Oran, Isha, Phineas, Freya,
   JohndoeII, and Mahi with preserved logs, environment metadata, input hashes, and full posterior
   samples suitable for corner plots.
3. [ ] Review residuals and posterior diagnostics for every fixed-index refit; reject or qualify rows
   that fail the same trust ladder used for the free-alpha joint fits.
4. [ ] Populate `tau_consistency_catalog.csv` only from validated refits, regenerate the four products,
   rerun the focused and full validation suites, and inspect the rendered manuscript.
5. [ ] Certify the specific DSA bandwidth components used in any screen calculation. Do not derive a
   screen result from a merely internally unflagged component.
6. [ ] Re-evaluate the foreground ledger conditional on valid screen results. Report per-sightline
   plausibility first; attempt a population statistic only if coverage censoring can be modeled.
7. [ ] If robust posterior samples are obtained, save reproducible corner plots and link them from the
   fit adjudication/provenance ledger rather than relying on marginal-summary JSON alone.

**Recommended Next Skill:** `running-experiments` for the seven production fixed-index refits,
followed by `ensuring-reproducibility` for the posterior/log/provenance package and
`validating-implementations` before any manuscript status is upgraded.

## Other Notes

- Never fold a `pipeline/` gitlink bump into a manuscript-content or handoff PR.
- Do not delete or overwrite the unrelated DM-host handoff in the shared checkout.
- The current provisional figures and tables are the best available manuscript artifacts, but their
  caveats are load-bearing. Preserve “provisional,” “diagnostic,” and “pending” wording until the
  corresponding verification step is actually complete.

---

**Handoff created by AI Assistant on 2026-07-15.**
