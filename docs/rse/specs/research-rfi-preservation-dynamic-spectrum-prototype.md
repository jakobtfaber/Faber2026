# Research: RFI preservation dynamic-spectrum prototype

**Date:** 2026-07-21
**Scope:** Internal codebase and live h17 development evidence
**Codebase state:** Faber2026 `e0dcdb8e`; pipeline `ab6af1f7`
**Related Documents:**
[baseline research](research-zach-chime-preprocessing-baseline.md),
[baseline validation](validation-zach-chime-preprocessing-baseline.md),
[visual-review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)

## Question / Scope

What is the smallest controlled dynamic-spectrum prototype that lets the owner
judge the tentative signal-preservation limits without opening sealed test data
or mistaking observed Zach data for known truth?

This pass covers only the existing development evidence, the exact rejected
cleaner, deterministic synthetic contamination, and a review figure. It excludes
the real burst interval, any newly sealed split, replacement-cleaner selection,
and all science-result promotion.

## Codebase Findings

### The existing audit can be reused as the rejected cleaner

The merged audit learns the package channel mask only from a caller-supplied
interval and maps it back onto the explicit source-valid grid
(`pipeline/analysis/scattering-refit-2026-06/baseband_recovery/audit_chime_preprocessing.py:55-76`).
Its bandpass model uses per-channel mean and sample standard deviation with an
80% finite-sample requirement (`audit_chime_preprocessing.py:79-107`). The
rejected combined order is initial RFI mask, bandpass estimation, normalization,
then a second package RFI mask (`audit_chime_preprocessing.py:249-280`).

The exact h17 audit-v2 source is hash-pinned separately as
`5df48f411c6d9f9ce59873b6ccb147de30e22fa8306b3543bb06632212340c83`.
It should be mounted read-only and executed in the same digest-pinned
`baseband-analysis` image, rather than silently substituting the related merged
source.

### Observed Zach intensity is unsuitable as truth

The real product contains natural interference, instrumental response, and a
possible burst. The baseline validation explicitly classifies it as a
diagnostic-only product and rejects the current RFI cleaner
(`docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:117-132`). It
also records an unresolved dispersion-measure and time-axis state
(`validation-zach-chime-preprocessing-baseline.md:153-164`). Therefore a
cleaned-minus-observed residual would not have known truth and could not support
the proposed preservation limits.

### Hash-pinned development inputs are sufficient for synthetic truth

The h17 evidence packet supplies an exact nominal frequency coordinate,
source-valid mask, and development bandpass mean and scale for all 65,536 fine
positions. The baseline establishes 55,744 measured and 9,792 missing positions,
6.103515625 kHz nominal spacing, and 0.3277 ms cadence
(`validation-zach-chime-preprocessing-baseline.md:166-203`). Missing positions
remain `NaN`; they are never synthetic measurements.

The prototype needs only these whitelisted inputs:

| Input | SHA-256 |
|---|---|
| `products/zach_chime_freq.npy` | `02c794745bd79ca235d1d3e18d46b2f43f7529616a5747ccab2a5db094a9cba2` |
| `products/zach_chime_source_valid.npy` | `b183f4aaed375ae78da8000cd5cb8bc3b8c4500c9ff23e56bb9555b0b85ba39e` |
| `diagnostics/audit-v2/zach_bandpass_mean.npy` | `472a58567d60221dd8fa2f91eb3fd855f7893cc28dff112b52c911c04900b753` |
| `diagnostics/audit-v2/zach_bandpass_scale.npy` | `e3082210b0ec2d49ed86517446f662b56f01ab14ec03b3903cb890cbaf30027c` |
| `code/audit_chime_preprocessing_v2.py` | `5df48f411c6d9f9ce59873b6ccb147de30e22fa8306b3543bb06632212340c83` |

The remote `SHA256SUMS` file verifies successfully and itself hashes to
`31a3cb340e8031e60f05dad75478b8013f24a2f63e8dca85e5064b5cce3d4300`.
The evidence root is writable (`0777`), so every input must be independently
hash-checked immediately before the run; directory location alone is not proof.

The saved development bandpass mean and scale are outputs of the rejected
RFI-first path and contain 5,118 cleaner-induced `NaN` rows. They may shape a
synthetic response only after explicit interpolation across independently
source-valid rows. They must not redefine the measured-channel geometry.

### The visual must separate truth, contamination, cleaning, and damage

The prior figure collapses frequency and therefore cannot show time-frequency
signal removal. The prototype needs known synthetic truth, the same truth plus
persistent narrow-band, intermittent, broadband, and 64-fine-channel comb
contamination, the exact rejected cleaner output, and output-minus-truth. The
source-valid and predicted masks remain separate. Time profiles and fluence by
broad frequency slice expose redistribution hidden by total fluence.

The existing audit already records that RFI-first flags 5,118 rows while
bandpass-first flags 432, and that order dominates the result
(`validation-zach-chime-preprocessing-baseline.md:205-234`). The prototype must
therefore label its RFI-first → bandpass → RFI order explicitly and cannot imply
that the order is accepted.

## Synthesis

Use standardized synthetic noise shaped by Zach's development bandpass
statistics and exact source-valid geometry. Add a deterministic burst-like
signal and deterministic interference with a fixed seed. Run the exact audit-v2
cleaner in the immutable container using a separate output directory. The review
figure should show truth, contaminated input, rejected-cleaner output,
output-minus-truth, and both masks, with the tentative preservation limits
annotated. This answers whether the proposed limits are understandable and
visually defensible; it does not validate a cleaner.

No recursive evidence copy is permitted. Compute on h17 with the existing
evidence root mounted read-only, or retrieve only the five whitelisted files
after a dry run and verify every hash locally. Sealed test data and the observed
burst interval remain unopened.

## References / Sources

- Code: `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/audit_chime_preprocessing.py:55-107,216-375`
- Validation: `docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:117-250`
- Remote evidence: `/data/Faber2026/evidence/zach-chime-preprocessing-20260721/`
- Container: `chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`
