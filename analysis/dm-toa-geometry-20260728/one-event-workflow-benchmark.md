# One-event workflow timing

Status: metadata-only estimate. No second event was run.

## Measured Casey receipts

H17 receipt: `casey-hybrid/run-provenance.json`.

| Stage | Start | End | Wall time |
|---|---:|---:|---:|
| CHIME/FRB anchored hybrid, including three fully coherent oracle trials | 13:53:30.479420 -0700 | 14:03:20.448146 -0700 | 589.969 s |
| DSA-110 product builder | 14:03:20.448146 -0700 | 14:04:53.072003 -0700 | 92.624 s |
| Measured consecutive tail | 13:53:30.479420 -0700 | 14:04:53.072003 -0700 | 682.593 s |

The DSA input-state audit log ended at 13:53:22.934136 -0700, before the
recorded CHIME start. Its start time was not recorded, so its wall time cannot
be recovered honestly. The new orchestrator records start, end, wall time,
command, and output hashes for every stage.

H17 read-only metadata checked 2026-07-28:

- Casey CHIME H5: 1,037,114,494 bytes.
- Casey DSA filterbank: 503,316,768 bytes.
- pinned cached container: 8,607,876,246 bytes,
  image ID `sha256:8c903ec6a5a8...`.

## One other event estimate

Chromatica was not opened by the science code. Only file sizes were read:
CHIME H5 1,031,538,710 bytes; DSA filterbank 503,316,768 bytes.

With the same U16 grid, one coherent anchor, three fully coherent oracle
trials, and accepted-support shape, the CHIME size ratio is 0.994624. A simple
linear estimate is 586.8 s. The equal DSA file size gives 92.6 s for its product
stage. Allow roughly 12 minutes warm, plus the unmeasured audit, geometry,
packet, and manifest stages.

A cold run adds the pinned image pull. Its 8.61 GB local size has ideal transfer
floors of 69 s at 1 Gbit/s, 138 s at 500 Mbit/s, or 275 s at 250 Mbit/s, before
registry, decompression, and disk overhead. Therefore a defensible cold
estimate is the warm estimate plus the measured image-pull time on that host;
none was fabricated from the cached-image run.

These are capacity estimates, not scientific validation or authorization to
run Chromatica.
