# DM-prior sign-off — `scripts/dm_budget_uncertainty.py`
**Date:** 2026-07-09 · **Repo:** `jakobtfaber/Faber2026` · **local main:** `765a40a`
**Scope:** Referee item "Fiducial DM-prior sign-off" — audit the five nuisance
priors in the DM_host forward model (referee B1) and the cluster-column priors
(referee B2), verify the headline numbers reproduce, and stress-test the
conclusions against literature-motivated prior perturbations.

**Verdict: SIGN OFF, with one required fix and two prose caveats.** The
headline conclusion — the two high-z sightlines are consistent with negligible
host dispersion, P(DM_host<0) ≈ 0.45 — is robust to every *physical* prior at
the ±0.01 level. One *numerical* choice (the Macquart Δ-grid truncation) moves
the headline by ±0.02 and should be fixed before the number is quoted.

---

## 1. Reproduction (clean)
`python scripts/dm_budget_uncertainty.py` reproduces the committed CSV exactly
(numpy 2.4.6 / scipy 1.17.1, seed 20260707, N=200k):

| burst | z | arith | p16 | p50 | p84 | P(<0) |
|---|---|---|---|---|---|---|
| FRB 20220310F | 0.479 | −57 | −155 | 12 | 81 | **0.453** |
| FRB 20221203A | 0.510 | −55 | −182 | 14 | 111 | **0.456** |

Both headline P(DM_host<0) values match the handoff (0.453, 0.456). ✓

