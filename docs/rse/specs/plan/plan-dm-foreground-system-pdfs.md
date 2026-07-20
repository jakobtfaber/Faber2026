# Plan: per-system foreground DM PDFs

---
**Date:** 2026-07-10  
**Status:** Scoped — not yet implemented  
**Depends on:** V4 census (cleared); `scripts/dm_budget_uncertainty.py` host/cluster PDFs  
**Wishlist:** O6 in `docs/rse/specs/misc/figure-wishlist.md`  
**Companion figure (done):** `fig:dm_host_posteriors` now shows full host PDFs + cluster MC  
---

## Goal

A manuscript figure (or appendix panel set) showing **probability densities for
every confirmed foreground galaxy and cluster column** that enters
`DM_int` — not only the sightline-summed intervening term and not only the
single R500-piercing cluster.

## Why this is not ready to draw today

| Layer | What exists | Gap |
|-------|-------------|-----|
| Host `DM_host` | Full MC in `dm_budget_uncertainty.py` | Done (Figure 7 left) |
| One cluster (20230307A / J115120.4+714435) | β-model MC | Done (Figure 7 right) |
| Sightline-sum `DM_int` | Lognormal smear around census point sum | Not per-object |
| Per galaxy / cluster | Point mNFW (+ cool) at fixed M, b (`foreground_unified`) | No MC over mass, f_gas, cool clumping, b |

`galaxies_cgm` / `clusters_icm` are **DM(b) profile curves**, not PDFs over
nuisance parameters.

## Proposed product

**`fig:foreground_dm_pdfs`** (working label):

1. **Panel A — galaxies:** one ridge (or small-multiple KDE) per confirmed
   foreground galaxy that contributes to any sightline’s `DM_int`, ordered by
   median column. Sample hot mNFW + cool CGM with the same prior families the
   budget already documents (mass scatter by `mass_source`, f_gas / cool-phase
   factors from the two-phase model).
2. **Panel B — clusters:** same for catalog clusters on the three
   cluster-bearing sightlines (not only the R500 piercer); mark which enter
   the budget (`b < R_500`) vs omitted outer systems.
3. **Caption contract:** state burst list / system list, prior table, and that
   these are **intervening-column** posteriors (not host).

Palette: manuscript set (`#1B365D`, `#4A90E2`, `#F5A623`, `#D0021B`, `#FAFBFC`)
matching `systems_figures.py` / `make_budget_figure`.

## Implementation sketch (when scheduled)

1. Export a frozen per-system table from `foreground_unified` (obj id, sightline,
   z, M, b, R_vir / R_500, dm_halo, dm_cool, mass_source, cluster flag) —
   byte-pinned under V4 provenance.
2. Add `sample_system_dm(row, n)` next to `host_posterior` (or in
   `galaxies/foreground/`) using existing mNFW callables + documented priors.
3. Plot script → `figures/foreground_dm_pdfs.{pdf,png}`; wire into appendix or
   §Obs-FG; add `repro_manifest` row.
4. Self-check: sum of per-system medians ≈ sightline `DM_int` within prior
   scatter; cluster piercer PDF consistent with Figure 7 right panel.

## Owner decisions before coding

1. **Which systems?** All confirmed foreground in `tab:foreground`, or only
   those with nonzero capped `DM_int`?
2. **Assumed-mass rows:** sample with the factor-of-two prior, or show as
   upper-limit markers only?
3. **Placement:** main §budget vs appendix next to `fig:dm_host_posteriors`?

## Out of scope here

- Measured-τ overlay on `fig:budget` (still V1+C gated).
- Changing host/cluster numbers already locked in Appendix C / `tab:budget`.
