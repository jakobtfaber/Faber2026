# Receipt: capture of the dsa110-FLITS working-tree WIP lane (2026-07-26)

**Objective/phase:** owner-chartered capture ("Charter its capture") of
the uncommitted separate-active lane found in the canonical dsa110-FLITS
clone during family-3 work. Capture only — no modification, no
reconciliation, no retirement.

## Source snapshot (frozen reference)

- Repo: `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS`
- Branch `main` at `fed4a02c` (152 behind origin/main, deliberately not
  advanced)
- 11 modified tracked files (crossmatching association + TOA crossmatch
  code and result JSONs, `flits/batch/codetection_data.py`, three
  `scintillation/scint_analysis/` modules, two test files); zero
  untracked; file mtimes 2026-07-17 ≈10:54 — the WIP dates from the
  window-tuning / model-TOA era, not current editing
- `lane-liveness`: "live (editor_lock)" — an editor holds the repo open;
  mtimes show no active writing
- Three pre-existing local stashes recorded, kept local (their tips sit
  on pre-rewrite history; pushing would reintroduce pre-rewrite
  objects): `b2053a45` (WIP on old main e3589b7c), `1d378019`,
  `cef002f9` (rebase hook churn)

## Capture (no-touch method)

Temporary-index commit: `GIT_INDEX_FILE` → `read-tree HEAD` →
`update-index --add` each dirty path → `write-tree` → `commit-tree -p
HEAD`. Working tree, real index, and local refs untouched throughout.

- Capture commit `2ac6e27e77e5cd3aaa7cce969a30a26684729b8f`, parent
  `fed4a02c`
- Pushed to origin `rescue/wip-crossmatch-scint-20260726`; full-hash
  `ls-remote` confirmed

## Verification

- `git diff 2ac6e27e` against the live working tree: **0 lines** — the
  capture is byte-exact
- Post-capture `git status`: same 11 modified files, HEAD unchanged —
  the source was not mutated
- Snapshot label: mid-edit-era WIP, not a reviewed state; any later
  change to the working tree makes this capture STALE for equivalence
  claims (the pushed branch itself remains valid history)

## Disposition

The lane's content is now double-held: live working tree (untouched) +
origin branch. Reconciling, landing, stashing, or cleaning the working
tree remains undone and unchartered; the local `main` fast-forward is
also deferred until the lane's owner decides. Stash triage deferred
likewise.
