# Machine inventory — live verification 2026-07-06

---
**Date:** 2026-07-06 (evening)
**Author:** claude-fable-5/session-provenance
**Method:** two layers — (1) exhaustive hostname grep across this repo +
`pipeline/` @ pin `7e77437`; (2) live read-only probes (ssh BatchMode /
`vls` / `rclone`) of every doc-grounded host, same session.
**Canonical upstream:** `pipeline/machine_inventory.yaml` (schema 3,
generated 2026-06-26) + `pipeline/docs/infrastructure/MACHINE_INVENTORY.md`.
This doc re-verifies that inventory against live state and records the
deltas; the YAML remains the machine-readable source of truth.
---

## Verified inventory (all probed live this session)

| Machine | Status | Role in this project | Live probe result (2026-07-06) |
|---|---|---|---|
| **jakob-mbp** (this Mac) | target | canonical FLITS clone + manuscript repo; `~/Data/Faber2026/dsa110/` data replica | direct: 24/24 scattering cubes present + sha256'd (`data-manifest.csv` now HASHED_LOCAL); upchan gen-2/3 products + PROVENANCE.md; runs store `~/Developer/scratch/flits-local-runs`; worktrees `flits-rerun` (frozen census CSVs), `flits-acf-lag-selector`, `flits-provenance` |
| **iacobus** (local Mac, Tailscale) | target | data staging for the gdrive authority; materialized CHIME/DSA products | ssh ✓ `iacobus.local`; `/Users/iacobus/Research/CHIME_DSA_Codetections` = **244 GB** (inventory said 218 GB — grown since 2026-06-26), expected subtree structure intact |
| **gdrive-jakob** (Google Drive, rclone) | **data authority** | canonical data root per the 2026-06-26 authority decision | `rclone lsd` ✓ — `Research/CHIME_DSA_Codetections` mirrors the iacobus structure (8 dirs) |
| **h17** = `lxd110h17` (OVRO, Tailscale direct) | target | active OVRO compute; CHIME baseband docker (`chimefrb/baseband-analysis`); upchan generation; arc-trash archive | ssh ✓ `lxd110h17`; project tree `/data/research/astrophysics/frbs/chime-dsa-codetections/` live (bin/, upchan_codetections/ incl. gen-3 freya + `DEFECTIVE_nodedisp_20260703` quarantine, archive/arc_trash_2026-06/) |
| **arc** (CANFAR VOSpace, CADC) | target | institutional storage + CANFAR compute; origin of the scattering cubes | `vls` ✓ from this Mac (`~/.ssl/cadcproxy.pem` + local `vls`/`vcp`): **12 DSA cubes** in `data/DSA_bursts/`, **12 CHIME cubes** in `data/CHIME_bursts/dmphase/` — all 24 accounted for |
| **h23** = `lxd110h23` (OVRO, via jump chain) | retired | drained to iacobus 2026-06-25 | ssh ✓ `lxd110h23`; quarantine `jfaber-drain-20260625` present; residual `/media/ubuntu/ssd/jfaber` holds only non-codetection dirs (dsa110-continuum, nihari, …) |
| **hpcc** (Caltech HPC) | retired | former SLURM batch for the foreground search (`scripts/hpcc/`); flits tree quarantined | ssh ✓ `login3.cm.cluster`; `/home/jfaber/_quarantine/flits-20260625` present |
| **dsacamera** (OVRO, via jump) | retired | negligible codetection content | ssh ✓; home dir holds unrelated pointing/imaging work — consistent |

## Hosts explicitly NOT part of this project

Grep of this repo + pipeline found **zero** project references to:
`ovro` (bastion only — appears solely in acknowledgements prose),
`dsa110maas` (jump host only), `dsastorage`, `calibration`, `h24`,
`tubular`/`frb-analysis` (McGill/CHIME — CHIME-side data comes via CANFAR,
never McGill), `major`, `potoroo`, `venice`, `ozstar`, `nt`, `digilab`,
`blph0`/`blpc0`/`blpc1`, `digocean`, `campus-pi` (jump for hpcc only).
These live in `~/.ssh/config` for other projects/infra; their presence
there is not evidence of a role here.

## Deltas found & fixed this session

1. **`data-manifest.csv` arc_path was wrong for all 12 CHIME rows** —
   pointed at `data/DSA_bursts/`; live `vls` shows the CHIME cubes at
   `data/CHIME_bursts/dmphase/`. Fixed in worktree branch
   `provenance/data-manifest` (commit `540e16a`), after `de74d97` filled
   all 24 sha256/bytes from the local replica.
2. **24 dangling symlinks** under `~/Data/Faber2026/dsa110/flits-runs/data/`
   (→ deleted `~/Developer/dsa110-local-data`) removed; real cubes verified
   intact in `DSA_bursts/` first.
3. **iacobus data root grew** 218 → 244 GB since the 2026-06-26 inventory
   snapshot (expected: 2026-07-06 upchan regeneration campaign).

## Still open (owned by plan §V Phase 2)

- **P2.2**: sha256 the cubes on h17/arc and cross-check against the local
  hashes — local hashes alone don't prove lineage; the manifest xfail
  stays until then.
- **P2.1**: locate the cube *builder* on h17 (`rg -l "cntr_bpc"` over
  `/data/research/...` + `/data/jfaber`) — still `UNVERIFIED_BUILDER`.
- gdrive↔iacobus content-level parity was NOT checked here (structure
  only); the authority decision assumed staged uploads continue.
