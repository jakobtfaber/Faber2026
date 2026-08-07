# Independent research: Phineas probabilistic halo crossing

Date: 2026-07-22

## Verdict

Adopt the probabilistic route for Phineas objects `983` and
`194021777634832653` (the canonical object paired with legacy object `832`).
This resolves the conflicting binary prescriptions in ticket 06.

The apparent contradiction was partly a radius-definition mismatch. The census
flag tests `R200c`; the modified-NFW gas model is truncated at its larger
Bryan--Norman virial radius. The foreground-dispersion model must use the radius
that bounds its own gas profile. `R200c` crossing remains a reported geometry
sensitivity, not a second zeroing rule.

Ticket 07 was resolved earlier on 2026-07-22. This model preserves its accepted
priors and headline logic while replacing only the Phineas binary-halo input.

## Frozen evidence

The input CSV freezes the two Legacy Survey photometric redshifts, Pan-STARRS
Kron `g` and `i` photometry with errors, match separations, source identifiers,
query hashes, verification hashes, and canonical row hashes. Both positional
matches are within `0.2 arcsec` and have Pan-STARRS quality value `53`.

The frozen Kron photometry independently reproduces the owner-adjudicated
central stellar masses:

| Object | log10 stellar mass |
|---|---:|
| `194021777634832653` / legacy `832` | 10.210534 |
| `983` | 8.944125 |

## Model

Each object uses `2^18` deterministic scrambled Sobol draws. A draw propagates:

1. the catalog photometric-redshift error;
2. the reported `g` and `i` measurement errors;
3. `0.10 dex` Taylor-relation calibration scatter;
4. `0.15 dex` intrinsic scatter in stellar mass at fixed halo mass for the
   redshift-dependent Moster relation;
5. `0.40` natural-log scatter in the circumgalactic gas column.

The same sampled `i` magnitude enters both color and absolute magnitude, so its
algebraic covariance is retained. Survey-to-survey covariance is unavailable
and is therefore not invented. A draw contributes exactly zero unless the
galaxy is in front of the burst, the stellar-to-halo inversion lies within its
declared mass domain, and the sightline enters the modified-NFW virial
truncation radius. Crossing draws use the independently reproduced modified-NFW
hot column plus the existing passive cool-gas expectation.

## Results

| Object | P(b < R200c) | P(b < mNFW virial radius) | Mixture DM median | Mixture DM 16th--84th percentile |
|---|---:|---:|---:|---:|
| `194021777634832653` / `832` | 0.8641 | 0.9944 | 10.94 | 6.11--19.45 |
| `983` | 0.2170 | 0.5104 | 0.56 | 0.00--5.31 |

The complete Phineas intervening distribution becomes `203, 255, 322`
pc cm^-3 at its 16th, 50th, and 84th percentiles. With the unchanged remaining
forward-model priors, the observer-frame host residual becomes
`62 (+82/-98) pc cm^-3`, with probability `0.257` below zero. These replace the
binary-halo diagnostic in the forward-model artifact only; ticket 07 governs
their manuscript use.

## Independent checks

- The vectorized modified-NFW column matches the clean-room standard-library
  implementation to relative tolerance `2e-13` at three Phineas points.
- The redshift-dependent Moster inversion round-trips its defining equation to
  `2e-14 dex` absolute tolerance.
- Fourfold sample growth changes either crossing probability by less than
  `0.002`.
- All non-crossing and out-of-domain draws have exactly zero dispersion
  measure; histogram normalization and its zero-valued probability mass are
  tested directly.
- Deterministic convolution agrees with an independent 500,000-draw random
  Monte Carlo oracle in the budget test suite.

## Limitations

- Taylor et al. define the calibration using rest-frame quantities. The
  available pipeline input lacks an object-specific spectral-energy-distribution
  correction; the adopted calibration scatter covers this only approximately.
- Legacy Survey redshift and Pan-STARRS magnitude errors are treated as
  independent because no cross-survey covariance is available.
- The Moster fit does not provide a directly usable full parameter covariance;
  the published intrinsic scatter is propagated instead.
- The inversion is a forward-relation uncertainty propagation, not a
  population-level Bayesian halo-mass posterior with a halo-mass-function prior.
- Gas-profile uncertainty remains the measured-halo prior accepted in ticket
  07.

## Repowire review record

Repowire job `work-cd1d5157201f` accepted the independent review but stopped
reporting and was cancelled after twelve minutes. Job `work-0ed524baf195` could
not register an OpenCode peer. An ask to the existing Antigravity peer was
delivered but that peer had not checked in for five hours. None produced a
scientific verdict; no missing reply is treated as approval.

## Primary sources

- Taylor et al. (2011), optical-color stellar-mass calibration:
  <https://arxiv.org/abs/1108.0635>
- Moster et al. (2013), redshift-dependent stellar-to-halo mass relation:
  <https://arxiv.org/abs/1205.5807>
- Bryan & Norman (1998), virial overdensity convention:
  <https://arxiv.org/abs/astro-ph/9710107>
