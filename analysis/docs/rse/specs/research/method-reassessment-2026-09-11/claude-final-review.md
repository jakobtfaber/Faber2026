---
title: "Independent final review — Codex corrections to the scattering method reassessment"
kind: review
comments: none
---

**Verdict: APPROVE for publication as a provisional evidence assessment in a draft pull request, with two should-fix corrections.** Not an approval of scientific validation. Ticket 01 stays open; no production or manuscript change is approved.

- Reviewer: Claude (Opus 5), cross-provider, did not author or shape the reviewed work.
- Reviewed state: repository `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026`, branch `method-reassessment-2026-09-11`, HEAD `237502d455dcdb9f691600b8773d589406962e52`, base `3afb381dcf3e2923b5e087e888a14c957523649f`, plus the uncommitted tracked edits and the untracked evidence root as of the final-state notice (report and figures regenerated 19:34–19:35 PDT, 2026-09-11).
- Repository was not modified during this review. All checks were read-only; no fits were rerun.
- All eight findings from the initial BLOCK are addressed. The block is resolved for provisional draft publication.

## Should-fix before opening the draft pull request

| # | Location | Problem |
| --- | --- | --- |
| 1 | `analysis/docs/rse/specs/research/method-reassessment-2026-09-11/codex-review.md:134` | "This artifact and its review-only check/render outputs are outside the repository. No repository file was edited." That is false for this in-repository copy and for the three files now at `initial-review-evidence/`. The sentence was true of the original Traycer artifact; in the copied receipt it misdescribes the very file a reader is holding. Rewrite to say the original review was conducted outside the repository and that this is a copied receipt whose review-only outputs are reproduced under `initial-review-evidence/`. |
| 2 | `analysis/docs/rse/specs/research/method-reassessment-2026-09-11/decision-memo.md:166`, `:167`, `:168` (and the sentence at `:57`) | Three flip-check cells still read "n/a (posterior far from the switch)" for `thin-b3.67`, `exp-a4.4` and `thin-b3.67-tau0.2`, and line 57 says the posterior-median flips give "+3.7 and -1.4 for the first two". The regenerated `injection-recovery-results.md:93–95` now prints computed steps for all five controls: −4.2, −19.0, −5.7. The memo is internally inconsistent with its own regenerated report. Replace "n/a" with "not diagnostic (posterior far from switch); step −4.2" and so on, and extend line 57 to all five. |

Neither is a numerical error and neither changes a conclusion. Both are consistency defects in the same publication set, so they are cheap to fix and expensive to leave.

## Low priority

`decision-memo.md:143–145`: the arm-c F1 gain-prior sweep table shows scales 0.1, 1 and 100, with no visible scale-10 row. That row exists elsewhere. The scale-10 F1 point is the signal-to-noise 100 entry at `:141` (beta 3.666 / 3.673 / 3.680), and the prose at `:134` says so, but a reader scanning the decade span can easily miss it. A parenthetical pointer in the table would close it.

## Findings from the initial block: disposition

| # | Original finding | Disposition | Evidence checked |
| --- | --- | --- | --- |
| 1 | Mean-delay / composite coverage invalid | Closed | Heavy-tail and composite kernels relabelled; the 4.16 index withdrawn (`decision-memo.md:107–108`); undefined coverage prints as a dash with the reason at `injection-recovery-results.md:6–7`; arm-b truth lines suppressed for non-finite/out-of-range alpha (`make_report.py:~180`). |
| 2 | Kernel-switch discontinuity understated | Closed | Alpha jump 4.020202 → 4 named at `decision-memo.md:38`; differing metrics stated at `injection-recovery-results.md:69`; the 0.04 percent shape-only figure withdrawn (`code-audit.md:21–22`); full forward-model continuity retained as an open hold. |
| 3 | "Never visited" / trapping | Closed | Corrected at `decision-memo.md:60–64` with positive weighted edge mass; independently recomputed from `results/production-path/*.json`: 4.51175600146337e-105 (alpha 3) and 2.7312399084559325e-79 (alpha 4). Trapping now labelled a hypothesis, not a demonstrated mechanism. |
| 4 | Overclaims outside the evidence root | Closed | Verified in all four tracked files: `analysis/CONTEXT.md` (provisional-recommendation block, "no fitted value is promoted"), `analysis/docs/rse/wayfinder/map-apj-submission.md` (two blocks), ticket `method-reassessment-01` decision card (family 3 provisional, charter requirement explicitly not waived, ticket stays open), ticket `…-07-adjudicate-zach-component-count` (parked with the reason). |
| 5 | Headline path not wired | Closed as a specification | `decision-memo.md:189–221` gives the intended entry point, per-band parameterization, priors, nuisance contract and deferred gates; `code-audit.md:45–51` corrects the alpha-flag and `radio_pipeline/fitting/joint_burst.py` claims. This is a contract, not tested code — see gates. |
| 6 | Low-tau truth labels | Closed | 0.15 ms and 0.83 / 1.04 / 1.15 samples at `decision-memo.md:94–95`; figure annotation "square: 0.15 ms (near one sample)"; the 29 = 10/10/9 split stated at `:20`. Independently recomputed: injected tau 0.00015 s, 1.4-GHz sample counts 0.829 / 1.043 / 1.15. |
| 7 | Rerun cannot reproduce the report safely | Closed | `tau_source` provenance in flip records; seeded resampling; `kernel_switch_check.py` added to the documented sequence (`decision-memo.md:253–273`); `--refresh-classifications` path documented. |
| 8 | Audit conflates historical and current | Closed | Seed assertion withdrawn (`code-audit.md:40–41`); `sim_gate.py:42` retired-import noted and any earlier "passed" report marked historical (`:55–58`); both thin controls stated to use the production kernel for injection and fitting, so a truth/model sampling mismatch is explicitly not demonstrated (`:61–63`). |

