# Decision: Figure 1 product and next CHIME qualification route

**Date:** 2026-07-14  
**Status:** product and experiment design selected; candidate bytes and CHIME
measurement remain unapproved  
**Decision authority:** manuscript owner  
**Scientific base:** Faber2026 `main` after PR #42, with `pipeline/` pinned to
FLITS `91a5120`

This record resolves the two decisions left open by
[`handoff-2026-07-14-chime-repair-and-figure-review-closeout.md`](../handoff/handoff-2026-07-14-chime-repair-and-figure-review-closeout.md).
It does not approve any candidate from the rejected July packet and does not
change the conclusion that there are zero qualified CHIME
scintillation-bandwidth measurements.

## Decision 1: Figure 1 is the twelve-burst data gallery

The selected stable product ID is **`fig1-gallery`**.

Figure 1 will be a single, sample-level overview of all twelve co-detections in
MJD order. Each burst tile will show the CHIME/FRB and DSA-110 dynamic spectra,
with compact time-profile and frequency-spectrum marginals. It will be a
**data-only** product: no fitted model, model contour, scattering parameter, or
scintillation annotation will be overlaid.

This chooses the product, not existing bytes. In particular:

- the archived `fig1-gallery` candidate from
  `archive/rejected-figure-candidates-20260714` remains `needs_revision` and
  must not be promoted;
- a new isolated batch and new candidate hash are required;
- the adopted-DM catalog, input-product DMs, physical re-dedispersion offsets,
  masks, input hashes, and display windows must be revalidated before render;
- exact candidate bytes still require owner approval and a hash-bound receipt.

### Locked presentation contract

- **Geometry:** compact 4-by-3 gallery on one full-width manuscript page.
- **Order:** MJD-ascending, matching the sample table.
- **Content:** observed CHIME/FRB and DSA-110 data only.
- **Alignment:** common physical time coordinate per burst after the accepted
  DM treatment; the same displayed interval applies to both bands.
- **Window:** observed on-pulse union plus
  `max(CHIME on-pulse width, 1.5 ms)` on each side, with any exceptional clip
  recorded explicitly.
- **Resolution:** preserve scientifically meaningful structure at print scale;
  target about 33 microseconds in time and 512 displayed channels per band,
  subject to native-resolution and legibility checks.
- **Labels:** TNS name, telescope/band identity, physical time, frequency, and
  a clear no-coverage gap; no nickname-only labels.
- **Caption:** sample and data-product description only. It must not imply that
  a joint fit or CHIME scintillation bandwidth has been accepted.

### Disposition of the triptychs

The `triptych-*` data/model/residual family remains a distinct fit-audit
product. It is not Figure 1 and is not approved as a twelve-page opening
sequence. After the adopted-DM and joint-fit revalidation, a small number of
representative triptychs may be proposed for the Results section, with the
full accepted audit family placed in an appendix or external artifact set.
Flagged or scientifically unaccepted fits cannot be made acceptable by a
dagger or caption disclaimer.

This supersedes the earlier product choice in
`docs/superpowers/specs/2026-07-11-codetection-triptych-fig1-design.md` while
retaining that document as historical design evidence.

## Decision 2: C1 cross-fitted all-pairs estimator

The next CHIME experiment ID is **`c1-allpairs-crossgp`**.

The purpose of C1 is to test whether the retained polarization-resolved,
upchannelized CHIME product contains enough information for unbiased recovery
at the observed modulation, without B4's fixed early/late compression. C1 is a
new qualification route, not a refit of B4's diagnostic ACF.

### Estimator

1. Start from the pinned polarization-resolved upchannelized intensity cube in
   the B4 band (`627--800 MHz`). Preserve the individual on-pulse time samples;
   do not collapse them into four spectra before estimation.
2. Prove the on-pulse window against the retained product before any burst fit.
   Freeze this window, channel mask, coarse-channel block map, and all
   hyperparameters before unblinding the real burst result.
3. Form every admissible cross-product between statistically independent
   polarization/time folds. Exclude auto-products. This retains the independent
   noise-null advantage of B4 while using all available cross-pair information.
