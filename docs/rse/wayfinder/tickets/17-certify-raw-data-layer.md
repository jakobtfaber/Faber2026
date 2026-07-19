# Stratum 1 — Certify the raw data layer (L0)

- Type: `wayfinder:task` (AFK build + owner spot-check)
- Status: open — **frontier; START HERE in the new session**
- Assignee: —
- Blocked by: —
- Blocks: [18](18-redo-dm-analysis-certified.md)
- Map: [ApJ submission](../map-apj-submission.md)

## Question

Certify the byte layer for all input products (12 bursts × {CHIME full-res,
CHIME upchan+freq, DSA}): checksums + lineage (gen-2+, builder identity, h5
source), and **axis conventions asserted from the data** (freq order per
product — the full-res order was assumed descending, never verified; upchan
is ascending). Deliverable: an L0 certificate table (registry section) +
executable convention tests (freq-order asserts, dedispersion sign test as a
unit test). Owner involvement: spot-check only. Per verification-protocol
Tier 0; nothing above L0 opens until this lands.
