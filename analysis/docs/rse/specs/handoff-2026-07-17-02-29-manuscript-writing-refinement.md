# Handoff: manuscript writing-quality pass (PR #104) — merged; loose ends inventoried

---
**Date:** 2026-07-17 02:29 PDT
**Author:** AI Assistant
**Status:** Handoff — work merged; follow-ups enumerated
**Branch (primary checkout):** `main` @ `c8e5639b` — **one behind** `origin/main` @ `c081dd27` (PR #104); deliberately NOT pulled, see Verification State
**Work branch:** `ms/writing-refinement-20260717` — merged (squash `c081dd27`), remote + local branch deleted, worktree removed

---

## Task(s)

Owner request: refine the manuscript's scientific writing — descriptions and arguments 100% accurate, compelling, clear — then oversee the GitHub review, implement feedback, merge, and remove the worktree.

| Task | Status | Notes |
|------|--------|-------|
| Full read of all sections + tables against CONTEXT.md gates | ✅ Complete | 13 hand-maintained `.tex` files edited; generated tables read but not touched |
| Confirmed-inaccuracy fixes | ✅ Complete | Cluster column 160→180; host-median span −5..180→−10..+170; garbled f_IGM sentence; barycentric-vs-topocentric contradiction; "tightest" residual mislabel |
| Register/clarity pass (trust-ladder vocab out of rendered prose) | ✅ Complete | best-so-far / V1 re-trust / policy-compliant / registry-authoritative V4 / citable-α / frozen / "July 14" / nickname "Oran" → field-register equivalents; gate semantics preserved verbatim in meaning |
| CI failure fix | ✅ Complete | Abstract rewording had dropped the `all twelve events` sample-count anchor of `scripts/consistency_audit.py` → restored explicit count (`605753cf`) |
| Review cycle (Codex + adversarial subagent) | ✅ Complete | Codex: no issues. Subagent blocker: introduced `$\alpha=4$` literal in conclusions tripped the retired-language audit → reworded to "$\alpha$ fixed to 4" (`34ce339d`) |
| Merge + cleanup | ✅ Complete | Squash-merged as `c081dd27`; branch (remote+local) deleted; worktree removed |
| Generated-table caption register fixes | 📋 Planned | Emitter-side; see Action Items |
| Primary-checkout dirty `toa.tex` lane classification | 🔄 In Progress (blocked on peer) | repowire ask `ask-791f955b` to `Faber2026-2-claude-code` unanswered |

**Current Workflow Phase:** Validate (writing lane closed; follow-ups are small implement tasks)

## Workflow Artifacts

**Previous handoffs consumed (still authoritative for science lanes):**
- [handoff-2026-07-15-17-14-unified-dirty-and-open-work.md](handoff-2026-07-15-17-14-unified-dirty-and-open-work.md) — dirty/open-work ledger (untracked in the primary checkout, along with three sibling specs — see Verification State)
- [plan-manuscript-science-gates-2026-07-15.md](plan-manuscript-science-gates-2026-07-15.md) — G1–G7 science gates, unaffected by this lane
- [handoff-2026-07-15-16-49-dm-host-convolution.md](handoff-2026-07-15-16-49-dm-host-convolution.md) — source of the adopted mNFW ≈184 pc cm⁻³ cluster point used to justify the 160→180 fix

No new research/plan/experiment artifacts; this was a prose lane. PR #104 body carries the full finding-by-finding table with evidence.

## Critical References

- `CONTEXT.md` (repo root) — the trust-reset contract governing what prose may claim; every edit in PR #104 was made against it. Read before ANY further manuscript prose work.
- PR #104 (merged) — complete inventory of what changed and why, incl. the "Not touched" list for emitters.
- `scripts/consistency_audit.py` — two traps for prose editors (see Learnings): SAMPLE_COUNT_EXPECTATIONS regex anchors and RETIRED_PATTERNS; run `python3 scripts/consistency_audit.py` standalone after any wording change (CI does NOT run the retired-language sweep).

## Recent Changes

All merged in `c081dd27` (squash of three commits):

- `main.tex` — abstract restructured; cluster column →180; host span →−10..+170; "all twelve events" anchor restored.
- `sections/intro.tex` — closing roadmap rewritten (validation-status framing).
- `sections/observations.tex` — reduction/census register fixes, paragraph splits, US spelling, workflow prose → TeX comment.
- `sections/budget.tex` — eq:dmbudget punctuation, missing verb, f_IGM digression deduped (defers to Appendix), "buys"→"adds".
- `sections/toa.tex` — "chance-maximizing" first-use cleanup, "largest normalized residual is 2.6σ", dangling clause fix. Hunks at ~l.94/l.180/l.195 only.
- `sections/results.tex` — garbled f_IGM sentence repaired, 160→180, nickname removal, C$m$D$n$ glossed, provisional register.
- `sections/discussion.tex` — two-screen/census paragraphs rewritten in field register (fixed-index τ-refit semantics preserved exactly).
- `sections/conclusions.tex` — 160→180, −10..+170, two-screen sentence de-jargoned, then re-fixed to "$\alpha$ fixed to 4" after audit catch.
- `sections/appendix.tex` — barycentric→topocentric convention fix, register cleanup, "old residual" changelog language reframed.
- `sections/{codetection_triptychs,jointmodel_pairs,dsa_scint_acf}.tex`, `sections/twoscreen_formalism.tex` — caption register, nickname, spelling.

## Verification State / Known-Broken

- **Tests:** all four PR checks green on `34ce339d`; local `uv run --project pipeline --frozen python -m pytest tests` = **97 passed, 1 xfailed** (the expected `test_association_diagnostics` xfail); `python3 scripts/consistency_audit.py` exits clean; `latexmk -pdf` clean, no undefined refs.
- **Primary checkout is one commit behind `origin/main` and was deliberately not pulled:** it holds a live, separate-lane dirty tree — `sections/toa.tex` (uncommitted model-TOA/scattering-shift subsection, mtime Jul 15 22:28, no journal entry, listed "fleet-blocked ToA model-centroid switch" in the 07-15 ledger) and `docs/rse/journal.jsonl` (journal appends). A `git pull` would abort on the dirty `toa.tex`. The landed PR-#104 `toa.tex` hunks do not overlap the dirty lane's region, so an eventual rebase/merge is clean.
- **Untracked docs in primary checkout (unchanged from the 07-15 ledger):** four `docs/rse/specs/` files (two handoffs, two plans) plus `plan-chime-window-tuning-2026-07-17.md`; the optional docs-only PR from the ledger was never opened. This handoff file adds a fifth.
- **Unanswered peer query:** repowire `ask-791f955b` to `Faber2026-2-claude-code` (does it own the dirty `toa.tex`?) — still open.
- **Unverified:** nothing in this lane. Science-gate lanes (G1–G7, CHIME window-tuning campaign) untouched and carry their own status.

## Learnings

- **`scripts/consistency_audit.py` is a prose contract.** (a) `SAMPLE_COUNT_EXPECTATIONS` pins regexes to exact sentences ("Here we analyze twelve FRBs…co-detected", "all twelve events", "All twelve residuals", "(24 spectra in total", "twelve-burst sample"…) — rewording any of them breaks `root-science-tests` CI. (b) `RETIRED_PATTERNS` flags `alpha=4` literals, rail-class vocabulary etc., but CI does **not** run that sweep (pytest only exercises sample-counts/figures/provenance) — run the script standalone before pushing prose.
- **"of order 160" vs adopted 184:** the β-model Monte-Carlo bracket is p16/p50/p84 = 159/254/384 (95%: 96–563); someone had quoted the p16 as the mNFW headline. Authoritative source: `handoff-2026-07-15-16-49-dm-host-convolution.md` + the `fig:clusters_icm` caption. Any future rewrite of cluster-column prose should cite ≈180 (mNFW point 184) with the 100–560 bracket.
- **Generated files:** `budget_table.tex`, `foreground_table.tex`, `sample_table.tex`, `dm_measurements_table.tex`, `*_provisional_table.tex` are emitter-owned (`render_budget_table.py`, `build_provisional_propagation_tables.py`, FLITS emitters) — never hand-edit; caption register fixes go in the emitters.
- **Nicknames leak:** the audit doc `language_audit.md` claimed no nickname leaks; stale — "Oran" was in rendered prose/captions. `language_audit.md` predates recent PRs; treat it as historical, not current.
- **Review flow that worked:** trigger Codex with a `@codex review` PR comment (bot also auto-reviews some PRs); pair it with an in-session adversarial subagent given the CONTEXT.md gate contract — the subagent caught the retired-language regression Codex and CI both missed.

## Action Items & Next Steps

1. [ ] **Emitter caption register pass** (small): in FLITS/scripts emitters — tab:joint-fit-provisional title/comments "Best-so-far" → "Provisional"; χ² sig-fig normalization; consider glossing the railed `4.00^{+0.00}_{-0.00}` α row; optional "no citable published provenance" note-r wording (mirrors `sections/appendix.tex:220` — change both or neither). Regenerate tables, never hand-edit.
2. [ ] **Close the `toa.tex` lane**: get the peer's answer on `ask-791f955b` (or owner adjudication). If orphaned: the content (model-TOA switch) was fleet-blocked in the 07-15 ledger — either charter it properly as a lane with predeclared gates or stash/park it. Do not commit it as-is; do not discard.
3. [ ] **Primary checkout sync**: once the `toa.tex` lane is resolved, `git pull --ff-only` in the primary checkout (currently clean-blocked by the dirty file).
4. [ ] **Optional docs-only PR** for the five untracked `docs/rse/specs/` files (four from the 07-15 ledger + this handoff), per the standing ledger recommendation.
5. [ ] Science gates G1–G7 and the CHIME window-tuning campaign proceed independently (see their own plans/handoffs) — nothing in this lane blocks them.

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` for item 1 (emitter tweaks); items 2–4 are coordination/hygiene, no skill needed.

## Other Notes

- Standing authorization (repo CLAUDE.md) covers branch push / PR / merge without per-action approval; squash-merge is the repo precedent; never delete `overleaf-*` branches.
- Abstract still carries the four gated `% [SLOT: …]` placeholders (scattering results, scintillation attribution, energies, closing claim) — they fill only when the corresponding §V ladders clear; the writing pass deliberately left them.
- Discussion/Results TODO skeletons remain gated on science, not prose — do not "finish the writing" there without the producing analyses clearing their ladders.

---

**Handoff created by AI Assistant on 2026-07-17.**