## Independent numerical checks performed

Read-only, no repository writes, no fits rerun.

- Heavy-tail stress kernel integrates to 1.9999999999999234 with a divergent first moment — consistent with the "integral 2, infinite mean" qualifier.
- All 29 classifications recompute identically from the saved truth metadata in `results/`.
- `injection-recovery-results.md` reproduces byte-identical from the current `results/` tree.
- Weighted edge masses match the memo for all five production controls; all five `mass_above.3.98` and `.3.99` equal-weight values are 0.0, which is why the memo's distinction between weighted and equal-weight mass is load-bearing rather than cosmetic.
- The arm-c signal-to-noise 100 baseline is the matched scale-10 arm-a case (`a-thin-b3.67-tau1e-03-F1`), as the corrected memo claims.
- Derived and implied alpha values recompute correctly throughout.
- `decision-memo.md:240` ("eleven scattering claim rows remain blocked; chromatica remains documented_fail") matches `analysis/docs/rse/control/board/claims-audit.md` exactly: eleven `scattering | blocked` rows at lines 281, 293, 305, 317, 329, 341, 353, 365, 377, 389, 413, and one `scattering | documented_fail` at line 401.
- Pre-review journal entries (02:06–03:41, `analysis/docs/rse/protocols/journal.jsonl`) carry beta 3.571±0.034, 3.748 −0.040/+0.039, 3.640±0.020 and the gain-scale shifts +0.17 / −0.18, all of which match the current records.
- The three files under `initial-review-evidence/` are byte-identical (SHA-256) to the originals in the initial reviewer's Traycer artifact.

## Unverified gates

These are stated so the draft pull request does not read as more settled than it is.

1. **"Original fit outputs unchanged" is corroborated, not proved.** `results/` is untracked, and it was rewritten at 19:34 by `--refresh-classifications`. No before/after diff exists. That the pre-review journal numbers match the current records is strong indirect corroboration, but it is not a byte comparison.
2. **`history-ledger.md` and `referee-methods-review.md` are pre-review documents, unmodified, and their source claims were not independently re-derived.** Both self-qualify appropriately (`referee-methods-review.md:9`; ledger entries labelled "landing not independently reconfirmed here"). Neither carries a withdrawn numerical claim; I swept every evidence `.md` for those and found none.
3. **Deferred throughout:** production convergence, repeated generative calibration, posterior predictive checks in both bands, competing-geometry comparison, and actual-sightline cause assignment. The memo's validation gate table (`:223–231`) states these; none is closed.
4. **The future per-band model is a specification, not tested code.** Nothing in this evidence set demonstrates that the proposed headline path runs, converges, or recovers truth.
5. **No long fits were rerun in this review,** per instruction. Every numerical check above is a recomputation from saved outputs or a closed-form check, not a refit.
6. **Nine interior harness recoveries do not clear production inference.** The harness uses a different likelihood, kernel and nuisance structure from production; the evidence set says so, and this review does not upgrade it.

## Exact approved scope

Approved:

- Open a **draft** pull request publishing the evidence root `analysis/docs/rse/specs/research/method-reassessment-2026-09-11/` and the four tracked framing edits (`analysis/CONTEXT.md`, `analysis/docs/rse/wayfinder/map-apj-submission.md`, tickets `method-reassessment-01` and `…-07`), plus the review receipts.
- Publish family 3 as a **provisional recommendation** with the continuity hold and calibration gaps retained as written.
- Record the review receipt, review status, journal entry and acceptance boxes as warranted.

Not approved by this review:

- Any claim of completed scientific validation, or promotion of any fitted value.
- Closing ticket `method-reassessment-01`. Actual-sightline cause assignment is the charter requirement and is unfinished and unwaived.
- Unparking ticket 07, changing production code, or any manuscript promotion.
- Merging. Scientific merge remains an owner gate.

Fix should-fix 1 and 2 before opening the draft pull request; they are textual and need no re-review. If either is deferred instead, say so in the pull request body rather than leaving the contradiction unremarked.


## Publication corrections applied

Both should-fix items above were applied before publication: the copied-receipt provenance is explicit, and all five conditional flip steps are in the memo. The scale-10 baseline pointer was also added. As allowed by this review, these textual corrections require no re-review.
