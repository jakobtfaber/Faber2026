# Handoff: board cleared — B3 closed, budget-table parity restored, submodule pin misfire caught and reverted

---
**Date:** 2026-07-09 03:05
**Author:** AI Assistant
**Status:** Handoff — all tracked items closed; no open PRs; one preserved lane and one preserved backup ref
**Branch:** work done in an isolated worktree (`/private/tmp/faber-closeout`); the shared checkout was never touched
**Commit (origin/main):** see below
**Supersedes:** `handoff-2026-07-09-02-15-igm-spline-fix-pr42-and-concurrent-writer.md`

---

## Context

The prior handoff left seven items and one live hazard (a second agent writing in
the shared checkout). This session closed all seven. Two of them turned out to be
mis-stated in the handoff itself, and one produced a real mistake of mine that
reddened another repository's CI. All three are recorded below, because the
mistakes are more instructive than the fixes.

The concurrent agent turned out to be a capable collaborator, not a hazard: it
independently revalidated PR #42 before merging it, landed #43/#44/#47/#50/#51/#52,
and opened #46. We converged rather than collided — but only because I stopped
editing the shared tree and moved to an isolated worktree after the first near-miss.

## Task(s)

| # | Item (from the prior handoff) | Status |
|---|---|---|
| 1 | Adjudicate the uncommitted `sections/toa.tex` B3 edit | ✅ Closed — landed by the other agent as #44; its residual defect fixed by my #45 |
| 2 | Review + merge PR #42 (IGM spline) | ✅ Merged (`8cef432`) by the other agent, independently revalidated |
| 3 | Serialize the writers / `grit init` | ✅ `grit init` run (3076 symbols); I moved to an isolated worktree |
| 4 | Journal + rebake the readiness board | ✅ This PR |
| 5 | Decide `data/` | ✅ Closed by #43 — physical files in `~/Data/Faber2026/`, `/data/` gitignored |
| 6 | Push or drop `681cfe2`; clean `backup/*` | ✅ Dropped (superseded); one backup deleted with proof, one preserved |
| 7 | #36 referee-response tracking | ✅ No response letter exists in-repo; `observations.tex` already matches `765a40a` |
| 8 | `budget_table.tex` emitter + parity test | ✅ It already existed — and was **broken**. See below. |

**Current Workflow Phase:** Complete. No open PRs in either repo.

## Merged this session

**Faber2026** — #45, #48, #53, #55, #56 (mine); #43, #44, #46, #47, #50, #51, #52 (the other agent's).
**dsa110-FLITS** — #143 (mine, **reverted**), #145 (the revert).

Final `origin/main` state: `latexmk -pdf` exit 0, 47 pp, 0 undefined refs/citations;
`pytest tests/test_dm_budget_uncertainty.py` 10 passed; pipeline parity suite 9 passed;
gitlink `pipeline` = `6c87890`.

## 1. B3 is closed, and the "10 vs 12" scare was a false alarm

The prior handoff called the `10 chime_event_no` vs `12 reported pairs` gap "a
bookkeeping mismatch in the co-detection sample itself." **It is not.** Resolved:

- 10 rows have a non-empty `chime_event_no`, but one (`220521aaat`, *benjy*) is a
  literal `-`. So there are **9 real event IDs.**
- **8** of those 9 are among the twelve accepted pairs.
- The 9th, `220726aabn` (**FRB20220726A**, *gertrude*), is listed in the imported
  co-detection sheets as a **rejected / no-baseband candidate**, alongside `pingu`
  and `FRB20220912A2`. It was never an accepted pair.
- The remaining **4** accepted pairs (*phineas*, *mahi*, *chromatica*, *casey*)
  simply carry no `chime_event_no` in the master spreadsheet.

The catalog's `chime_event_no` column is incomplete *and* contains a rejected
candidate. **It is not the authority for the co-detection sample.**
`pipeline/analysis/chance-coincidence/bursts.json` is, and it holds exactly twelve.

### `N = 64` is right — but not for the reason the README gave

The catalog README claimed the count is "stable under two independent methods (MJD
field vs. YYMMDD candname date)." Both methods return 64. **They agree by
coincidence, on different sets**, each including exactly one row the other drops:

