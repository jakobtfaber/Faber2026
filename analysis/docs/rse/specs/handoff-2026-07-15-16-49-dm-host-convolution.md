# Handoff: Deterministic DM-host convolution and updated foreground census

---
**Date:** 2026-07-15 16:49 PDT
**Author:** AI Assistant
**Status:** Handoff — scoped implementation validated, merged, and reproduced; manuscript-wide submission readiness remains open
**Branch:** `docs/dm-host-convolution-handoff-20260715`
**Commit:** `0f96f1d37e25cd349991130e089fb2f4db79c8b0` (branch point; current `origin/main` at handoff creation)

---

## Task(s)

The immediate task was to replace the sampling/KDE construction of the nine
redshift-constrained host-DM posteriors with direct propagation of the component
probability densities, while incorporating the current per-system foreground
census and preserving the manuscript's observer/rest-frame and census-completeness
semantics.

| Task | Status | Notes |
|------|--------|-------|
| Determine whether the published host-DM curves were convolutions | ✅ Complete | They were previously sampled by Monte Carlo and smoothed; the current products are direct numerical PDFs. |
| Define the replacement probability model | ✅ Complete | Quoted MW-disk, MW-halo, and individual intervening columns are lognormal medians; the IGM PDF is marginalized over the asymmetric clipped `f_IGM` prior. |
| Implement deterministic convolution | ✅ Complete | Full FFT convolution on a `0.1 pc cm^-3` grid; no sampling or KDE enters the published host products. |
| Join the current foreground census at per-system resolution | ✅ Complete | Every nonzero foreground contribution is represented by its own independent PDF before convolution. |
| Regenerate manuscript data, table, and figure | ✅ Complete | CSV, root budget table, appendix table/text, PNG, and PDF were regenerated and checked. |
| Validate against an independent Monte Carlo oracle | ✅ Complete | Maximum quantile difference `0.313 pc cm^-3`; maximum `P(DM_host<0)` difference `0.0008` for 500,000 draws per sightline. |
| Integrate and publish | ✅ Complete | FLITS PR #188 and Faber2026 PR #98 are merged; subsequent PR #99 is also present on current `main`. |
| Certify the entire manuscript as collaborator/journal ready | 📋 Planned | This scoped DM-host lane is ready to circulate, but provisional redshifts, incomplete foreground coverage, and other provisional analysis lanes prevent a manuscript-wide certification. |

**Current Workflow Phase:** Validate/closeout for the DM-host convolution; Research/triage for the next manuscript-wide scientific gate.

## Workflow Artifacts

**Research Documents:**

- [research-dm-host-convolution.md](research-dm-host-convolution.md) — method choice, prior semantics, and deterministic-convolution design.
- [research-dm-igm-pdf-connor2024.md](research-dm-igm-pdf-connor2024.md) — provenance and interpretation of the TNG/Connor IGM calibration.
- [research-v4-census-gap-extension.md](research-v4-census-gap-extension.md) — discovery-to-validation foreground-census gaps that motivated refreshing the inputs.

**Plan Documents:**

- [plan-dm-host-convolution.md](plan-dm-host-convolution.md) — approved implementation and validation plan.
- [plan-v4-census-gap-extension.md](plan-v4-census-gap-extension.md) — foreground-census extension plan and adjudication boundaries.

**Implementation Summary:**

- [implement-dm-host-convolution.md](implement-dm-host-convolution.md) — numerical method, canonical environment, input/output hashes, and exact regeneration commands.

**Validation Reports:**

- [validation-dm-host-convolution.md](validation-dm-host-convolution.md) — numerical oracle, convergence, full-suite, manuscript-build, rendering, and clean-worktree evidence.
- [validation-v4-census-gap-extension.md](validation-v4-census-gap-extension.md) — current census-gap decisions and limitations.

## Critical References

Read these first before changing or interpreting this analysis:

- `docs/rse/specs/validation-dm-host-convolution.md` — concise statement of what was actually verified, including the clean-worktree reproduction and remaining manuscript-wide caveats.
- `scripts/dm_budget_uncertainty.py` — authoritative host-DM engine, model assumptions, direct PDF construction, Monte Carlo oracle, and output generation.
- `sections/appendix.tex:195` — table and figure interpretation, including observer/rest frames, provisional-redshift notes, and the six census-incomplete upper limits.

## Recent Changes

