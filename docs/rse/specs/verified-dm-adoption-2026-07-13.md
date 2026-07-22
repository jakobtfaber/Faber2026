# Verified dispersion-measure adoption record

Date: 2026-07-13

Status: adopted for the manuscript

Authoritative catalog: `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv`

## Decision

The manuscript adopts the independently fitted CHIME/FRB phase-coherence DM
for each of the twelve bursts. The DSA-110 fits remain reported as independent
cross-checks. The Gaussian or random-effects CHIME+DSA combinations are retained
as diagnostics, but they are not the manuscript's primary DMs.

This supersedes:

- the rounded DSA catalog values previously used as `DM_obs`;
- the earlier adaptive-arrival `UNCONSTRAINED` statuses, which were application
  failures rather than evidence that the bursts were absent; and
- the phase-suite v1 campaign, whose baseline-DM and fit-gate implementation was
  retracted.

The obsolete `scripts/plot_codetection_gallery_arrivaldm.py` producer was
removed in the same change so that the invalid adaptive-arrival result cannot
be regenerated or mistaken for Figure 1.

## Why CHIME is primary

The observed CHIME phase-coherence peaks are generally narrower and more stable
than the DSA peaks. This is physically expected: the cold-plasma delay per unit
DM across 400--800 MHz is about 19.4 ms, whereas it is about 0.57 ms across
1311--1499 MHz, a factor of roughly 34 greater DM leverage for CHIME. CHIME also
has 2.56 microsecond native sampling. DSA provides valuable confirmation at a
widely separated band, but its narrower fractional bandwidth produces broader
DM response curves and greater cutoff sensitivity.

The adopted policy does not choose whichever band happens to be closer to a
previous catalog value. It applies the same instrument rule to every event:
CHIME is the measurement; DSA is the cross-check.

## What the formal combinations did

For statistically consistent bands, the diagnostic joint estimator used the
inverse-variance mean

    DM_joint = sum(DM_i / sigma_i^2) / sum(1 / sigma_i^2).

The per-band sigma was not read directly from the plotted curve width. It was
the maximum of the channel-block jackknife variation, native-resolution
variation, fluctuation-frequency-cutoff variation, and a 0.005 pc cm^-3
numerical floor. Consequently, narrow and stable CHIME fits usually dominated
the inverse-variance result.

When the two band estimates scattered more than these errors predicted, a
non-negative between-band term tau was fitted and the weights became

    w_i = 1 / (sigma_i^2 + tau^2).

That random-effects step correctly exposed band-dependent morphology, but with
only two bands it also partly equalized their weights. In Phineas, for example,
the result moved close to the midpoint even though the CHIME curve was visibly
sharper. This is why the random-effects values are kept as sensitivity tests
rather than adopted as the total DMs.

## Validation and quality statement

- All twelve bursts are detected in both bands.
- All 24 independent band fits have finite maxima interior to their final fine
  grids.
- All 24 selected native frequency and time resolution; no averaging was
  required to stabilize a fit.
- The error budget includes channel jackknifes, resolution dependence, cutoff
  dependence, and a numerical floor.
- The held-out paired injection matrix has joint RMSE 0.0028 pc cm^-3 and
  maximum absolute error 0.0062 pc cm^-3.
- The largest measured CHIME-DSA difference is 0.1170 pc cm^-3.
- Freya, Isha, Phineas, and Zach require a nonzero between-band term in the
  diagnostic random-effects calculation. This is treated as frequency-dependent
  burst structure, not as an unconstrained fit.

## Figure 1 rule

Figure 1 is regenerated from the 24 archival `_cntr_bpc.npy` products. Each
product is already dedispersed at the exact DM encoded in its filename. Before
display downsampling, each waterfall is shifted by

    delta_DM = DM_adopted - DM_filename,

using a zero-filled, non-wrapping residual-DM shift. Thus both CHIME and DSA are
displayed at the same adopted CHIME-primary DM for that event. The operation is
performed on the native arrays; only then are the arrays block-averaged for the
figure.

## Reproducibility surfaces

- full fits: `analysis/dm-joint-phase-v2/results/fits.json`
- adopted catalog: `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv`
- contact sheet: `analysis/dm-joint-phase-v2/results/diagnostics/all_events_contact_sheet.jpg`
- per-event diagnostics: `analysis/dm-joint-phase-v2/results/diagnostics/`
- injection validation: `analysis/dm-joint-phase-v2/results/validation/`
- raw-product hashes: `analysis/dm-joint-phase-v2/results/run_provenance.json`
- implementation snapshot: `analysis/dm-joint-phase-v2/code/`
- source implementation commit: `dsa110-FLITS` `c07f1f1`
