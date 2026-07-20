# Plan: FLITS org-main migration (fork → dsa110/dsa110-FLITS)

**Status: EXECUTED (2026-07-14).** The fork `jakobtfaber/dsa110-FLITS` is the
canonical development repo; org `main` was reset to the fork's scrubbed
history on the owner's explicit instruction (collaborator notification
waived). Fork→org sync is now a plain fast-forward push.

## Execution record (2026-07-14)

- Precondition re-verified live: org main `c97177c`, fork main `fed4a02`.
- `archive/pre-rewrite-main` created at `c97177c` (agent-side push).
- Reset pushed from the user terminal (oneway-guard fail-closes force pushes
  in agent sessions):
  `git push upstream --force-with-lease=refs/heads/main:c97177c… fed4a02…:refs/heads/main`
  → `+ c97177c...fed4a02 -> main (forced update)`.
- Verified: org main == fork main == `fed4a02c1b022b22a3853dbcca81e4e53c4910b4`,
  trees identical (`193bedd851b3e33c774f9944837168ff7ae94cb5`);
  archive ref intact at `c97177c`.
- Untouched per instruction: PR #49, org branches (`dm-campaign-2026-07`,
  `pin/faber2026`, `entire/checkpoints/v1`), Faber2026 `pipeline` pin
  (`0e0f58b`).
- **Deferred follow-up:** protect org `main` / document it as a downstream
  mirror (runbook step 6); adjudicate PR #49 separately.

## Verified facts (2026-07-14 session)

- Fork main and org main share **no common ancestor** (2026-07-13 bot-author
  scrub rewrote the fork's entire history). GitHub's "629 ahead / 280 behind"
  banner counts the two entire histories; it is SHA-only noise and can never
  converge. **No upstream content is missing from the fork.**
- The fork DAG embeds a scrubbed copy of org history: `de24ceb` (second
  parent of fork merge `4269124`) is **tree-identical** to org HEAD
  `c97177ce878b521e8ab4dba3d2e9e7420fa59f74` (tree
  `683d0e715e448a1cd425ce8ae12b0f8abf0bdc73`, PR #43, 2026-07-05).
- `4269124` is a documented `-s ours` merge: org's alpha-era tree was
  deliberately not taken (fork carries the gain-evidence fix in
  beta-co-model form).
- Fork main tip at time of writing: `fed4a02c1b022b22a3853dbcca81e4e53c4910b4`
  (3 commits past the reconcile merge). Faber2026 `pipeline` pin: `0e0f58b`.
- Org main authorship: 278/280 commits are Jakob Faber (email variants),
  2 are Copilot — the reset also cleans the org default-branch graph.
- Org repo access: admin; `main` is **not protected**.
- **Blast radius (why this is deferred):** org repo had 472 clones from 44
  unique cloners in the last 14 days and has 27 collaborators with
  write/admin access. A silent reset breaks their checkouts and possibly
  automation.
- Org branches `dm-campaign-2026-07`, `pin/faber2026`, `entire/checkpoints/v1`
  are untouched by a main reset and keep pre-rewrite SHAs resolvable.
- **PR #49** (`revert(dm): remove invalid DM-phase v1 campaign`) targets
  `pin/faber2026`, **not** `main`. It is unrelated to this migration —
  adjudicate separately; never close it as "superseded" by the reset.

## Cutover runbook (when coordinated)

1. Confirm org `main` is still exactly `c97177c`:
   `git -C pipeline ls-remote upstream refs/heads/main`
   — if it moved, stop and re-reconcile first.
2. Archive: `git -C pipeline push upstream c97177c:refs/heads/archive/pre-rewrite-main`
   (keeps every pre-rewrite SHA cited in REPRODUCE.md / journal / handoffs
   resolvable forever).
3. Notify the 27 collaborators / automation owners: clones tracking org
   `main` must `git fetch && git reset --hard origin/main` (or re-clone).
4. Reset (from the user terminal — push-gate blocks agent-side force pushes):
   `git -C pipeline push upstream --force-with-lease=refs/heads/main:c97177ce878b521e8ab4dba3d2e9e7420fa59f74 <fork-main-tip>:main`
   — never a bare `--force`; re-read the fork tip at execution time.
5. Verify: both remotes' `main` equal the intended fork commit and trees
   match (`git ls-remote`, `git rev-parse <sha>^{tree}` on both).
6. Protect org `main`; document it as a downstream mirror — no independent
   commits to org `main`; sync = plain fast-forward
   `git push upstream main:main`. The cherry-pick-only upstream-sync policy
   is obsolete from this point.
7. Handle PR #49 and the other org branches independently.

## Rejected alternatives

- **Join merge (`git commit-tree` with both mains as parents):** avoids the
  force-push but permanently retains both histories, keeps bot authors on the
  org graph, and makes every future sync a scripted join — standing tech
  debt. Rejected.
- **Detaching the fork from the fork network:** was floated while the sync
  direction was assumed org→fork; wrong for a fork-canonical → org-mirror
  topology. Rejected.
