# Receipt: Phase 5 follow-up scratch sweep (2026-07-26)

**Objective/phase:** the follow-up sweep of `~/Developer/scratch/` items
the consolidation plan never enumerated, per the owner instruction
"Let's proceed with (1) and then after that (2)", and the owner's
"Approved." for the nine-item staging batch.

**Correction to receipt-phase5-trackB-batch3:** its claim that scratch
retained "only the follow-up sweep candidates" was wrong — the scratch
root also held the mid-July scintillation-campaign workbench (~21 dirs +
53 loose files), the 2026-07-22/24 worktree-retirement receipt estate
(2.1 GB), and the Phase-4 source preservation directory (1.6 GB).
Consequence: all were classified and dispositioned in this sweep.

## Preservation performed (all verified)

- Both unadopted 2026-07-13 rewrite mirrors
  (`2026-07/faber2026-cursor-rewrite`, `…-full-contributor-scrub`, bare
  `Faber2026.git` each, 133 refs, 60 and 75 ref tips absent from the
  canonical store, no `archive/pre-rewrite-*` ref on origin — potentially
  last-copy) bundled with `--all` to
  `~/Data/Faber2026/preservation/`; `git bundle verify` OK; sha256
  `4ef7e35f…d77` and `3c469e6d…556` (208 MB each).
- Worktree-retirement receipt estate (`scratch/receipts/Faber2026/`)
  manifest-first copied to
  `~/Data/Faber2026/preservation/worktree-retirement-receipts-202607/`:
  7,719 files, sha256 manifest diff empty, `MANIFEST.sha256` archived.
- `scratch/preservation/` re-proven a strict byte-subset of the terminal
  home (per-file sha256 manifests; only destination surplus is the known
  `entire-checkpoints-v1-supplement.bundle`, sha256 `eb0208ee…`).

## Science products routed to `~/Data` (same-volume renames)

To `~/Data/Faber2026/scratch-outputs-20260726/`: `campaign_final`,
`campaign_rerun`, `campaign_rerun_v2`, `chromatica_e2e`,
`chromatica_flits_runs`, `chromatica_h17_stage`, `autorfi_fits`,
`flits-refit-202606`, `chromatica-dm-window-review-202607`, and the
scint-campaign workbench (21 dirs + 53 root files, 426 files / 66 MB) as
`scint-workbench-root-20260726/`. README at the destination lists each.

## Staged to `~/Documents/_trash/` (owner-approved nine)

The two rewrite mirrors, `Faber2026-lane-preserve-20260717` (superseded
safety copies; the approval is the owner confirmation its PROVENANCE.md
required), `Faber2026-logs`, `chime-dsa-dsa-filterbanks-logs`,
`dsa110-mission-control-prototype`, `scratch/preservation/`,
`scratch/receipts/`, and the empty `recovery/` (rmdir). Batch provenance:
`~/Documents/_trash/PROVENANCE-scratch-sweep-20260726.md`.

## Left untouched (out of scope or live)

`hpcc-mirror/` (mutagen holds it open), `2026-06/synapseml-local` (live
python process), `worktrees/` (dotfiles lane), `retired/` and
`my-skillset*` (my-skillset lane), dispatch infra (`cc-dispatch`,
`codex-dispatch`, `codex-review-*`), `rebuild/`, `router-status/`,
`env_diag/`, `citest/`, `vgtest-work/`, `claude-iterm-cockpit/`,
`tools/`, and non-Faber2026 content of the dated `2026-0*/` dirs.
`2026-05/` contained nothing Faber2026-related.

## Post-state

`~/Developer/scratch/` contains no Faber2026 material outside the
untouched lanes above. Deletion of the `_trash/` staging areas proceeds
under the owner's standing "(2)" instruction with a pre-delete
re-verification of every preservation copy.
