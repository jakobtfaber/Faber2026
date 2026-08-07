# Handoff: freya β co-model DAG — #101/#102/#111 implemented, merged; #103 ready-for-agent

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Handoff
**Branch:** main (Faber2026)
**Commit:** `pipeline/` still pinned at `6ce3e58` (deliberate) · upstream dsa110-FLITS main at `d0d3592a`

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Implement #101 (tail-coverage preflight) | ✅ Complete | PR #109, **merged** as `d8348f68`; Codex review APPROVE, zero findings |
| Implement #102 (Route A / POC β-native completion) | ✅ Complete | PR #110, **merged** as `37d76a49`; Codex MAJORs pre-existing from #96 → filed as #111 |
| Implement #111 (POC `_validate()` + diagnostics) as its own slice | ✅ Complete | PR #112, **merged** as `d0d3592a`; Codex re-review after Q-Q panel fix |
| Re-triage #103 → `ready-for-agent` with agent brief | ✅ Complete | Brief posted 2026-07-03; epistemically phrased |
| Implement #103 (likelihood equivalence Route A vs B) | 📋 Planned | Unblocked; brief on the issue |

**Current Workflow Phase:** Implement (DAG slice-by-slice, via the tracker)

## Workflow Artifacts

**Plan Documents:**
- [prd-freya-beta-comodel-real-data-fit.md](../notes/prd-freya-beta-comodel-real-data-fit.md) — the PRD; **the tracker issues #103–#106 + their agent briefs are the plan** (no `plan-*.md`)

