# Memo: the FRB 20230307A rotation-measure budget needs an intervening-cluster term

**To:** the spectropolarimetry companion authors (Pandhi et al.)
**From:** Faber2026 (paper I) — prepared under the predeclared record
[`plan-rm-cluster-bfield-repartition-2026-07-17.md`](plan-rm-cluster-bfield-repartition-2026-07-17.md)
**Date:** 2026-07-17
**Status:** For discussion. Nothing in either manuscript changes until both
sides agree (the record's "both-owners gate"). Machine-readable backing:
`scripts/rm_cluster_repartition.json` (seeded, reproducible); figure:
`docs/rse/specs/thread1-figures/rm_repartition_sensitivity.pdf`.

---

## The seam in one paragraph

Your RM budget (eq. `eq:rm_comps`) decomposes RM_obs into ionosphere + Milky
Way + IGM + host, and for FRB 20230307A attributes essentially the entire
non-Galactic residual to the host: RM_host = −756 ± 15 rad m⁻²,
⟨B∥,host⟩ = −2.0 μG (Table `tb:host_props`). Paper I's foreground census,
however, finds this sightline crosses the cluster **J115120.4+714435**
(z = 0.200, DESI spec) at impact parameter b = 604 kpc = **0.83 R500**, and
carries an intracluster electron column of ≈184 pc cm⁻³ (observer frame;
95% systematic bracket 84–328) — now capped from above by a ROSAT All-Sky
Survey non-detection (M500 ≤ 1.7×10¹⁴ M☉; paper I §results + the S1
experiment record). A magnetized intracluster medium crossed at 0.83 R500
contributes to RM_obs, and every rad m⁻² assigned to it comes out of
RM_host.

## Why the zero-cluster assumption is not safe

The conversion is fixed by the census column alone:

RM_cl(observed) = 0.812 · ⟨B∥,cl⟩ · DM_cl(rest) / (1+z_cl)² =
**124.5 rad m⁻² per μG** of coherent field at the central column
(56.8–221.9 across the bracket).

Your quoted σ(RM_host) = 15 rad m⁻² is 9.29 rad m⁻² at the observer. So
neglecting the cluster term is equivalent to asserting
**|⟨B∥,cl⟩| < 0.04–0.16 μG** along the chord — an order of magnitude below
measured cluster-outskirt fields. Statistical RM studies through cluster
outskirts near 0.6–1.0 R500 measure (local values; ×1/1.44 at our z = 0.2
screen):

| study | sample | σ_RM at ~0.6–1.0 R500 |
|---|---|---|
| Böhringer, Chon & Kronberg 2016 (CLASSIX) | 1722 RMs; masses 0.02–19×10¹⁴, mean ~3×10¹⁴; mixed member/background | **112 ± 43** (Table 1, Galactic-corrected, their 0.5–1.0 r500 bin; their text prints 144 ± 43 for the same bin — table adopted) |
| Osinga et al. 2024/25 (124 Planck clusters, mean 5.7×10¹⁴) | 363 background sources | **51 ± 6** (their tabulated 0.5–1.0 R500 background bin, cluster rest frame — the FRB's source class) |
| Alonso-López et al. 2025 (Shapley SC core; 0.5–9.8×10¹⁴ incl. two group-scale members) | 34 cluster-region sources | **27.2 ± 5.0** (printed excess after off-target subtraction; overlapping halos) |
| Anderson et al. 2021 (Fornax, 6×10¹³ — *below* our cluster's mass) | 76 sources < 1° | **16.8 ± 2.4** |
| Loi et al. 2025 (Fornax again — densest grid, same system as Anderson) | 503 background sources | ~**11.5** (outer 0.86–1.10 R500 annuli, non-cluster floor removed) |
| Khadir et al. 2025 (A3581, 2.15×10¹⁴ — nearest mass to ours) | 111 background sources | ~**8** (5–12 across the bin, figure estimate) |

(Set updated 2026-07-17 after a systematic literature sweep; selection
criteria unchanged from the predeclared record, every value re-verified
against the paper full text.) Median 22.1 → 15.3 rad m⁻² at the observer =
**1.65× your quoted RM_host error**. Under the record's frozen rule this now
classifies as **marginal** (material ≥ 18.6, null < 9.3), which routes to
explicit owner adjudication rather than an automatic verdict. One structural
sensitivity worth both owners seeing: Fornax appears twice (Anderson and Loi
are the same system); counting it once — under either study — moves the
median to 27.2 → 18.9 observed, back over the material line. The
qualitative point is unchanged either way: plausible outskirt fields
contribute at or above your quoted RM_host uncertainty, and the ±0.5 μG
sensitivity table below does not depend on the literature median at all.

## What re-partitioning does (MC, mirroring your procedure)

We reproduced your MC (10⁴ trials, your priors; Galactic prior recovered by
closure on your published medians: −5.5 ± 7.1 rad m⁻²) and added one term:
RM_cl from the census column (truncated-prior MC draw) at a scanned coherent
field. Zero-cluster corner reproduces your row (RM_host p50 = −755.8,
⟨B∥,host⟩ = −2.02). Then:

| ⟨B∥,cl⟩ (μG) | RM_cl(obs) | RM_host (host frame) | ⟨B∥,host⟩ (your DM_host) |
|---|---|---|---|
| −0.5 | −67 [−89, −46] | −647 ± ~38 | −1.75 |
| −0.25 | −34 | −701 | −1.88 |
| 0 | 0 | −756 | −2.02 |
| +0.25 | +34 | −811 | −2.17 |
| +0.5 | +67 | −865 | −2.33 |

A ±0.5 μG field — unremarkable at 0.83 R500 — moves your RM_host by ~7σ of
its quoted error. The error bar on RM_host is therefore dominated by the
un-modeled cluster term, not by the foreground terms currently in the MC.

**The DM side of the same seam (independent of B):** your DM_host = 464
(+56/−130) contains no intervening term either. Subtracting the census
column (host-frame equivalent ≈ 234 pc cm⁻³ at the central value) gives
DM_host ≈ 230, which at your RM_host **doubles** the host field:
⟨B∥,host⟩ ≈ −4.5 μG (−3.0 to −10.0 across the column bracket), and in
~9% of joint draws the published DM_host cannot absorb the cluster column at
all. This is worth reconciling regardless of what is decided about the RM
term: paper I's host-DM posterior for this burst
(87 [−37, +191] pc cm⁻³ rest frame, `scripts/dm_budget_uncertainty.csv`)
already carries the subtraction.

## Two language options (either works for paper I)

**Option A — add the intervening term (recommended).** Add
DM_int/RM_int terms to eqs. `eq:dm_comps`/`eq:rm_comps` for this burst only,
with DM_cl from paper I's census (184, bracket 84–328, X-ray-capped mass) and
⟨B∥,cl⟩ either marginalized over a stated prior (e.g. |B| ≤ 0.5 μG uniform)
or profiled. RM_host for 20230307A then carries an honest
systematic: RM_host = −756 ± 15 (stat) ∓ ~65 (intervening, at |B| ≤ 0.5 μG);
⟨B∥,host⟩ = −2.0 → −4.5 μG if the DM subtraction is adopted too. All other
eleven bursts are untouched (no other budget-eligible cluster in the census).

**Option B — keep host-only, state the implied ceiling.** Keep the current
numbers and add one sentence: attributing the full residual to the host
assumes |⟨B∥,ICM⟩| ≲ 0.08 μG through the intervening cluster at 0.83 R500,
below typically measured outskirt fields; the host-attributed RM and B∥ for
this burst are therefore upper limits on the host contribution in magnitude.

Either way, paper I would add at most one forward-reference sentence in its
dominant-systems discussion — and, symmetric case worth stating in your
draft's favor: if you *keep* host-only and future data (e.g. a background-RM
grid through this cluster) pins the cluster term, this sightline becomes a
direct ⟨B∥⟩ measurement of a 1.5×10¹⁴ M☉ cluster at 0.83 R500 — the
FRB-as-ICM-magnetometer result — which is a paper-level payoff for the
companion either way.

## Fine print

- The coherent-field convention makes every number here conservative in the
  same direction: field reversals along the chord lower |RM_cl| at fixed
  field strength, so the negligibility ceilings are, if anything, too
  generous to the zero-cluster reading.
- Your depolarization σ_RM (0.82 rad m⁻² for this burst) is *not* implicated
  — the ICM is smooth across the emission patch; only the mean LOS RM is at
  stake.
- τ firewall: nothing here consumes any scattering quantity; your depol–RM–τ
  correlation is a separate conversation (paper I's refits are in flight).
- Values consumed from your draft are pinned in the JSON artifact
  (2026-07-17 zip refresh). If your Table `tb:host_props` row changes, we
  re-run and re-issue this memo (the record's interface-freeze rule).

**Asks:** (1) agree on Option A or B (or propose C); (2) confirm the
20230814B/20221203A z-bookkeeping fix (ISSUE-009) lands in the same
revision, since the MC's z inputs move with it for those bursts (not for
20230307A, whose z = 0.271 is stable).
