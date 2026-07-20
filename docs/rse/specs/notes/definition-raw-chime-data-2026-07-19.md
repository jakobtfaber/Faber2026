# Definition: raw CHIME data

**Owner decision 2026-07-19. Binding.**

## Raw CHIME data

The **only** raw CHIME data for this project are the twelve singlebeam
voltage files:

```text
h17:/data/research/astrophysics/frbs/chime-dsa-codetections/chime_singlebeam/singlebeam_<event_id>.h5
```

| Nickname   | File                         |
|------------|------------------------------|
| zach       | `singlebeam_210456524.h5`    |
| whitney    | `singlebeam_215063905.h5`    |
| oran       | `singlebeam_224263996.h5`    |
| isha       | `singlebeam_252069198.h5`    |
| wilhelm    | `singlebeam_253635173.h5`    |
| phineas    | `singlebeam_274819243.h5`    |
| freya      | `singlebeam_278720455.h5`    |
| johndoeII  | `singlebeam_311723353.h5`    |
| hamilton   | `singlebeam_318353610.h5`    |
| mahi       | `singlebeam_354049284.h5`    |
| chromatica | `singlebeam_356959136.h5`    |
| casey      | `singlebeam_362593221.h5`    |

Live presence on h17 confirmed 2026-07-19 (~1 GB each). Upstream copies also
exist on CANFAR under
`arc:projects/chime_frb/data/chime/baseband/processed/<date>/astro_<id>/singlebeam_<id>.h5`;
h17 is the staged working set used for analysis builds.

These files are **voltages**. A dispersion measure is **not** frozen in them;
it is chosen when a dynamic-spectrum product is built from the voltages.

## Not raw data

Everything else derived from those voltages is **not** raw data. That includes,
without exception:

- full-resolution CHIME intensity cubes (`.npy` on CANFAR / local `DSA_bursts/`)
- upchannelized CHIME products and companion frequency files
- packaged scintillation `.npz` products
- any remade / remediated upchannelized directories
- fits, tables, figures, and manuscript numbers

Those products are **derived inputs**. They must carry an explicit applied
dispersion measure and build provenance; they must not be called “raw.”

## Consequence for certification

Stratum-0 / “raw-layer” certification for CHIME means certifying the twelve
`.h5` voltage files (bytes, lineage, host path). Certifying `.npy` products is
a derived-input (stratum-1) concern, including which dispersion measure was
applied when they were built.
