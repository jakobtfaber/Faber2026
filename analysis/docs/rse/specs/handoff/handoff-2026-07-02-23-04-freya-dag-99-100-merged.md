# Handoff: freya β co-model DAG — #99/#100 implemented, merged; #101/#102 ready-for-agent

---
**Date:** 2026-07-02 23:04
**Author:** AI Assistant
**Status:** Handoff
**Branch:** main (Faber2026, clean, pushed at `7d7419a`)
**Commit:** `7d7419a` (Faber2026) · `pipeline/` still pinned at `6ce3e58` (deliberate) · upstream dsa110-FLITS main at `424d724c`

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Resume prior handoff; commit spec docs to Faber2026 main | ✅ Complete | `d9cc36f` (PRD, research doc, prior handoff) — Overleaf pulls from main |
| Implement #99 (freya local-runs configs + band-prep smoke) | ✅ Complete | PR #107, **merged** as `00a66262`; Codex review APPROVE, zero findings |
| Implement #100 (posterior comparator) | ✅ Complete | PR #108, **merged** as `424d724c`; adversarial-review findings fixed pre-merge |
| Epistemic remediation sweep (maintainer directive) | ✅ Complete | "freya is the α>4 sightline" → "deprecated exp-era fit *suggested* α>4" across PR #107 body, PRD, prior handoff, implement doc, issue #104 body; guardrail persisted to memory (see Learnings) |
| Re-triage #101/#102 → `ready-for-agent` with agent briefs | ✅ Complete | Briefs posted 2026-07-03 (post-merge); epistemically phrased |
| Implement #101 (tail-coverage preflight) | 📋 Planned | Unblocked; brief on the issue |
| Implement #102 (Route A / POC completion) | 📋 Planned | Unblocked; brief on the issue |

**Current Workflow Phase:** Implement (DAG slice-by-slice, via the tracker)

## Workflow Artifacts

**Research Documents:**
- [research-pipeline-2d-fit-scattering-index.md](../research/research-pipeline-2d-fit-scattering-index.md) — pipeline 2D-fit survey (anchors valid at pin `6ce3e58`)

**Plan Documents:**
- [prd-freya-beta-comodel-real-data-fit.md](../prd/prd-freya-beta-comodel-real-data-fit.md) — the PRD; **the tracker issues #101–#106 + their agent briefs are the plan** (no `plan-*.md`)

**Implementation Summaries:**
- [implement-freya-local-runs-configs.md](../implement/implement-freya-local-runs-configs.md) — #99: configs, smoke test, verification (env-scoped), deviations
- [implement-posterior-comparator.md](../implement/implement-posterior-comparator.md) — #100: comparator module, adversarial-review findings + fixes, caveats for #105/#106

**Prior handoff:** [handoff-2026-07-02-20-06-freya-beta-fit-issues-triage.md](../handoff/handoff-2026-07-02-20-06-freya-beta-fit-issues-triage.md)

## Critical References

- Tracker: https://github.com/jakobtfaber/dsa110-FLITS/issues — open DAG is exactly #101–#106; **#101 and #102 carry authoritative Agent Brief comments** (the contract). Read the target issue's brief first.
- `docs/rse/specs/prd/prd-freya-beta-comodel-real-data-fit.md` — scope + implementation/testing decisions (epistemically corrected 2026-07-02).
- `pipeline/CLAUDE.md` — binding: worktree-per-agent, protected-branch guard, Stop-gates, entire-ledger closeout, autoformatter import-strip trap, ponytail style.

## Recent Changes

