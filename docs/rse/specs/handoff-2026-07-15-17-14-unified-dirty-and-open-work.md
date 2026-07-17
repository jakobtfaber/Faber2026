# Handoff: unified dirty / un-PR'd / open-work ledger (2026-07-15)

---
**Date:** 2026-07-15 17:14 PDT
**Author:** AI Assistant
**Status:** Handoff — workspace + science ledger; no open PRs; execution not started
**Branch (local checkout):** `docs/dm-host-convolution-handoff-20260715` @ `3c22046d` (**behind** authority)
**Authority tip:** `origin/main` @ `6889effc` (PRs #89–#101 landed today as applicable)
---

## Task(s)

Unify every remaining **uncommitted**, **un-PR'd**, **dirty worktree**, and **open-PR** item into one handoff so the next session does not rediscover lanes, reopen closed merges, or confuse archival dirt with load-bearing science.

| Task | Status | Notes |
|------|--------|-------|
| Inventory open PRs | ✅ Complete | **None** open on `jakobtfaber/Faber2026` |
| Inventory uncommitted dirt (main checkout) | ✅ Complete | Three untracked docs under `docs/rse/specs/` (plan + two handoffs) |
| Inventory dirty worktrees | ✅ Complete | See ledger below; two detached DM-host repro trees + f3 pipeline drift |
| Inventory un-PR'd unique branches | ✅ Complete | Science `ms/*` / `docs/*` of interest are merged or cherry-empty vs `origin/main`; leftover `entire/*` session branches exist (ignore) |
| Merge Claude Science fleet carry-forward | ✅ Complete | Blocked science listed; do not speculative-merge |
| Point next session at science gates | ✅ Complete | Use existing unified plan/handoff; do not re-plan from scratch |
| Sync checkout to `origin/main` + durable docs PR | 📋 Planned | Phase 0 before any science |
| Execute G1–G7 science gates | 📋 Planned | See `plan-manuscript-science-gates-2026-07-15.md` |

**Current Workflow Phase:** Plan / closeout inventory. Next execution phase after Phase 0 sync: **Experiment** (α=4 `tau_consistency` refits) via `running-experiments`.

## Dirty / uncommitted / un-PR'd ledger

### Open PRs

**None.** Recent merges on authority tip include (non-exhaustive today): #89 review-prose park, #90 V3 energetics contract, #91 V4 census gap, #93–#101 DM-host / provisional propagation / handoff docs.

### Main checkout — uncommitted (intentional docs)

Path: `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026`  
Branch: `docs/dm-host-convolution-handoff-20260715` @ `3c22046d` (0 unique commits ahead of `origin/main`; **behind** `6889effc`)

| Path | Classification | Action |
|------|----------------|--------|
| `docs/rse/specs/plan-manuscript-science-gates-2026-07-15.md` | Intentional plan (Draft) | Include in optional docs-only PR from fresh `origin/main` branch |
| `docs/rse/specs/handoff-2026-07-15-17-12-manuscript-science-gates.md` | Intentional science-gate handoff | Same docs PR |
| `docs/rse/specs/handoff-2026-07-15-16-44-dm-host-budget-clarify.md` | Archival; method description **superseded** by #98 convolution | Optional archival in same docs PR; do not treat as live method |
| `docs/rse/specs/handoff-2026-07-15-17-14-unified-dirty-and-open-work.md` | This file | Same docs PR |

No manuscript TeX, no science code, no `pipeline/` gitlink changes in this checkout.

### Dirty worktrees (do not sweep into a science commit)

| Worktree | Branch / HEAD | Dirt | Classification |
|----------|---------------|------|----------------|
| `…/Faber2026` (primary) | `docs/dm-host-convolution-handoff-20260715` | Untracked docs above | Intentional — durable-docs PR |
| `…/scratch/…/Faber2026-dm-host-convolution-repro` | detached `6e5049fb` | `M figures/dm_host_posteriors.pdf` (same byte size; binary metadata churn) | Disposable / ignore — not a content delta to promote |
| `…/scratch/…/Faber2026-dm-host-convolution-repro2` | detached `d63aacc4` | same PDF churn | Disposable / ignore |
| `…/scratch/…/Faber2026-f3-consistency-audit` | `state/f3-closeout` | `M pipeline` (submodule checkout drift; points at `pipeline` `main` tip locally) | Hygiene — restore pin; **never** fold into manuscript PR |

### Clean / closed worktrees (merged or empty vs main)

| Worktree | Branch | Note |
|----------|--------|------|
| `/private/tmp/Faber2026-propagation-handoff` | `docs/provisional-propagation-handoff-20260715` | PR #100 MERGED; clean |
| `.worktrees/review-prose-89` | `ms/review-prose-20260715` | PR #89 MERGED; clean |
| `…/Faber2026-alpha4-method-wording` | `ms/alpha4-method-wording` | PR #70 MERGED |
| `…/Faber2026-common-mode-research` | `docs/chime-common-mode-research` | PR #73 MERGED |
| `…/Faber2026-dm-host-convolution` | `ms/dm-host-convolution-20260715` | PR #98 MERGED; behind main |
| `…/Faber2026-p1-window-plan` | `codex/p1-window-upchan-plan` | PR #47 MERGED; remote gone; cherry-empty |
| `…/Faber2026-p3-gate0b-reconcile` | `state/p3-gate0b-reconcile` | cherry-empty vs `origin/main` |
| `…/Faber2026-v4-census-gap` | `ms/v4-census-gap-20260715` | PR #91 MERGED; behind main |

### Branches that looked “un-PR'd” earlier — current status

| Branch | Unique vs `origin/main` | PR | Verdict |
|--------|-------------------------|----|---------|
| `ms/provisional-joint-scint-twoscreen-20260715` | 0 | #95 CLOSED (superseded by reviewed path) | **No open work** — content on main via #97 |
| `ms/provisional-joint-scint-twoscreen-reviewed-20260715` | 0 | #97 MERGED | Closed |
| `docs/dm-host-convolution-handoff-20260715` | 0 | #101 MERGED | Closed as PR; local checkout only behind tip |
| `docs/provisional-propagation-handoff-20260715` | 0 | #100 MERGED | Closed |
| `entire/*` session branches | many cherry `+` | n/a | **Ignore** — agent session leftovers; not manuscript lanes |

Earlier inventory (mid-day) that still showed **uncommitted provisional scint TeX/scripts** on `ms/provisional-…` is **stale**: that work landed via PRs #97/#99 (and follow-through #100). Do not re-commit it.

### Claude Science fleet artifacts (local; not git-tracked science)

- Reports: `.claude-science/fleet-study/reports/A01`–`A06_*_study.md`
- Blocked-science note: `.claude-science/fleet-study/CARRY_FORWARD.md`
- Recovered arts: `.claude-science/artifacts/recovered/` (from daemon after yolo fleet wiped export zips/JSON)
- **Do not** run Codex/`danger-full-access` against export dirs again
- Re-download UI zips/JSON into a **read-only** copy if transcript re-audit needed

## Workflow Artifacts

**This session / durable untracked (commit via docs PR):**

- [plan-manuscript-science-gates-2026-07-15.md](plan-manuscript-science-gates-2026-07-15.md) — unified G0–G8 science plan
- [handoff-2026-07-15-17-12-manuscript-science-gates.md](handoff-2026-07-15-17-12-manuscript-science-gates.md) — science-gate execution handoff
- [handoff-2026-07-15-17-14-unified-dirty-and-open-work.md](handoff-2026-07-15-17-14-unified-dirty-and-open-work.md) — this ledger
- [handoff-2026-07-15-16-44-dm-host-budget-clarify.md](handoff-2026-07-15-16-44-dm-host-budget-clarify.md) — archival clarify (superseded method)

**Already on `origin/main` (do not redo):**

- [handoff-2026-07-15-16-49-dm-host-convolution.md](handoff-2026-07-15-16-49-dm-host-convolution.md) — via PR #101
- [handoff-2026-07-15-16-49-provisional-propagation-next.md](handoff-2026-07-15-16-49-provisional-propagation-next.md) — via PR #100
- [validation-dm-host-convolution.md](validation-dm-host-convolution.md)
- [validation-provisional-joint-scint-twoscreen.md](validation-provisional-joint-scint-twoscreen.md)
- [validation-v3-energetics-2026-07-15.md](validation-v3-energetics-2026-07-15.md)
- [plan-provisional-joint-scint-twoscreen.md](plan-provisional-joint-scint-twoscreen.md) — integration **done**
- [research-provisional-joint-scint-twoscreen.md](research-provisional-joint-scint-twoscreen.md)
- [research-foreground-propagation-alignment.md](research-foreground-propagation-alignment.md)

## Critical References

Read first, in order:

1. `docs/rse/specs/handoff-2026-07-15-17-14-unified-dirty-and-open-work.md` — this ledger (what is dirty vs closed).
2. `docs/rse/specs/plan-manuscript-science-gates-2026-07-15.md` — open gates G1–G7 and fail-closed rules.
3. `docs/rse/specs/handoff-2026-07-15-17-12-manuscript-science-gates.md` — execution checklist after Phase 0 sync.

Then as needed: `pipeline/CONTEXT.md` (α-fixed screen τ policy); `.claude-science/fleet-study/CARRY_FORWARD.md` (CHIME/ToA blocked list).

## Recent Changes

**On `origin/main` (authority — already merged):**

- Provisional joint/DSA manuscript integration + provenance: PRs #97, #99, #100
- Deterministic host-DM convolution + pin: PRs #98, #96, #101; FLITS #188 @ `af78543d`
- DM-host findings 1–7 (attribution/upper limits/rest frame): #93 (method description later superseded by #98)
- V3 energetics contract / review-prose park / V4 census: #90, #89, #91
- Claude Science ignore hygiene: #92

**Local only (this ledger session):**

- Created this unified dirty/open-work handoff
- No science code or TeX edits

## Reproducibility & Data State

- **Authority tip:** `origin/main` @ `6889effc`
- **Pipeline pin (expected on main):** `af78543d` (confirm inside initialized submodule after sync)
- **Host-DM (closed unless inputs change):** `scripts/dm_budget_uncertainty.py`; seeds/controls per convolution handoff (`20260707` cluster RNG; oracle `20260715 + sightline_index`)
- **Joint-fit root:** `${FLITS_RUNS:-/central/scratch/jfaber/flits-runs}/data/joint`
- **July adjudication:** `pipeline/analysis/scattering-dm-locked-2026-07-14/`
- **In-flight jobs:** none known from this inventory
- **Partial α=4 refits:** none launched from the science-gates plan

## Verification State / Known-Broken

> **Known-broken / unverified**
>
> - This ledger session ran **no** science tests.
> - G1–G7 remain open; fail-closed pending screen / energy language is intentional.
> - Primary checkout is **behind** `origin/main`; untracked docs are not on remote.
> - Detached DM-host repro worktrees show PDF “modifications” with **unchanged size** — treat as noise, not a figure update.
> - `state/f3-closeout` worktree has drifted `pipeline` checkout — restore, do not bump pin casually.
> - Claude Science export zips/JSON under `./.claude-science/` were wiped earlier by a yolo fleet; recovered from `~/.claude-science` daemon store only.

- **Tests (this session):** not run.
- **Open PRs:** none.
- **Uncommitted / unpushed:** four `docs/rse/specs/*` files listed above (after this handoff exists).
- **Unverified science:** all G1–G7 products; fleet-blocked ToA switch / dual-band CHIME+DSA alpha / CHIME statistical redesign / Mahi–Oran off-pulse gap / joint-fit trust reset.

**Expected xfail (unchanged):**  
`tests/test_association_diagnostics.py::test_committed_report_has_eight_dm_filtered_and_four_position_time_rows`

## Learnings

- Mid-day “uncommitted provisional scint” inventory went stale after #97/#99/#100; always re-check `git cherry` vs `origin/main` before opening a PR.
- Several worktrees exist under `~/Developer/scratch/worktrees/` and `.worktrees/`; inventory read-only; never sweep concurrent dirt into a science commit.
- Never use Codex `danger-full-access` / yolo against Claude Science export directories.
- CHIME scintillation remains `diagnostic_only` on main; do not promote point measurements into alpha/screen claims.
- Screen consistency uses **alpha-fixed** `tau_consistency` only — never free-α joint τ (`pipeline/CONTEXT.md`).
- Pin bumps are their own reviewed step; f3 worktree submodule drift is not a pin bump request.

## Action Items & Next Steps

1. [ ] **Phase 0 — Sync:** checkout/create branch from `origin/main` @ `6889effc` (or newer). Confirm `pipeline/` @ `af78543d`. Leave scratch worktrees alone except optional `git restore` / `git submodule update` hygiene.
2. [ ] **Durable docs PR (optional, docs-only):** commit the four untracked `docs/rse/specs/` files from the primary dirty list; no TeX/science/pin.
3. [ ] **Hygiene (optional):** discard detached PDF churn in dm-host-convolution-repro{,2}; restore `pipeline` pin in `Faber2026-f3-consistency-audit`; prune stale worktrees only with full staleness proof.
4. [ ] **Execute science gates G1→G3** per `plan-manuscript-science-gates-2026-07-15.md` (runner parity → α=4 refits → certify DSA widths → catalog/tables). Preserve fail-closed pending language until cleared per row.
5. [ ] **Parallel OK — G5:** V3 CHIME data-driven fluences → independent verify → owner sign-off before ungating energy prose.
6. [ ] **Later — G4/G6/G7:** foreground–propagation re-read only after valid screens; census adjudication; provisional-z provenance or retained flags; regenerate host-DM **only** if authoritative inputs change.
7. [ ] **Do not speculative-merge** fleet-blocked items (ToA model-centroid switch; dual-band CHIME+DSA alpha point-fit; CHIME detection redesign) — see `.claude-science/fleet-study/CARRY_FORWARD.md`.

**Recommended Next Skill:** `ai-research-workflows:running-experiments` after Phase 0 sync and G1(a) runner-parity tests; pair with `ai-research-workflows:ensuring-reproducibility` for posterior/log/hash packages; `ai-research-workflows:validating-implementations` before any manuscript status-language upgrades. Docs-only durable publish of this ledger does not need `implementing-plans`.

## Other Notes

Suggested next-session prompt:

> Read `docs/rse/specs/handoff-2026-07-15-17-14-unified-dirty-and-open-work.md`, then `plan-manuscript-science-gates-2026-07-15.md` and `handoff-2026-07-15-17-12-manuscript-science-gates.md`. Work from `origin/main`. Optional: docs-only PR for the untracked specs. Then Phase 0 sync and G1(a) only. Do not reopen closed #97–#101 lanes. Do not touch dirty scratch worktrees except hygiene. Keep CHIME diagnostic-only and fail-closed screen language until G1–G3 clear.

- Standing authorization: push/PR/merge allowed with care; never force-push shared history; never delete `overleaf-*` branches.
- `lane-liveness` may report `live` on the primary checkout — proceed around contested paths; prefer a fresh branch from `origin/main` for execution.

---

**Handoff created by AI Assistant on 2026-07-15.**
