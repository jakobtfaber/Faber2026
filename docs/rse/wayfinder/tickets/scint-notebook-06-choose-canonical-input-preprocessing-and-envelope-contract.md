<!-- wayfinder:ticket -->
# Ticket: Choose canonical input, preprocessing, and burst-envelope contract

- Type: grilling
- Status: resolved
- Assignee: codex
- Blocked by: [`scint-notebook-01-locate-canonical-scintillation-code-and-data.md`](scint-notebook-01-locate-canonical-scintillation-code-and-data.md)
- Map: [`../map-interactive-scintillation-notebook.md`](../map-interactive-scintillation-notebook.md)

## Question

Which CHIME/FRB and DSA-110 Stokes-I products are authoritative notebook inputs; how are those products converted into the canonical dynamic-spectrum representation; which preprocessing failures must stop analysis; and how are band-specific, multi-component burst and off-pulse envelopes chosen, reviewed, and recorded before autocorrelation fitting?

## Resolution

Owner-ratified contract:

1. **Band-specific input authority**
   - CHIME/FRB: the verified upchannelized waterfall `.npy`, frequency-axis `.npy`, and time-metadata JSON form one inseparable source set.
   - DSA-110: the CANFAR `DynamicSpectrum` NPZ is authoritative. A local copy is usable only after its hash matches that object.
   - Native-resolution CHIME cubes and local DSA-110 cubes are not substitute scintillation inputs. Establishing a new lineage requires separate validation.

2. **Conversion and cache boundary**
   - A deterministic preflight outside the notebook builds or verifies an analysis-ready cache.
   - CHIME packaging records all three source hashes, time-axis synthesis parameters, builder revision, schema version, output hash, and physical-axis checks.
   - DSA preflight verifies the authoritative NPZ hash and schema; it does not regenerate the product.
   - The notebook consumes the verified cache read-only. It neither constructs nor overwrites caches.

3. **Fail-closed preprocessing**
   - Order: verify provenance/schema/axes; establish band-specific burst and off-pulse windows; mask radio-frequency interference while protecting those windows; fit and subtract the off-pulse baseline; then check usable support before autocorrelation fitting.
   - Stop on missing or mismatched provenance, invalid or non-monotonic axes, window overlap, insufficient off-pulse support, masking or baseline failure, excessive masking, or insufficient usable channels in any requested sub-band.
   - No broad exception handler may turn a failed required stage into a warning or success message. Preprocessing changes a run-local working copy, never the cache.

4. **Burst-envelope contract**
   - CHIME/FRB and DSA-110 use independently selected windows; one band's window is never copied to the other.
   - Automated detection may propose a window. The reviewer must see the dynamic spectrum and profile before accepting or overriding it.
   - A multi-component envelope spans the first through last component, with band-specific off-pulse padding. The off-pulse window is emission-free, disjoint from the envelope and guard region, and checked for representative noise.
   - Record bin indices, physical time bounds, selection method, source/cache/config hashes, diagnostic artifact, reviewer decision, and any override rationale.
   - Owner visual review is required before an envelope-dependent measurement can leave diagnostic status.

5. **Scientific boundary**
   - Passing this contract establishes reproducible inputs and preprocessing only. It does not validate an autocorrelation fit, scaling exponent, or manuscript claim.