All upstream code changes are merged; no open branches. On dsa110-FLITS main:
- `analysis/scattering-refit-2026-06/local_runs/configs/freya_{chime,dsa}_run.yaml` — new (#99): pinned-checkout data paths, DSA `dm_init: 912.4` (catalog), CHIME `0.0`; `alpha_fixed` omitted (unconstrained-β rationale).
- `tests/test_freya_local_runs_smoke.py` — new (#99): slow-marked, drives the joint driver's `prepare()` on real freya `.npy`s.
- `analysis/scattering-refit-2026-06/posterior_compare.py` + `test_posterior_compare.py` — new (#100): pure deterministic comparator; `pyproject.toml` testpaths +1.
- Faber2026: implement docs + epistemic corrections (`a84f79e`, `7d7419a`).

## Reproducibility & Data State

- **Environment:** conda env `flits` (Python 3.12). ⚠ editable-installs the **canonical clone** (`~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS/`, now at `424d724c`), not the pinned submodule — run from inside `pipeline/` to exercise pinned code (`module.__file__` when in doubt).
- **Pins:** `pipeline/` at `6ce3e58` (intentional; **pin bump target now ≥ `424d724c`**, only after more DAG code merges — deliberate `build:` commit in Faber2026).
- **Data:** freya real `.npy` via data symlinks in **both** checkouts (`data/{chime,dsa}/freya_*` → `~/Data/Faber2026/dsa110/DSA_bursts/`). The #99 configs point at the **pinned** checkout's symlinks by design.
- **Seeds / partial results:** no fits run; no seeds in play (comparator + smoke test are deterministic). POC artifact `pipeline/analysis/beta_poc/freya/freya_beta_poc_fit.json` remains API-stale synthetic provenance (#102's job).
- **In-flight jobs:** none.

## Verification State / Known-Broken

- **Tests:** #99 smoke 2/2 passed (real data, `flits` env; Codex reproduced independently); #100 comparator 12/12 passed; full collection 484, no import errors — **all env-scoped to `flits` on jakob-mbp**: a clean py312 runner fails collection on missing `ipywidgets` (pre-existing on main, not from these PRs). CI green ≠ real-data coverage: the smoke test skips where the pinned-checkout symlinks are absent.
- **Uncommitted / unpushed:** Faber2026 clean/pushed. Canonical dsa110-FLITS clone (main checkout): `docs/entire-tracing-checkpoints.md` **dirty** — hook-appended after the post-merge pull; expected per that repo's ledger convention ("often dirty even when otherwise clean"). Do not sweep it into a feature commit; it rides along with the next lane's ledger closeout. The protected-branch guard blocks committing it on main directly.
- **Unverified:** nothing claimed beyond the above. Comparator caveats (zero-width degenerate inputs; `params=None` nuisance footgun) documented in `implement-posterior-comparator.md`.

## Learnings

- **Epistemic guardrail (maintainer directive, binding for all further freya/fit work):** classify every science claim as (1) measured under the current model, (2) suggested by deprecated/fraught prior fits, (3) assumed for configuration, (4) hypothesis under test — never collapse into "is". freya's α ≈ 4.36 / τ ≈ 0.119 ms are class (2): the deprecated exp-era fit *suggested* them; their survival is what #104–#106 test. Config choices justified by *not constraining* a parameter, never by old fits. Persisted: dotfiles `memory/feedback_science-claim-epistemic-status.md` (canonical, on dotfiles main) + project memory `science-claim-epistemic-status.md`. **State each claim's class before starting new fit work.** Audit sweeps must cover issue **bodies**, not just comments.
- **Post-#98 MLE init rails β** to the thin-screen floor on both freya bands (CHIME β→2.065, derived α≈63; DSA β→2.495) — init-only, nested sampling is init-independent (absolute prior bounds), but eyes on it at #104. Noted in PR #107 body and #102's brief.
- **Entire-ledger merge conflicts** between parallel lanes are expected (both branches append at the same spot): resolve by **union** (keep both entries chronologically); post-commit hook re-dirties → one `--no-verify` tail commit.
- **Comparator usage (#105/#106):** pass `params=["beta","tau_1ghz"]` / `["alpha"]` explicitly — `params=None` intersects nuisance params (t0, delta_dm) across unrelated fits and returns a meaningless verdict.
- **Repo squash-merges** — branch commit messages don't survive; PR title/body are the permanent record (one stale-wording branch commit, `9328bf8`, was deliberately left unrewritten for this reason).
- Prior session's gotchas still live: whitney configs' canonical-clone paths are the provenance trap (#99 corrected the pattern); autoformatter strips consumer-less imports (add import + consumer in same edit); one agent per worktree; branch before committing (guard blocks main).

## Action Items & Next Steps

1. [ ] Implement **#101** (tail-coverage preflight) from its agent brief — pure module + analytic unit tests startable immediately; real-window application uses the merged #99 configs via the driver's `prepare()`. Own worktree, branch off `424d724c`, PR `Closes #101`.
2. [ ] Implement **#102** (POC β-native migration + real-data branch + dead-code deletion) from its agent brief — independent of #101, parallel-safe in a separate worktree.
3. [ ] As both merge: re-triage **#103** (likelihood equivalence) → `ready-for-agent` with a brief; it consumes Route A (#102) + the #99 configs.
4. [ ] Then #104 (production joint fit — gated on #101 PASS + #103 PASS; hours-long dynesty run, plan for background + monitoring), #105, #106 per the DAG.
5. [ ] Pin bump (deliberate `build:` commit in Faber2026) only after the DAG's code has merged upstream; target ≥ `424d724c`.

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` — treat issue #101's (and/or #102's) agent brief + the PRD's Implementation/Testing Decisions as the approved plan.

## Other Notes

- Triage conventions: `pipeline/docs/agents/triage-labels.md`, `pipeline/docs/agents/issue-tracker.md`; AI-disclaimer line opens all triage comments.
- Review pattern this session (owner-approved): owner delegates PR review to Codex (`codex exec -s read-only -m gpt-5.5 -c 'model_reasoning_effort="high"'`) and/or an adversarial subagent; owner's own review deferred until the fit exists. Merges remain owner-gated — ask before merging.
- Faber2026 pushes to main are outward-facing (Overleaf pulls); the owner pulls via Overleaf UI GitHub Sync.
- Manuscript motion (`tab:beta` row, budget claim, pin bump) stays out of scope until #106's verdict artifact exists; if Route A vs B disagree beyond tolerance at #105 — **stop; that disagreement is the Phase 1 finding.**

---

**Handoff created by AI Assistant on 2026-07-02**