- the MJD method includes the candname-less `johndoe` row and excludes
  `240204aacb` (*misfortune*, no MJD);
- the candname method does the reverse.

The **MJD set is correct**. `240204aacb` is one of the eight measurement-free
candidate stubs. `johndoe` is a real detection (S/N 72.6, DM 696.4) of the same
repeating source as `johndoeII` = FRB 20230814B (DM 696.2, identical `z = 0.5535`,
same beam declination, 47 days earlier) — two detections of one repeater are two
trials, so it belongs in the denominator.

**`~/Data/Faber2026/dsa110/catalog/dsa110_frb_catalog_README.md` has been corrected**
(both claims). It is outside git (`/data/` is ignored), so it will not appear in any diff.

### What #44 left behind, fixed in #45

#44 landed the right numbers but left the sentence that *defines* the trial set
calling it "the complete list of DSA-110 **triggers**." A trigger is a single-pulse
candidate — `10⁴`–`10⁶` of them, overwhelmingly RFI, never searched against CHIME.
Read literally it overstated the trial set by four orders of magnitude, and it is
the exact confusion that sent two earlier sessions hunting a nonexistent trigger
database. Now "detections."

Independently re-derived before merging: `mu_analytic(DM=500) = 5.02×10⁻⁹`, so
`64μ = 3.2×10⁻⁷`; the twelve pairs sum to `5.46×10⁻⁸`, and `×64/12 = 2.9×10⁻⁷`. Consistent.

## 2. The budget-table emitter existed — and would have reverted the manuscript

The prior handoff's item 8 said to *build* an emitter + parity test. **Both already
existed**, in the pinned submodule, written weeks ago. `REPRODUCE.md`'s "no
generator exists" was stale, which is what #46 set out to fix.

But `galaxies/foreground/budget_table_data.json` at the pin still held the
**pre-#40 Macquart-era** `DM_host` posteriors. So the regeneration command #46 was
about to document —

```bash
uv run python -m galaxies.foreground.budget_table_emitter --out ../budget_table.tex
```

— would have **silently reverted 8 of 9 `DM_host` cells and the `tablecomments`
prose** to a prior this manuscript deleted. `FRB 20220310F` would have gone from
`-10^{+88}_{-107}` back to `12^{+69}_{-167}`.

The emitter's own parity test, `test_dm_host_matches_forward_model`, ties the table
to `scripts/dm_budget_uncertainty.csv`. **It had been red since #40 landed.** Nobody
ran it. The test was never broken — it was correct, and it was the only thing
standing between the pipeline and that revert.

Fixed at source (`6c87890`): data file re-synced from the CSV, `_TAIL` tablecomments
updated to the manuscript's wording, `exports/budget_table.tex` regenerated. The
emitter's output is now **byte-identical** to the committed `budget_table.tex`;
running the documented command on `main` is a clean no-op for both tables. Parity
suite 9/9.

## 3. 🔴 My mistake: the pin is not on the upstream default branch

**`f9e1c24` — the commit this repo has pinned since #39 — is not an ancestor of
`dsa110-FLITS` `main`.** It lives on `agent/sightline-halo-grid-figure`, 22 commits
divergent since the fork at `6647753`. The budget-table emitter exists **only** on
that line; `main` has never carried it.

I branched the fix off the pin (correct) and opened the PR against FLITS `main`
(wrong). The squash merge did not land 3 files — it merged the entire fork delta:
**127 files, +137,005 / −1,322**, rolling back an unrelated 2026-07-07 `johndoeII`
beta-native C2D2 promotion and turning FLITS CI red:

```
FAILED tests/test_joint_summary_reproducible.py::test_summary_matches_generator_output
```

I compounded it by merging while `mergeStateStatus` was `UNSTABLE` — checks pending,
not passed — instead of waiting.

**Remediation, complete:** FLITS #145 reverts `c69d043`; FLITS `main` is back to its
pre-#143 tree with all four checks green (`8b5c64e`). Faber2026 #53 re-pins the
gitlink to `6c87890` = `f9e1c24` + exactly the three intended files. #55 and #56
correct the five stale `c69d043` references #51 had written into `REPRODUCE.md` and
`repro_manifest.csv`.

