# Validation Complete: Zach CHIME preprocessing baseline

> Validated against `plan-zach-chime-preprocessing-baseline.md` /
> `implement-zach-chime-preprocessing-baseline.md` at parent commit `e1eb74b0`
> and merged pipeline commit `ab6af1f7` on 2026-07-21.

## Overall Status: Issues Found

- Phases: 3 of 3 implemented.
- Automated checks: 7 passing, 0 failing.
- Manual testing: 1 owner review remains.
- Critical implementation issues: 0.
- Important scientific-method issues: 1 — current RFI excision is rejected.

## Implementation Status

### Phase 1: Durable migration preflight

**Status:** Fully implemented.

- Complete 51-path packet: pass.
- Atomic local then remote persistence: pass.
- Matching SHA-256 gate before mutation: pass.
- Journal binding and source re-stat: pass.
- Historical move left honestly unchanged: pass.

### Phase 2: Nominal-grid worker

**Status:** Fully implemented and merged through pipeline PR
[#216](https://github.com/jakobtfaber/dsa110-FLITS/pull/216).

- Fine-channel identifier preservation: pass.
- Exact 65,536-position nominal grid: pass.
- Missing=`NaN`, source-valid=false: pass.
- Package and nominal coordinates both retained: pass.
- Always-on provenance metadata: pass.

### Phase 3: Live Zach run and preprocessing audit

**Status:** Fully implemented as a diagnostic; science use remains blocked.

- Read-only, network-disabled live run: pass.
- Input/output invariant checks: pass.
- Disjoint off-pulse training and validation: pass.
- Five planned variants plus one ordering control: pass.
- Science fit or promotion: correctly not run.

## Automated Verification Results

- `pytest -q tests/test_h17_source_data_layout.py` — 12 passed.
- Focused pipeline suite — 15 passed.
- Audit-only repeat after warning handling — 3 passed, no warnings.
- `python3 -m py_compile` for all changed Python entry points — passed.
- Parent and pipeline `git diff --check` excluding generated SVG whitespace — passed.
- Live grid assertion — 65,536 total, 55,744 source-present, 9,792 missing.
- Live source SHA-256 before/after — unchanged.

No automated verification failed.

## Code Review Findings

### What matches the plan

- Mutation is unreachable before durable matching preflight evidence.
- Missing data never become measured zero-valued data.
- The live worker is byte-identical to pipeline commit `67d6a670` and is now
  contained in merged commit `ab6af1f7`.
- Cleaning models use no burst or held-out validation sample.
- The output is explicitly diagnostic-only and does not claim science readiness.

### Deviations from the plan

1. The package's inclusive fine-frequency coordinate differs from exact nominal
   centers by up to half a fine channel. Integer identifiers became authoritative,
   and both coordinates are emitted. This is safer than silently choosing one.
2. A sixth control, bandpass then RFI, was added after the planned combined
   sequence failed. It isolated operation order without changing the source or
   fitting science.

Both deviations are accepted and evidence-bearing.

### Potential issues

- The current RFI routine is scientifically inadmissible for this product.
- Bandpass gains vary by roughly 29% between training halves; stationarity is
  not established.
- Dispersion measure and time-axis interpretation remain outside this ticket.

## Manual Testing Required

1. Review the [diagnostic figure](../verify/zach-chime-preprocessing-20260721/zach_rfi_bandpass_audit.svg)
   and the no-go interpretation below. Expected outcome: accept the nominal
   grid/mask contract while leaving current RFI/bandpass science use blocked.

## Recommendations

### Critical

- None for merge or custody.

### Important

- Keep CHIME scintillation ratification blocked.
- Test any next RFI method only after an independently stable bandpass model,
  with held-out improvement and stationarity gates.

### Nice to have

- Reduce plotting density in a future review-only figure; the committed SVG is
  diagnostic evidence, not a manuscript figure.

### Follow-up work

- Validate Zach's dispersion measure and exact time axis before science.
- Open a separate bounded RFI-method ticket; do not expand this baseline ticket.

## Technical Verdict

## Verdict

- **PASS — source preservation:** Zach H5 SHA-256 remained
  `215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9`.
- **PASS — nominal grid:** factor 64 output has 65,536 positions: 55,744
  source-present and 9,792 missing. Missing values are `NaN` and mask=false.
- **PASS — padding neutrality:** compact and padded held-out metrics are identical.
- **PASS — bandpass necessity:** off-pulse normalization removes most static
  spectral response on held-out data.
- **FAIL — current RFI excision:** the package RFI pass is unstable and worsens
  the held-out coarse-grid response when applied before bandpass correction.
- **NO-GO — science:** this product is a preprocessing diagnostic. It does not
  validate Zach's dispersion measure, arrival time, scintillation, scattering,
  or any manuscript claim.

## Frozen input and runtime

| Item | Verified value |
|---|---|
| Source | `/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5` |
| Source size | 1,171,470,638 bytes |
| Source SHA-256 | `215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9` |
| Container | `chimefrb/baseband-analysis` |
| Repository digest | `sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41` |
| Image identifier | `sha256:8c903ec6a5a836e8a97fe3468fd3ee02177c220ead84e6d1d25e8f41b735db4b` |
| Package | `baseband-analysis` 1.9.0; `/opt/pysetup` revision `e08df9dacc49e1007f28759b7edca71c7b8e5273` |
| Worker SHA-256 | `1825746445782cb2f36b806668241cfcd7e03a9c11531457b903d43974007b4e` |
| Audit-v2 SHA-256 | `5df48f411c6d9f9ce59873b6ccb147de30e22fa8306b3543bb06632212340c83` |
| Remote evidence root | `/data/Faber2026/evidence/zach-chime-preprocessing-20260721/` |

Live checks found no competing baseband job, 1.4 TB free, and no pre-existing
evidence directory. The source was mounted read-only; the container had no
network; outputs were confined to the new evidence directory.

## H5 processing state

- Root metadata records event `210456524`, archive `NT_3.1.0`, base sample
  interval 2.56 microseconds, and producer revision
  `0ec3f4c38b56389b2e4193dcc23877e9593818d`.
- `tiedbeam_baseband` has no `DM` attribute. `coherent_dedisp` therefore reported
  `DM0=0` and applied the worker's full provisional value 262.368 pc cm⁻³.
- `tiedbeam_power` separately records `DM_coherent=262.4359033801`. That derived
  power attribute is not proof that the voltage dataset was already dedispersed.
- The run used `--no-time-shift`; it did not circularly shift short buffers.
- The worker value 262.368 is not adopted. Prior full-resolution referral value
  262.3621 differs, and the time-axis/arrival-time audit remains open.

## Channel restoration

The H5 contains 871 unique coarse identifiers from 2 through 1,023; 153 are
absent. At factor 64:

| Quantity | Value |
|---|---:|
| Nominal fine positions | 65,536 |
| Source-present fine positions | 55,744 |
| Source-missing fine positions | 9,792 |
| Time bins | 437 |
| Nominal spacing | 6.103515625 kHz |
| Maximum package/nominal coordinate difference | 3.0517578125 kHz |

Integer fine-channel identifiers are authoritative. The worker emits both:

- exact nominal centers:
  `800.1953125 - (fine_id + 0.5) * (0.390625 / 64) MHz`;
- the package's inclusive-linspace coordinate, preserved for provenance.

No source H5 dataset is rewritten. Package `fill_waterfall(write=True)` is not
used because it zero-fills missing voltages and invents timing rows.

## Exact live processing command

```bash
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=2g \
  -v /data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5:/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5:ro \
  -v /data/Faber2026/evidence/zach-chime-preprocessing-20260721/code:/work/code:ro \
  -v /data/Faber2026/evidence/zach-chime-preprocessing-20260721/products:/work/products:rw \
  chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41 \
  python /work/code/upchannelize_chime.py zach \
  --out /work/products --scratch /tmp --save-polarizations --no-time-shift
```

The run completed with `shape=(65536, 437)`, 6.104 kHz spacing, 0.3277 ms
time cadence, and 78.4% finite values over the full nominal array.

## RFI and bandpass audit

All model values were learned only from off-pulse bins 55:137. Bins 138:220
were held out for validation. The burst window was never used. The current
package RFI routine iteratively flags frequency rows whose time mean or standard
deviation is an outlier after a linear spectral detrend. Bandpass correction
subtracts each training-channel mean and divides by its training-channel sample
standard deviation; undersampled or nonpositive scales are masked.

| Variant | Nominal masked | Lag-1 frequency correlation | Coarse comb fraction | Verdict |
|---|---:|---:|---:|---|
| Compact / grid only | 14.94% | 0.9166 | 0.3330 | Padding neutral; static response dominant |
| RFI only | 22.75% | 0.9501 | 0.3785 | Worse |
| Bandpass only | 14.94% | 0.1861 | 0.01613 | Large improvement; residual structure remains |
| Bandpass → RFI | 15.60% | 0.1851 | 0.01600 | Negligible change; 432 rows added |
| RFI → bandpass → RFI | 23.34% | 0.1395 | 0.01782 | Lower correlation, but excessive/unstable mask and worse comb than bandpass-only |

Additional stability checks:

- RFI-mask agreement between the two halves of the training window: Jaccard
  0.649. This is too unstable for adoption.
- Bandpass-scale half-to-half log-ratio robust spread: 0.256, corresponding to
  roughly 29% multiplicative spread. The estimated gain is not yet stationary.
- Pre-bandpass RFI flagged 5,118 source-present rows. Post-bandpass-only RFI
  flagged 432. The operation order controls most of the masking difference.

Interpretation: bandpass correction is mandatory. The present
`get_RFI_channels` thresholds/order are not a standardized science method.
Bandpass-first RFI adds almost no held-out improvement; pre-bandpass RFI removes
far more data and gives an unstable mask. Neither is accepted for scintillation.

## Evidence

- [Preprocessing metadata](../verify/zach-chime-preprocessing-20260721/zach_chime_preprocessing_metadata.json)
- [Held-out audit JSON, including ordering control](../verify/zach-chime-preprocessing-20260721/audit-v2/zach_preprocessing_audit.json)
- [Readable diagnostic figure](../verify/zach-chime-preprocessing-20260721/zach_rfi_bandpass_audit.svg)
- [Baseband run log](../verify/zach-chime-preprocessing-20260721/baseband-run.log)
- [Audit-v2 run log](../verify/zach-chime-preprocessing-20260721/audit-v2-run.log)
- [Remote evidence checksums](../verify/zach-chime-preprocessing-20260721/SHA256SUMS)

The remote packet contains 36 hashed files and occupies 334 MB. Both audit runs
recorded exit 0. No processing container or audit process remained after closeout.

## Next method decision

The nominal grid/mask contract is ready for reuse. The next RFI ticket must test
a mask learned after an independently stable bandpass model, use explicit
stationarity gates, and prove improvement on held-out off-pulse data. Until then,
[Ratify the CHIME-band scintillation method](../wayfinder/tickets/02-ratify-chime-scintillation-method.md)
remains blocked.

## References

- [Plan](plan-zach-chime-preprocessing-baseline.md)
- [Implementation](implement-zach-chime-preprocessing-baseline.md)
- [Research](research-zach-chime-preprocessing-baseline.md)
