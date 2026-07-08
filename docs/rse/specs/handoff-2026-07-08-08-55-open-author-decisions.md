# Handoff: Open author-decision items (B3 trials, B7 aperture, fiducial DM priors)

---
**Date:** 2026-07-08 08:55
**Author:** AI Assistant
**Status:** Handoff — open items require author physical/pipeline input (not implementable without it)
**Branch:** `main` (Overleaf-synced) tip `25c8ca7`; working lane `docs/clarify-chance-coincidence` tip `b81d8c5`
**Commit:** referee impl `c330d77`; bib fixes `25c8ca7`; `\phantomsection` fix `1e2cb4c`

---

## Context

The referee-implementation, figure/font, Overleaf-propagation, and ADS
citation-spot-check lanes are **closed** (see the four prior 2026-07-08 handoffs +
`runbook-overleaf-propagation-2026-07-08.md`). `origin/main @ 25c8ca7` compiles
clean (32 pp, 0 undefined refs). What remains are the referee/author-decision
flags the implementation deliberately did **not** invent numbers for — each needs
a value only the author or the pipeline can supply.

## Task(s)

| # | Open item | Kind | Status |
|---|-----------|------|--------|
| 1 | **B3** — exact DSA-110 trial count | pipeline number | 📋 open |
| 2 | **B7** — galaxy-search aperture wording ↔ actual pipeline aperture | pipeline number + prose | 📋 open |
| 3 | **Fiducial DM priors** (+ coupled `DM_host` headline acceptance) | author physical call | 📋 open |
| 4 | minor-9 ↔ F1 opening-prose consistency | carry-forward note | 📋 watch |

**Workflow Phase:** Validate / author review.

## Critical References

- `scripts/dm_budget_uncertainty.py` — B1/B2 forward model; **all prior values live at lines 60–70**. Rerun `python3 scripts/dm_budget_uncertainty.py` after any prior change → regenerates `scripts/dm_budget_uncertainty.csv` + `figures/dm_host_posteriors.{pdf,png}`.
- `sections/appendix.tex` — Appendix C prior list (lines ~80–95) and `tab:host-forward-model`; the prose mirror of the script priors.
- `sections/toa.tex` — B3 trials paragraph, lines ~66–79.
- `sections/observations.tex` — B7 aperture prose, lines ~115–124.

---

## Item 1 — B3: exact DSA-110 trial count

**Where:** `sections/toa.tex` ~L66–79 (the `\sum_j \mu_j` "trial set" paragraph).

**Current state:** the look-elsewhere denominator is stated only by order of
magnitude — *"the entire DSA-110 detection list — of order $10^{2}$–$10^{3}$
events across the two-year window"*, giving $\sum_j\mu_j\lesssim10^{-5}$ with
per-event $\mu_j\sim5\times10^{-9}$.

**Needed:** the **precise number of independent DSA-110 triggers searched for a
CHIME/FRB counterpart** over the 2022-Feb–2024-Feb overlap (the trial-set
denominator, not the 12 matches). Replace "$10^{2}$–$10^{3}$" with the actual
count.

**Note:** conclusion is already insensitive — the bound holds for any count
$\lesssim10^{3}$ — so this is a rigor/completeness fix, not a result change. Pull
the count from the DSA-110 trigger database for the overlap window.

## Item 2 — B7: galaxy-search aperture

**Where:** `sections/observations.tex` ~L115–124 (census completeness paragraph).

**Current state:** galaxy cones "extend to a fixed proper impact parameter at the
circumgalactic scale"; *recovered* galaxies span $b\approx60$–$280\,\mathrm{kpc}$.
Clusters retained within $2R_{200}\approx3R_{500}$; only $<R_{500}$ crossings
enter the budget.

**Needed:** confirm the **fixed proper impact-parameter cut the census pipeline
actually applied** (the search aperture itself — the text quotes the recovered
*span*, not the aperture radius) and make the prose state it explicitly and
correctly. Check against the foreground-census code / `validation-sightline-halo-grid.md`.

