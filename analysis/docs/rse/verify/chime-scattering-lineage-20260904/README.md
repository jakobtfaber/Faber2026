# CHIME scattering-input lineage check — 2026-09-04

Status: **partial pass**. No tested cube has the greater-than-5-sigma edge
power expected from the generation-1 circular de-chirp defect. Sixteen of 24
copies also pass the pre-registered centering test. The remaining eight copies
(four byte-unique bursts) are inconclusive because their band-averaged profiles
never exceed 5 sigma, so a signal centroid cannot be measured. This receipt
does not close the full lineage gate.

## Scope and execution

- Host: `lxd110h17`; run at `2026-09-04T17:19:21Z`.
- Base repository revision: `5ad64c3521ca58407f6c69734c384ae28bea3036`.
- Checker: `analysis/scripts/check_chime_scattering_lineage.py`, SHA-256
  `e54fbbff5d701d8e5ae4db1be5e7a8ca8c2aed4623ee26ef7284e2e67767e194`.
- Remote runtime: Python 3.8.10, NumPy 1.24.4.
- h17 access was read-only. The checker opened arrays with NumPy memory
  mapping and streamed SHA-256; it wrote nothing on h17.
- Roots:
  `/data/Faber2026/runs/flits-runs/data` and
  `/data/research/astrophysics/frbs/chime-dsa-codetections/manifest_cubes`.
- Inventory: 24 files, 12 filenames appearing once in each root. Every pair is
  byte-identical. Each file is a 1024 × 32000 float32 array of 131,072,128
  bytes.

## Pre-registered test

For each cube, form the NaN-aware frequency mean. Estimate noise as 1.4826
times the median absolute deviation from the profile median. Require:

1. at least one time sample above 5 sigma;
2. no sample above 5 sigma in either outer 2% of the time axis; and
3. the signal-to-noise-weighted centroid of samples above 5 sigma inside the
   central 20% of the 32000-bin window.

The criteria are fixed in
`docs/rse/specs/plan-trust-reset-revalidation.md` P2.3. A missing 5-sigma
detection is a failed acceptance test but not positive evidence of wrapping.
Thresholds were not adjusted after seeing the data.

## Results

Each row represents both byte-identical copies, so the table covers all 24
files. `Edge hot` is the number of greater-than-5-sigma samples in the two edge
regions combined.

| Burst | SHA-256 | Maximum S/N | Edge hot | Centroid / 32000 | Verdict per copy |
|---|---|---:|---:|---:|---|
| casey | `79e9cba92716263d7644cafafe4d35a3ea646f18509be094033b67c6fc4440c4` | 118.684 | 0 | 0.50276 | pass |
| chromatica | `609a8751415323f3191ea2f45b07d6598c5336247f523eda887668f26b29b2b5` | 19.118 | 0 | 0.50736 | pass |
| freya | `55561c3d9daad2023f876d62e7579ecea987b214022882a6930fe8c242d59f80` | 30.331 | 0 | 0.50548 | pass |
| hamilton | `86be9081500950735bd3f5d5cdd3370f101c260501f56001bb9cc9ce439652cb` | 45.646 | 0 | 0.50029 | pass |
| isha | `c372d6cb2ef62c1ceca28fb6f130cc6fac253bcf97087c3f0555c3f4580b9c2c` | 4.877 | 0 | — | inconclusive: no >5σ detection |
| johndoeII | `d5f35c8b94de82dbc080938bf8e2ce4b725d189d8e5c66ef83b3ca6c84edede6` | 6.735 | 0 | 0.50198 | pass |
| mahi | `be722c48157beb989c53b209f0842e5445f08d7695cba49f23593c6b5d06d61f` | 4.375 | 0 | — | inconclusive: no >5σ detection |
| oran | `73ca14a4d467e7a612cb5c8a9df5d1b17e4dba448e23710663dd1195b0f12092` | 4.265 | 0 | — | inconclusive: no >5σ detection |
| phineas | `6f2e3f4c09c131af98dc061e3788fae6817406f4239e77e91dbe209631ebccd7` | 4.817 | 0 | — | inconclusive: no >5σ detection |
| whitney | `fb1e5c93291cf35d0b269ebfa6a63409954b4da0aac097b404b926c380f24959` | 5.571 | 0 | 0.49988 | pass |
| wilhelm | `fe64e87f4a0e33b73572ea498a1b6ba2405d38a979a15dc858647b33357e7c65` | 9.403 | 0 | 0.50178 | pass |
| zach | `bf317648879936ce4d019f116c17e0c33a22042610e37bddceef0ba48fe40deb` | 33.299 | 0 | 0.52049 | pass |

Totals: 16 direct passes; 8 inconclusive copies; 0 edge-significance
detections; 12 of 12 paired hashes match.

## Scientific verdict

The direct array test finds **no positive evidence that any of the 24 cubes
contains the generation-1 wrap defect**. It rules out the pre-registered edge
signature for the sixteen copies with detected profiles. It cannot rule the
defect out for isha, mahi, oran or phineas because the required signal is below
5 sigma in both byte-identical copies.

The full lineage gate remains open. Closing it requires a more sensitive,
pre-registered follow-up for the four inconclusive unique cubes and the
builder/cross-lineage checks specified by P2.1 and P2.3. No scattering fit or
manuscript value becomes trusted from this receipt alone.

## Reproduction

- Production calculation has no random inputs. Tests use NumPy seed `20260904`.
- Remote environment: Linux 5.4.0-216, Python 3.8.10, NumPy 1.24.4.
- Local test environment: macOS arm64, Python 3.14.7, uv 0.12.9; locked by
  `analysis/uv.lock` at SHA-256
  `3af5a39d2dd51bbb6e833df933fb0891156d62b7e0a7501ccceb496ee2cee43c`.
- From the repository root, reproduce the read-only h17 calculation with:

  ```bash
  ssh -o BatchMode=yes h17 'python3 -' \
    < analysis/scripts/check_chime_scattering_lineage.py
  ```

- Reproduce local invariants with:

  ```bash
  cd analysis
  uv run --group test --frozen pytest -q tests/test_chime_scattering_lineage.py
  ```

An independent rerun at `2026-09-04T18:49:08Z` reproduced all 24 file hashes,
12 matching pairs, 16 passes, eight inconclusive copies, zero edge detections,
and every reported maximum signal-to-noise ratio and centroid.
