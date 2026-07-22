# Low-redshift intergalactic dispersion-measure alternatives

Date checked: 2026-07-22

## Conclusion

There is **no public, drop-in replacement** that simultaneously provides all of:

1. direct calibration at redshifts 0.043 and 0.074;
2. a full probability distribution for the diffuse intergalactic component alone;
3. sightline specificity; and
4. clean separation from independently modeled intervening halos.

There are, however, two stronger low-redshift resources than a blind continuation of the Walker/Connor distribution:

- **Huang et al. `pyhesdm`** is a sightline-specific reconstruction of the real Local Universe to 120 Mpc. It returns a diffuse-intergalactic estimate and uncertainty separately from halo terms. This is the strongest available low-redshift augmentation.
- **Konietzka et al.** provide newer continuous IllustrisTNG ray tracing and public full distributions at redshift steps of 0.01 from redshift zero. Their method corrects errors exceeding 50% in the scatter and higher moments from sparse-snapshot TNG integrations, including the method used by Walker et al. It is the strongest random-sightline distributional cross-check, but it includes halos and therefore cannot be inserted alongside the existing halo budget.

Recommendation: **do not sign off the unchanged continuation without a sensitivity check**. Keep it as the fiducial model for now, but benchmark both low-redshift sightlines against `pyhesdm` and the Konietzka total-cosmic distributions. Promote a hybrid only if that benchmark materially changes the host-dispersion posterior or headline.

## Comparison

| Model | Low-redshift support | Full distribution? | Diffuse gas separated from halos? | Released? | Judgment |
|---|---|---:|---:|---:|---|
| Huang et al. Local Universe / `pyhesdm` | Real local structure, 3.4–120 Mpc | Mean and standard deviation, not posterior draws | Yes | Code and maps | Best sightline-specific augmentation; incomplete path |
| Konietzka et al. continuous TNG300 | Redshift 0–5.5; catalogs every 0.01 | Yes | No; total cosmic web | More than 20 catalogs | Best full-distribution check; not a drop-in diffuse term |
| Batten et al. EAGLE | Direct bins spanning both target redshifts | Yes | No; diffuse gas plus intervening halos | `FRUITBAT` HDF5 | Independent check; same double-counting problem |
| Zhu & Feng hydrodynamic model | Redshift 0–0.82 | Component samples exist in analysis; released interface not found | Yes | Paper, but no reusable per-redshift distribution found | Scientifically relevant; not reproducible enough for production use |
| FLIMFLAM / ARGO | Field-specific reconstructions | Posterior realizations | Yes | Only surveyed fields | Strong in principle; unavailable for these two fields without new spectroscopy |
| Analytic cosmological mean | Any redshift | No | Mean can represent chosen baryon component | Equation | Good normalization; cannot determine tail probabilities |
| Baryonification III | Claimed redshift 0–5 | Yes | Large-scale-structure model is halo-centric | Paper; no production release found | Not validated below redshift 0.2; authors report deviation below about 0.3 |

## Strongest practical alternative: local reconstruction plus statistical remainder

