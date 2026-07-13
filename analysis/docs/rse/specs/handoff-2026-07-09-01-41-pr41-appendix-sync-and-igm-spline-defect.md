# Handoff: PR #41 opened (Appendix C ↔ #40 sync); IGM spline low-z defect found; B3 unblocked-but-dirty

---
**Date:** 2026-07-09 01:41
**Author:** AI Assistant
**Status:** Handoff — PR #41 open and mergeable; two follow-ups queued; one author decision pending
**Branch:** `ms/appendix-c-sync-pr40` (in sync with its remote)
**Commit:** `35abbbd`
**Supersedes:** `handoff-2026-07-08-18-12-b7-cgm-census-resolved.md` (its DM sign-off is void; its B3 reframing is still correct and reproduced below)

---

## Context

The session began as "resume the open author-decision items (B3 trial count, DM
prior sign-off)." Both items turned out to rest on premises that had gone stale
within hours, so the session became a repair job:

1. The **DM prior sign-off was obtained at 18:35 and voided at 20:05** by PR #40
   (`64158aa`), which rewrote the cosmic-DM model. The author signed off on
   priors that no longer exist.
2. **PR #40 was a half-migration.** It updated the script, the CSV, `budget.tex`,
   `bib/refs.bib`, and the posterior figure — but not `appendix.tex`,
   `budget_table.tex`, `results.tex`, or `conclusions.tex`. `origin/main` was
   simultaneously describing a deleted prior and printing pre-#40 numbers next to
   a post-#40 figure. **Fixed in PR #41.**
3. **B3 was never blocked on a database.** It was blocked on `toa.tex` calling a
   detection count a "trigger" count. The catalog that answers it appeared on disk
   this session, but is not yet trustworthy.
4. A **new physics defect** surfaced while investigating #40: the TNG spline
   extrapolates below its grid.

## Task(s)

| # | Item | Kind | Status |
|---|------|------|--------|
| — | Sync Appendix C / budget table / results / conclusions to #40 | manuscript | ✅ **PR #41 open, MERGEABLE** — needs review + merge |
| DM | Fiducial DM priors + `DM_host` headline | author call | ✅ Resolved — interpretation survived, numerals synced (see Learnings) |
| 🐛 | TNG IGM spline extrapolates below `z=0.1` | physics defect | 📋 **Open — needs its own PR** (rerun required) |
| B3 | DSA-110 trial-set denominator | pipeline number | ⏸ Deferred by author; now *reframed* and *nearly* answerable — data is dirty |
| — | `data/` untracked: track or ignore? | author decision | 📋 **Decision pending** |
| — | Author's unpushed `681cfe2` on `main` | git | 📋 Unpushed by design; awaiting author |
| — | #36 referee-response supersession | tracking note | 📋 Watch (carried forward) |

**Current Workflow Phase:** Validate / author review.

## Workflow Artifacts

**Handoff Documents (this lane):**
- [handoff-2026-07-08-18-12-b7-cgm-census-resolved.md](handoff-2026-07-08-18-12-b7-cgm-census-resolved.md) — B7 CGM census; **updated this session** with the #40 blocker, the B3 reframing, the spline defect, and corrected git state. Committed in `35abbbd`.
- [handoff-2026-07-08-08-55-open-author-decisions.md](handoff-2026-07-08-08-55-open-author-decisions.md) — the original B3/B7/DM item list. Its Item 1 (B3) *diagnosis* is superseded; see "The B3 reframing" below.

**Other agents' untracked handoffs (separate lanes — preserved, not mine):**
- `handoff-2026-07-08-18-42-submodule-roundtrip-figure-refresh.md`
- `handoff-2026-07-08-22-49-flits-pipeline-commits-and-repo-state.md`

## Critical References

