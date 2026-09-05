# CHIME aligned central-waveform verification

**Four passes; three inconclusive. No whole-cube certification.** Read-only h17
execution completed September 4, 2026 (Pacific time). Fresh references were
reconstructed from canonical singlebeam voltages at each native cube's
dispersion measure. Alignment used separate noncentral samples, never the
tested pulse. All seven full-band and both frequency-half residual lags are
zero, but zero lag alone does not determine acceptance.

No fits launched, manuscript changed, or raw-layer trust granted. This does
not certify downstream science readiness: central discrepancies, edge
provenance and the owner raw-layer spot-check remain open.

## Results

Errors are maximum normalized pointwise differences over untouched validation
and pulse intervals; fixed bound **7.62939453125e-6**. These are numerical
waveform differences, not timing uncertainties.

| Event | Matched / eligible channels | Maximum error | Result |
|---|---:|---:|---|
| casey | 720 / 720 | 2.002e-6 | Central-waveform pass |
| freya | 717 / 717 | 2.626e-6 | Central-waveform pass |
| isha | 729 / 729 | 2.079e-6 | Central-waveform pass |
| mahi | 670 / 670 | 2.023e-6 | Central-waveform pass |
| oran | 728 / 729 | 2.023e-6 on matched channels | Inconclusive: channel 466 alignment |
| phineas | 739 / 739 | 6.082e-4 | Inconclusive: channel 910 waveform |
| whitney | 694 / 694 | 7.769e-3 | Inconclusive: channels 241, 352, 544 waveforms |

All eligible channels exist in the voltage files. Constant native rows are
excluded and individually listed in the machine receipt: counts 4, 15, 12,
18, 13, 8, 19 respectively. No substantive missing channel was dropped.
Reconstructed 400-MHz origin spreads are 1.067–1.084 native bins, within the
declared 1.1-bin integer-placement consistency bound.

Targeted read-only diagnosis of Oran 466 found training and validation
correlations above 0.9999999999998, but an alternative alignment correlation
0.5738268909839124 exceeds the fixed 0.5 ceiling. Candidate origin: 23621 raw
samples. Phineas 910 aligns at 15038 raw samples, but high correlation does
not excuse its pointwise discrepancy. Thresholds and channel support were
not relaxed; the discrepancy causes remain unresolved.

The six historical failures stretched unequal-duration records to 32000
points without arrival-time alignment. Those lags were not valid tests of
the five-native-bin bound. The original CSV remains intact. This execution
supersedes it only for central comparison to fresh native-rate voltage
references: Casey, Freya, Isha and Mahi pass; Phineas and Whitney remain
inconclusive. Oran is the additional low-signal target.

## Whole-window limitations

First/last 4096-sample correlations are separate diagnostics. Counts below
use correlation below 0.95; missing edge coverage is not disagreement.

| Event | Early disagreement | Late disagreement | Channels missing some reference edge coverage |
|---|---:|---:|---:|
| casey | 0 | 709 | 11 |
| freya | 0 | 573 | 144 |
| isha | 0 | 728 | 0 |
| mahi | 0 | 628 | 42 |
| oran | 728 | 0 | 0 |
| phineas | 739 | 0 | 0 |
| whitney | 0 | 694 | 0 |

Every event has edge disagreements. Missing reference samples are not wrapped
into the comparison. Central identity does not establish complete-window
builder history or close the complete P2.3 gate.

## Low-signal bursts

The initial [audit](audit.json) retains 35 input hashes and 27 descriptive
diagnostic rows. Its null aligned lags describe that earlier stage, not this
final execution. Fixed 256-sample means span 655.36 microseconds.

| Event | Native central maximum / noise | 256-sample central maximum / noise | Aligned outcome |
|---|---:|---:|---|
| isha | 4.877 | 25.406 | Central-waveform pass |
| mahi | 4.375 | 14.615 | Central-waveform pass |
| oran | 4.265 | 8.905 | Inconclusive alignment support |
| phineas | 4.817 | 24.576 | Inconclusive waveform identity |

Noise is 1.4826 times the median absolute deviation of the averaged profile.
Multiple widths, broad signal and interference prevent interpreting these
maxima as calibrated detection significance. The original native
greater-than-five-noise requirement remains unmet for these four.

## Method and reproduction

The [design](../../specs/experiment-chime-aligned-lineage.md) fixes training
[4096,8192), validation [8192,12288), and pulse [12800,19200) intervals.
Both alignment correlations must be at least 0.95; alternative peaks more than
two samples away must be below 0.5. Affine normalization uses training only.
Every matched validation and pulse sample must meet the fixed error bound.
Full-band and below/above-600-MHz lags must satisfy abs(lag)<5 native bins
(12.8 microseconds), without a search-boundary optimum. Shared noise can force
zero lag for changed weak pulses; pointwise comparison prevents that false pass.

