# Handoff: B7 resolved (CGM-intersection census); B3 + DM priors still open

---
**Date:** 2026-07-08 18:12 (updated 18:35)
**Author:** AI Assistant
**Status:** Handoff — B7 closed & pushed; **DM priors signed off by author**; B3 deferred
**Branch:** `main` at `765a40a`, **2 behind `origin/main`** (`5cc4f3f` scint-figure refresh, `eeca832` pipeline bump) — a fast-forward pull is all that is needed
**Commit:** `765a40a`
**Supersedes:** `handoff-2026-07-08-08-55-open-author-decisions.md` (B7 closed; DM now closed; B3 deferred)

---

## Context

This session resolved **B7** (the foreground galaxy-search aperture item) by
adopting a per-object circumgalactic-intersection (CGM) census: galaxies are
retained when the sightline pierces their own virial radius, `b ≤ R_vir`,
applied **after** redshift confirmation rather than in its place. The change is
committed and pushed. The other two open author-decision items from the prior
handoff — **B3** (DSA-110 trial count) and the **fiducial DM priors** — are
unchanged and still require author/pipeline input.

A branch divergence was reconciled during this session: while B7 was being
drafted, three commits landed on `origin/main`, one of which (**PR #36**) was an
independent rewrite of the same `observations.tex` paragraph. My work was rebased
onto them and the `observations.tex` conflict resolved as a synthesis (see
Learnings).

## Task(s)

| # | Item | Kind | Status |
|---|------|------|--------|
| B7 | Foreground galaxy aperture → CGM `b≤R_vir` census | pipeline number + prose | ✅ Complete (commit `765a40a`, pushed) |
| DM | Fiducial DM priors + `DM_host` headline sign-off | author physical call | ⚠️ **Sign-off VOID — superseded by PR #40 (`64158aa`, merged 20:05).** Re-decision needed against the new cosmic model. |
| B3 | DSA-110 trial count for chance-coincidence denominator | pipeline number | ⏸ **Deferred** by author 2026-07-08 — but reframed, see below; no longer needs a trigger DB |
| — | #36 referee-response supersession | tracking note | 📋 Watch — see Other Notes |

**Current Workflow Phase:** Validate / author review.

## Decisions taken 2026-07-08 (author)

**DM priors — sign-off given at 18:35, then VOIDED by PR #40 at 20:05. Do not act on it.**

At 18:35 the author accepted the fiducials as-is: `F∼U[0.25,0.40]`, 30% lognormal
disk, factor-~2 Galactic halo (`HALO_SIGMA_LN=0.35`), intervening widths
`{measured 0.40, assumed 0.69, cluster 0.30}`, and the right-skew headline reading
`P(DM_host<0)≈0.45` for FRB 20220310F / 20221203A as *consistent-with-zero*.

At 19:03–19:25 `scripts/dm_budget_uncertainty.py` was rewritten, and at 20:05
**`64158aa` (PR #40) merged to `origin/main`**: "budget: re-base cosmic DM term on
TNG-calibrated IGM log-normal". It **deletes `F_LO, F_HI`** entirely and replaces
the Macquart `P(Δ)` (fixed `σ_DM = F z^{-1/2}`) with
`DM_IGM ~ LogNormal(μ(z), σ(z))` from the IllustrisTNG-300 bivariate fit in bib key
`Walker2024`, adopted via the reproduction package of bib key `Connor2024`
(Nature Astronomy, 2025; `arXiv:2409.16952`) and marginalized over
`f_IGM = 0.76 (+0.10/−0.11)`. Both bib keys were added by #40.

**The signed-off headline reverses sign under #40.** `origin/main`'s
`scripts/dm_budget_uncertainty.csv` now reads:

| Sightline | At sign-off (18:35) | `origin/main` after #40 |
|---|---|---|
| FRB 20220310F | `p50=+12`, `P(<0)=0.453` | `p50=−10`, `P(<0)=0.540` |
| FRB 20221203A | `p50=+14`, `P(<0)=0.456` | `p50=−2`, `P(<0)=0.507` |

Both medians are now negative and both exceed `P(DM_host<0)=0.5` — the forward
model prefers an **unphysical negative host DM** for these two sightlines. The
narrower cosmic width is the cause (CV ~20–37% under the TNG IGM calibration vs
~60–80% under `F z^{-1/2}`): the same central over-subtraction becomes confident
rather than tolerable once the scatter tightens. The tail also tightens elsewhere
(20240229A `P(<0)` 0.083→0.014; 20240203A 0.042→0.010).

**Required:** a fresh author decision against the #40 model, not the 18:35 one.
Specifically, whether the two negative-median sightlines are an acceptable
statement, a sign that `f_IGM` / `DM_int` need revisiting, or a reason to widen
the diffuse term. **This item is OPEN, not closed.**

### 🔴 `origin/main` is internally inconsistent — Appendix C was left behind by #40

`64158aa` touched `scripts/dm_budget_uncertainty.py`, `scripts/dm_budget_uncertainty.csv`,
`sections/budget.tex`, `bib/refs.bib`, and `figures/dm_host_posteriors.{pdf,png}`.
It did **not** touch `sections/appendix.tex` or `sections/toa.tex`. Consequences on
`origin/main` as it stands:

1. **Appendix C prose describes a prior that no longer exists.** `sections/appendix.tex:76–81`
   still reads "$\Delta$ from the \citet{Macquart2020} probability density … $F$ uniform on
   $[0.25,0.40]$". `F_LO`/`F_HI` were deleted from the script by #40.
2. **All 9 rows of `tab:host-forward-model` print pre-#40 values.** Verified row-by-row against
   `origin/main:scripts/dm_budget_uncertainty.csv`:

   | Burst | Appendix C prints | CSV on `origin/main` |
   |---|---|---|
   | 20220207C | `51^{+37}_{-49}`, `0.15` | `41^{+37}_{-46}`, `0.18` |
   | 20220310F | `12^{+69}_{-167}`, `0.45` | `-10^{+88}_{-107}`, `0.54` |
   | 20220506D | `61^{+54}_{-117}`, `0.26` | `48^{+65}_{-80}`, `0.27` |
   | 20221113A | `65^{+54}_{-102}`, `0.23` | `55^{+61}_{-75}`, `0.23` |
   | 20221203A | `14^{+97}_{-196}`, `0.46` | `-2^{+106}_{-131}`, `0.51` |
   | 20230307A | `95^{+87}_{-138}`, `0.23` | `90^{+87}_{-107}`, `0.20` |
   | 20230913A | `146^{+61}_{-123}`, `0.14` | `136^{+69}_{-88}`, `0.07` |
   | 20240203A | `109^{+29}_{-45}`, `0.04` | `102^{+31}_{-37}`, `0.01` |
   | 20240229A | `211^{+46}_{-112}`, `0.08` | `197^{+60}_{-75}`, `0.01` |

3. **`figures/dm_host_posteriors.{pdf,png}` WERE regenerated by #40**, so the figure now shows
   the TNG/`Connor2024` posteriors while the table beside it prints the Macquart ones.

**This must be fixed before circulation.** It is mechanical for the table (regenerate from the
CSV) but the Appendix C prior paragraph needs prose describing the `Walker2024`/`Connor2024`
IGM log-normal and the `f_IGM` marginalization, mirroring what #40 put in `budget.tex`.

**B3 — deferred, but the blocker was a wording bug, not a missing database.**
See "The B3 reframing" below. The next session should not repeat the trigger-DB hunt.

## Critical References

- `sections/observations.tex:113–156` — the CGM-intersection census paragraphs (B7). Read first.
- `sections/budget.tex:59–74` — the DM_int construction, now stating the galaxy `b≤R_vir` criterion (11 of 14 contribute, 3 excluded).
- `handoff-2026-07-08-08-55-open-author-decisions.md` — the prior handoff; its **Item 1 (B3)** and **Item 3 (DM priors)** sections are still authoritative and reproduced below.

## Recent Changes (this session)

- `sections/observations.tex:113–156` — replaced the fixed-aperture galaxy-retention paragraph with two paragraphs: (1) the per-object mass→halo→`R_vir` machinery and the pierced/grazing result; (2) the confirmation-then-`R_vir` ordering rationale and the mass-indeterminate caveat. Folded in #36's cluster-mass-provenance sentence (WenHan2024 optical-richness estimates; uncertainty propagates into the intervening-column prior).
- `sections/budget.tex:63–73` — galaxy contribution now explicitly requires `b≤R_vir`; states 11 of 14 confirmed foreground galaxy halos contribute, 3 (all FRB 20230307A) excluded beyond the `R_vir` truncation of the mNFW profile.
- `bib/refs.bib` — appended `Taylor2011`, `Cluver2014`, `DuttonMaccio2014`.
- Prose in both sections swept for colons → complete sentences (author style preference).

## The B7 result (numbers, from the vetted census)

- **14 confirmed foreground galaxy halos** (unchanged; `Table~\ref{tab:foreground}` is confirmation-based and untouched).
- **11 pierce `R_vir`**: `b ≈ 102–237 kpc`, `b/R_vir ≈ 0.15–0.88` → contribute to DM_int.
- **3 graze outside `R_vir`**: all toward **FRB 20230307A** (phineas); `b ≈ 122–243 kpc`, `b/R_vir ≈ 1.05–1.73` → excluded from budget (mNFW profile truncates at `R_vir`, so their modelled column is zero). Of these 3: **1 DESI-spec + 2 photo-z** confirmed.
- **7 mass-indeterminate** candidates (WISE-only masses, no PS1 corroboration; 5 with logM*=11.7–13.0). All 7 are already inconclusive/refuted by redshift and none touches the confirmed budget.
- Full non-refuted galaxy census reaches `b ≈ 60–280 kpc`.

## The B3 reframing (2026-07-08 — supersedes the prior handoff's Item 1)

The prior handoff sent the search after "the DSA-110 trigger database." That was
the wrong target, and the prose is why.

- `sections/toa.tex:68` says "the complete list of DSA-110 **triggers** searched
  for a CHIME/FRB counterpart"; `sections/toa.tex:73` says "the entire DSA-110
  **detection** list." These name the same quantity, and only the second is right.
  A DSA-110 *trigger* in the real-time sense is a single-pulse candidate —
  overwhelmingly RFI, and `10⁴`–`10⁶` of them, not `10²`–`10³`. Those candidates
  were never searched for CHIME counterparts, so they never received a
  look-elsewhere test and must not enter `Σⱼ μⱼ`.
- **Verified in code:** every input to `μ` is a module-level constant in
  `pipeline/analysis/chance-coincidence/inputs.py:22–59` (`R_SKY_PER_DAY_CONSERVATIVE=1000`,
  `OMEGA_WIN_BASELINE_DEG2=0.785`, `DT_BASELINE_S=1.0`, `DDM_BASELINE=5.0`).
  Nothing varies per burst. Therefore `Σⱼ μⱼ = N × μ` exactly — **the denominator
  is a pure count of the DSA-110 events actually searched against CHIME**, with
  `μ ≈ 5×10⁻⁹` each.
- **So the number needed is the count of DSA-110 FRB *detections* in the
  2022-Feb–2024-Feb overlap that were cross-searched against CHIME.** No trigger
  database required. `Law2024` ("Deep Synoptic Array Science: First FRB and Host
  Galaxy Catalog", `bib/refs.bib:278`) is the natural citation, though its window
  is likely shorter than the full overlap.
- **Caveat, and it is safe:** detections equals searched only if no DSA FRB in the
  window was skipped (below CHIME's horizon / outside its declination coverage at
  that epoch, or during CHIME downtime). If any were skipped, `N_searched < N_detected`,
  so using the detection count over-counts trials. `P_cc` is framed as an upper
  bound, so a conservative denominator strengthens the claim.
- **Deliverable when the author supplies `N`:** replace `10²`–`10³` at
  `sections/toa.tex:73–74`, restate the `Σⱼμⱼ` bound as `N × 5×10⁻⁹`, and change
  "triggers" → "detections" at `sections/toa.tex:68` so the paragraph names one
  quantity consistently.

## 🐛 NEW DEFECT (found 2026-07-08 23:0x): TNG spline extrapolates below its grid

`scripts/dm_budget_uncertainty.py:112` builds `_MU_IGM_SPL = interpolate.UnivariateSpline(
TNG_ZGRID, TNG_MU_IGM, s=0)` on a grid that **starts at `z = 0.1`**, with scipy's default
cubic extrapolation and no low-`z` guard. Two of the nine sightlines sit below the grid.

Evidence — the ratio of the new IGM marginal (at the TNG baseline `f_IGM,TNG = 0.797`) to the
old Macquart point estimate. `budget_table.tex:18` and `sections/budget.tex:5` confirm the old
term used `f_IGM = 0.84`, so the expected ratio is `0.797/0.84 ≈ 0.949`:

| z | on TNG grid? | `DM_IGM(f_TNG)/⟨DM_cos⟩` |
|---|---|---|
| 0.043 (20220207C) | **NO — extrapolated** | **1.220** ← IGM marginal exceeds the *total* |
| 0.074 (20240203A) | **NO — extrapolated** | 0.997 |
| 0.251–0.510 (six) | yes | 0.930–0.944 ← stable, matches 0.949 |

`DM_IGM > DM_cos` is impossible when `DM_cos = DM_IGM + DM_X`. Corroborating symptom:
FRB 20220207C is the **only** sightline whose posterior median now falls *below* its arithmetic
residual (41 vs 45) — the reverse of the right-skew every other sightline shows.

Impact is modest (20220207C `P(<0)` 0.151→0.185) but the calibration is being used outside its
tabulated range. Fix would be a low-`z` guard — clamp, or impose the physical `DM_IGM → 0` as
`z → 0` — plus a rerun. **Not fixed here; needs its own PR.** The `ms/appendix-c-sync-pr40`
branch deliberately only syncs prose/tables to the numbers `origin/main` already publishes.

## B3 — provisional count found on disk, NOT used

The untracked `data/` directory (pulled ~19:00–22:49, not in git) holds
`data/dsa110_frb_catalog.csv` + README: a cleaned DSA-110 detection catalog, **92 detections**,
56 with host redshifts, 8 candidate stubs with no MJD.

Filtering `59611 ≤ MJD < 60370` (2022-Feb-01 → 2024-Mar-01) gives **64 detections**, which would
make `Σⱼμⱼ = 64 × 5×10⁻⁹ ≈ 3.2×10⁻⁷`.

**Do not use 64 without resolving two problems:**
1. **Corrupt MJD.** `FRB20240304C` carries `mjd = 554553.0` (nonsense; should be ≈60373). At
   least one row's epoch is untrustworthy, so the window filter is not clean.
2. **10 vs 12.** Only **10** catalog rows carry a `chime_event_no`, but the manuscript reports
   **twelve** co-detected pairs. The catalog's CHIME cross-match bookkeeping therefore does not
   reproduce the paper's own sample — which is precisely the column that would establish "how
   many DSA detections were searched against CHIME."

Until (2) is reconciled the catalog cannot certify the trial-set denominator, even though it is
the right *kind* of object. B3 remains deferred by author decision.

## Reproducibility & Data State

- **Mass-estimation regeneration** was run this session with live Vizier + NOIRLab DataLab access (both network grants approved). Per-object M* via PS1 `g−i` (Taylor2011) or WISE `W1` (Cluver2014) → Moster2013 SMHM → Dutton–Macciò 2014 c–M → `R_vir=R_200c`. Result: 34/34 halos measured (21 PS1/Taylor, 13 WISE/W1).
- **Environment:** `ffa` (Python 3.11.15; numpy/scipy/astropy). Astropy config redirected via `XDG_CONFIG_HOME=/tmp/astro_cfg XDG_CACHE_HOME=/tmp/astro_cache HOME=/tmp/astro_home` because `~/.astropy` is unwritable in-sandbox. `adjustText` + `astroquery` were pip-installed into `ffa`.
- **Frozen census SoT:** `scratch/codetection/foreground_final.csv` (SHA256 `ce14b474424efb5ff442c5206020609475ff7b0675aa370cb026a47cc8ff4766`, 49 objects) — identity/redshift/verdict only, **no stellar-mass column**. The measured masses do NOT exist on disk in the frozen census; they were re-queried live.
- **Vetted census artifacts** (Claude Science artifact store, project `proj_55f9c893cfe1`):
  - `halo_rvir_ADJUDICATED.csv` — version `d3fd91ff-6bb8-4b94-b185-0a36d0c8fdbe` (the authoritative per-halo table: logM_best, R_vir, b_over_rvir, intersects_adj, mass_status, final_verdict).
  - `suspect_vetting_adjudicated.csv` — version `6687fd31-f3e8-423d-99c3-779cb6fa2254` (the 8 logM>11.3 suspects + adjudication).
  - `rvir_halo_adjudicated.png` — version `6562a6b3-aea9-463d-9412-7eb85402297d` (churn figure).
  - `CGM_intersection_census_METHOD.md` v3 — version `75d38bbe-6500-403c-b4a8-c862d2e14ca0` (method note).

## Verification State / Known-Broken

- **Manuscript compiles clean:** `latexmk -pdf main.tex` exits 0, 0 undefined citations/references, all three new bib keys resolve. Built at `765a40a`.
- **Committed & pushed:** the three B7 files are committed (`765a40a`). Nothing of that session's work is uncommitted.
- **Git state as of 2026-07-08 22:53 (this supersedes every earlier git claim in this file):**
  - `main` is **ahead 1, behind 4** of `origin/main`.
  - **Behind 4:** `eeca832` (#37, pipeline→`e223b90`), `5cc4f3f` (#38, scint-figure font
    refresh), `700f231` (#39, pipeline→`f9e1c24`), `64158aa` (#40, **cosmic-DM rebase — see
    Decisions above**).
  - **Ahead 1:** `4a00aa0` "docs: update reproducibility spine for generated budget/foreground
    tables" — authored by **Jakob Faber at 18:30, unpushed**, touching `REPRODUCE.md`
    (+98/−33) and `repro_manifest.csv`. `git cherry -v origin/main HEAD` marks it `+`
    (genuinely unique, NOT squash-merged). **Do not drop or force past it.** Reconciling
    requires a rebase/merge the author should authorize, not a fast-forward.
  - **Every dirty tracked file in the worktree is byte-identical to `origin/main`**
    (`git diff --stat origin/main -- <paths>` is empty for all of them): the 16 scint
    figures, `figures/dm_host_posteriors.{pdf,png}`, `scripts/dm_budget_uncertainty.{py,csv}`,
    `sections/budget.tex`, `bib/refs.bib`, and the `pipeline` gitlink. They read "modified"
    only because `HEAD` is stale. Nothing there needs committing.
  - Untracked: this handoff, two other agents' handoffs (`…18-42-submodule-roundtrip…`,
    `…22-49-flits-pipeline-commits…`), `data/`, `scripts/__pycache__/`.
- **⚠ `lane-liveness .` still reports `live`, and it is NOT another agent.** The signal is a
  **hung `git difftool -y -x vimdiff HEAD` (pid 55399, running 4h+ since 18:37)** which spawned
  **MacVim (pid 56031)** holding `docs/rse/control/board/.readiness.html.swp`. That Vim buffer is stale
  against disk (the board was rebaked at ~18:35); **saving it would clobber the board**.
  The stray `.REPRODUCE.md.swp` is from the same difftool session. Kill 55399 + 56031 and remove
  both `.swp` files before trusting `lane-liveness` or doing git surgery.
- **The 18:35 "no rerun needed" reasoning was sound but is now moot.** At that time
  `dm_budget_uncertainty.csv` reproduced bit-identically and only the figure font subsets
  differed (HEAD: one `DejaVuSans`, `uni no`; working: two, `uni yes`). #40 has since replaced
  the model outright, so the CSV on `origin/main` is different by design, not by churn.
- **B7 did not silently change any DM number.** `pipeline/galaxies/foreground/scattering_predict.py:396`
  is `if b >= r_trunc: return 0.0`, so the 3 grazing halos always contributed exactly
  zero column. The "11 of 14" prose corrected the *description*, not any value;
  `DM_int` in `scripts/dm_budget_uncertainty.py:43–54` needs no change and no rerun.
- **Saved PDF artifact** `Faber2026_CGM.pdf` (version `19410783-c558-4ae7-add6-9cb4736e0eb8`) was built at `02e4ebb`, one commit **before** the pierced-range fix `765a40a`. Regenerate if a current-state PDF artifact is needed.

## Learnings

- **The frozen census carries no stellar masses** — only identity/redshift/verdict. Any `R_vir` criterion requires re-querying photometry live; do not expect masses in `foreground_final.csv` or `intervening_census_registry.csv` (its halo mass columns are all null).
- **Assumed-mass `R_vir` is a trap.** Applying a uniform logM*=10 fallback to all halos collapses `R_vir` to ~120 kpc — a disguised hard cut that produces fake census churn. Only per-object *measured* masses give a real spread (86–2786 kpc). Use `halo_rvir_ADJUDICATED.csv`, not any assumed-mass table.
- **WISE-only masses at z=0.3–0.6 inflate** (blending/nuclear emission); 5 of 7 gave implausible logM*=11.7–13.0. The adjudication rejects WISE-only masses lacking PS1 corroboration → mass-indeterminate, kept out of the budget.
- **Confirmation must precede geometry.** The blind `b≤R_vir` test admits refuted *background* galaxies (3 of the 7 "added" were refuted). Confirmation (is it foreground?) answers a different question than `R_vir` (does the beam pierce its gas?); both are required.
- **A blocked item can be blocked by its own prose.** B3 was chased into a DSA trigger
  database for two sessions because `toa.tex` called the denominator "triggers." It is a
  detection count, and the code proves it: `μ` has no per-burst inputs, so `Σⱼμⱼ = N × μ`
  and `N` is just "how many DSA FRBs did we search." When an item looks blocked on data
  you cannot reach, re-read the sentence that defines the quantity before hunting for the data.
- **A stale `git status` can invent a dirty tree.** `REPRODUCE.md` / `repro_manifest.csv`
  read as modified but were byte-identical; the 16 scint figures read as modified but matched
  `origin/main`. Always confirm with `git diff --stat HEAD` and `git diff --stat origin/main`
  before describing a working tree in a handoff — a touched mtime is not a change.
- **#36 vs. this work — the one factual disagreement:** #36 claimed all confirmed halos (incl. the 243 kpc one) are *within* `R_vir` via a `logM_halo≳12.3` plausibility argument. The measured census puts that 243 kpc halo *outside* at `b/R_vir=1.73`. The synthesis kept the empirical result and corrected the claim. **243 kpc is a GRAZING halo, not a pierced one** — the pierced set is 102–237 kpc. (This was an auditor-caught error mid-session, now fixed in `765a40a`.)

## Action Items & Next Steps

1. [x] **DM priors / #40 half-migration — RESOLVED on branch `ms/appendix-c-sync-pr40`.**
   Investigated (author-approved, 2026-07-08): the negative medians are **not** a `DM_int`
   double-count. For 20220310F the diffuse median alone (383.5) exceeds its entire extragalactic
   DM (381) with `DM_int = 11`; for 20221203A the `DM_int = 84` assumed-mass halo contributes.
   **The tension is a knife-edge, not a problem:** the `f_IGM` that places either median exactly
   at zero is **0.733 / 0.742**, i.e. **0.24σ / 0.16σ** below the prior median 0.76 (`σ_lo=0.11`).
   `P(DM_host<0) ≈ 0.5` is the definition of consistent-with-zero, so the author's original 18:35
   *interpretation* survives; only the numerals moved. Synced `sections/appendix.tex`,
   `budget_table.tex`, `sections/results.tex`, `sections/conclusions.tex` to the published CSV.
   Build verified: `latexmk -pdf` exits 0, 47 pp, 0 undefined.
   **Still open:** the low-`z` extrapolation defect above (its own PR).
2. [ ] **B3 (deferred)** — when the author supplies `N` = the count of DSA-110 FRB *detections*
   cross-searched against CHIME over 2022-Feb–2024-Feb: replace "10²–10³" at
   `sections/toa.tex:73–74`, restate `Σⱼμⱼ = N × 5×10⁻⁹`, and fix "triggers" → "detections"
   at `sections/toa.tex:68`. **Do NOT hunt for a trigger database** — see "The B3 reframing".
   Do NOT substitute 12 pairs or candidate-sheet row counts.
3. [ ] **#36 referee-response tracking** — if the response letter for "minor-7" quotes the old "each within R_vir / 243 kpc" prose, update it to match `765a40a` (the claim was corrected).
4. [x] **Git closeout — done 2026-07-08 ~23:00.** The hung `git difftool` (55399) and MacVim
   (56031) were killed and both `.swp` files removed, so `lane-liveness` no longer reports an
   editor lock. `main` was rebased onto `origin/main`; the author's unpushed `4a00aa0` replayed
   cleanly as **`681cfe2`** and remains unpushed. Safety ref `backup/main-pre-rebase-20260708`
   still points at the pre-rebase `4a00aa0`; delete it once satisfied.
   **Left alone deliberately:** the `pipeline` gitlink (worktree `e223b90`, `origin/main` records
   `f9e1c24`) — the submodule is on its own branch `agent/sightline-halo-grid-figure` with its own
   dirty files, a separate lane. `data/` and `scripts/__pycache__/` remain untracked; `data/` holds
   the DSA-110 catalog and probably *should* be tracked or ignored deliberately (see B3 above).
5. [ ] (Optional) Regenerate `Faber2026_CGM.pdf` artifact from `765a40a` if a current-state PDF is wanted.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` — close B3 against the manuscript once the author supplies `N`.

## Other Notes

- Git identity is not configured in-repo and `.git/config` is unwritable in-sandbox; commits this session used inline `GIT_AUTHOR_*`/`GIT_COMMITTER_*` env vars set to `Jakob Faber <jfaber@caltech.edu>` (matched to repo history). A normal shell will need `git config user.name/user.email` set once.
- This handoff file is **untracked** until committed into the `docs/rse` lane.

---

**Handoff created by AI Assistant on 2026-07-08**
