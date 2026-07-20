# Implementation Plan: manuscript science gates after 2026-07-15 merges

---
**Date:** 2026-07-15
**Author:** AI Assistant
**Status:** Executing — Phase 0–1 (G1a) complete; pause before Phase 2
**Authority tip:** `origin/main` @ `6889effc` (PRs #97–#101 landed)
**Related Documents:**
- [Handoff: provisional propagation follow-through](handoff-2026-07-15-16-49-provisional-propagation-next.md) (PR #100)
- [Handoff: DM-host convolution](handoff-2026-07-15-16-49-dm-host-convolution.md) (PR #101)
- [Handoff: DM-host budget clarify (superseded)](handoff-2026-07-15-16-44-dm-host-budget-clarify.md) (local archival; optional durable PR)
- [V3 energetics validation](validation-v3-energetics-2026-07-15.md)
- [Plan: provisional joint/scint/twoscreen](plan-provisional-joint-scint-twoscreen.md) (integration **done**; refits remain)
- [Research: provisional joint/scint/twoscreen](research-provisional-joint-scint-twoscreen.md)
- [Research: foreground–propagation alignment](research-foreground-propagation-alignment.md)

---

## Overview

Four handoff streams and the V3 energetics contract all point at the same
manuscript readiness problem: several lanes are **validated and closed** on
`main`, but the remaining scientific gates are still open. This plan merges
those streams into one ordered task series so the next session does not reopen
closed work or claim two-screen / energy / journal-ready results early.

**Goal:** Clear the next load-bearing science gates in dependency order —
alpha-fixed consistency refits → certified DSA pairings → two-screen products
→ conditional foreground re-read; in parallel, finish V3 CHIME fluences; keep
DM-host closed unless inputs change; only then consider manuscript-wide
circulate/submit language.

**Motivation:** Manuscript integration and provenance for provisional
propagation and deterministic host-DM are complete. What is missing is
policy-compliant science: seven alpha-fixed `tau_consistency` refits, most DSA
component certification, CHIME data-driven energetics, and census/redshift
caveats that still bound submission claims.

## Current State Analysis (merged ledger)

### Closed on `origin/main` — do not redo

| Lane | Evidence | Boundary |
|---|---|---|
| Provisional joint/DSA manuscript integration | PRs #97, #99 | Figures/tables provisional; not V1-certified measurements |
| Deterministic DM-host convolution | PRs #98, #101; FLITS #188; pin `af78543d` | Collaborator-circulable with upper-limit + provisional-z flags; not journal-ready alone |
| DM-host findings 1–7 (f_IGM attribution, upper limits, rest frame) | PRs #93, #96; FLITS #187 | **Superseded as method description** by #98 convolution; conventions retained |
| Redshift roster closure (V3) | `validation-v3-energetics-2026-07-15.md` | No new z acquisition; Wilhelm/Hamilton/Chromatica provisional; Casey photometric → excluded from energy table |

### Open science gates (this plan)

Wording rules for this table: a gate is **open** only if the work is not yet
done; “blocks” means a claim or product that must not be asserted until that
gate clears. Fail-closed pending rows are intentional, not incomplete analysis.

| Gate | What remains undone | Must not be claimed until this gate clears |
|---|---|---|
| **G1** | (a) Show the α-fixed runner selects the accepted July component counts and PBF morphologies for Whitney, Oran, Isha, Phineas, Freya, JohndoeII, and Mahi; (b) run production-quality α=4 `tau_consistency` refits for those seven with full posterior samples, logs, hashes, and environment provenance; (c) validate each refit on the same trust ladder used for the free-α joints | Policy-compliant screen τ values; any screen distance, screen verdict, or medium assignment derived from consistency τ |
| **G2** | Certify each DSA scintillation-bandwidth **component** that would enter a screen calculation (today only Oran / FRB 20220506D at 1328.24 MHz is certified; internally unflagged ≠ certified) | A screen product that consumes an uncertified DSA width |
| **G3** | After G1–G2: write only validated rows into `tau_consistency_catalog.csv`; regenerate the four provisional products and `results.json`; re-run focused and full validation; inspect the rendered manuscript | Changing `PENDING_ALPHA4_CONSISTENCY_REFITS` / pending screen-table language to imply validated screen results for rows that have not cleared G1–G2 |
| **G4** | Re-read the foreground–propagation ledger **conditional on** validated screen results from G1–G3; keep per-sightline plausibility primary | Causal foreground→propagation association; sample-wide correlation without an explicit coverage-censoring model |
| **G5** | V3 E2 remainder: CHIME-side data-driven fluence run, independent verification of that output, regenerated energy-table review, and owner sign-off (DSA data-driven path already done; redshift roster already closed) | Ungating the source-commented Results/Discussion energy prose; treating V3 as scientifically cleared |
| **G6** | Finish foreground-census extension/adjudication still open on current main—especially FRB 20230307A WHL12 vs Wen+Han 2024—knowing six host-DM posteriors remain **upper limits** while their census is incomplete. Regenerate host-DM PDFs **only if** an authoritative input hash or census decision changes; the convolution method itself is closed | Two-sided host-DM intervals for census-incomplete sightlines; silent host-product edits without revalidation |
| **G7** | Supply citable public provenance for the three provisional internal host redshifts (FRB 20221203A / Wilhelm, FRB 20230913A / Hamilton, FRB 20240203A / Chromatica), **or** keep the provisional flags everywhere those values appear. This is not a request for new redshift acquisition (roster closed) | Presenting those three redshifts as published measurements |

### Explicit scientific fail-closed rules (load-bearing)

1. Screen consistency uses **alpha-fixed** `tau_consistency` only — never free-α joint τ (`pipeline/CONTEXT.md`).
2. Do **not** resurrect the superseded “six favored” free-α screen pairing.
3. `screen_analysis_status = PENDING_ALPHA4_CONSISTENCY_REFITS` until G1–G3 clear.
4. Host-DM lane stays closed unless an authoritative input hash or census decision changes; then revalidate via `validating-implementations`.
5. Never fold a `pipeline/` gitlink bump into a manuscript-content PR.

**Authoritative paths:**

- Adjudication: `pipeline/analysis/scattering-dm-locked-2026-07-14/results/fit_adjudication.csv`
- Consistency roster: `pipeline/galaxies/foreground/data/tau_consistency_catalog.csv` (all eligible rows still `pending`)
- Runner: `pipeline/galaxies/foreground/run_tau_consistency_refits.py`
- Table generator: `scripts/build_provisional_propagation_tables.py`
- Host-DM engine: `scripts/dm_budget_uncertainty.py`
- V3 CHIME runbook: `docs/rse/specs/validation-v3-energetics-2026-07-15.md` §6
- Ledger: `analysis/provisional_propagation/results.json`

**Seven eligible accepted-physical sightlines (refit roster):** Whitney, Oran, Isha, Phineas, Freya, JohndoeII, Mahi.

## Desired End State

- All seven α=4 refits have full posterior samples, logs, env provenance, and input hashes; catalog rows filled only from validated refits.
- Each screen product pairs a validated consistency τ with a **certified** DSA bandwidth component (Oran 1328.24 MHz already certified; others must climb the same ladder).
- Four provisional tables + `results.json` regenerated; focused + full science suites green; manuscript wording upgrades only where gates actually clear.
- V3 energy table rebuilt from DSA+CHIME data-driven fluences; independent verifier green; owner clearance before ungating Results/Discussion.
- DM-host products unchanged unless G6 inputs change; provisional-z footnotes remain until G7 cites them.
- No causal sample-wide foreground–propagation claim without modeled coverage censoring.

**Success Looks Like:**

- `analysis/provisional_propagation/results.json` no longer `PENDING_ALPHA4_CONSISTENCY_REFITS` for validated rows
- `tau_consistency_catalog.csv` has non-empty validated τ columns for the seven
- V3 contract E2 marked PASS for both DSA and CHIME
- Host CSV/PNG hashes unchanged unless a deliberate census regen is documented

## What We're NOT Doing

- [ ] Re-deriving or “improving” free-α joint fits for the screen track
- [ ] Claiming two-screen distances from pending/invalid refits
- [ ] Certifying the 40 non-Oran DSA components without the certification ladder
- [ ] Reopening DM-host convolution numerics without an input/census change
- [ ] Acquiring new redshifts (roster closed)
- [ ] Promoting Wilhelm/Hamilton/Chromatica z to published without provenance
- [ ] Including Casey in the energy table (photometric z)
- [ ] Manuscript-wide “journal ready” claim from any single gate clearing
- [ ] Sweeping unrelated worktrees / the superseded clarify handoff into science PRs without intent
- [ ] Bumping `pipeline/` as a side effect of parent-only edits

**Rationale:** Closed lanes stay closed; fail-closed products are correct, not incomplete analyses.

## Implementation Approach

**Technical Strategy:** Treat this as three parallel tracks with a hard join
before interpretation:

1. **Track A (Experiment → Validate):** α=4 consistency refits and DSA
   certification → two-screen regeneration.
2. **Track B (Implement → Validate):** V3 CHIME fluences → verifier → table.
3. **Track C (Research/adjudicate, conditional Implement):** census gaps +
   redshift provenance; regenerate host-DM only if inputs change.

**Key Architectural Decisions:**

1. **Decision:** Dual-τ policy remains absolute for screens.
   - **Rationale:** Already adjudicated; free-α τ is morphology/provisional only.
   - **Trade-offs:** Blocks polished screen numbers until G1–G3 complete.
2. **Decision:** DM-host convolution is production; MC is oracle only.
   - **Rationale:** PR #98/#101 closed and reproduced.
3. **Decision:** V3 energies use data-driven band integrals (DSA done; CHIME pending).
   - **Rationale:** Avoids revoked fit products (E2).

**Patterns to Follow:**

- Fail-closed generators (`build_provisional_propagation_tables.py`)
- Clean Conda launcher for host-DM / science Python
- Separate PRs: science content vs `pipeline/` pin
- Preserve “provisional” / “diagnostic” / “pending” wording until the matching gate clears

**Workflow skills by phase:**

| Phase | Skill |
|---|---|
| 0 | (hygiene) |
| 1–2 | `running-experiments` then `ensuring-reproducibility` |
| 3–4 | `validating-implementations` |
| 5 | `implementing-plans` + `validating-implementations` |
| 6–7 | `researching` / owner adjudication; regenerate only if needed |
| closeout | `creating-handoffs` |

## Implementation Phases

### Phase 0: Sync and hygiene

**Objective:** Work from `origin/main` @ `6889effc+`; preserve separate lanes.

**Tasks:**

- [x] Confirm tip: `git fetch origin && git rev-parse origin/main` → expect `6889effc` ancestry including #100/#101.
- [x] Start a dedicated branch from `origin/main` (do not build on stale `docs/dm-host-convolution-handoff-*` unless only publishing docs).
- [ ] Classify dirty/untracked: keep
  `handoff-2026-07-15-16-44-dm-host-budget-clarify.md` as **archival**
  (superseded method narrative). Optional later: durable docs PR only.
- [ ] Inventory other worktrees read-only; do not sweep
  `Faber2026-dm-host-convolution*`, `alpha4-method-wording`,
  `common-mode-research`, `review-prose-89`, etc.
- [x] Verify FLITS pin inside initialized `pipeline/`: `af78543d…`.

**Verification:**

- [x] `git status` on the working branch shows only intentional new/edited paths.
- [x] `git -C pipeline rev-parse HEAD` equals pin (from inside initialized submodule).

### Phase 1: Runner parity for the seven July morphologies

**Objective:** Prove `run_tau_consistency_refits.py` selects the accepted July
component counts and PBF morphologies before any production nested sampling.

**Tasks:**

- [x] Read adjudication + runner; map each of Whitney, Oran, Isha, Phineas,
  Freya, JohndoeII, Mahi → exact morphology/component variant paths under
  `pipeline/analysis/scattering-dm-locked-2026-07-14/`.
- [x] **Write failing tests** that assert explicit component count + PBF
  morphology per burst (no ambient defaults).
  - Home: `pipeline/galaxies/foreground/test_tau_consistency.py` (Claude `sonnet[1m]`).
- [x] Run tests → expect FAIL if runner still points at June `_a1_fits` defaults
  (catalog currently references June paths for several rows).
- [x] Patch runner/config so each eligible row’s morphology is an **explicit
  input**; re-run tests → PASS (Codex `gpt-5.6-luna`).
- [x] Dry-run / `--help` / dry selection dump (whatever the runner supports)
  listing the seven planned jobs: nlive, nproc, joint-fit input path, α=4.

**Dependencies:** Phase 0.

**Verification:**

- [x] Focused pytest green for all seven morphology assertions (`36 passed`; 3 pre-existing unrelated failures).
- [x] Selection dump matches July adjudication (not June topology).

### Phase 2: Production α=4 `tau_consistency` refits

**Objective:** Produce full posterior packages for all seven sightlines.

**Tasks:**

- [ ] Confirm joint-fit data root:
  `${FLITS_RUNS:-/central/scratch/jfaber/flits-runs}/data/joint` (or documented
  local mirror) is complete for the seven.
- [ ] Launch production runs with defaults documented in the propagation
  handoff (`nlive=600`, `nproc=8` unless overridden with recorded rationale).
- [ ] For each burst, archive: stdout/stderr logs, environment metadata
  (Python, package versions, host), input SHA-256s, **full posterior samples**
  (not marginal JSON only), and fit summary.
- [ ] Do not edit `tau_consistency_catalog.csv` until Phase 3 validation passes
  per row.

**Dependencies:** Phase 1.

**Verification:**

- [ ] Seven completed run directories with sample files present.
- [ ] Provenance sidecar (or ledger update draft) lists seeds, hashes, env.

**Skill:** `running-experiments` for execution discipline;
`ensuring-reproducibility` for the provenance package.

### Phase 3: Per-refit validation + DSA pairing gate

**Objective:** Apply the same trust ladder as free-α joint fits; refuse bad
rows; certify DSA components used in any screen product.

**Tasks:**

- [ ] Review residuals, PPC, and posterior diagnostics per refit; reject or
  qualify failures.
- [ ] For each row that will enter a screen product, identify the DSA
  bandwidth **component** and run/complete the certification ladder (only Oran
  @ 1328.24 MHz is already certified:
  `γ = 0.446^{+0.239}_{-0.250} MHz`).
- [ ] Write/extend tests: generator still fail-closes if consistency τ missing
  or DSA component uncertified.
- [ ] Populate `tau_consistency_catalog.csv` **only** from validated refits
  (pipeline change → separate pin PR if committed in FLITS).

**Dependencies:** Phase 2.

**Verification:**

- [ ] Invalid rows remain pending/rejected in catalog + ledger.
- [ ] No screen distance emitted for uncertified DSA pairings.

### Phase 4: Regenerate provisional products and manuscript check

**Objective:** Refresh tables/ledger; upgrade wording only where gates clear.

**Tasks:**

- [ ] `python3 scripts/build_provisional_propagation_tables.py`
- [ ] Inspect `analysis/provisional_propagation/results.json` screen status.
- [ ] `make test-science` (expect existing association xfail only unless owner
  re-lands that lane).
- [ ] `python3 scripts/consistency_audit.py`
- [ ] `python3 scripts/figure_review.py verify`
- [ ] Forced LaTeX build; PDF-inspect two-screen and foreground tables.
- [ ] If full posteriors exist: save corner plots; link from adjudication /
  provenance ledger (do not invent covariance from marginal summaries).

**Dependencies:** Phase 3.

**Verification:**

- [ ] Regenerated TeX + JSON committed with hashes recorded.
- [ ] Captions still say provisional/diagnostic wherever certification incomplete.

### Phase 5: V3 energetics — CHIME data-driven completion

**Objective:** Clear V3 E2 for CHIME; prepare owner sign-off package.

**Tasks:**

- [ ] Stage eight CHIME `.npy` under `pipeline/data/chime/` per §6 of
  `validation-v3-energetics-2026-07-15.md` (h17/iacobus paths).
- [ ] Implement `chime_band_fluence_jy_ms_hz(nick)` mirroring DSA; emit
  `chime_fluences.csv`.
- [ ] Independent data-driven verifier (extend or sibling of
  `analysis/v3_energetics/recompute_energies.py` — must not pretend legacy
  audit is the data-driven verifier).
- [ ] Regenerate energy table; review; keep provisional-z footnotes;
  Casey remains excluded.
- [ ] Owner sign-off gate; only then uncomment Results/Discussion energy prose.

**Dependencies:** None on Track A (parallel OK). Join before “manuscript ready.”

**Verification:**

- [ ] V3 contract table: E2 PASS (DSA+CHIME); E1 flags preserved.
- [ ] Focused energetics tests + `make test-science` green.

### Phase 6: Foreground ledger conditional on valid screens

**Objective:** Per-sightline plausibility only; no unjustified population claim.

**Tasks:**

- [ ] Re-join V4 census to validated screen rows (TNS parity).
- [ ] Re-state Phineas / Whitney / Isha / Freya / Casey notes with screen
  distances in hand — still non-causal unless budget + redshift confidence +
  impact parameter support it.
- [ ] Population statistic only if coverage censoring is modeled; otherwise
  withhold.

**Dependencies:** Phase 4 (and Phase 3 DSA certification for any screen-using row).

**Verification:**

- [ ] Updated ledger/table; prose still forbids unsupported causality.

### Phase 7: Census gaps + provisional-z provenance (submission blockers)

**Objective:** Close remaining host-DM / redshift caveats that bound journal
language — without reopening closed convolution numerics unnecessarily.

**Tasks:**

- [ ] Adjudicate FRB 20230307A WHL12 vs Wen+Han 2024 cluster-scale identity/mass
  (`research-v4-census-gap-extension.md` / plan-v4).
- [ ] Advance foreground-census extension for the six upper-limit sightlines.
- [ ] If any authoritative input hash changes: regenerate host-DM with clean
  Conda launcher; re-run MC oracle + `tests/test_dm_budget_uncertainty.py` +
  `scripts/render_budget_table.py --check`; update hashes in docs.
- [ ] Add citable provenance or keep explicit provisional flags for
  FRB 20221203A, 20230913A, 20240203A (align with V3 disposition).

**Dependencies:** Can proceed in parallel with Phases 1–5; regen host-DM only on input change.

**Verification:**

- [ ] Either cited z or retained provisional footnotes everywhere the values appear.
- [ ] Host products hash-stable or deliberately regenerated with validation report.

### Phase 8: Closeout handoff

**Objective:** Single durable handoff superseding the four source handoffs for
“what’s next.”

**Tasks:**

- [ ] Write `docs/rse/specs/handoff-YYYY-MM-DD-HH-MM-manuscript-science-gates.md`
  via `creating-handoffs`.
- [ ] Optional: durable PR for superseded
  `handoff-2026-07-15-16-44-dm-host-budget-clarify.md` (docs-only; no science churn).
- [ ] `agent-closeout-check` on touched repos; separate pin PR if FLITS moved.

**Dependencies:** Whatever phases were executed this session.

## Success Criteria

### Automated Verification

- [x] Phase 1 morphology tests pass for all seven bursts
- [ ] `python3 scripts/build_provisional_propagation_tables.py` exits 0 after catalog update
- [ ] `make test-science` — only the documented association xfail unless re-landed
- [ ] `python3 scripts/consistency_audit.py` clean
- [ ] `python3 scripts/figure_review.py verify` passes
- [ ] V3 data-driven verifier passes on DSA+CHIME products
- [ ] If host inputs changed: `pytest tests/test_dm_budget_uncertainty.py` + table `--check`

### Manual Verification

- [ ] Residual/PPC review recorded per α=4 refit
- [ ] DSA certification evidence per screen-used component
- [ ] PDF table/figure inspection after regeneration
- [ ] Owner V3 sign-off before ungating energy Results/Discussion
- [ ] No causal sample-wide foreground claim without censoring model

### Reproducibility & Correctness

- [ ] Seeds, data versions, env, commands captured per
  `ensuring-reproducibility` for every production refit and fluence run
- [ ] Numerical criteria: morphology parity tests; host MC-oracle tolerances if regen
- [ ] Clean-worktree or clean-env reproduction for regenerated products

## Testing Strategy

**Unit / focused (in-phase):** runner morphology selection; fail-closed screen
generator; CHIME fluence schema parity with DSA.

**Integration:** full `make test-science`; provisional propagation tests;
DM-host suite only if regenerating.

**Manual:** posterior diagnostics; PDF inspection; owner clearance.

**Test Data:** July DM-locked joint outputs; DSA ACF components; CHIME `.npy` +
`chime_sefd.csv`; foreground budget JSON / intervening systems CSV.

## Migration Strategy

Not a code migration. Product status migrates pending → validated per row.
Rollback: leave catalog cells pending; generator remains fail-closed.

## Risk Assessment

1. **Risk:** Runner silently uses wrong morphology/topology.
   - **Likelihood:** Medium — catalog still shows June paths.
   - **Impact:** High — invalid screen science.
   - **Mitigation:** Phase 1 explicit tests before any nested sampling.

2. **Risk:** Long-running refits on incomplete `FLITS_RUNS` data.
   - **Likelihood:** Medium.
   - **Impact:** High wasted compute / partial catalog.
   - **Mitigation:** Preflight data presence; per-burst archive; no catalog write until validated.

3. **Risk:** Interpreting foreground objects as causal once screens exist.
   - **Likelihood:** Medium.
   - **Impact:** High scientific overclaim.
   - **Mitigation:** Phase 6 non-causal rules; fail prose review.

4. **Risk:** Reopening DM-host or mixing pin bumps into content PRs.
   - **Likelihood:** Low–Medium with concurrent worktrees.
   - **Impact:** Medium process / review cost.
   - **Mitigation:** Phase 0 hygiene; pin policy.

5. **Risk:** Ungating V3 Results before CHIME+owner clearance.
   - **Likelihood:** Low if checklist followed.
   - **Impact:** High trust-reset regression.
   - **Mitigation:** Source-comment gates stay until E2 PASS + sign-off.

## Edge Cases and Error Handling

- Morphology-only / rejected joint fits: never enter the seven-refit production set.
- Refit fails trust ladder: catalog stays pending/rejected; manuscript keeps pending row.
- DSA component uncertified: screen product withheld even if τ exists.
- Host census input change: full host-DM validation suite, not a silent CSV edit.
- Casey / no-z bursts: remain outside energy table; redshift roster stays closed.

## Performance Considerations

- Nested sampling: `nlive=600`, `nproc=8` baseline; record any deviation.
- Host-DM FFT convolution: already cheap; regen only on input change.
- CHIME fluence: I/O bound on staged `.npy`; keep schema identical to DSA CSV.

## Documentation Updates

- [ ] This plan (approved status bump when execution starts)
- [ ] Update/replace handoff after session work
- [ ] V3 validation status table when E2 clears
- [ ] Propagation validation doc when screens leave pending
- [ ] Host-DM validation hashes only if regenerated
- [ ] Optional durable commit of superseded clarify handoff

## Timeline Estimate

- Phase 0: short
- Phase 1: short–medium (tests + runner fix)
- Phase 2: long (HPC / nested sampling wall-clock)
- Phase 3–4: medium
- Phase 5: medium (data staging + implement + verify)
- Phase 6–7: medium (adjudication-heavy)
- Phase 8: short

## Open Questions

*(None blocking plan approval — owner decisions already recorded.)*

- CHIME `.npy` staging host (h17 vs iacobus): follow V3 §6 paths at execution time.
- Whether to durable-publish the superseded clarify handoff: docs-only preference, not a science gate.

---

## References

**Handoffs combined:**

- `handoff-2026-07-15-16-49-provisional-propagation-next.md` (PR #100, merge `6889effc`)
- `handoff-2026-07-15-16-49-dm-host-convolution.md` (PR #101, merge `dc4c7ce8`)
- `handoff-2026-07-15-16-44-dm-host-budget-clarify.md` (superseded; archival)
- Merge note stream: PRs #97–#99 at `0f96f1d3` then #100/#101

**Validation / research:**

- `validation-v3-energetics-2026-07-15.md`
- `validation-provisional-joint-scint-twoscreen.md`
- `validation-dm-host-convolution.md`
- `research-provisional-joint-scint-twoscreen.md`
- `research-foreground-propagation-alignment.md`
- `research-v4-census-gap-extension.md`

**Files analyzed:**

- `pipeline/galaxies/foreground/run_tau_consistency_refits.py`
- `pipeline/galaxies/foreground/data/tau_consistency_catalog.csv`
- `scripts/build_provisional_propagation_tables.py`
- `scripts/dm_budget_uncertainty.py`
- `analysis/provisional_propagation/results.json`
- `analysis/v3_energetics/recompute_energies.py`

---

## Review History

### Version 1.0 — 2026-07-15

- Combined propagation, DM-host convolution, superseded clarify, and V3
  energetics handoffs into one phased gate plan on `origin/main` @ `6889effc`.