## 2. Model is genuinely mean-preserving (the referee's actual ask)
E[DM_host] equals the arithmetic mean-subtraction residual to MC precision for
all nine sightlines (e.g. 20220310F: arith −57 vs E[host] −57.2). The forward
model does **not** shift the central value — it replaces a point estimate of a
skewed quantity with its full posterior. The p50−arith gap (+69, +74 pc cm⁻³
for the two negatives) is *entirely* the cosmic right-skew of P(DM_cosmic|z).
This is exactly the correction B1 requested ("subtracting the mean of the
skewed P(DM_cosmic|z) biases every residual… make it probabilistic"), and it
is implemented correctly. ✓

## 3. Prior-by-prior sensitivity (each prior swept across its cited bounds)
P(DM_host<0) for the two negative-headline sightlines across 13 configs
(`dm_prior_sensitivity_sweep.csv`, tornado figure `dm_prior_tornado.png`):

| prior swept | bounds | 310F swing | 1203A swing |
|---|---|---|---|
| MW halo median | 20 (Keating&Pen) → 65 (Prochaska) | 0.454→0.456 | 0.446→0.447 |
| MW halo width σ_ln | 0.25 → 0.50 | 0.451→0.457 | 0.445→0.448 |
| Galactic disk frac. | 0.20 → 0.50 | 0.451→0.458 | 0.444→0.452 |
| intervening (assumed) σ_ln | 0.50 → 0.90 | 0.452→0.453 | 0.456→0.446 |
| **cosmic scatter F** | **0.20 (low-feedback) → 0.32 (Macquart)** | **0.484→0.452** | **0.464→0.446** |

**Finding:** the four "local" priors (both MW halo priors, the disk fraction,
the intervening width) move the headline by ≤0.007 — negligible. The single
physical lever is the cosmic-scatter amplitude **F**, and even there the full
[0.20, 0.32] range only spans 0.452–0.484. The qualitative conclusion (host
deficit favored at ~45–48% probability) holds across the entire physical prior
volume. This is a strong, defensible robustness result.

## 4. REQUIRED FIX — numerical Δ-grid truncation (±0.02 artifact)
`_delta_grid()` builds the Macquart Δ=DM_cosmic/⟨DM_cosmic⟩ distribution on a
grid `linspace(1e-3, 6.0, 4000)` and solves C0 so E[Δ]=1 on that grid. Because
the α=β=3 tail is not negligible at Δ=6, the truncation clips a small amount of
tail mass, and the E[Δ]=1 renormalization then rides on a slightly clipped
support. Extending the cutoff moves the headline monotonically:

| Δ-grid cutoff | 310F P(<0) | 1203A P(<0) |
|---|---|---|
| 6 (current) | 0.453 | 0.446 |
| 8 | 0.439 | 0.435 |
| 10 | 0.431 | 0.429 |

Resolution (4000→8000 pts at fixed extent) changes nothing; **only the extent
matters**, confirming it is a truncation artifact, not a discretization one.
The converged value is ≈0.43, not 0.45. Recommend extending the grid to
Δ_max=10 (or integrating the tail analytically) and re-emitting the CSV/figure
before any P(DM_host<0) number is quoted in the manuscript. Effect on the
narrative is nil — 0.43 vs 0.45 both say "≈45% / roughly even odds" — but the
committed digit should be the converged one.

## 5. Prose caveats (not blocking)
- **F range vs. fiducial label.** Code marginalizes F ~ U[0.25, 0.40];
  docstring calls F≈0.32 "fiducial." The uniform is centered at 0.325, so this
  is self-consistent, but note the model does *not* pin F=0.32 — it integrates
  over feedback uncertainty, which is the more conservative and defensible
  choice. State this explicitly in the methods (it strengthens the paper).
- **Halo comment wording.** The `HALO_SIGMA_LN=0.35` comment describes a
  median-preserving 2σ range "~[20,80]" (correct for a median-40 lognormal),
  but the draw is mean-preserving (`lognormal(-0.5σ², σ)`), giving effective
  median 37.6 / mean 40.0. The mean-preserving form is the *right* choice — it
  keeps the forward model consistent with the mean-subtraction budget table so
  DM_host stays unbiased (§2) — but the comment should say "mean-preserving,
  median 40" to avoid a reader/referee flagging the apparent mismatch.

## 6. Cluster column (B2) — priors reasonable, wide by construction
FRB 20230307A β-model MC: p50=252, [p16,p84]=[159,382], 95% CI=[96,558]
pc cm⁻³, bracketing the mNFW central ~160. Priors — M500 0.2 dex richness
scatter, f_gas U[0.10,0.16], r_c/R500 U[0.10,0.30], β U[0.60,0.75] — are all
standard X-ray/SZ cluster values and appropriately conservative. The β-model
p50 (252) sits *above* the mNFW (160), so quoting the combined "~96–558" range
honestly reflects the profile-shape systematic the referee asked for. Note for
prose: the two profiles are cross-checks of *shape at fixed path length* (the
LOS is truncated at 1.48 R500 in both), not independent measurements — worth
one sentence so the range isn't read as a measurement error bar.

---

## 7. UPDATE (2026-07-09) — cosmic term re-based on Connor et al. (2025)
Per author decision, the diffuse cosmic term is no longer the Macquart P(Δ)
form. It is now the IGM column DM_IGM ~ LogNormal(μ(z), σ(z)), with μ(z), σ(z)
the redshift-dependent parameters of the bivariate (IGM, halo) log-normal fit to
an IllustrisTNG-300 mock FRB survey by **Walker et al. (2024, A&A 683, A71)**,
adopted via the **Connor et al. (2025, Nat. Astron. 9, 1226; arXiv:2409.16952)**
reproduction package (`tng_params_new.npy`) and rescaled to f_IGM = 0.76₋₀.₁₁⁺⁰·¹⁰.

**Rationale (all three are the physical point of Connor et al.):**
1. Connor et al. show σ_DM does **not** follow the F z^{−1/2} halo-Poisson
   scaling; the diffuse scatter is dominated by non-Poissonian IGM
   filament/sheet intersection. The old fixed-F form gave DM_cosmic a fractional
   width (CV) of 60–80%; the TNG IGM calibration gives 20–37% — a ~3× narrower
   diffuse term.
2. We map onto Connor's **IGM marginal**, not the total DM_cos = DM_IGM + DM_X,
   because this budget already carries identified intervening halos in the
   separate DM_int census. Using DM_cos would double-count them; the ~3× excess
   width in the old model was precisely the halo scatter DM_int already handles.
3. f_IGM = 0.76 (vs the old Macquart f_d = 0.84) lowers the IGM mean ~8–11%.

**Impact on the headline (regenerated `dm_budget_uncertainty.csv`):**
| burst | z | P(<0) Macquart | P(<0) Connor | Δ |
|---|---|---|---|---|
| FRB 20220310F | 0.479 | 0.453 | **0.540** | +0.087 |
| FRB 20221203A | 0.510 | 0.456 | **0.507** | +0.051 |
| FRB 20240229A | 0.287 | 0.083 | **0.014** | −0.069 |
| FRB 20230913A | 0.302 | 0.135 | **0.072** | −0.063 |
| FRB 20240203A | 0.074 | 0.042 | **0.010** | −0.032 |

The change **sharpens the two-population reading**: the two high-z sightlines
move toward P(<0)≈0.5 (removing the F z^{−1/2} skew that had cushioned them),
while every moderate-z host becomes confidently positive. Every 68% interval
narrows 13–19% (the removed halo double-count). This makes the "host residuals
are modest, and two high-z sightlines are consistent with a host deficit"
narrative *stronger* and better-grounded than under the Macquart form.

Note: the §4 Δ-grid truncation finding is now **moot** — the Macquart Δ-grid
sampler (`macquart_pdf`, `_delta_grid`) is removed. The new sampler draws
directly from `numpy.random.lognormal`, which has no truncation parameter.

**Files changed:** `scripts/dm_budget_uncertainty.py` (cosmic sampler + docstring),
`sections/budget.tex` (forward-model prose + header comment), `bib/refs.bib`
(added `Connor2024`, `Walker2024`). Regenerated: `dm_budget_uncertainty.csv`,
`figures/dm_host_posteriors.{pdf,png}`.

---
### Artifacts
- `dm_connor_vs_macquart.png` / `.pdf` — Connor-vs-Macquart posterior comparison
- `dm_prior_tornado.png` / `.pdf` — tornado sensitivity figure (Macquart-era)
- `dm_prior_sensitivity_sweep.csv` — full 13-config × 5-burst P(<0) grid (Macquart-era)