**Two rules earned:**
1. Before bumping a submodule pin, run `git merge-base --is-ancestor <old> <new>`.
   A pin that lives off the upstream default branch makes "just merge it upstream"
   the wrong reflex.
2. `MERGEABLE` is not `CLEAN`. Wait for checks; `UNSTABLE` means pending or failing.

## Reproducibility & Data State

- **Seed / env unchanged.** Agent-safe runner used throughout:
  `env -i HOME=$HOME PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin /opt/anaconda3/bin/conda run --no-capture-output -n py312 …`
  (bare `conda run` resolves base Anaconda Python on this machine).
- **The parity test spans two repos** — it reads a super-repo CSV from a submodule
  test — so its verdict is a property of the *pair* (super-repo commit, pin), never
  of either alone. `REPRODUCE.md` hazard 1 records this.
- **`data/`** holds machine-local absolute symlinks into `~/Data/Faber2026/dsa110/catalog/`;
  `/data/` is gitignored (#43). `dsa110_frb_catalog.csv` resolves.
- **In-flight jobs:** none.

## Verification State

- Faber2026 `main`: build green (47 pp, 0 undefined), 10/10 manuscript tests,
  9/9 pipeline parity, documented regeneration is a byte-exact no-op.
- dsa110-FLITS `main`: green at `8b5c64e`.
- No open PRs in either repo.

## Preserved lanes (untouched, reported)

- **`sections/toa.tex` in the shared checkout** — still shows as modified there. Its
  content is the #44 edit, now superseded on `main` (which also carries my #45
  wording). Belongs to the other agent's lane; not mine to revert.
- **`backup/dirty-state-before-rebase-20260707`** — carries a unique commit
  `f1030eb` "Reconcile foreground and DM diagnostic state" that is on no other ref.
  **Not provably stale. Left alone.**
- **`backup/main-pre-rebase-20260708`** (`4a00aa0`) — retained as the safety copy of
  the dropped `681cfe2`.
- **Eight stale worktrees under `/private/tmp/`** from earlier sessions
  (`faber-rebase`, `faber2026-*`). Not mine; not cleaned.

### Resolved with proof
- `681cfe2` **dropped** from local `main` — content landed via #46/#51/#55/#56;
  `git branch -f main origin/main`. Recoverable from `backup/main-pre-rebase-20260708`.
- `backup/local-main-before-origin-reconcile-20260707` **deleted** —
  `git cherry -v origin/main <branch>` showed only `-` (0 unique patches), no open PR,
  no remote copy.

## Action Items & Next Steps

1. [ ] **Nothing is blocking.** The board is clear.
2. [ ] Consider whether `FRB20220726A` (*gertrude*) deserves a sentence in the
   manuscript. It is a real DSA detection with a CHIME event ID inside the trial
   window, rejected only for lack of baseband. A referee who finds the catalog may
   ask why the sample is twelve and not thirteen.
3. [ ] The `pipeline` pin lives on `agent/sightline-halo-grid-figure`, permanently
   divergent from FLITS `main`. That is a standing hazard, not a bug — but someone
   should decide whether the manuscript's line ever merges upstream.
4. [ ] `backup/dirty-state-before-rebase-20260707` needs an owner's verdict on
   `f1030eb`.

## Other Notes

- **Standing push/PR authorization** exercised in both repos. One force-push, to my
  own unmerged branch (`docs/manifest-pin-correction`) with `--force-with-lease`,
  to correct a CRLF-normalizing edit that had touched all 26 lines of
  `repro_manifest.csv` instead of one. Caught before merge. No shared history rewritten.
- Commits used inline `GIT_AUTHOR_*`/`GIT_COMMITTER_*` = `Jakob Faber <jfaber@caltech.edu>`.
- `grit init` was run in this repo (registry at `.grit/registry.db`, gitignored). It
  appended a redundant `.grit` line to `.gitignore`, which was reverted — the repo
  already ignored `.grit/` at line 21.

---

**Handoff created by AI Assistant on 2026-07-09**
