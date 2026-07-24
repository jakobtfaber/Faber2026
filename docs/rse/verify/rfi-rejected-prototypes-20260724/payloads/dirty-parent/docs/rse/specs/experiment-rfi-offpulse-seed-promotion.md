# Experiment: Protected off-pulse seed-row promotion

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** Automated variants rejected for science use
**Related Documents:**
- [Earlier horizontal-row experiment](experiment-rfi-horizontal-structure-capture.md)
- [Implementation plan](plan-rfi-horizontal-row-component.md)
---

## Question

Can isolated Pixel-6 detections outside the protected burst window be promoted
to whole-row vetoes without converting a broadband impulse into loss of the
entire band?

This is not a complete RFI method. It targets saturated, horizontally
persistent fine-frequency rows only.

## Frozen rule

1. Exclude the complete on-pulse interval from all decisions.
2. Mark an off-pulse seed where absolute standardized intensity is at least
   `6.0`.
3. Exclude any time column in which more than 1% of valid rows are seeds; that
   is broadband, time-local evidence.
4. Promote any remaining seed row, not the full coarse group, to a whole-row
   veto. The earlier four-row coarse-group gate is preserved as the rejected
   first application: it missed owner-visible isolated rows.

## Known-truth setup

Twelve coarse groups each received seven saturated fine rows. Each row had
pre-burst, burst, and post-burst segments with standardized amplitudes 7.5–9.0;
none occurred in the original package-training interval. Exact truth was
recorded on the full 65,536-row by 512-time-bin grid. Three deterministic seeds
were compared with interference-free controls.

The first implementation did not exclude broadband seed columns. The existing
synthetic broadband impulse then selected roughly 51,400 rows and removed the
entire injected burst. Those outputs are preserved under
`results/broadband-failure-v1/`. A five-row coarse recurrence gate then missed
four of 84 saturated rows per seed; those outputs are preserved under
`results/minimum-five-v2/`.

## Four-row checkpoint

The four-row coarse-group gate recovered every injected saturated row in all
three deterministic seeds. It selected no row in the clean controls and
excluded all three broadband-impulse columns.

| Seed | Saturated rows recovered | Surviving saturated intensity | Clean-control rows | Added burst support lost |
|---|---:|---:|---:|---:|
| 2026072101 | 84/84 | 0% | 0 | 0.138% |
| 2026072102 | 84/84 | 0% | 0 | 0.143% |
| 2026072103 | 84/84 | 0% | 0 | 0.143% |

The original and first repeat for seed 2026072101 are byte-identical with
SHA-256 `87c66aa2a8449483390903a6d9f5e04bb9d04859b3b5084588fd5557ff33dd99`.
A new clean-container reproduction on 2026-07-22 produced the same bytes.

Exact reproduction command:

```bash
EXP=/data/Faber2026/evidence/rfi-offpulse-seed-promotion-experiment-20260721
INPUT=/data/Faber2026/evidence/zach-chime-preprocessing-20260721
OUT=$EXP/reproduction-20260722-four-row
docker run --rm --network none --cpus 4 --memory 5g \
  -v "$INPUT:/evidence:ro" \
  -v "$EXP/code:/experiment:ro" \
  -v "$OUT:/output" \
  chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41 \
  python /experiment/seed_promotion_experiment.py \
    --input-root /evidence \
    --prototype-script /experiment/prototype_rfi_preservation_review.py \
    --candidate-script /experiment/rfi_offpulse_row_candidate.py \
    --audit-script /evidence/code/audit_chime_preprocessing_v2.py \
    --seed 2026072101 \
    --output /output/seed-2026072101.json
cmp "$EXP/results/seed-2026072101.json" \
  "$OUT/seed-2026072101.json"
```

Two failed 2026-07-22 attempts resolved missing provenance in the earlier
record. The input root is `zach-chime-preprocessing-20260721`, not the
preservation-prototype output directory. The required audit implementation is
`/evidence/code/audit_chime_preprocessing_v2.py`, not the time-frequency
candidate copied into the experiment code directory.

Frozen input SHA-256 values:

- frequency: `02c794745bd79ca235d1d3e18d46b2f43f7529616a5747ccab2a5db094a9cba2`
- source-valid mask: `b183f4aaed375ae78da8000cd5cb8bc3b8c4500c9ff23e56bb9555b0b85ba39e`
- bandpass mean: `472a58567d60221dd8fa2f91eb3fd855f7893cc28dff112b52c911c04900b753`
- bandpass scale: `e3082210b0ec2d49ed86517446f662b56f01ab14ec03b3903cb890cbaf30027c`
- audit script: `5df48f411c6d9f9ce59873b6ccb147de30e22fa8306b3543bb06632212340c83`

## Revised results

| Seed | Saturated rows recovered | Surviving saturated intensity | Added clean rows | Added burst support lost |
|---|---:|---:|---:|---:|
| 2026072101 | 84/84 | 0% | 1 | 0.526% |
| 2026072102 | 84/84 | 0% | 0 | 0.521% |
| 2026072103 | 84/84 | 0% | 1 | 0.527% |

The method excluded the three synthetic broadband-impulse columns on every
seed. A fresh-container repeat of seed 2026072101 is byte-identical; both JSON
files have SHA-256
`4f62f64b409524ec4e770e4e57f4339c0f4cf1eb0f29895ef39bf07f02e06fa7`.

## Reproducibility

- Remote evidence:
  `/data/Faber2026/evidence/rfi-offpulse-seed-promotion-experiment-20260721/`
- Container:
  `chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`
- Network disabled; four CPUs; 5 GiB memory limit.
- Revised code and results: `code-v2/` and `results-v2/`; the earlier four-row
  rule remains under `code/` and `results/`.
- Candidate module SHA-256:
  `e94ddb92e06a88909db8044870385c8047be8a9c99d3f926b65cc1af7d9a1ba0`
- Experiment script SHA-256:
  `f59914a3eb1c77e6137da594614c5a08fde4f96bbd348bced3f342e70e1cf9d0`
- Preserved prototype SHA-256:
  `e283a66d089e738de0839e00660bcde3224efb98abb2e4c8e38dc318987a26cc`

## Interpretation

The revised rule is admitted only for strong off-pulse rows represented by the
known-truth injection. Selecting at most one clean-control row per 55,744-row
grid is recorded, not hidden. It does not handle weak rows, drifting lines, or
broadband time-local interference. Zach has no truth; its application remains
an owner-review diagnostic. The real composite that used this one-row gate was
rejected by the owner as far too aggressive. Owner-reviewed event maps now
replace this rule as bad-channel authority.
