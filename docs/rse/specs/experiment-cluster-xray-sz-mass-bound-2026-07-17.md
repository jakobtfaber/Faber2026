# Experiment record: X-ray/SZ upper-limit mass bound for J115120.4+714435 (Kulkarni S1) — results

---
**Date:** 2026-07-17
**Author:** AI Assistant
**Status:** ADJUDICATED (owner, 2026-07-17, this session): **constraining, conservative endpoint** — corrected-intent threshold (registry mass $10^{14.17}$ + 0.2 dex = $10^{14.37}$) adopted; quoted limit is the worst-case-ECF $M_{500}\le1.7\times10^{14}\,M_\odot$. Derived bracket via the truncated-mass-prior MC in `scripts/dm_budget_uncertainty.py` (seed 20260707): β-model 95% CI [84, 328] pc cm$^{-3}$ (untruncated control reproduces [96, 563] ≈ the published 100–560); prose quotes ≈80–330, factor ~4. Landed via `ms/s1-xray-mass-cap-20260717`.
**Plan:** [plan-cluster-xray-sz-mass-bound-2026-07-17.md](plan-cluster-xray-sz-mass-bound-2026-07-17.md) (owner-sanctioned 2026-07-17, this session)

---

## Headline

The **RASS X-ray non-detection independently caps the cluster mass at
essentially the catalog value**: $M_{500}^{\rm UL,X} = 1.3$–$1.7\times10^{14}\,M_\odot$
($\log M = 14.12$–$14.22$, ECF systematic band), against the registry's adopted
$M_{500}=1.48\times10^{14}$ ($\log M = 14.17$). The SZ limb is a clean null
(Planck PSZ2 is blind below $2.5\times10^{14}$ at $z\approx0.2$). The X-ray cap
**excludes the $+0.2$ dex mass upper tail** ($\log M = 14.37$) that generates
the 560 pc cm$^{-3}$ end of the current column bracket — under the corrected
central mass. Whether the frozen rule fires "constraining" depends on two
ambiguities discovered at application time (below); adjudication is the owner's.

## Phase 0 — availability & non-detection (confirmed)

- Position RA 177.835°, Dec +71.743° → galactic $l=129.48°$, $b=+44.61°$.
- **eROSITA eRASS1 DR1: OUT of footprint** (RU half; no public release). As
  predeclared, the X-ray limb rests on RASS.
- `ClusterEngine().query()` (PSZ2 + MCXC + MCXC-II via Vizier): **empty at 10′
  and 30′** — the non-detection premise holds.
- No 1RXS (BSC or FSC) source within 6′ of the cluster — clean field, no
  confusion.

## Phase 1 — SZ limb (null)

