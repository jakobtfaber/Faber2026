# Handoff

## State
Joint-model figure prototypes for freya in `figures/prototypes/freya/` (vA/vB/vC, untracked). `plot_jointmodel_prototypes.py` uses **measured TOA** (`toa_crossmatch_results.json` `measured_offset_ms` @400 MHz), not joint-fit t0 co-alignment. Manuscript has DSA-only `jointmodel_montage` only; CHIME+DSA layout not picked yet.

## Next
1. User picks layout (vA/vB/vC) → batch all bursts + manuscript figure
2. Commit prototypes script + optional push pipeline branch

## Context
Dual-band time axes: measured TOA @400 MHz. Layout: tight on-pulse xlim + grey `///` hatch strip for unobserved 0.80–1.31 GHz between DSA/CHIME rows (vA/vC) or cols (vB).
