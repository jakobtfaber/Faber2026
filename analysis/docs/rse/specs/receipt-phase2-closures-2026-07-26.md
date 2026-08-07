# Phase 2 closure receipt — non-branch WIP lanes and DECIDE items (2026-07-26)

**Objective/phase:** Phase 2 of the owner-chartered closure campaign
(`closure-roster-2026-07-26.md`): close the non-branch WIP lanes (FLITS
canonical clone, parent canonical clone, nested analysis checkout) and resolve
the roster's DECIDE items with evidence. Phase 3 (the approved 132-name branch
retirement) ran first and is documented in
`retirement-receipt-2026-07-26.md`.

**Preservation root:** `~/Data/Faber2026/preservation/` (local machine,
jakob-mbp). Nothing in this phase was deleted without a verified capture; no
pre-rewrite FLITS objects were pushed to any remote.

## 1. dsa110-FLITS canonical clone — reconciled

Source: `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS`.

- The dirty working tree (11 modified crossmatching/scintillation files from
  July 17) was already captured as branch
  `rescue/wip-crossmatch-scint-20260726` (tip `2ac6e27e77e5`); the working
  copy was verified content-identical to the capture before reset.
- Local `main` fast-forwarded to `origin/main` (`f5c1d1f3`); working tree now
  clean.
- **Correction:** the earlier capture receipt recorded 3 local stashes; live
  enumeration found **11**. The earlier count is STALE. All 11 stash tips
  (pre-rewrite history — must never be pushed) were given temporary refs and
  bundled locally:
  - `flits-stashes-20260726.bundle` — 11 refs, `git bundle verify` pass,
    sha256
    `0f2aa5507486243038aba0dad53a6ca5237a78980a6e83ce37fdaa085d922930`.
  - The stashes themselves remain in the clone's stash list untouched;
    scint-related stashes (s3–s5) are Phase-4 walkthrough material.

## 2. Parent canonical clone — tidied to a clean main

Source: `~/Developer/repos/github.com/jakobtfaber/Faber2026`.

- Modified `AGENTS.md` / `CLAUDE.md` (the agent briefs, previously local-only)
  were landed on parent main via PR #254.
- `pipeline` gitlink drift resolved: detached at the pinned commit
  `78b448f05946923ef1c0acc19068fed313911ec6`.
- Loose local notes archived (not deleted) to
  `~/Data/Faber2026/preservation/parent-local-notes-20260726/`:
  `update-072326-1535.md`, `worktree-reconciliation.md`,
  `plan-authority-reconciliation-action-2026-07-23.md`, `running-notes/`,
  `figures-receipts/`, `figures-prototypes/`, `graphify-out/`, and
  `pipeline-untracked-expanded_catalog_cross_references.csv` (this CSV differs
  by checksum from the pinned version — archived as distinct, per the
  never-merge-unequal-checksums rule).
- `.claude-science/` left in place deliberately: live tool state, not project
  WIP.
- Local-only commit `8d492fea` ("foreground: apply probabilistic Phineas
  budget") is cited by the results registry (`budget.cluster_column`); its
  branch `codex/scintillation-notebook-wayfinder` was pushed to the parent
  remote as a durable provenance ref and is upgraded from RETIRE-candidate to
  **KEEP** (provenance class, alongside
  `archive/foreground-source-freeze-pr231` in FLITS, tip `c913175e567d`).
- Final state: `main` at parity with `origin/main`, working tree clean.

## 3. Nested analysis checkout — captured and re-pinned

Source: the parent's `analysis/` submodule checkout
(gitdir `.git/modules/analysis`), which sat on a pre-relink local `main`
(`11b716c`) that could not fast-forward to `origin/main`.

- All 83 local refs bundled:
  `analysis-nested-checkout-refs-20260726.bundle` — verify pass, sha256
  `ca489d482502d43845b936e0d61876a80f498180bda992e943540c632fb39006`.
- The unique lane (Phineas-budget work plus 4 untracked files) was pushed as
  `rescue/nested-checkout-phineas-lane-20260726` (tip `0c5875949dd1`).
- Every remaining untracked file was verified either byte-identical to
  `origin/main` or archived to
  `parent-local-notes-20260726/nested-analysis-untracked/`
  (`defect-register.md`, `journal.jsonl`, `handoff-h17-ovro-monitoring.md`)
  before a scoped `git clean` of `docs/rse`.
- `git submodule update --init analysis` then detached the checkout at the
  parent's pin `7585e1638d1a495086e416e4418e82dbb0658340`. Parent `git status`
  is clean.

## 4. DECIDE items — evidence resolutions

The roster carried four DECIDE items. Three are the provenance-map trio; the
fourth is scint material.

1. **analysis `publish/repository-provenance-map`** (3 commits, tip
   `e753fa9c`): the repository map (`17aca27f`) is on main via PR #106; the
   replay-pin move (`0bdec1a6`) is superseded by the `78b448f0` pin on main;
   the reproducibility refresh (`e753fa9c`) had its `repro_manifest.csv` and
   `figure_review/slots.json` content landed via PR #119, and its one
   genuinely unlanded piece — the REPRODUCE.md three-repository rewrite — was
   verified correct against the live parent layout and landed as **PR #122**.
   Main's two-repository text was confirmed stale (the parent has pinned
   `analysis/` as a submodule since the 2026-07-13 relink).
   → retire-eligible once PR #122 merges.
2. **parent `publish/repository-provenance-map-followup`** (3 commits): the
   README provenance-map link is on main (README.md line 27); both gitlink
   targets (`analysis e753fa9c`, `pipeline 1d5633c1`) are superseded by main's
   pins (`7585e163` / `78b448f0`); its README otherwise predates PR #245.
   → retire-eligible.
3. **FLITS `publish/repository-provenance-map`** (1 commit `1d5633c1`, "repair
   results library paths"): the exact repaired lines are on FLITS main
   (DATA_LOCATIONS.md lines 137–138). → retire-eligible.
4. **FLITS `codex/chromatica-cross-band-scintillation`**: HOLD unchanged —
   scint material, reserved for the Phase-4 owner walkthrough.

Deleting the three retire-eligible branches is **not covered** by the consumed
132-name retirement approval; it awaits a separate owner approval naming those
exact refs.

## 5. Verification summary

- Both bundles pass `git bundle verify`; checksums recorded above.
- Rescue/durable refs confirmed on their remotes by `ls-remote`:
  `rescue/nested-checkout-phineas-lane-20260726` (`0c5875949dd1`),
  `rescue/wip-crossmatch-scint-20260726` (`2ac6e27e77e5`),
  `archive/foreground-source-freeze-pr231` (`c913175e567d`),
  `codex/scintillation-notebook-wayfinder` (`8d492fea`).
- All three canonical clones end clean on their expected commits; the parent's
  submodules sit exactly on main's recorded pins.
- Absorption claims in §4 were checked by content (file-level diff or exact
  line presence on main), not by branch-tip tree diffs.

## Final disposition

Phase 2 complete. Remaining campaign state: owner merge call on parent
PR #216 (all checks green); owner approval for the three retire-eligible
provenance-map branches; PR #122 landing; ticket-05 agent lane; Phase-4 scint
walkthrough.