[Huang et al. (2025)](https://doi.org/10.1093/mnras/staf417) use the Bayesian Hamlet density reconstruction from Cosmicflows-4 for diffuse intergalactic gas and galaxy catalogs for a separate halo component. Their public [`pyhesdm` package](https://github.com/FRBs/pyhesdm) exposes the components independently; its diffuse-gas call returns a mean and standard deviation. A packaged release is also available as [`pyhesdm` 0.1.6](https://pypi.org/project/pyhesdm/).

This is directly relevant:

- The two sightlines are outside the model's stated Galactic zone of avoidance.
- Their Planck-2018 comoving distances are approximately 188.6 and 322.1 Mpc.
- The 120 Mpc reconstruction therefore covers roughly 64% and 37% of their paths.

It is not a complete replacement. A rigorous hybrid would use only `get_dmigm` for 3.4–120 Mpc, then add a statistical diffuse-gas increment from 120 Mpc to the source. The existing Milky Way, Local Group, and intervening-halo terms must remain excluded from `pyhesdm`; otherwise they are counted twice. The package supplies a standard deviation rather than a full posterior sample, so the distributional form and covariance with the remainder must be declared and tested.

## Strongest full-distribution cross-check

[Konietzka et al. (2025)](https://arxiv.org/abs/2507.07090) continuously trace rays through the IllustrisTNG Voronoi mesh. They report that sparse snapshot sampling in earlier TNG work misestimated the standard deviation and higher moments of the dispersion-measure distribution at fixed redshift by more than 50%. Their public [ray-tracing catalogs](https://ralfkonietzka.github.io/fast-radio-bursts/ray-tracing-catalogs/) contain ray-by-redshift arrays at steps of 0.01, directly covering redshifts 0.04 and 0.07.

This is methodologically stronger than Walker for the low-redshift **shape**. It is not an intergalactic-only marginal: halos, filaments, and voids all contribute. It can replace the entire random cosmic-web term, or serve as an external bracket, but it cannot be convolved with the existing explicit intervening-halo terms.

## Other alternatives

[Batten et al. (2021)](https://arxiv.org/abs/2011.14547) measured more than one billion EAGLE sightlines and released the full two-dimensional redshift–dispersion histogram through [`FRUITBAT`](https://github.com/abatten/fruitbat). Its first redshift edges are 0, 0.0227, 0.0454, 0.0684, and 0.0916, so both target redshifts are directly represented. The paper explicitly defines its cosmic term as diffuse intergalactic gas plus intervening galaxy halos. It is therefore a useful independent cross-check, not a compatible replacement.

[Zhu & Feng (2021)](https://arxiv.org/abs/2011.08519) separately simulate diffuse intergalactic gas, foreground halos, and hosts over redshift 0–0.82. This is the right physical decomposition, but the public paper mainly exposes fitted summaries and figures; no maintained code or downloadable per-redshift diffuse-gas distribution was found. It is weaker operationally than the released alternatives.

[FLIMFLAM DR1](https://arxiv.org/abs/2402.00505) reconstructs the matter field with 61 ARGO posterior realizations and models foreground halos separately. This is the cleanest end-to-end framework in principle. It covers eight targeted fields, not these sightlines, and requires dedicated spectroscopy. It also replaces the nearest 50 comoving Mpc divided by the Hubble parameter with a fixed cosmic-mean contribution, making `pyhesdm` more appropriate for the immediate Local Universe.

The standard analytic cosmological integral, as used in the [Macquart et al. baryon census](https://arxiv.org/abs/2005.13161), is robust for the mean and correctly tends to zero with path length. It supplies neither the skewed low-redshift distribution nor sightline-specific structure, so it cannot by itself support probabilities such as a residual falling below zero.

[Baryonification III](https://arxiv.org/abs/2601.18784) is a promising analytic full-distribution model. It constructs the large-scale-structure distribution by convolving gas profiles of halos across mass and redshift; it does not supply a released diffuse-intergalactic-only marginal. Adding it to the present explicit foreground-halo terms would therefore double-count halo gas. Its direct comparisons use redshifts of at least 0.2, it matches the simulation only down to about redshift 0.3, and the authors report deviations below that. It is not ready for redshifts 0.043 or 0.074.

## Minimum decision-grade benchmark

1. Evaluate `pyhesdm.get_dmigm` at both sightlines, using its stated uncertainty and no halo/Milky-Way outputs.
2. Compare current low-redshift medians and intervals with public Konietzka catalogs at redshifts 0.04 and 0.07, treating those catalogs as **total cosmic web**.
3. Recompute the two host posteriors under:
   - current continuation;
   - `pyhesdm` local segment plus the current statistical diffuse-gas remainder.
4. Accept the simpler continuation only if the headline classification and reported intervals are insensitive to this change.

## Benchmark result (2026-07-22)

The approved benchmark is reproducible with
[`scripts/dm_budget_low_z_sensitivity.py`](../../../scripts/dm_budget_low_z_sensitivity.py);
the exact results and source hashes are in
[`scripts/dm_budget_low_z_sensitivity.json`](../../../scripts/dm_budget_low_z_sensitivity.json).

| Sightline | Model | Host p16 | Host median | Host p84 | P(host < 0) |
|---|---|---:|---:|---:|---:|
| FRB 20220207C | Current continuation | 82.5 | 114.8 | 141.1 | 0.002 |
|  | `pyhesdm` hybrid | 93.3 | 123.4 | 147.5 | 0.001 |
|  | Konietzka total cosmic | 73.2 | 114.6 | 143.9 | 0.027 |
| FRB 20240203A | Current continuation | 32.8 | 72.2 | 104.9 | 0.045 |
|  | `pyhesdm` hybrid | 44.8 | 80.2 | 109.9 | 0.021 |
|  | Konietzka total cosmic | 48.4 | 99.0 | 133.0 | 0.059 |

All columns are observer-frame pc cm^-3. The `pyhesdm` hybrid replaces only the
diffuse 3.4--120 Mpc segment and retains the explicit known-halo term. The
Konietzka calculation uses its total-cosmic rays and omits the explicit
known-halo term, preventing double counting.

The sightline-specific local diffuse estimate is about 7 pc cm^-3 below the
generic continuation on both paths. This raises the hybrid host medians by
8.6 and 8.1 pc cm^-3. The much longer high-DM tail in the Konietzka catalog
raises P(host < 0), but its maximum remains 0.059. Every tested median remains
positive, and neither sightline changes interpretation. The current
component-consistent continuation is therefore acceptable as the fiducial
model, provided the manuscript identifies this benchmark as a sensitivity
check rather than claiming direct Walker calibration below redshift 0.1.