## Item 3 — Fiducial DM priors (+ `DM_host` headline acceptance)

**Where:** `scripts/dm_budget_uncertainty.py` L60–70; mirrored in `sections/appendix.tex` L80–95.

**The fiducial values (each drives every posterior width and every $P(\mathrm{DM_{host}}<0)$):**

| Prior | Symbol / var | Fiducial value |
|-------|--------------|----------------|
| Macquart scatter | `F_LO, F_HI` | $F\sim\mathcal{U}[0.25,0.40]$ |
| Galactic disk (NE2025) | `SIGMA_DISK_FRAC` | 30% lognormal |
| Galactic halo | median 40, `HALO_SIGMA_LN=0.35` | 40 pc cm⁻³, factor-~2 ($2\sigma\approx[20,80]$) |
| Intervening CGM | `INT_SIGMA_LN` | measured 0.40 / assumed 0.69 / cluster 0.30 (dex-ish lognormal) |

**Needed (author call):**
1. Sign off on or revise these fiducials. If changed, rerun the one script — no other edits.
2. **Accept the headline `DM_host` change:** posterior medians run *higher* than the old mean-subtracted residuals (intended right-skew correction; Appendix C L93–94). Per the referee handoff, the two formerly-negative sightlines (**20220310F, 20221203A**) now read $P(\mathrm{DM_{host}}<0)\approx0.45$ — i.e. consistent-with-zero rather than negative. Confirm this framing is the desired headline.

Appendix C already flags these as "fiducial … documented so they can be revised" (L94–95), so revision needs no structural change.

## Item 4 — minor-9 ↔ F1 (carry-forward)

The de-processed opening prose (`intro`, `results`, `conclusions`) assumes the
withheld-slots **F1** plan. When the scattering / scintillation / energetics slots
are repopulated, keep the opening consistent with what actually gets stated. No
action now — a consistency guard for the next content pass.

## Verification State / Known-Broken

- Nothing broken. All four items are *additions of author-supplied values*, not bug fixes.
- Items 1–2 are one-line prose edits once the numbers are in hand; both land on `main` (Overleaf-synced) → mirror via Overleaf pull or edit in Overleaf, same discipline as the `\phantomsection` fix.
- Item 3 rerun changes `dm_budget_uncertainty.{csv}` + `figures/dm_host_posteriors.{pdf,png}` and the Appendix C table numbers — regenerate together if priors move.

## Action Items & Next Steps