Empirical PSZ2 detection floor from the catalog itself (Vizier
`J/A+A/594/A27/psz2`, $0.15<z<0.25$): all-sky $n=279$, minimum detected
$M_{\rm SZ} = 2.51\times10^{14}$, p5 $=3.16\times10^{14}$, median
$4.34\times10^{14}$ (restricting to $|b|>30°$ changes nothing). The survey is
blind to a $\approx1.5\times10^{14}$ cluster at $z=0.2$:
$M_{500}^{\rm UL,SZ}\gtrsim2.5\times10^{14}$ — **not constraining** (as the
plan's risk assessment anticipated).

## Phase 2 — X-ray limb (the result)

- **Local exposure** (ExpTime of 1RXS neighbours within 3°; BSC n=18, FSC
  n=106): p10/p50/p90 = 689/759/874 s. Conservative adoption: 689 s.
- **Aperture photometry** on the SkyView `RASS-Cnt Broad` (0.1–2.4 keV) cutout:
  $\theta_{500}=3.57'$ aperture at the cluster position, background annulus
  2–4 $\theta_{500}$; aperture counts 195 vs background-predicted 211 (excess
  $-16.5$, i.e. consistent with pure background); 3σ upper limit 45.5 counts →
  **rate UL = 0.066 ct/s** (conservative composite: 3σ counts at p10 exposure).
  Consistency: faintest local BSC detection is 0.054 ct/s; FSC point-source
  floor 0.007–0.010 ct/s (extended-source sensitivity is worse, so 0.066 is a
  defensible one-sided bound). Caveat: SkyView resampling is not
  flux-conserving; the Poisson σ on resampled counts over-estimates, making the
  UL conservative (larger), not optimistic.
- **Flux → $L_X$:** ECF (PSPC, 0.1–2.4 keV, $T\sim2$ keV, high-lat
  $N_H\approx1.3\times10^{20}$): $1.0\times10^{-11}$ (erg cm$^{-2}$ s$^{-1}$)/(ct/s),
  band $\pm20\%$. FlatΛCDM $H_0=70$, $\Omega_m=0.3$; $z=0.200$.
- **$L_X$–$M_{500}$ inversion:** mapping recovered by regression on the MCXC
  catalog itself (`J/A+A/534/A109/mcxc`; $\log(M E(z)^{2/5})$ vs
  $\log(L/E(z)^{7/3})$): slope $0.619$ (≡ the known REXCESS $1/1.64=0.610$),
  round-trip median error **1.9%**, p95 7.1% — passes the plan's <15% gate.

| ECF | $L_X$ UL (erg/s) | $M_{500}^{\rm UL,X}$ | $\log M$ |
|---|---|---|---|
| $0.8\times10^{-11}$ | $6.1\times10^{43}$ | $1.30\times10^{14}$ | 14.115 |
| $1.0\times10^{-11}$ (central) | $7.6\times10^{43}$ | $1.50\times10^{14}$ | **14.175** |
| $1.2\times10^{-11}$ (worst) | $9.1\times10^{43}$ | $1.67\times10^{14}$ | 14.224 |

## Phase 3 — DM propagation (mNFW, production path)

Anchor: `dm_cluster_mnfw_model` with the **registry input**
$M_{500}=1.48\times10^{14}$, $z=0.200$, $b=603.6$ kpc reproduces the carried
column (≈183 vs the appendix's ≈184 pc cm$^{-3}$) — the 162.7 obtained with the
prose-rounded $10^{14.1}$ exposed that the prose "$\log M_{500}=14.1$" is a
**rounding of the registry's 14.17**, resolved in the pipeline's single source
of truth (`intervening_census_registry.csv:23`, `m500_1e14msun = 1.48`).

- DM$_{\rm mNFW}(M_{500}^{\rm UL}$, central ECF$)$ = 185 pc cm$^{-3}$
- DM$_{\rm mNFW}(M_{500}^{\rm UL}$, worst ECF$)$ = 201 pc cm$^{-3}$
- Frozen-rule DM condition (≤500): **passes** at every ECF endpoint.
- Effect on the prose bracket high end (β-model + high $f_{\rm gas}$ stack,
  DM ∝ $M^{\approx0.72}$ at fixed $b$): capping the mass at the worst-case
  $1.67\times10^{14}$ instead of the $+0.2$ dex tail $2.34\times10^{14}$ trims
  **560 → ≈440**; central ECF gives **≈410**. Bracket becomes ≈100–440
  (factor ~4.2) instead of 100–560 (factor ~5.6).

## Phase 4 — frozen rule application: GATE-EDGE, two discovered ambiguities

The plan froze: *constraining iff $M_{500}^{\rm UL} < M_{\rm rich}^{+}$ by
≥0.1 dex AND DM(UL) ≤ 500*, with $M_{\rm rich}^{+}$ written as $10^{14.3}$.

**Ambiguity A — the rule's threshold was computed from rounded prose.** The
plan set $M_{\rm rich}=10^{14.1}$ from `results.tex`; the actual pipeline input
is $10^{14.17}$ ($1.48\times10^{14}$), making the intended "+0.2 dex tail"
$10^{14.37}$ and the intended margin threshold $10^{14.27}$, not $10^{14.2}$.

**Ambiguity B — which ECF endpoint consumes the rule.** The plan specified a
single derivation with systematics reported, but did not pin whether the rule
tests the central or worst-case endpoint.

| Reading | Threshold | central-ECF UL (14.175) | worst-ECF UL (14.224) |
|---|---|---|---|
| Literal (rounded prose) | ≤14.20 | **constraining** | null (misses by 0.02 dex) |
| Corrected intent (registry mass) | ≤14.27 | **constraining** | **constraining** (0.15 dex below tail) |

Under the corrected central mass the result is constraining at **every** ECF
endpoint; under the literal-but-erroneous threshold it is constraining only at
the central ECF. Per CONTEXT.md discipline, moving a frozen gate after data
inspection — even to correct an input rounding — is not the agent's call.
**Owner adjudication required.** Both branches were journaled; no prose has
been touched.

## If adjudicated constraining — proposed prose (draft, NOT applied)

`sections/results.tex` (`sec:dominant-systems`): replace the bracket sentence's
high end with the X-ray-capped value, e.g. "…spans
$\approx100$–$440\,\mathrm{pc\,cm^{-3}}$, with the upper end capped by the
ROSAT All-Sky Survey non-detection ($L_X < 9\times10^{43}$ erg s$^{-1}$,
0.1–2.4 keV, implying $M_{500}\lesssim1.7\times10^{14}\,M_\odot$ through the
MCXC $L$–$M$ relation), a factor of $\sim$4 end to end…"; mirror in the
`fig:clusters_icm` caption. Sub-$\pm3\%$ geometry systematic unchanged.
Consistency-audit anchors for "100--560" and "factor of $\sim$6" must be
updated in the same change.

## Reproducibility

- Scripts: scratchpad `s1/rass_limit.py`, `s1/harden_and_phase3.py` (session
  0acc6eea); to be landed as `pipeline/analysis/cluster_mass_bound/` with tests
  per the plan once the verdict is adjudicated (submodule currently carries the
  live joint-tf lane's working-tree state — landing deferred deliberately).
- Queries: Vizier `J/A+A/594/A27/psz2`, `IX/10A/1rxs`, `IX/29/rass_fsc`,
  `J/A+A/534/A109/mcxc`; SkyView `RASS-Cnt Broad` 1° cutout.
- Cosmology FlatΛCDM(70, 0.3); ECF band (0.8–1.2)$\times10^{-11}$; registry
  mass source `pipeline/galaxies/foreground/data/intervening_census_registry.csv:23`.
- Catalog (`WenHan2024` bib key) mass $1.48\times10^{14}\,M_\odot$, $R_{500}=729$ kpc,
  $b=603.6$ kpc, $b/R_{500}=0.83$, $z=0.200$ (DESI spec).

---

**Verdict: gate-edge; owner adjudication pending. SZ: null. X-ray: caps
$M_{500}$ at ≈ the catalog value, excludes the +0.2 dex tail under the
corrected-intent reading.**
