# Research: Zach CHIME preprocessing baseline

**Date:** 2026-07-21
**Scope:** Local migration code, pinned CHIME baseband worker, live h17 input and container
**Related Documents:** [Wayfinder task](../wayfinder/tickets/16-build-verified-zach-chime-preprocessing-baseline.md)

## Question / Scope

What must change before the Zach CHIME/FRB singlebeam file can produce a
reproducible, nominal 1,024-channel preprocessing baseline? This pass covers
durable source-migration evidence, frequency-grid restoration, and diagnosis of
radio-frequency-interference (RFI) excision and bandpass correction. It does not
fit dispersion, scattering, scintillation, or burst morphology.

## Codebase Findings

### Migration evidence is not durable before mutation

`scripts/h17_source_data_layout.py:289-313` computes source and target identities,
including SHA-256 hashes, in memory. `migrate()` then starts remote renames before
writing those identities (`scripts/h17_source_data_layout.py:320-375`). The remote
journal records move progress, not the preflight identity packet. The completed
2026-07-21 migration receipt is truthful, but no pre-rename artifact survived a
process crash. Future reuse must atomically persist identical local and remote
preflight bytes, verify their hashes, and only then permit a rename. The historical
migration must not be retroactively relabeled.

### The Zach input has a sparse but internally consistent coarse grid

Live, read-only inspection used
`chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`
with `baseband-analysis` 1.9.0. The Zach file
`/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5` has 871 unique
coarse-channel identifiers spanning 2 through 1,023. Exactly 153 of the nominal
1,024 identifiers are absent. Retained centers obey
`800 - id * 0.390625 MHz`. The source SHA-256 is
`215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9`.

The package helper `baseband_analysis.core.sampling.fill_waterfall` restores
1,024 positions but fills absent voltages with zeros and emits no validity mask.
The package waterfall helper instead uses `NaN` and a validity mask. Missing
measurements must remain distinguishable from measured zero power.

At factor 64 the package reports fine frequencies using inclusive
`linspace(800.1953125, 400.1953125, 65536)`. Exact nominal bin centers are
`800.1953125 - (fine_id + 0.5) * (0.390625 / 64) MHz`. The two differ by at
most 3.052 kHz, half a fine channel. The integer fine identifier is therefore
the authoritative coordinate; both frequency arrays must be preserved rather
than silently replacing one with the other.

### The pinned worker keeps only retained channels

`pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:240-423`
coherently dedisperses, upchannelizes, detects Stokes I, and saves a compact
frequency axis. It discards the fine-channel identifiers returned by the package.
At Zach's factor 64, it produces 55,744 measured rows. A nominal grid has 65,536
rows: 55,744 measured and 9,792 missing. The companion channelizer already returns
fine identifiers (`pipeline/analysis/scattering-refit-2026-06/baseband_recovery/windowed_upchan.py:42-146`).

The exact local worker is pinned by pipeline commit `d0d1e278` and SHA-256
`f3fe5ee9...`; no current h17 copy matches it. A live run must stage an exact
worker and record its complete hash rather than select among divergent remote
copies.

### RFI and bandpass handling are not a standardized preprocessing stage

The worker performs neither RFI excision nor bandpass correction. Zach's normal
configuration has an RFI block but no bandpass-normalization block
(`pipeline/scintillation/configs/bursts/zach_chime.yaml:1-41`). A campaign-only
entry point enables additional cleaning, so results depend on entry point.

Historical scattering input converted missing values to zero before correction
and averaging. The mask-aware correction changed fitted parameters materially
(`pipeline/analysis/scattering-refit-2026-06/RFI_FIX_FLIP_RECORD.md:1-30`). Owner
review also found visible unexcised RFI and residual sweep in Zach
(`docs/rse/specs/notes/owner-data-review-findings-2026-07-18.md:12-57`). Prior
CHIME scintillation controls found an approximately 35 kHz response in off-burst
data. Therefore burst-inclusive cleaning and a visually plausible spectrum are
not sufficient validation.

## Synthesis

The safe baseline has three separable products:

1. A future migration attempt cannot begin until a complete, attempt-specific
   preflight packet exists locally and remotely with matching SHA-256 hashes.
2. The baseband worker must expose the nominal 1,024-channel grid and an explicit
   validity mask while preserving measured values exactly. Missing positions are
   `NaN`, never zeros.
3. RFI masks and bandpass gains must be learned only from one off-pulse interval
   and tested on a disjoint off-pulse interval. This run should compare the raw,
   grid-only, RFI-only, bandpass-only, and combined sequences. It can validate
   preprocessing behavior but cannot certify a scintillation measurement.

## References / Sources

- Code: `scripts/h17_source_data_layout.py:153-215,258-375,469-491`
- Code: `tests/test_h17_source_data_layout.py:1-95`
- Code: `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:200-488`
- Code: `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/windowed_upchan.py:1-146`
- Config: `pipeline/scintillation/configs/bursts/zach_chime.yaml:1-41`
- Evidence: `docs/rse/specs/notes/owner-data-review-findings-2026-07-18.md:1-82`
- Live image: `chimefrb/baseband-analysis` repository digest
  `sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`
