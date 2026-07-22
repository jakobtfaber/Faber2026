# Research: sample raw products and time axes

**Date:** 2026-07-22

**Codebase state:** `Faber2026` branch `codex/prototype-chime-rfi-preservation-gates`, starting commit `1250b26a`

**Scope:** Eleven events beyond the accepted Zach reference

## Question

For every paired event, what are the preliminary DSA-110 filterbank and
CHIME/FRB single-beam HDF5 products, their dispersion state, native time and
frequency coordinates, and remaining provenance ambiguities?

## Findings

1. All 24 current project products are present on `h17`; live SHA-256 values
   match the migration manifest.
2. All DSA-110 files share one 20,480 × 6,144 grid at 32.768 μs and
   30.51757812 kHz. Producer code selects the optimized dispersion measure and
   references delays to 1530 MHz. Neither value is embedded in the final
   filterbank header.
3. CHIME/FRB grids differ by event: 756–907 of 1,024 coarse channels are
   retained, with 55,938–72,845 time samples at 2.56 μs. Missing channels are
   explicit in each HDF5 frequency index.
4. Every voltage dataset lacks a dispersion-measure attribute. Every power
   dataset has `DM_coherent`. The power value cannot establish voltage
   processing history.
5. Eight non-Zach DSA candidate files are byte-identical between `dsastorage`
   and the `h17` project copy. Mahi and Casey differ on current `dsastorage`,
   and Chromatica is absent there. All three have byte-identical recovery
   copies under `h23:/dataz/dsa110/candidates/`.

## Evidence

- `h17`: live filterbank and HDF5 headers plus recomputed SHA-256 values.
- `h24`: DSA producer table and the table → `DM0` → beamformer → toolkit code
  chain, all hash-pinned in the certificate.
- `dsastorage`: current Level-3 files, sidecars, hashes, and missing-file state.
- `h23`: live hashes for the Mahi, Chromatica, and Casey recovery copies.
- Pinned CHIME container: per-file FPGA clock epochs using the producer's own
  function.

The durable evidence is
[`sample-raw-products-time-axes-2026-07-22`](../certificates/sample-raw-products-time-axes-2026-07-22/README.md).

## Limits

- Exact DSA per-run command logs were not found.
- CHIME voltage dedispersion history is not encoded in the source product.
- Neither format establishes sample edge versus centre; DSA time scale is also
  not encoded.
- The extraction establishes inputs and conventions, not fitted dispersion
  measures or validated bad-channel maps.

## Decision

Eleven event records await owner review. Zach remains the sole accepted raw
coordinate reference until those decisions are recorded.
