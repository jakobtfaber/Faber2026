# Rebuild upchannelized products (Input Data Products + data cards)

- Type: `wayfinder:task` (AFK build + HITL card approval)
- Status: open
- Assignee: —
- Blocked by: [18](18-redo-dm-analysis-certified.md)
- Blocks: [22](22-redo-scintillation-certified.md)
- Map: [ApJ submission](../map-apj-submission.md)

## Question

Rebuild all 12 CHIME upchannelized products at the adjudicated alignment
DMs (corrected-sign transform, sub-bin interpolation) with the aggressive
RFI recipe (owner spec: spectral kurtosis + MAD z + time-domain spikiness +
iteration; visual bar = no visible streaks; renderer views its own output);
fix the DSA central-channel RFI (live in isha/phineas/zach). Never touch
originals; new directory with md5-chained provenance. Deliverable: **12
hash-bound data cards** for owner approval — the Input Data Product certificates that gate
the scintillation stratum. Failed prior attempts (weak masks, catalog-DM
alignment, sign bug) are documented in the ticket-18 handoff; do not repeat.
