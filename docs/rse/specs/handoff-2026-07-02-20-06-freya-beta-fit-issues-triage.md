# Handoff: freya β co-model real-data fit — PRD decomposed into tracker issues, triaged

---
**Date:** 2026-07-02 20:06
**Author:** AI Assistant
**Status:** Handoff
**Branch:** main (Faber2026, clean of tracked changes; two untracked spec docs — see Verification State)
**Commit:** `40e78c0` (Faber2026) · `pipeline/` pinned at `6ce3e58` · upstream dsa110-FLITS main at `43f4c824`

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Scout research: 2D fit + scattering index in dsa110-FLITS | ✅ Complete | `research-pipeline-2d-fit-scattering-index.md` (2026-07-01, anchors against pin `6ce3e58`) |
| PRD: first real-data β co-model joint fit for freya | ✅ Complete | `prd-freya-beta-comodel-real-data-fit.md`, verified against ground truth by the maintainer |
| /to-issues: break PRD into vertical slices | ✅ Complete | 8 issues published to `jakobtfaber/dsa110-FLITS` #99–#106, dependency-ordered |
| /triage: label + brief the batch | ✅ Complete | #99/#100 `ready-for-agent` with agent briefs; #101–#106 `needs-triage` + blocked notes |
| Investigate stale pre-existing issues #4/#5 | ✅ Complete | Both already implemented on main; closed as completed with evidence comments |
| Implement the slices (starting #99, #100) | 📋 Planned | Not started — next session's work |

**Current Workflow Phase:** Plan complete → Implement (slice-by-slice, via the tracker)

## Workflow Artifacts

**Research Documents:**
- `docs/rse/specs/research-pipeline-2d-fit-scattering-index.md` — how the pipeline fits 2D dynamic spectra; β co-model (ADR-0006); joint CHIME+DSA driver; priors/gates inventory; gaps (all `file:line` anchors valid at pin `6ce3e58`)

**Plan Documents:**
- `docs/rse/specs/prd-freya-beta-comodel-real-data-fit.md` — the PRD this work executes. Status line lists the issue mapping. No separate `plan-*.md` exists: **the 8 tracker issues + their agent briefs are the plan.**

## Critical References

- `docs/rse/specs/prd-freya-beta-comodel-real-data-fit.md` — scope, implementation decisions, testing decisions, out-of-scope. Read first.
- Tracker: https://github.com/jakobtfaber/dsa110-FLITS/issues — open issues are exactly #99–#106. #99 and #100 carry authoritative **Agent Brief** comments (the contract for an implementing agent).
- `pipeline/CLAUDE.md` — pinned-submodule non-negotiables, fit-validation contract, ponytail style, Stop-gates, protected-branch guard, worktree-per-agent rule. Binding for all pipeline work.

## Issue DAG (all `enhancement`)

| # | Slice | State | Blocked by |
|---|-------|-------|-----------|
| 99 | freya local-runs configs + band-prep smoke | **ready-for-agent** (brief posted) | — |
| 100 | posterior comparator module | **ready-for-agent** (brief posted) | — |
| 101 | tail-coverage preflight | needs-triage | 99 |
| 102 | Route A completion (β-native POC + real-data branch) | needs-triage | 99 |
| 103 | likelihood equivalence check (A vs B) | needs-triage | 99, 102 |
| 104 | Route B production joint fit + gates | needs-triage | 99, 101, 103 |
| 105 | Route A cross-check + A-vs-B verdict | needs-triage | 100, 102, 104 |
| 106 | verdict artifact + provisional-citable β row candidate | needs-triage | 100, 104, 105 |

Blocked issues stay `needs-triage` by design (tracker vocabulary has no blocked state); promote each to `ready-for-agent` **with an agent brief** as its blockers close (see `/triage` + `docs/agents/triage-labels.md` in the pipeline repo).

## Recent Changes

- Created `docs/rse/specs/prd-freya-beta-comodel-real-data-fit.md` and `docs/rse/specs/research-pipeline-2d-fit-scattering-index.md` (both untracked).
- PRD status line updated to reference issues #99–#106.
- Tracker (`jakobtfaber/dsa110-FLITS`): created labels `needs-triage`, `ready-for-agent`; published #99–#106; posted 2 agent briefs + 6 blocked notes; labeled `bug` and closed #4 (resolved by `75a917ce` force_multi + PR #56 tests) and #5 (resolved by PR #11 per-band `dt_min`) as completed.
- **No code was written or modified anywhere this session.**

## Reproducibility & Data State

- **Environment:** conda env `flits` (Python 3.12). ⚠ It editable-installs the **canonical clone** (`~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS/`), not the pinned submodule — run from inside `pipeline/` to exercise pinned code; print `module.__file__` when in doubt.
- **Pins:** `pipeline/` at `6ce3e58` (detached HEAD intentional). Upstream main at `43f4c824` (#97 ADR-0006 addendum, #98 fixed-α/EMG fixes). Eventual pin bump targets ≥ `43f4c824` (PRD explains why: #98's MLE-init rewrite silently no-ops on the pin).
- **Data:** freya real `.npy` present via the pinned checkout's data symlinks (`pipeline/data/{dsa,chime}` → `~/Data/Faber2026/...`). Configs authored for #99 must point at these, not canonical-clone paths.
- **Seeds / partial results:** none — no fits run yet. POC artifact `pipeline/analysis/beta_poc/freya/freya_beta_poc_fit.json` predates the co-model API (cannot be regenerated on the pin as-is; that is #102's job).
- **In-flight jobs:** none.

## Verification State / Known-Broken

- **Tests:** none run this session (no code changes). Upstream suite last known green at PR #11 era (356 passed, per PR body).
- **Uncommitted / unpushed:** both spec docs (`prd-…`, `research-…`) are **untracked** in Faber2026 — the next session cannot see them from git history until committed. Committing/pushing to Faber2026 `main` is outward-facing (Overleaf pulls it) — gate accordingly.
- **Verified this session:** issue DAG on the tracker cross-checked against the PRD status line (gh queries, recorded via verify-gate); #4/#5 closure evidence read directly from current upstream main code + tests.
- **Unverified:** nothing claimed beyond the above.

## Learnings

- **Pinned POC is API-stale:** `analysis/beta_poc/run_beta_poc.py` constructs `FRBParams(alpha=…)` → TypeError under the co-model; its per-model PBF attribute writes are dead code. #102 = migration + real-data branch + dead-code deletion, developed upstream (branch off ≥ `43f4c824`), never on the pin.
- **Whitney configs are a provenance trap:** `pipeline/analysis/scattering-refit-2026-06/local_runs/whitney_fine_{chime,dsa}_run.yaml` point at canonical-clone data paths. #99 must not copy them verbatim.
- **Only α ≥ 4 is reachable** through the β co-model's thin-screen closure — fine for freya (the roster's only single-component α > 4 sightline). Extended-medium (β > 4) branch is an open `@decision`, out of scope.
- **Tracker hygiene:** issues #4/#5 sat open 10 days after their fixes merged because the PRs lacked closing keywords. When PRs for #99–#106 land, use `Closes #N`.
- **PR #11 leaves a non-blocking science follow-up** (manual N=1 vs N=2 lnZ ladder on a real single-component burst) tracked only in that PR's body — relevant context if multi-component questions resurface.
- **Repo gates that will bite an implementing agent:** pipeline Stop-gates (figure review, deferred tasks), protected-branch commit guard (branch before committing), one-agent-per-worktree rule, and the post-edit autoformatter that strips imports unused at edit time (add import + consumer in the same edit).

## Action Items & Next Steps

1. [ ] Commit the two spec docs (+ this handoff) to Faber2026 — push is outward-facing (Overleaf pulls); gate per repo policy.
2. [ ] Implement **#99** from its agent brief: freya CHIME+DSA run-configs + slow-marked band-prep smoke test. Work in the canonical clone on a feature branch off `43f4c824`; PR with `Closes #99`.
3. [ ] Implement **#100** (posterior comparator) — independent of #99, can run in parallel (separate worktree per the one-agent-per-tree rule).
4. [ ] As #99 merges: re-triage #101/#102 → `ready-for-agent` with agent briefs; continue down the DAG.
5. [ ] Pin bump only after the DAG's code has merged upstream (deliberate `build:` commit in Faber2026; target ≥ `43f4c824`).

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` — treat issue #99's agent brief (plus the PRD's Implementation/Testing Decisions) as the approved plan. If a formal `plan-*.md` is wanted first, use `ai-research-workflows:planning-implementations` scoped to #99 only.

## Other Notes

- Triage vocabulary + tracker conventions: `pipeline/docs/agents/triage-labels.md`, `pipeline/docs/agents/issue-tracker.md`. All triage comments must open with the AI-disclaimer line.
- Manuscript motion (`tab:beta` row, budget-section claim, pin bump) is explicitly out of scope until #106's verdict artifact exists (PRD "Out of Scope").
- If Route A and Route B disagree beyond tolerance at #105: **stop — that disagreement is the Phase 1 finding.** No manuscript motion.

---

**Handoff created by AI Assistant on 2026-07-02**