The reference applies intrachannel Fourier de-chirping with K=1/2.41e-4,
subtracting recorded input voltage dispersion measure, without interchannel
phase translation. Sampled stored-power comparisons distinguish this from
the archived producer's time-shift default. Absolute astronomical timing and
timing confidence intervals are not inferred from digital identity.

Final per-channel results, input paths, raw/native SHA-256 values, support,
errors, edge coverage and runtime: [voltage-identity-final.jsonl](voltage-identity-final.jsonl).

Base: `27c7d962d8cf64a897cb81aedfda0fc2cf586eda`.
Executed verifier SHA-256 (first complete run):
`49cceed743eb3c5cbb1a2689168013ee8b4176f2aa2febf9a92c58b725703f0c`.
Executed reporting-corrected verifier SHA-256:
`d7291b750cef01ca9fe4af66e6c02b15013037511928e2a8943d12b09e655fc2`.
The reporting-only correction names otherwise silently skipped unusable
channels. Its full seven-event confirmation run completed successfully;
all seven complete result dictionaries exactly equal the first run in
`voltage-identity.jsonl`, preserving every reported scientific result.
Executed audit verifier SHA-256:
`8910e27b17c6747cf14723979edea4c3d79e55b280497d25924ce6efa8dbf6fa`.
Current source separates input loading, channel collection and reporting,
and simplifies validation conditions; numerical thresholds are unchanged.
Current waveform verifier SHA-256:
`d2924d15c58f659db49cbfbb11d79f66c60458565781c3cfd1a10a97ab251a9b`.
Current audit verifier SHA-256:
`0b256bd46e3e956965a03f1d6b29028923e996e154cc38cf366c66661545dc6a`.
Lockfile SHA-256:
`3af5a39d2dd51bbb6e833df933fb0891156d62b7e0a7501ccceb496ee2cee43c`.

From repository root; outputs local, h17 inputs read-only:

```sh
ssh -o BatchMode=yes h17 'python3 -' \
  < analysis/scripts/audit_chime_alignment_inputs.py \
  > analysis/docs/rse/verify/chime-aligned-lineage-20260904/audit.json
ssh -o BatchMode=yes h17 'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -' \
  < analysis/scripts/verify_chime_voltage_lineage.py \
  > analysis/docs/rse/verify/chime-aligned-lineage-20260904/voltage-identity-final.jsonl
OPENBLAS_NUM_THREADS=1 uv run --project analysis --frozen --group dev pytest \
  analysis/tests/test_chime_alignment_audit.py \
  analysis/tests/test_chime_voltage_lineage.py \
  analysis/tests/test_chime_scattering_lineage.py -q
```

Initial execution: 2026-09-05 04:01:30–04:05:50 UTC, exit 0.
Final reporting-corrected execution: 04:08:19–04:11:22 UTC, exit 0.
Python 3.8.10, NumPy 1.24.4, SciPy 1.10.1, h5py 3.11.0;
Linux 5.4.0-216 x86_64; one numerical-library thread; no random production
steps. Remote environment is reported, not claimed to match the lockfile.

## Correctness checks

- 34 targeted tests pass. Analytic Fourier modes check phase; injected delays
  survive independent alignment. Weak broad pulse shifts and removal fail
  identity even when ordinary correlation returns zero. Twelve in-memory
  criterion-violating mutations were rejected.
  Event-level regressions also require explicit rejected-channel reasons for
  partially nonfinite rows and constant training intervals, without relaxing
  the required channel count; the all-usable control passes.
- A clean isolated lockfile environment (Python 3.12.13, NumPy 2.5.1)
  reproduces Casey channel 33: origin 12480, validation error 7.31504e-7,
  pulse error 7.45777e-7, lag zero. Exported raw/native fixture SHA-256:
  `616197fef2547f3b1d51711cd55d9637765e062c7d62b9af0907068f9dbef4b8`.
- Initial audit independently reproduced 35/35 hashes and 27/27 diagnostic
  rows; record `904e58debf40`.
- Independent review approves the revised design and scoped results
  (record `e57eea010054`), superseding the initial metadata-only design failure.
  Separate sine/cosine Fourier phase and scalar normalization reproduce
  all 14 raw/native hashes, seven sampled channel origins and waveforms,
  and the failing Phineas 910 / Whitney 544 waveform errors. Tables and all
  21 zero lags agree. Final independent approval includes the reporting-only
  correction (fresh review `1d543a02eba2`) and independent confirmation that
  all seven complete output dictionaries equal the earlier run. Final spec,
  receipt and output verification: `e80680420b68`. No implementation findings
  remain; this is not whole-cube certification or merge/CI approval.

Local `voltage-casey.jsonl` and `voltage-results.jsonl` are exploratory
prototypes, not final evidence or intended integration inputs. The latter
was stopped after the shared-noise false-pass finding.