- `scripts/dm_budget_uncertainty.py:1` — documents the IGM marginal, foreground/host identity, frame convention, and direct-PDF figure semantics.
- `scripts/dm_budget_uncertainty.py:78` — freezes the cluster beta-model RNG (`20260707`) and the deterministic numerical controls (`dx=0.1`, tail mass `1e-10`, quadrature order 64).
- `scripts/dm_budget_uncertainty.py:140` — preserves the six census-incomplete sightlines as host-DM upper limits.
- `scripts/dm_budget_uncertainty.py:295` — defines lognormal component PDFs with the quoted point value as the median.
- `scripts/dm_budget_uncertainty.py:322` — marginalizes the IGM lognormal over the split asymmetric `f_IGM` prior with Gauss--Legendre quadrature and analytic clipped-endpoint masses.
- `scripts/dm_budget_uncertainty.py:367` — performs unit-preserving full FFT convolution of independent PDFs.
- `scripts/dm_budget_uncertainty.py:410` — loads the current individual intervening systems and fails closed on roster/budget mismatches.
- `scripts/dm_budget_uncertainty.py:475` — builds the observer-frame host PDF by convolving disk, halo, IGM, and each individual foreground system, then reflects about exact observed DM and rescales quantiles to the rest frame.
- `scripts/dm_budget_uncertainty.py:515` — retains Monte Carlo only as an independent validation oracle, not as a publication path.
- `sections/appendix.tex:195` — publishes the nine observer/rest-frame intervals and negative-host probabilities; rows 20221203A, 20230913A, and 20240203A carry provisional-redshift note `r`.
- `sections/appendix.tex:227` — explains every plotted direct component PDF, the convolved intervening PDF, and the six upper-limit daggers.

The implementation was merged through Faber2026 PR #98 (merge
`8a2c2eff412fb20ab929f5d965b1641aaee2dfc2`; implementation head
`9a27f154e04f48eb15661851600a14d536721112`). The corresponding FLITS work was
merged through PR #188 (merge `af78543d4747d339b9f13283b4b8528c91a71cb3`;
implementation head `90d8f2dadb36c2cbcd6caf2cbe0919797a577ff0`). Current parent `main` is
`0f96f1d37e25cd349991130e089fb2f4db79c8b0`, which also includes subsequent
provisional-propagation provenance PR #99; do not undo those integrated semantics.

## Reproducibility & Data State

- **Seeds:** cluster beta-model uses `np.random.default_rng(20260707)`; the independent 500,000-draw host oracle uses `20260715 + sightline_index`.
- **Environment:** canonical clean runtime is `/Users/jakobfaber/.conda/envs/flits/bin/python`, Python 3.12.13, NumPy 2.4.6, SciPy 1.17.1, Matplotlib 3.10.8. Use the clean launcher below; inherited interactive PATH can make a bare `conda run -n flits python` resolve the base interpreter.
- **Submodule:** parent pins `pipeline/` at FLITS `af78543d4747d339b9f13283b4b8528c91a71cb3` (detached HEAD is expected).
- **In-flight jobs:** none were launched or left running for this work.

Canonical launcher:

```sh
env -i HOME="/Users/jakobfaber" \
  PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  /opt/anaconda3/bin/conda run -n flits \
  python scripts/dm_budget_uncertainty.py
```

Authoritative inputs and current SHA-256 values:

| Input | SHA-256 |
|---|---|
| `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv` | `86f631aaedefc6a37571360b718589e864d80c05c7864ac1e4c21661367a11c8` |
| `pipeline/galaxies/foreground/budget_table_data.json` | `d5dd5e2a2959be55773f69ef54be4eb494346c6868e316f91e02e7218b10a272` |
| `scripts/dm_budget_intervening_systems.csv` | `8a50fd78c48c61c0ba08ca348710100e7c1840893c68318b186de7e915ec4376` |

Reproduced outputs:

| Output | SHA-256 |
|---|---|
| `scripts/dm_budget_uncertainty.csv` | `5cee3a81ad94b02b5f22bd2e3ffaff277a403d798f7a50aaf983bee07b8e29ff` |
| `budget_table.tex` | `e4b3d43e6ec58666809903f6bbbef4b89e5f08c04e35386e1cdc8fccafdc2b86` |
| `figures/dm_host_posteriors.png` | `89fb8d49144ede86b53ea850ec088b13be935ffed5636742e01da64c266f991d` |

The current observer-frame summaries are:

| Sightline | p16 | p50 | p84 | `P(DM_host<0)` |
|---|---:|---:|---:|---:|
| FRB 20220207C | 83 | 115 | 141 | 0.002 |
| FRB 20220310F | -116 | -10 | 77 | 0.540 |
| FRB 20220506D | -39 | 42 | 108 | 0.293 |
| FRB 20221113A | 16 | 90 | 149 | 0.118 |
| FRB 20221203A | -40 | 73 | 166 | 0.254 |
| FRB 20230307A | -29 | 69 | 150 | 0.236 |
| FRB 20230913A | 90 | 171 | 236 | 0.030 |
| FRB 20240203A | 33 | 72 | 105 | 0.045 |
| FRB 20240229A | -20 | 66 | 136 | 0.217 |

The cluster beta-model bracket remains a separately seeded Monte Carlo result:
p16/p50/p84 = `159/254/384 pc cm^-3`, with 95% interval `96--563`; the current
mNFW census point is approximately `184 pc cm^-3`.

## Verification State / Known-Broken

