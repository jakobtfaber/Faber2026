# h17 capture receipt — 2026-07-27

Objective: open the h17 consolidation lane (owner direction, 2026-07-27).
Phase completed here: **discovery + capture** — read-only per-snapshot
verification of every worktree and run tree in the owner's 2026-07-27
inventory, then zero-loss capture of all unlanded Git content. No h17
worktree, folder, branch, or file was modified, moved, or deleted; the
capture commits were built through a temporary index, leaving each
worktree's real index and files untouched (dirty-file counts identical
before and after: 33 / 1 / 1).

## Per-snapshot verification (read-only, `ssh h17`, 2026-07-27)

All 12 controlled-fit worktrees (`~/Developer/worktrees/
dsa110-FLITS-controlled-{johndoeII,oran,zach}-2026072{2,3}[-v2..-v4]`)
are **clean, detached**, at one of four tips — `67b73a85e105` (v1),
`08649392d9c9` (v2), `31f7744758cc` (v3), `fba755ad7edb` (v4) — and every
tip is reachable from the `origin` refs that survived the 2026-07-27
remote sweep. 683 MB each, ~8.2 GB total. No unique Git content.

Also verified clean with tips on origin: `~/worktrees/flits-window-tuning`
(`b8154451923e`), and the extra registered worktree
`~/Developer/worktrees/dsa110-FLITS/a1-trigger-calibration`
(`e0776116525f`, clean).

Unique content found and captured:

| Source (h17) | Base commit | Dirty state | Capture |
|---|---|---|---|
| `~/worktrees/joint-tf-fits` | `d292f4b91ef0` | 5 modified + 28 untracked (scattering-refit sprint: two-screen / zach-fine scripts, provenance docs, +237-line fitter diffs, local-only "v2 re-run harvest" audit section) | `origin/archive/h17-joint-tf-fits-snapshot-20260727` = `643ecb0bb2a0` |
| `~/Developer/worktrees/dsa110-FLITS-model-grid-diagnostic-20260722` | `31f7744758cc` | 1 modified (`joint_model_grid.py`, +6/−4, not on origin/main) | `origin/archive/h17-model-grid-diagnostic-snapshot-20260727` = `923b1eae6b3d` |
| `~/Developer/worktrees/dsa110-FLITS-resolution-diagnostic-20260722` | `08649392d9c9` | 1 modified (`joint_tf_prep.py`, +44/−37, not on origin/main) | `origin/archive/h17-resolution-diagnostic-snapshot-20260727` = `e7a274774026` |
| `~/worktrees/t0audit-pr` branch `ms/audit-standing-line-toa-note-20260719` | tip `99dcef138a84` | clean; its one commit's file content is byte-identical on origin/main (landed via another route) | branch pushed to origin as-is |

Of joint-tf-fits' 28 untracked files, 15 are byte-identical to
origin/main (already landed), 11 are absent from origin/main (the
two-screen Stage-0 and zach-fine campaign scripts plus
`TWOSCREEN_FITTER_PROVENANCE.md`), 1 is a `.bak` editor backup, and
`COMPONENT_COUNT_LADDER_AUDIT.md` diverges in both directions from the
origin/main version (local carries a "v2 re-run harvest (jobs 169–182)"
section origin lacks; origin carries the t0-clamp versioning section the
local copy predates). All variants are preserved in the snapshot.

## Verification method

- Push verified by `ls-remote` against `origin` (all three archive refs
  present at the stated SHAs).
- Restoration check: `git diff <snapshot> --quiet` empty for the two
  diagnostic worktrees; for joint-tf-fits (where `git diff` cannot see
  untracked files) every one of the 33 dirty/untracked paths was
  hash-compared (`git hash-object` vs the snapshot blob): 33/33 exact.

## Findings requiring disposition (owner decisions, not taken here)

1. **Canonical clone `main` is pre-rewrite.** h17's
   `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS` has `main` at
   `bad0ba49b049` — the pre-2026-07-13 history (356 ahead / 785 behind
   `origin/main`). It was never reset after the fork history rewrite.
   Realigning it is a hard reset of a shared checkout (OPERON and past
   sprints ran here) and is explicitly reserved to the owner. The
   pre-rewrite history already exists at `origin/archive/pre-rewrite-main`
   and in the jakob-mbp bundles.
2. **Worktree retirement candidates.** The 12 controlled worktrees +
   `flits-window-tuning` are clean with tips on origin (~8.3 GB); the
   three captured-dirty worktrees are now fully preserved on origin.
   Under the retirement rules each removal still needs the owner to name
   the paths.
3. **`t0audit-pr` branch** is content-landed; branch deletion (local and
   remote) awaits owner naming.
4. Non-Git run trees (`~/flits-runs` 3.4 GB, `~/flits-controlled`,
   `~/runs/faber2026_dm_power`, `~/scratch/faber2026-fit-envelope-input-20260722`,
   `~/scint-injection-harness`) and the `/data` stores were not assessed
   beyond enumeration — separate capture/verification pass required
   before any disposition, per the deletion-safety rules.

Both h17 disks are at 91 % (13 T `/data`, 916 G `/`), which motivates the
lane but does not change the verification bar.