- **[PR #41](https://github.com/jakobtfaber/Faber2026/pull/41)** — the deliverable. Read its body first; it states the problem, the fix, and what it deliberately does *not* fix.
- `scripts/dm_budget_uncertainty.py:105-113` — the TNG grid + spline. **This is where the open defect lives.**
- `sections/appendix.tex:76-96` — the rewritten Cosmological prior bullet (the prose #40 should have written).

## Recent Changes

**Commit `620aabc` — "ms: sync Appendix C, budget table, and results/conclusions to PR #40"**

- `sections/appendix.tex:76-93` — replaced the `Macquart2020` `p(Δ)` / `F∼U[0.25,0.40]` bullet with the IGM log-normal description: `Walker2024` TNG-300 bivariate fit, adopted via the `Connor2024` reproduction package, IGM *marginal* (not the total `DM_cos = DM_IGM + DM_X`, since `DM_X` is carried by `DM_int`), rescaled by `ln(f_IGM/f_IGM,TNG)` with `f_IGM,TNG = 0.797`.
- `sections/appendix.tex:99-110` — right-skew claim softened to "generally exceed" (FRB 20220207C is now an exception, see the defect); the two near-zero medians stated explicitly with the `0.25σ` framing.
- `sections/appendix.tex:124-132` — all 9 rows of `tab:host-forward-model` refreshed.
- `sections/appendix.tex:142-145` — figure caption: `P(DM_cosmic|z)` → `P(DM_IGM|z)`.
- `budget_table.tex:40-51` — 9 `DM_host` cells refreshed; `:76-85` `tablecomments` rewritten.
- `sections/results.tex:54-63` — median span `10–210` → `-10–200`; largest host `211` → `197`; `P(<0)≈0.45` → `≈0.5`.
- `sections/conclusions.tex:34-40` — same two corrections.

**Commit `35abbbd` — "docs(rse): handoff + journal for the PR #40 half-migration"**
- Updated the 18-12 handoff; appended 3 journal entries; rebaked `docs/rse/board/readiness.html`.

**Git repair (no commit):** the author's unpushed `4a00aa0` was rebased onto `origin/main` and replayed cleanly as **`681cfe2`** on `main`. Safety ref **`backup/main-pre-rebase-20260708` → `4a00aa0`** still exists.

## Reproducibility & Data State

- **Seed:** `scripts/dm_budget_uncertainty.py:54` — `np.random.default_rng(20260707)`; `N_DRAW = 200_000`. The CSV reproduces bit-identically across reruns (verified: an 18:25 rerun by another process produced an identical `dm_budget_uncertainty.csv`; only the figures' embedded font subsets differed, a matplotlib-version artifact).
- **Environment:** conda `py312` for the read-only probes; `latexmk` for the build. The `ffa` env from the prior (B7) session was not needed.
- **Data — `data/` is UNTRACKED and unreferenced by any tracked script:**
  - `data/dsa110_frb_catalog.csv` (sha256 `6ac39ef6d33c937d…`), 92 detections, 56 with host z, 8 candidate stubs with no MJD. Plus README + overview `.pdf`/`.png`.
  - It is the right *kind* of object for B3 but is **not clean** — see the B3 section.
- **Calibration input not in git:** the TNG values at `scripts/dm_budget_uncertainty.py:105-111` are transcribed verbatim from `tng_params_new.npy` in the `Connor2024` reproduction package. That `.npy` is **not** in this repo. Regenerating the calibration requires fetching it.
- **In-flight jobs:** none.

## Verification State / Known-Broken

- **Build: green.** `latexmk -pdf main.tex` exits 0, **47 pp**, **0** undefined references or citations (final `main.log`, `main.blg` reports 0 warnings). The two `natbib` "undefined citations" lines in the raw latexmk log are first-pass artifacts before BibTeX ran — benign.
- **Every table value in PR #41 was cross-checked row-by-row** against `origin/main:scripts/dm_budget_uncertainty.csv`. No value was hand-computed.
- **PR #41 is OPEN and MERGEABLE.** Branch `ms/appendix-c-sync-pr40` is pushed and in sync. Not merged.
- **🔴 `origin/main` is still internally inconsistent until #41 merges.** It describes the deleted prior in Appendix C while printing pre-#40 numbers in two tables and three sections, beside a post-#40 figure.
- **🐛 Open defect (not fixed, see below):** the IGM spline extrapolates below its grid. This affects published numbers for FRB 20220207C on `origin/main` *and* in PR #41 — #41 syncs prose to whatever the script emits; it does not correct the script.
- **Unpushed:** `main` is 1 ahead of `origin/main` with the author's own `681cfe2` (repro spine: `REPRODUCE.md` +98/−33, `repro_manifest.csv`). Left unpushed deliberately.
- **Separate lanes preserved, untouched:** the `pipeline` gitlink (submodule worktree is at `e223b90` on its own branch `agent/sightline-halo-grid-figure`, with its own dirty files; `origin/main` records `f9e1c24`), and two other agents' untracked handoffs.
- **`data/` and `scripts/__pycache__/`** are untracked and neither committed nor gitignored.

## 🐛 The open defect: TNG spline extrapolates below `z = 0.1`

`scripts/dm_budget_uncertainty.py:112` builds

```python
_MU_IGM_SPL = interpolate.UnivariateSpline(TNG_ZGRID, TNG_MU_IGM, s=0)
```

on `TNG_ZGRID` (`:105`) which **starts at `z = 0.1`**. That is a cubic spline with
scipy's default extrapolation and **no low-`z` guard**. Two of the nine sightlines
sit below the grid.

Diagnostic — ratio of the new IGM marginal (at the TNG baseline `f_IGM,TNG = 0.797`)
to the old Macquart point estimate. `budget_table.tex:18` and `sections/budget.tex:5`
record that the old term used `f_IGM = 0.84`, so the expected ratio is
`0.797/0.84 ≈ 0.949`:

| z | on TNG grid? | `DM_IGM(f_TNG)/⟨DM_cos⟩` |
|---|---|---|
| 0.043 (FRB 20220207C) | **NO — extrapolated** | **1.220** ← IGM marginal exceeds the *total* |
| 0.074 (FRB 20240203A) | **NO — extrapolated** | 0.997 |
| 0.251–0.510 (six sightlines) | yes | 0.930–0.944 ← stable, matches 0.949 |

`DM_IGM > DM_cos` is impossible when `DM_cos = DM_IGM + DM_X` with `DM_X ≥ 0`.

**Corroborating symptom:** FRB 20220207C is the *only* sightline whose posterior
median now falls **below** its arithmetic residual (41 vs 45) — the reverse of the
right-skew every other sightline shows, and the reason `appendix.tex` now says
"generally exceed" instead of "exceed."

**Impact is modest but real:** 20220207C `P(DM_host<0)` moved 0.151 → 0.185, and it
is a *published* number on `origin/main` and in PR #41. The calibration is being
evaluated outside its tabulated range.

**Fix (needs its own PR):** add a low-`z` guard — clamp to the grid edge, or impose
the physical `DM_IGM → 0` as `z → 0` — then rerun `scripts/dm_budget_uncertainty.py`,
which regenerates `scripts/dm_budget_uncertainty.csv` and
`figures/dm_host_posteriors.{pdf,png}`. **Both `tab:host-forward-model`
(`appendix.tex`) and the 9 `DM_host` cells in `budget_table.tex` must then be
re-synced by hand** — `budget_table.tex` has no emitter (see Learnings).

## The B3 reframing (still authoritative; carried forward)

The prior handoff sent two sessions hunting for a "DSA-110 trigger database." That
was the wrong target, and the manuscript's own prose is why.

- `sections/toa.tex:68` says "the complete list of DSA-110 **triggers** searched for
  a CHIME/FRB counterpart"; `sections/toa.tex:73` says "the entire DSA-110
  **detection** list." Same quantity, two names; **only the second is right.** A
  DSA-110 *trigger* is a single-pulse candidate — overwhelmingly RFI, `10⁴`–`10⁶` of
  them. Those were never searched against CHIME, so they never received a
  look-elsewhere test and must not enter `Σⱼμⱼ`.
- **Verified in code:** every input to `μ` is a module-level constant in
  `pipeline/analysis/chance-coincidence/inputs.py:22-59`
  (`R_SKY_PER_DAY_CONSERVATIVE=1000`, `OMEGA_WIN_BASELINE_DEG2=0.785`,
  `DT_BASELINE_S=1.0`, `DDM_BASELINE=5.0`). Nothing varies per burst. Therefore
  **`Σⱼμⱼ = N × μ` exactly** — the denominator is a pure count, `μ ≈ 5×10⁻⁹` each.
- **So B3 needs one number:** how many DSA-110 FRB *detections* over
  2022-Feb–2024-Feb were cross-searched against CHIME. No database required.

### What the on-disk catalog says — and why it is NOT usable yet

Filtering `data/dsa110_frb_catalog.csv` on `59611 ≤ MJD < 60370` (2022-Feb-01 →
2024-Mar-01) gives **64 detections**, which would make `Σⱼμⱼ = 64 × 5×10⁻⁹ ≈ 3.2×10⁻⁷`.

**Do not write 64 into `toa.tex` without resolving two problems:**

1. **Corrupt epoch.** `FRB20240304C` carries `mjd = 554553.0` — nonsense (should be
   ≈60373). At least one row's epoch is untrustworthy, so the window filter is not clean.
2. **10 vs 12.** Only **10** catalog rows carry a `chime_event_no`, but the manuscript
   reports **twelve** co-detected pairs. The catalog's CHIME cross-match bookkeeping
   does not reproduce the paper's own sample — and that is precisely the column that
   would establish "how many DSA detections were searched against CHIME." *This may
   matter beyond B3.*

**Deliverable once `N` is trustworthy:** replace `10²`–`10³` at `sections/toa.tex:73-74`,
restate the bound as `Σⱼμⱼ = N × 5×10⁻⁹`, and fix "triggers" → "detections" at
`sections/toa.tex:68` so the paragraph names one quantity consistently.
**Caveat, and it is safe:** detections = searched only if no DSA FRB in the window was
skipped (below CHIME's horizon, outside its declination coverage at that epoch, or
during CHIME downtime). If any were skipped, `N_searched < N_detected`, so the
detection count over-counts trials — and `P_cc` is framed as an upper bound, so a
conservative denominator strengthens the claim.

## Learnings

- **A blocked item can be blocked by its own prose.** B3 was chased into a
  nonexistent trigger database for two sessions because `toa.tex` called a detection
  count a "trigger" count. When an item looks blocked on data you cannot reach,
  re-read the sentence that *defines* the quantity before hunting for the data.
- **The negative host medians are a knife-edge, not a tension — and not the cause
  #40 predicted.** #40's rationale implies a `DM_int` double-count would be the
  culprit. It is not: for FRB 20220310F the diffuse median alone (383.5) already
  exceeds its entire extragalactic DM (`DM_obs − DM_MW = 381`) with `DM_int` only 11.
  The `f_IGM` that places either median exactly at zero is **0.733** (20220310F) and
  **0.742** (20221203A) — **0.24σ** and **0.16σ** below the prior median 0.76
  (`σ_lo = 0.11`). `P(DM_host<0) ≈ 0.5` is the definition of consistent-with-zero.
  **The author's 18:35 *interpretation* survived #40; only the numerals moved.**
- **Why the sign flipped at all:** the TNG IGM calibration has CV ~20–37% vs the old
  `F z^{-1/2}` form's ~60–80%. Same central over-subtraction, tighter scatter ⇒ the
  residual becomes *confidently* near-zero instead of *tolerably* so. Narrowing a
  prior can flip a median's sign without any physics changing.
- **`budget_table.tex` and `foreground_table.tex` are hand-maintained — no emitter.**
  `REPRODUCE.md` (the author's own `681cfe2`) warns "a hand edit can silently drift
  from the pipeline." **PR #40 is exactly that drift.** Any future rerun of
  `dm_budget_uncertainty.py` must re-sync `budget_table.tex` *and*
  `appendix.tex`'s table by hand. Building the planned emitter + parity test would
  have prevented this entire session.
- **A stale `git status` can invent a dirty tree.** `REPRODUCE.md` /
  `repro_manifest.csv` read as modified but were byte-identical; 16 scint figures read
  as modified but matched `origin/main` exactly. Confirm with
  `git diff --stat HEAD` **and** `git diff --stat origin/main` before describing a
  working tree — a touched mtime is not a change.
- **`lane-liveness` "live" is not always an agent.** It reported a live writer for
  hours; the cause was a hung `git difftool -y -x vimdiff HEAD` (pid 55399, 4h+) that
  had spawned MacVim holding a swap on `docs/rse/board/.readiness.html.swp` — a
  *stale* buffer that would have clobbered the rebaked board on save. Killed both,
  removed `.readiness.html.swp` and `.REPRODUCE.md.swp`. Check `ps`/`lsof` before
  concluding another agent owns the lane.
- **#36 vs the B7 census (carried forward):** #36 claimed all confirmed halos incl.
  the 243 kpc one are within `R_vir`. The measured census puts it outside at
  `b/R_vir = 1.73`. **243 kpc is a GRAZING halo; the pierced set is 102–237 kpc.**
  Corrected in `765a40a`.

## Action Items & Next Steps

1. [ ] **Review and merge [PR #41](https://github.com/jakobtfaber/Faber2026/pull/41).**
   Until it lands, `origin/main` contradicts itself. It is MERGEABLE and touches no
   submodule pointer.
2. [ ] **Fix the IGM spline low-`z` extrapolation** (own PR). Guard
   `scripts/dm_budget_uncertainty.py:112` below `z=0.1`, rerun the script, then
   **hand-sync** `tab:host-forward-model` (`sections/appendix.tex:124-132`) and the 9
   `DM_host` cells in `budget_table.tex:40-51`. Expect FRB 20220207C to move.
   Do this **after** #41 merges, or the two syncs will conflict.
3. [ ] **Decide `data/`:** track it (after fixing `FRB20240304C`'s MJD and reconciling
   10 `chime_event_no` vs 12 reported pairs) or add it to `.gitignore`.
   **The 10-vs-12 discrepancy deserves a look on its own merits.**
4. [ ] **B3, once `N` is trustworthy:** the three-line edit at `sections/toa.tex:68,73-74`
   described above. Still author-deferred.
5. [ ] **Push or drop `681cfe2`** (author's repro-spine commit on `main`, unpushed).
   Delete `backup/main-pre-rebase-20260708` once satisfied with the rebase.
6. [ ] **#36 referee-response tracking** — if the "minor-7" response letter quotes the
   old "each within R_vir / 243 kpc" prose, update it to match `765a40a`.
7. [ ] (Optional) Regenerate the `Faber2026_CGM.pdf` artifact if a current-state PDF is wanted.

**Recommended Next Skill:** `ai-research-workflows:hardening-research-code` — item 2 is a
numerical-correctness defect in research code (an unguarded extrapolation outside a
calibration's tabulated range), which is exactly that skill's remit. Use
`ai-research-workflows:validating-implementations` for item 4 once the author supplies `N`.

## Other Notes

- **Standing push/PR authorization** (`CLAUDE.md`) was exercised this session: branch
  pushed, PR #41 opened. No force-push, no merge, no submodule bump, no shared-history
  rewrite.
- Git identity is not configured in-repo; commits used inline `GIT_AUTHOR_*`/
  `GIT_COMMITTER_*` env vars set to `Jakob Faber <jfaber@caltech.edu>`, matching repo
  history. A normal shell should set `git config user.name/user.email` once.
- `agent-closeout-check` passes with a dirty-state packet classifying all 5 dirty
  paths (`pipeline` → preserve; two other agents' handoffs → preserve; `data/` →
  decision-pending; `scripts/__pycache__/` → ignore).
- The readiness board is redeployed at the existing artifact URL
  (`https://claude.ai/code/artifact/fdc8d749-f3a6-4296-bbd2-9f1052fe57f6`); rebake with
  `python3 scripts/render_journal_panel.py` and redeploy with the same `url=` to keep it stable.
- Journal protocol: `bash scripts/journal-append.sh "<agent>" "<lane>" "<state>" "<note>"`
  (positional args — the script has no `--flag` interface, despite what a `--help` attempt suggests).

---

**Handoff created by AI Assistant on 2026-07-09**