> **Known-broken / unverified:** no known defect remains in the scoped DM-host
> convolution implementation, but this handoff does **not** certify the entire
> manuscript as journal-ready. Three internal host redshifts lack citable public
> provenance; six posteriors are upper limits because their foreground census is
> incomplete; other current-main propagation/scintillation lanes remain explicitly
> provisional. Regenerated PDF bytes are not deterministic because of metadata;
> numerical products and the PNG were reproduced exactly.

- **Tests:** 42 focused parent integration/provenance tests passed; the integrated full parent suite passed `97 passed, 1 xfailed`; 14 focused FLITS attribution/budget tests passed; Ruff passed. The grid, quadrature, normalization, analytic convolution, lognormal semantics, roster parity, rest-frame scaling, upper-limit roster, and independent MC-oracle checks all passed.
- **Manuscript:** `scripts/render_budget_table.py --check` passed byte-exactly. Forced `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex` passed and produced a 54-page PDF. Rendered pages 33 and 34 were inspected directly for table/figure legibility and semantics.
- **Clean reproduction:** a fresh detached worktree at integrated commit `d63aacc4`, with the FLITS pin initialized at `af78543d`, reproduced the CSV, root budget table, and PNG hashes exactly.
- **Uncommitted / unpushed at handoff creation:** this new handoff is the only task-scoped change. The separate untracked draft `docs/rse/specs/handoff-2026-07-15-16-44-dm-host-budget-clarify.md` belongs to the superseded pre-convolution review lane and was deliberately not edited, staged, or included. The concurrent provisional-propagation handoff was published independently on its own branch.
- **Unverified manuscript claims:** the provisional host redshifts for FRB 20221203A, FRB 20230913A, and FRB 20240203A still need citable provenance before submission. The WHL12-vs-Wen+Han-2024 identity/mass issue toward FRB 20230307A remains an adjudication/modeling question outside the standard galaxy-halo route.

## Learnings

- Convolution and Monte Carlo solve the same uncertainty-propagation problem when they encode the same independent priors. Here convolution is the production method because the one-dimensional additive PDFs are available directly; Monte Carlo is retained as an independent correctness oracle.
- The numerical-method change itself is negligible at manuscript precision. The visible median shifts come from correcting the prior definition so that quoted component values are lognormal medians, not from convolution being intrinsically different from Monte Carlo. The nine median shifts range from `-4.93` to `-17.39 pc cm^-3`.
- The IGM is a mixture distribution because `f_IGM` is uncertain. Splitting quadrature at the asymmetric prior's mode and carrying clipped endpoint mass analytically avoids sampling noise and preserves normalization.
- Individual foreground-system PDFs must be convolved independently. Applying one lognormal to the summed `DM_int` changes the implied uncertainty model and is no longer the live implementation.
- The host calculation is in the observer frame. Because rest-frame DM is a positive linear rescaling, its quantiles are exactly `(1+z)` times the unrounded observer-frame quantiles.
- A fresh worktree must initialize the submodule from that worktree. An empty `pipeline/` directory can cause `git -C pipeline rev-parse HEAD` to walk upward and misleadingly return the parent hash; verify the submodule directory and commit explicitly before claiming reproduction.
- Current `main` includes post-convolution provenance edits. Treat current source and TeX as authoritative rather than replaying an older handoff or branch verbatim.

## Action Items & Next Steps

1. [ ] Run `using-research-workflows` on current `main` to reassess the manuscript-wide scientific gates; keep the validated DM-host lane closed unless an input hash or foreground-census decision changes.
2. [ ] Resolve or cite the provisional internal redshifts for FRB 20221203A, FRB 20230913A, and FRB 20240203A; do not silently promote them to publication-grade values.
3. [ ] Complete the foreground-census extension/adjudication, especially the FRB 20230307A WHL12-vs-Wen+Han-2024 cluster-scale system. If any authoritative input changes, regenerate and re-run `validating-implementations` for this host-DM lane.
4. [ ] Audit the remaining provisional propagation/scintillation sections before making a manuscript-wide circulate/submit claim.
5. [ ] When reproducing, use the clean Conda launcher and verify the actual FLITS pin from within the initialized fresh worktree.

**Recommended Next Skill:** `using-research-workflows` to survey current `main` and select the next unresolved manuscript-wide science gate. If a foreground input changes, use `validating-implementations` to revalidate the deterministic host-DM artifacts.

## Other Notes

- The scoped host-DM products are suitable to circulate to collaborators with the upper-limit and provisional-redshift qualifications intact. They are not, by themselves, evidence that the whole manuscript is ready to submit.
- The old FLITS `pipeline/galaxies/foreground/dm_host_posterior.py` path is marked exploratory/superseded. The authoritative engine is the parent-repo `scripts/dm_budget_uncertainty.py`.
- Parent and FLITS PRs are merged and no long-running computation needs monitoring. The current FLITS detached HEAD at the pinned commit is normal submodule state.
- Never fold an incidental `pipeline/` gitlink change into a manuscript-only commit; the pin is a separately reviewed change.

---

**Handoff created by AI Assistant on 2026-07-15**
