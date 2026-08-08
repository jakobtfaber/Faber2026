# Definition: raw CHIME data

**Owner decision 2026-07-19. Binding.**

## Raw CHIME data

The only raw CHIME data for this project are the twelve singlebeam voltage
files:

```text
h17:/data/research/astrophysics/frbs/chime-dsa-codetections/chime_singlebeam/singlebeam_<event_id>.h5
```

| Nickname | File |
|---|---|
| zach | `singlebeam_210456524.h5` |
| whitney | `singlebeam_215063905.h5` |
| oran | `singlebeam_224263996.h5` |
| isha | `singlebeam_252069198.h5` |
| wilhelm | `singlebeam_253635173.h5` |
| phineas | `singlebeam_274819243.h5` |
| freya | `singlebeam_278720455.h5` |
| johndoeII | `singlebeam_311723353.h5` |
| hamilton | `singlebeam_318353610.h5` |
| mahi | `singlebeam_354049284.h5` |
| chromatica | `singlebeam_356959136.h5` |
| casey | `singlebeam_362593221.h5` |

Live presence on h17 was confirmed 2026-07-19. Upstream copies also exist on
CANFAR under
`arc:projects/chime_frb/data/chime/baseband/processed/<date>/astro_<id>/singlebeam_<id>.h5`.

These files are voltages. A dispersion measure is not frozen in them; it is
chosen when a dynamic-spectrum product is built.

## Not raw data

Full-resolution intensity cubes, upchannelized products, packaged
scintillation products, remediated products, fits, tables, figures, and
manuscript numbers are derived. Derived inputs must record the applied
dispersion measure and build provenance.

## Certification consequence

Raw-layer certification covers the twelve voltage files: bytes, lineage, and
host path. Dynamic-spectrum certification is an Input Data Product concern.