**Implementation Summaries (this session's slices):**
- [implement-freya-tail-coverage-preflight.md](../implement/implement-freya-tail-coverage-preflight.md) — #101: closed-form tail-coverage math, the two science findings that gate #104
- [implement-poc-beta-native.md](../implement/implement-poc-beta-native.md) — #102: β-native migration, `--real` branch, behavior-preservation evidence
- [implement-poc-validate-diagnostics.md](../implement/implement-poc-validate-diagnostics.md) — #111: `_validate()` delegates to `classify_fit_quality`, 3-panel diagnostics

**Prior handoff:** [handoff-2026-07-02-23-04-freya-dag-99-100-merged.md](../handoff/handoff-2026-07-02-23-04-freya-dag-99-100-merged.md)

## Critical References

- Tracker: https://github.com/jakobtfaber/dsa110-FLITS/issues — open DAG is #103–#106; **#103 carries the authoritative Agent Brief comment** (the contract). Read it first.
- `pipeline/CLAUDE.md` — binding: worktree-per-agent, protected-branch guard, Stop-gates, entire-ledger closeout, autoformatter import-strip trap, ponytail style. Its Level-2 validation prose was corrected in the #111 lane (χ²_red bands live beside `classify_fit_quality` in `burstfit.py`: 0.3/1.5/10.0; `VALIDATION_THRESHOLDS.py`'s `CHI_SQ_RED_MARGINAL_MAX=3.0` superseded for Level 2).

## Recent Changes

All upstream code changes are merged; no open branches or worktrees. On dsa110-FLITS main since `424d724c`:
- `analysis/scattering-refit-2026-06/tail_coverage.py` + `test_tail_coverage.py` + `local_runs/freya_tail_coverage.json` — new (#101).
- `analysis/beta_poc/run_beta_poc.py` — β-native + `--real` (#102), then `_validate()`/diagnostics fix (#111); refreshed `freya/freya_beta_poc_fit.json`; tracked diagnostic PNGs + manifest/review JSONs (#111).
- `CLAUDE.md` — Level-2 validation semantics corrected (#111).
- `pyproject.toml` — one testpaths entry (#101).
- Faber2026: three implement docs + this handoff.

## Reproducibility & Data State

- **Environment:** conda env `flits` (Python 3.12). ⚠ editable-installs the **canonical clone** (`~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS/`, now at `d0d3592a`), not the pinned submodule — run from inside `pipeline/` to exercise pinned code (`module.__file__` when in doubt).
- **Pins:** `pipeline/` at `6ce3e58` (intentional; **pin bump target now ≥ `d0d3592a`**, only after more DAG code merges — deliberate `build:` commit in Faber2026).
- **Data:** freya real `.npy` via data symlinks in both checkouts; the #99 configs point at the **pinned** checkout's symlinks by design.
- **Seeds / partial results:** POC synthetic fit is seed-pinned and was reproduced exactly twice (β = 3.7136, ncall = 181,743) across #102 and #111 — the artifact on main is current-API provenance with PASS verdict + diagnostics. No real fits run yet.
- **In-flight jobs:** none.

## Verification State / Known-Broken

- **Tests:** #101 suite 23/23 (incl. slow real-window run); full collection 510, no import errors — env-scoped to `flits` on jakob-mbp (a clean py312 runner still fails collection on missing `ipywidgets`, pre-existing). The slow/real tests skip where the pinned-checkout data symlinks are absent.
- **Uncommitted / unpushed:** canonical dsa110-FLITS clone's `docs/entire-tracing-checkpoints.md` **dirty on main** — hook-appended after the post-merge pulls; expected per that repo's ledger convention. Entries were union-merged and re-ordered chronologically this session (verified 23:25:22 → … → 00:16:08). Do not sweep into a feature commit; it rides with the next lane.
- **Infra:** ICM memory store failed this session ("database disk image is malformed") — durable facts were written to repo artifacts/docs instead; the ICM DB needs owner attention.

## Learnings

- **Science finding 1 (gates #104): CHIME fails the tail-coverage preflight at all β ≤ 3.7 grid candidates** — at the exp-era-suggested scale (τ=0.119 ms, β=3.7) only 2.08 e-folds / 87.5% of the PBF area fits the prepared window; DSA passes everywhere (≥3.95 e-folds). #104 must either widen the window (`FLITS_ONPULSE_CROP`/`FLITS_ONPULSE_PAD` env knobs, zero code change) or accept a near-exponential-only sensitivity regime. Conditional claim: class (2) epistemic status — *if* τ/β land near the deprecated suggestion.
- **Science finding 2: the post-#98 MLE init refine drags t0** (CHIME 17.6 → 31.4 ms) besides railing β — never inherit refined `init.t0` as a location/prior center; use the raw `data_driven_initial_guess`. Both the preflight and the POC `--real` prior centers now do.
- **Route A vs B structural note for #103:** post-#110, `BetaCoupledLogL` and `_JointLogLikelihoodGainSharedZeta` (burstfit_joint.py:669) take the identical 8-vector θ and call the identical `log_likelihood_gain_marginal` kernel — the equivalence check can demand near-exact agreement, and it verifies wiring, not the kernel. The stale "alpha" θ-docstring at line 672 is assigned to the #103 lane.
- **Scope discipline pays:** Codex's #110 MAJORs were pre-existing (from #96); filing #111 instead of scope-creeping kept the migration PR's behavior-preservation evidence clean, and the owner ordered #111 as its own slice anyway.
- **Diagnostic figures vs `.gitignore`:** `*.png` is repo-ignored; reviewed figures are force-added per the tracked `dsa_figs` precedent, with manifest/review JSON pairs (figure-review Stop gate: Read the PNGs visually before verdicting).
- Prior session's gotchas still live: epistemic guardrail (class every fit claim; never "is"); entire-ledger union merges + `--no-verify` tail commits; squash merges make PR title/body the permanent record; one agent per worktree; branch before committing.

## Action Items & Next Steps

1. [ ] Implement **#103** (likelihood equivalence) from its agent brief — pure comparison module + tests under `analysis/scattering-refit-2026-06/`, real freya application slow-marked; fix the burstfit_joint.py:672 docstring in the same lane. Own worktree, branch off `d0d3592a`, PR `Closes #103`. Merges owner-gated — ask before merging.
2. [ ] Then **#104** (production joint fit) — gated on #103 PASS **and** the #101 preflight at its adopted candidates; must decide the CHIME window question first; hours-long dynesty run (background + monitoring).
3. [ ] Then #105 (Route A cross-check fit; now quality-bearing post-#111), #106 (verdict artifact) per the DAG.
4. [ ] Pin bump (deliberate `build:` commit in Faber2026) once the DAG's code has merged; target ≥ `d0d3592a`.

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` — treat issue #103's agent brief + the PRD's Implementation/Testing Decisions as the approved plan.

## Other Notes

- Review pattern (owner-approved): delegate PR review to Codex (`codex exec -s read-only -m gpt-5.5 -c 'model_reasoning_effort="high"'`); merges owner-gated (this session's three merges were explicitly pre-authorized by the owner's instruction).
- Faber2026 pushes to main are outward-facing (Overleaf pulls via UI GitHub Sync).
- Manuscript motion (`tab:beta` row, budget claim, pin bump) stays out of scope until #106's verdict artifact exists; if Route A vs B disagree beyond tolerance at #105 — **stop; that disagreement is the Phase 1 finding.**

---

**Handoff created by AI Assistant on 2026-07-03**