4. Estimate weights and the instrumental nuisance basis only from training
   off-pulse blocks. Evaluate nulls and injections on held-out real-background
   blocks. Rotate the held-out fold so no block trains and tests the same
   nuisance estimate.
5. Fit a shared scintillation covariance in channel space with parameters
   `(decorrelation bandwidth, modulation index)` while profiling the frozen
   off-pulse nuisance basis. Use the Lorentzian covariance convention already
   exercised by B4 so the estimator change, rather than a width-definition
   change, is tested.
6. Derive uncertainty and coverage from the complete real-background
   injection ensemble, not from the local fit Hessian alone. Preserve both the
   raw estimate and any calibration mapping in machine-readable output.

An efficient implementation may use a generalized least-squares quadratic
estimator followed by a bounded covariance likelihood. The scientific contract
is the all-pairs, cross-fitted data use and the held-out real-background
calibration; a particular optimizer is not part of the claim.

### Blinded calibration matrix

Run at least 128 deterministic, reproducibly seeded trials per cell using
untouched real off-pulse backgrounds:

- modulation indices: `0.10, 0.15, 0.17, 0.20, 0.30, 1.00`;
- widths: `3, 6, 10, 16` native channels;
- independent held-out background placement across the available off-pulse
  blocks;
- the same masks, folds, nuisance training, estimator, and uncertainty path as
  the later on-pulse analysis.

The `m=0.10` cells are a declared stress test. Every `m=0.15` and `m=0.17`
cell is a qualification gate because these bracket the retained product's
observed `m approximately 0.15--0.17`. Higher-modulation cells diagnose the
estimator envelope but cannot compensate for failure at the real regime.

### Gates carried forward unchanged from B4

For every required low-modulation cell:

- all trials return finite estimates;
- median absolute width bias is less than
  `max(0.10 * true_width, 0.25 * native_channel_width)`;
- empirical 68 percent interval coverage is between `0.53` and `0.83`;
- median absolute modulation-index bias is less than
  `max(0.10 * true_modulation, 0.05)`.

Additional gates are:

- family-wise false-positive probability at most `0.01` across held-out
  off-pulse and pairing-scramble nulls;
- no coherent fitted scale in time-scrambled, polarization-scrambled, or
  coarse-channel phase-shift controls;
- less than 20 percent width movement across predeclared fit windows;
- compatible frequency-split widths after applying the predeclared
  scintillation-frequency scaling convention;
- compatible time-fold estimates;
- portable data, configuration, seed, artifact, and hash provenance;
- independent visual review that cannot override a failed quantitative gate.

No threshold may be relaxed after the real burst estimate is inspected. Any
changed threshold creates a new experiment ID and a fresh blinded campaign.

### Go/no-go rule

The real burst may be unblinded only if every prerequisite, null, and required
`m=0.15` and `m=0.17` recovery cell passes. After unblinding, all stability and
validated-envelope gates must also pass before a bandwidth can be marked
`qualified_measurement`.

If C1 fails the low-modulation calibration, stop estimator tuning on this
retained product. The next route must change the information content of the
input product—for example, a verified voltage-level or finer-time-resolution
reduction—not merely change the ACF fit window or optimizer. A C1 failure is a
valid conclusion that the current product is information-limited.

## Immediate execution order

1. Freeze and independently revalidate the adopted-DM catalog and both
   telescope input products for all twelve bursts.
2. Render a new isolated `fig1-gallery` candidate; do not touch the protected
   manuscript target.
3. Review and decide the exact new gallery bytes by stable candidate ID.
4. Implement C1 in a new FLITS experiment root with a machine-readable config
   and no access to the on-pulse fit during calibration.
5. Run the null and real-background injection campaign.
6. Unblind only if the predeclared go rule passes; otherwise publish the
   documented failure and move to a new data-product route.

Figure work and C1 implementation belong in separate focused branches and
pull requests. Neither may bump the Faber2026 `pipeline/` gitlink as an
incidental side effect.
