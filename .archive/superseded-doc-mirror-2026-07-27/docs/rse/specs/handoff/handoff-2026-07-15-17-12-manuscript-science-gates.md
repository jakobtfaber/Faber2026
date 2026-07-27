# Handoff: unified manuscript science gates after 2026-07-15 merges

---
**Date:** 2026-07-15 17:12 PDT
**Author:** AI Assistant
**Status:** Handoff — planning complete; scientific execution not started
**Branch (local checkout):** `docs/dm-host-convolution-handoff-20260715` @ `3c22046d` (**behind** authority)
**Authority tip:** `origin/main` @ `6889effc` (includes PRs #97–#101)
---

## Task(s)

Combine four concurrent handoff streams plus the V3 energetics contract into one
ordered science-gate series, with careful claim boundaries, and leave the next
session ready to execute without reopening closed lanes.

| Task | Status | Notes |
|------|--------|-------|
| Merge source handoffs into one gate inventory | ✅ Complete | Propagation follow-through (#100), DM-host convolution (#101), superseded DM-host clarify (local), V3 energetics, and PR #97–#99 merge notes |
| Draft unified implementation plan | ✅ Complete | `plan-manuscript-science-gates-2026-07-15.md` (Draft; wording of open gates tightened this session) |
| Tighten open-gate wording (no overclaim) | ✅ Complete | Gates G1–G7 rewritten as “what remains undone” vs “must not be claimed until clear” |
| Sync local checkout to `origin/main` | 📋 Planned | Local branch is behind `6889effc`; do this before any science work |
| Execute G1 (runner parity + α=4 refits) | 📋 Planned | First load-bearing science step; nothing executed this session |
| Execute G2–G7 | 📋 Planned | See open gates below; Tracks B/C may run parallel to Track A where noted |

**Current Workflow Phase:** Plan (approved for handoff; execution not started). Next
execution phase for Track A is **Experiment** (`running-experiments` for the
seven α=4 refits), after Phase 0 sync and Phase 1 runner-parity tests.

## Workflow Artifacts

**Plan Documents (this session):**

- [plan-manuscript-science-gates-2026-07-15.md](../plan/plan-manuscript-science-gates-2026-07-15.md) — unified phased plan (G0–G8 / Phases 0–8); **read this after the Critical References**

**Source handoffs (merged into this document; do not restart their closed work):**

- [handoff-2026-07-15-16-49-provisional-propagation-next.md](../handoff/handoff-2026-07-15-16-49-provisional-propagation-next.md) — on `origin/main` via PR #100; manuscript integration done; α=4 refits pending
- [handoff-2026-07-15-16-49-dm-host-convolution.md](../handoff/handoff-2026-07-15-16-49-dm-host-convolution.md) — on `origin/main` via PR #101; convolution lane closed
- [handoff-2026-07-15-16-44-dm-host-budget-clarify.md](../handoff/handoff-2026-07-15-16-44-dm-host-budget-clarify.md) — **untracked locally**; superseded as method description by #98; archival only (optional durable docs PR)

**Validation / research still authoritative:**

- [validation-v3-energetics-2026-07-15.md](../validation/validation-v3-energetics-2026-07-15.md) — V3 contract; E2 CHIME remainder open
- [validation-provisional-joint-scint-twoscreen.md](../validation/validation-provisional-joint-scint-twoscreen.md)
- [validation-dm-host-convolution.md](../validation/validation-dm-host-convolution.md)
- [research-provisional-joint-scint-twoscreen.md](../research/research-provisional-joint-scint-twoscreen.md)
- [research-foreground-propagation-alignment.md](../research/research-foreground-propagation-alignment.md)
- [plan-provisional-joint-scint-twoscreen.md](../plan/plan-provisional-joint-scint-twoscreen.md) — integration **done**; do not re-execute its closed phases

## Critical References

Read these first, in order:

1. `docs/rse/specs/plan/plan-manuscript-science-gates-2026-07-15.md` — unified gates, phases, fail-closed rules, and “what we’re not doing.”
2. `docs/rse/specs/handoff/handoff-2026-07-15-16-49-provisional-propagation-next.md` (from `origin/main` if missing locally) — scientific detail for Track A (refits / DSA / two-screen).
3. `pipeline/CONTEXT.md` — accepted dual-τ policy: screen consistency uses alpha-fixed `tau_consistency`, never free-α joint τ.

Then, as needed by track:

- Track A runner: `pipeline/galaxies/foreground/run_tau_consistency_refits.py`
- July adjudication: `pipeline/analysis/scattering-dm-locked-2026-07-14/results/fit_adjudication.csv`
- Consistency catalog: `pipeline/galaxies/foreground/data/tau_consistency_catalog.csv`
- Table generator: `scripts/build_provisional_propagation_tables.py`
- Host-DM (closed unless inputs change): `scripts/dm_budget_uncertainty.py`
- V3 CHIME runbook: `docs/rse/specs/validation/validation-v3-energetics-2026-07-15.md` §6

## Recent Changes

**On `origin/main` (authority — already merged; do not redo):**

- PR #97 — provisional joint/DSA figures and tables; policy-correct pending two-screen table; foreground ledger
- PR #98 / FLITS #188 — deterministic host-DM convolution; pin `af78543d`
- PR #99 — figure-approval provenance correction
- PR #100 — propagation follow-through handoff (`6889effc`)
- PR #101 — DM-host convolution handoff (`dc4c7ce8`)

**This session (local only; not committed):**

- `docs/rse/specs/plan/plan-manuscript-science-gates-2026-07-15.md` — new unified plan; open-gate table rewritten for claim precision
- No science code, refits, catalog edits, or manuscript TeX changes
- Pre-existing untracked archival: `docs/rse/specs/handoff/handoff-2026-07-15-16-44-dm-host-budget-clarify.md`

## Open science gates (G1–G7)

A gate is **open** only if the work is not yet done. “Must not be claimed”
means a product or assertion that is forbidden until that gate clears.
Fail-closed pending rows are intentional, not failed analysis.

Clearing any subset does **not** make the manuscript journal-ready.

| Gate | What remains undone | Must not be claimed until this gate clears |
|---|---|---|
| **G1** | (a) Show the α-fixed runner selects the accepted July component counts and PBF morphologies for Whitney, Oran, Isha, Phineas, Freya, JohndoeII, and Mahi; (b) run production-quality α=4 `tau_consistency` refits for those seven with full posterior samples, logs, hashes, and environment provenance; (c) validate each refit on the same trust ladder used for the free-α joints | Policy-compliant screen τ; any screen distance, screen verdict, or medium assignment derived from consistency τ |
| **G2** | Certify each DSA scintillation-bandwidth **component** that would enter a screen calculation (today only Oran / FRB 20220506D at 1328.24 MHz is certified; internally unflagged ≠ certified) | A screen product that consumes an uncertified DSA width |
| **G3** | After G1–G2: write only validated rows into `tau_consistency_catalog.csv`; regenerate the four provisional products and `results.json`; re-run focused and full validation; inspect the rendered manuscript | Changing `PENDING_ALPHA4_CONSISTENCY_REFITS` / pending screen-table language to imply validated screen results for rows that have not cleared G1–G2 |
| **G4** | Re-read the foreground–propagation ledger **conditional on** validated screen results from G1–G3; keep per-sightline plausibility primary | Causal foreground→propagation association; sample-wide correlation without an explicit coverage-censoring model |
| **G5** | V3 E2 remainder: CHIME-side data-driven fluence run, independent verification of that output, regenerated energy-table review, and owner sign-off (DSA data-driven path already done; redshift roster already closed) | Ungating the source-commented Results/Discussion energy prose; treating V3 as scientifically cleared |
| **G6** | Finish foreground-census extension/adjudication still open on current main—especially FRB 20230307A WHL12 vs Wen+Han 2024—knowing six host-DM posteriors remain **upper limits** while their census is incomplete. Regenerate host-DM PDFs **only if** an authoritative input hash or census decision changes; the convolution method itself is closed | Two-sided host-DM intervals for census-incomplete sightlines; silent host-product edits without revalidation |
| **G7** | Supply citable public provenance for the three provisional internal host redshifts (FRB 20221203A / Wilhelm, FRB 20230913A / Hamilton, FRB 20240203A / Chromatica), **or** keep the provisional flags everywhere those values appear. Not a request for new redshift acquisition (roster closed) | Presenting those three redshifts as published measurements |

**Fail-closed rules (load-bearing):**

1. Screen consistency uses alpha-fixed `tau_consistency` only — never free-α joint τ.
2. Do not resurrect the superseded “six favored” free-α screen pairing.
3. `screen_analysis_status = PENDING_ALPHA4_CONSISTENCY_REFITS` until G1–G3 clear for the relevant rows.
4. Host-DM convolution stays closed unless an authoritative input hash or census decision changes; then revalidate.
5. Never fold a `pipeline/` gitlink bump into a manuscript-content PR.

**Closed on `origin/main` — do not redo:** provisional joint/DSA manuscript integration (#97, #99); deterministic DM-host convolution (#98, #101; FLITS #188); DM-host findings 1–7 as *method description* (superseded by #98; conventions retained); redshift roster closure (no new z acquisition; Casey photometric → excluded from energy table).

## Reproducibility & Data State

- **Seeds / env (host-DM, if ever regenerated):** cluster RNG `20260707`; oracle `20260715 + sightline_index`; clean Conda launcher in the convolution handoff; pin `pipeline/` @ `af78543d`.
- **Environment (broader science):** frozen pipeline via `uv run --project pipeline --frozen ...` where applicable; parent science tests via `make test-science`.
- **Data / catalogs:** July DM-locked adjudication under `pipeline/analysis/scattering-dm-locked-2026-07-14/`; consistency catalog still pending for eligible rows; joint-fit root `${FLITS_RUNS:-/central/scratch/jfaber/flits-runs}/data/joint`.
- **Partial results:** none from this session. No α=4 production refit launched.
- **In-flight jobs:** none known from this lane.

## Verification State / Known-Broken

> **Known-broken / unverified:** This session produced planning artifacts only.
> No new science tests were run. Prior merged lanes reported green on their own
> PRs; that does not clear G1–G7.

- **Tests (this session):** not run.
- **Prior merged state (do not treat as current session verification):** propagation lane reported `make test-science` 83 passed / 1 expected xfail; DM-host convolution reported focused + full suites green with clean-worktree hash reproduction; V3 contract landing reported green with Results/Discussion still source-gated.
- **Uncommitted / unpushed:**
  - `?? docs/rse/specs/plan/plan-manuscript-science-gates-2026-07-15.md` (this session)
  - `?? docs/rse/specs/handoff/handoff-2026-07-15-16-44-dm-host-budget-clarify.md` (archival; pre-existing)
  - This handoff file (new)
  - Local checkout branch `docs/dm-host-convolution-handoff-20260715` @ `3c22046d` is **behind** `origin/main` @ `6889effc`
- **Unverified / unreproducible:** all G1–G7 scientific products remain pending or fail-closed as documented; do not invent screen distances, energy ungating, or journal-ready claims.

**Documented expected xfail (unchanged owner decision):**  
`tests/test_association_diagnostics.py::test_committed_report_has_eight_dm_filtered_and_four_position_time_rows`

## Learnings

- Several handoffs described closed work; the next session’s job is the **open gates**, not replaying #97–#101.
- The DM-host budget-clarify handoff is **superseded as a method description**, not stale provenance: findings 1–7 explain attribution/upper-limit/rest-frame conventions; live numerics are the convolution engine.
- Catalog rows still referencing June `_a1_fits` paths are a concrete risk that Phase 1 / G1(a) must catch before nested sampling.
- Internally unflagged DSA components are not certified; Oran @ 1328.24 MHz is the only certified screen-eligible DSA width today.
- Wording discipline matters: “pending” fail-closed tables are a successful policy outcome; upgrading language without G1–G3 is an overclaim.
- Concurrent worktrees exist under `~/Developer/scratch/worktrees/` and `.worktrees/`; inventory read-only; do not sweep them into a science commit.
- Local `lane-liveness` can report `live` on this checkout; sync and edit carefully; prefer a fresh branch from `origin/main` for execution.

## Action Items & Next Steps

1. [ ] **Phase 0 — Sync:** create/checkout a branch from `origin/main` @ `6889effc` (or newer). Preserve untracked archival clarify handoff; do not mix unrelated worktree dirt. Confirm `pipeline/` pin `af78543d` from inside an initialized submodule.
2. [ ] **Durable docs (optional, separate PR):** commit this handoff + `plan-manuscript-science-gates-2026-07-15.md` (+ optional archival clarify handoff) as docs-only; no science churn.
3. [ ] **G1(a) — Runner parity:** add/run tests that the α-fixed runner selects July morphologies/component counts for all seven eligible sightlines; fix runner/config if it still defaults to older topologies.
4. [ ] **G1(b)–(c) — Production refits + validation:** run α=4 `tau_consistency` refits with full posteriors, logs, hashes, env provenance; validate each on the joint-fit trust ladder; do not write the catalog until validated.
5. [ ] **G2:** certify any DSA bandwidth component that will enter a screen product (beyond Oran @ 1328.24 MHz).
6. [ ] **G3:** populate catalog from validated rows only; regenerate tables/`results.json`; full validation + PDF inspect; upgrade pending language only for cleared rows.
7. [ ] **G5 (parallel OK):** CHIME data-driven fluences → independent verifier → table review → owner sign-off before ungating energy Results/Discussion.
8. [ ] **G4:** only after valid screens — per-sightline foreground plausibility; no causal/sample-wide claim without coverage-censoring model.
9. [ ] **G6–G7:** census adjudication (esp. FRB 20230307A cluster identity); provisional-z provenance or retained flags; regenerate host-DM only if authoritative inputs change, then revalidate.
10. [ ] **Closeout:** new session handoff via `creating-handoffs` after execution; keep pin bumps in separate PRs.

**Recommended Next Skill:** `ai-research-workflows:running-experiments` for G1 after Phase 0 sync and runner-parity tests; use `ai-research-workflows:ensuring-reproducibility` for the posterior/log/provenance package; use `ai-research-workflows:validating-implementations` before any manuscript status language upgrades. For the optional docs-only durable publish of this plan/handoff, `ai-research-workflows:implementing-plans` is unnecessary — a narrow docs PR suffices.

## Other Notes

- Suggested continuation prompt after sync:

> Read `docs/rse/specs/handoff/handoff-2026-07-15-17-12-manuscript-science-gates.md` and `docs/rse/specs/plan/plan-manuscript-science-gates-2026-07-15.md`. Work from `origin/main`. Execute Phase 0 then G1(a) runner-parity tests before any production α=4 refit. Do not reopen closed DM-host convolution or provisional manuscript-integration lanes. Preserve fail-closed pending screen language until G1–G3 clear per row.

- Never delete `overleaf-*` sync branches.
- Standing repo policy: agents may push/PR with care; never force-push shared history; pin is its own reviewed step.

---

**Handoff created by AI Assistant on 2026-07-15.**
