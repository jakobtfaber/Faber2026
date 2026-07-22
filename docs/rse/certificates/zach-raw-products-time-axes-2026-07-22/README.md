# Zach raw products and coordinate audit

Status: **owner accepted 2026-07-22**. This accepts the source identities and
coordinate conventions below. It does not accept a new dispersion-measure fit
or science result.

| Item | DSA-110 | CHIME/FRB |
|---|---|---|
| Original product | `220207aabh_dev_polcal_I.fil` | `singlebeam_210456524.h5` |
| Authority path | `dsastorage:/mnt/data/dsa110/candidates/candidates/220207aabh/Level3/…` | `h17:/data/Faber2026/data/chime-frb/zach/…` |
| SHA-256 | `074cf21a…bac79` | `215079a6…f1a9` |
| Native array | 20,480 × 6,144 Stokes-I samples | 871 × 2 × 55,949 complex-voltage and power samples |
| Time sampling | 32.768 μs; `tstart=59617.808504` MJD | 2.56 μs; per-channel `time0` plus FPGA offsets |
| Frequency sampling | 6,144 descending centres; 30.51757812 kHz | 871 of 1,024 descending centres; 390.625 kHz |
| Dedispersion record | Incoherent; DSA `DM (opt)` = 262.3 pc cm⁻³; referenced to 1530 MHz | Power records coherent DM = 262.4359033801 pc cm⁻³; voltage records no DM |
| Do not substitute | Heimdall trigger DM 263.0 for the optimized/applied DM | Power DM for voltage history |

The original DSA `220207aabh_filaxes.json` is partial metadata. Its channel mask
and 6,144-channel identity belong to the Level-3 package, but its 5,120-entry
time array does not cover the current 20,480-sample filterbank. Its last listed
frequency also differs from the SIGPROC header's channel-centre formula. It is
therefore not used as the full coordinate axis.

The DSA dispersion measure comes from
`dsastorage:/mnt/data/dsa110/gechen/software/DSA110-FRBs_231121.csv`, row
`Candname=220207aabh`: `DM (Heimdall)=263.0`, `DM (opt)=262.3`. The filterbank
header and `filaxes.json` do not duplicate either field. The Level-3 workflow
passes that optimized value to `dsa110-bbproc/toolkit`; its delay equation is
explicitly relative to 1.53 GHz. The calibrated Level-3 writer preserves those
already-dedispersed samples and their header.

CHIME's pinned `baseband-analysis` code defines two conventions. Coherent
whole-channel time shifting defaults to 400 MHz. Incoherent alignment defaults
to `min(f)`, which is 400.390625 MHz for Zach's native retained coarse channels.
The approved Zach preprocessing used `--no-time-shift` and no separate
incoherent step: coherent de-smearing was applied, while padded arrival-time
alignment remains downstream work from the per-channel `time0` metadata.

## Common timing convention for later work

- Preserve each native sample index without an unproven half-sample shift.
- DSA provisional coordinate: `tstart + sample_index × 32.768 μs`; retain the
  unknown edge-versus-centre convention and unencoded time scale.
- CHIME coordinate: first reconstruct each channel's FPGA dump time from its
  `time0` row. The recorded rows share the exact FPGA epoch
  `2022-01-27T18:58:36.999999960` UTC under the producer function. Then add the
  stored sample `offset_fpga × 2.56 μs`.
- Do not align the two instruments by crop position. Later time-of-arrival work
  must carry these native conventions and a measured inter-instrument offset.

## Exact read-only extraction commands

```bash
ssh h17 'sha256sum /data/Faber2026/data/dsa-110/zach/220207aabh_dev_polcal_I.fil /data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5'

ssh h17 'stat -c "%n %s %y" /data/Faber2026/data/dsa-110/zach/220207aabh_dev_polcal_I.fil /data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5'

ssh dsastorage 'sha256sum /mnt/data/dsa110/candidates/candidates/220207aabh/Level3/220207aabh_dev_polcal_I.fil /mnt/data/dsa110/candidates/candidates/220207aabh/Level3/220207aabh_filaxes.json /mnt/data/dsa110/gechen/software/DSA110-FRBs_231121.csv'

ssh dsastorage 'python3 - <<"PY"
import csv
p = "/mnt/data/dsa110/gechen/software/DSA110-FRBs_231121.csv"
with open(p, newline="") as fh:
    rows = csv.DictReader(fh)
    print(next(row for row in rows if row["Candname"] == "220207aabh"))
PY'

ssh h17 'python3 - <<"PY"
from blimpy import Waterfall
w = Waterfall("/data/Faber2026/data/dsa-110/zach/220207aabh_dev_polcal_I.fil", load_data=False)
print(w.header)
print(w.file_header)
print(w.container.idx_data, w.container.n_ints_in_file, w.container.file_shape)
PY'

ssh h17 'python3 - <<"PY"
import h5py
p = "/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5"
with h5py.File(p) as f:
    print(dict(f.attrs))
    for name in ("index_map/freq", "index_map/time", "time0", "tiedbeam_baseband", "tiedbeam_power"):
        d = f[name]
        print(name, d.shape, d.dtype, dict(d.attrs))
PY'
```

The CHIME FPGA epoch was checked in the pinned container
`chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`
with `baseband_analysis.core.sampling.fpga_start_time`. The full extracted
values and all unresolved fields are in `metadata.json`.

The reference-frequency trace is recorded in
[`research-zach-dedispersion-reference-frequencies.md`](../../specs/research-zach-dedispersion-reference-frequencies.md).

## Owner decision

Accepted 2026-07-22 after review of `native-grids.svg`. The source identities,
native coordinates, and explicit unknowns are adequate inputs to the next
dispersion-measure ticket. The decision accepts 262.3 pc cm⁻³ as the
DSA-recorded optimized/applied starting value at 1530 MHz, not as a new fitted
result.