1. [ ] Pull exact DSA-110 trial count → `toa.tex` L66–79 (Item 1).
2. [ ] Confirm census galaxy aperture → `observations.tex` L115–124 (Item 2).
3. [ ] Author sign-off / revision of fiducial priors; rerun `dm_budget_uncertainty.py` if changed (Item 3.1).
4. [ ] Confirm the `DM_host` right-skew headline + the two $P(<0)\approx0.45$ sightlines (Item 3.2).
5. [ ] Consistency guard when repopulating scattering/scint/energy slots (Item 4).

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` — close each author-decision flag against the manuscript once the numbers are supplied.

## Other Notes

- Closed this session (no action needed): all 11 new `bib/refs.bib` entries spot-checked against ADS; `James2022` corrected to the z-DM paper (MNRAS 509, 4775; stab3051; arXiv:2101.08005) and `Cook2023` to Amanda M. Cook / correct CHIME title — pushed as `25c8ca7`. `\phantomsection` Data-Availability fix on `main` (`1e2cb4c`).
- This handoff is **untracked** — commit it into the `docs/rse` lane when ready.

---

**Handoff created by AI Assistant on 2026-07-08**

---

## Follow-up evidence pass — 2026-07-08 09:07 PDT

Status: evidence gathered; no manuscript prose changed because the missing values
are still not proven to manuscript standard.

### B3 trial count

Local search did **not** find the requested full DSA-110 trigger denominator.
Checked surfaces included:

- `pipeline/analysis/chance-coincidence/{bursts.json,inputs.py,run.py}` — only
  the 12 reported pairs; `run.py` reports `sum_mu` across those 12, not the full
  trial set.
- Local data and Drive/iCloud mirrors under `~/Data/Faber2026/dsa110/` and
  `~/Library/Mobile Documents/com~apple~CloudDocs/Research/CHIME_DSA_Codetections/`.
- Imported co-detection sheets in `~/Developer/scratch/2026-06/_downloads-import/`.
  These give 12 accepted pairs plus rejected/no-baseband candidate rows
  (`gertrude`, `pingu`, `FRB20220912A2`), but they are **not** the full DSA
  trigger denominator requested here.
- Local Python env `py312` has no `dsautils`, `realfast`, `psycopg`, `psycopg2`,
  or `pymongo`; no local DSA database client/config was found.

Conclusion: Item 1 still needs a live DSA trigger database query or an author-
supplied count. Do not substitute 12, 15, or the imported candidate-sheet row
count for the denominator.

### B7 aperture

Two distinct foreground surfaces are now identified:

- Current reproducible live-search code:
  `pipeline/galaxies/foreground/config.py` sets
  `DEFAULT_IMPACT_KPC = 100.0`, `DEFAULT_CLUSTER_IMPACT_KPC = 5000.0`, and
  `CLUSTER_R200_FACTOR = 2.0`; `pipeline/docs/rse/specs/reproducibility-foreground-galaxies.md`
  repeats the 100 kpc galaxy / 5000 kpc cluster defaults.
- Frozen manuscript census:
  `pipeline/galaxies/foreground/data/intervening_census_registry.csv` has 34
  `halo` rows spanning `b=12.2`--`281.4 kpc` and 15 `cluster` rows spanning
  `b=603.6`--`5690.0 kpc`. The old spreadsheet-normalization path in
  `~/Developer/scratch/worktrees/flits-ssot-regen/scratch/codetection/` parses
  those listed impacts but does not record the original query aperture. The
  canonical FLITS `scratch/codetection/why_missed.csv` explicitly flags many
  frozen halo rows as `impact_gt_100`, confirming the 100 kpc replay gate would
  not recover the frozen manuscript census.
- The budget gate is also not a 100 kpc impact cut: among the 34 frozen `halo`
  rows, `budget_eligible=True` has 14 rows spanning `b=101.7`--`242.7 kpc`,
  while `budget_eligible=False` has 20 rows spanning `b=12.2`--`281.4 kpc`.
  All four halo rows with `b<100 kpc` are budget-ineligible, and all
  budget-eligible halo rows are beyond 100 kpc. The eligible rows are therefore
  selected by object-level confirmation/provenance columns such as
  `final_verdict`, `classification`, and `best_z_source`, not by the live
  `DEFAULT_IMPACT_KPC` gate.

Conclusion: the manuscript must not simply state "100 kpc" for the frozen
galaxy/halo census unless the author intentionally changes the manuscript to
describe the newer live-search replay rather than the frozen 49-object census.
For the frozen census, the budget-eligible halo envelope reaches 242.7 kpc and
the retained near-miss/ineligible halo envelope reaches 281.4 kpc. A hard
100 kpc statement would be wrong both as a frozen-census aperture and as a
budget-eligibility rule.

### Fiducial DM priors

Script/prose mirror is internally consistent:

- `scripts/dm_budget_uncertainty.py` still uses `F_LO,F_HI = 0.25,0.40`,
  `SIGMA_DISK_FRAC = 0.30`, `HALO_SIGMA_LN = 0.35`, and
  `INT_SIGMA_LN = {"measured": 0.40, "assumed": 0.69, "cluster": 0.30}`.
- `sections/appendix.tex` mirrors those priors and says they are fiducial and
  revisable.
- `scripts/dm_budget_uncertainty.csv` and Appendix C agree that
  `FRB 20220310F` has `P(DM_host<0)=0.453` / table `0.45`, and
  `FRB 20221203A` has `0.456` / table `0.46`.

Conclusion: no regeneration is needed unless the author revises priors or the
headline framing.
