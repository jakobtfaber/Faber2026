# Validation: post-estate worktree content disposition

> Validated against
> [`handoff-2026-07-24-12-40-worktree-content-disposition.md`](handoff-2026-07-24-12-40-worktree-content-disposition.md)
> and its operational annex
> [`handoff-2026-07-24-12-33-worktree-content-disposition.md`](handoff-2026-07-24-12-33-worktree-content-disposition.md)
> at commit `37646ede` on 2026-07-24.

**Date:** 2026-07-24 13:00 -0700 / 2026-07-24T20:00Z
**Branch:** `docs/handoff-worktree-disposition-20260724`
**Owner:** `jakobtfaber`
**Receipt wave:** `~/Developer/scratch/receipts/Faber2026/worktree-retirement/post-estate-delta-20260724T195430Z/`

---

## Verdict

The ten-worktree delta is **settled**. All ten internal checkouts are absent,
all ten branch references are preserved, and issue #227's protected path remains
absent and unregistered in every one of the five authority Git common
directories.

Two of the handoff's closure criteria are **not** met and are not achievable by
worktree work alone:

- Issue #229 cannot close: three of its own research/task sub-tickets (#242,
  #243, #244) are still open.
- Issue #233 cannot close: it is an explicit owner-decision ticket whose body
  offers the owner a choice and states it is blocked until research tickets
  produce manifests.

---

## 1. Implementation status

| Handoff action item | Status | Evidence |
| --- | --- | --- |
| 1. Read companion handoff's ten-row table and safety rules | Complete | Both handoff documents read in full. |
| 2. Recheck each target's live state before mutation | Complete | Section 2 below. |
| 3. Receipt-retire the eight merged/patch-equivalent worktrees | Complete | Eight receipts under the wave directory. |
| 4. Copy the two unmatched-commit worktrees to `ArtifexBackupDrive` | **Superseded by owner decision** | Section 3 below. Both were retired instead, after their content was proven to be on GitHub. |
| 5. SHA-256-seal relocation manifests; annotate the faulty RFI receipt | **Not done** | Out of scope of the ten-row delta; carried forward. Section 6. |
| 6. Fresh five-common census; record on #229 and close it | Census complete; **#229 stays open** | Section 4. Blocked by open sub-tickets #242/#243/#244. |
| 7. Update #233 with final archive caveats; close if owner accepts | **Owner decision required** | Section 6. |
| 8. Keep #227 absent; leave PRs #56/#204 unmerged | Complete | Section 5. |

---

## 2. Pre-mutation re-verification (fresh output, not inherited claims)

Every value below was re-derived in this session; none was taken from the
handoff.

**Baseline refs — unchanged from the handoff's audit:**

- Parent `origin/main` = `1dfb5c2ae5523e9acd83ba9ddc2ede1d1944736a`
- Analysis `origin/main` = `759ad238b427c06375facb3a659bc67355e643a3`

**All ten HEADs matched the handoff exactly.** All ten were clean in tracked and
untracked state. The only ignored payload anywhere was Python test and bytecode
caches (`.pytest_cache/`, `__pycache__/`).

**Merged-pull-request state** (re-queried, not inherited):

| Worktree | Branch | Pull request |
| --- | --- | --- |
| `crossmatch-contract-20260724` | `feature/crossmatch-contract-20260724` | none — HEAD is an **ancestor of** `origin/main` |
| `raw-chime-definition-20260724` | `docs/raw-chime-definition-20260724` | analysis #92 merged |
| `technical-review-20260724` | `docs/technical-review-decision-packet-20260724` | analysis #93 merged |
| `trust-docs-20260724` | `docs/land-trust-deltas-20260724` | analysis #91 merged |
| `overleaf-research-20260724` | `docs/overleaf-native-git-research-20260724` | parent #240 merged |
| `repository-map-followup` | `publish/repository-provenance-refresh` | parent #246 merged |
| `results-library-audit-20260724` | `docs/results-library-audit-revalidation-20260724` | none — HEAD is an **ancestor of** `origin/main` |
| `rfi-archive-20260724` | `archive/rejected-rfi-prototypes-20260724` | parent #236 merged |

Deviation from the handoff, immaterial to safety: the handoff attributed
`crossmatch-contract-20260724` to analysis #91 and
`results-library-audit-20260724` to parent #236. Neither branch has a pull
request. Both are safe for a stronger reason — each HEAD is a direct ancestor of
its `origin/main`, so the content is already in the main line.

**Operation-marker adjudication.** The handoff flagged an unresolved policy
disagreement about whether sibling markers block. It is resolved here on
evidence rather than by inheriting either interpretation:

- The marker landscape had **changed** since the handoff. All four markers it
  listed under `.git/modules/analysis/worktrees/…` were gone. New ones appeared:
  `AUTO_MERGE`, `CHERRY_PICK_HEAD`, and `sequencer/` at the root of
  `Faber2026-analysis/.git`, plus three sibling worktree `AUTO_MERGE` files.
- Those root markers are an abandoned four-commit cherry-pick in the canonical
  `Faber2026-analysis` **primary** checkout, dated 2026-07-22 05:00 and 13:08,
  with an unresolved conflict in
  `docs/rse/wayfinder/map-apj-submission.md`. It is a separate lane and was left
  completely untouched.
- Decisive fact: **that repository is not a common directory for any of the ten
  targets.** The four analysis worktrees are registered against
  `Faber2026/.git/modules/analysis`, not `Faber2026-analysis/.git`.
- Across the two relevant commons, **no target-specific marker existed** for any
  of the ten. The one marker under `Faber2026/.git/worktrees/…` is a zero-byte
  `index.lock` dated 2026-07-23 23:01 belonging to
  `Faber2026-expanded-foreground-phase-two`, a sibling. It was not touched.
- No process owned any target; `lsof` on all ten target directories returned
  nothing; no `git` process was running.

Policy recorded for future waves: **fail closed on a marker in the target's own
per-worktree Git directory or in the common directory that actually backs the
target.** A marker in an unrelated repository, or in a sibling's per-worktree
directory with no open handle and no owning process, is evidence only.

---

## 3. The two "unmatched commit" worktrees — handoff finding overturned

The handoff classified these as preserve-to-external-storage because they held
commits not matched upstream. Re-derivation shows **neither holds content that
is absent from GitHub.**

**`Faber2026-worktrees/repository-map-publish`** (branch
`publish/repository-provenance-map-followup`, HEAD `46aa1316`):

- `git cherry origin/main HEAD` marks `d625c94a` and `3fafbc41` as unmatched
  **against `main`** — but `git branch -r --contains` places both on
  `origin/publish/repository-provenance-map-followup`. The branch is pushed;
  `git ls-remote` confirms the remote tip is `46aa1316`.

**`Developer/scratch/worktrees/Faber2026-repository-map`** (branch
`docs/repository-provenance-map`, HEAD `3d50b721`) — the harder case, because
this branch has **no** remote:

- `git patch-id --stable` on `3d50b721` yields `d455a1c26d3aa415…`.
- `git patch-id --stable` on `d625c94a` (which *is* on
  `origin/publish/repository-provenance-map-followup`) yields the **identical**
  `d455a1c26d3aa415…`.
- The two commits' trees differ by exactly one file,
  `docs/rse/research/research-overleaf-native-git-contract-2026-07-21.md`, which
  is present on the other branch's base and is itself on `origin/main` via
  merged parent #240. Nothing is unique to the scratch checkout.

**Nested submodule content, checked independently of the parent:**

| Worktree | Submodule | HEAD | Preserved at |
| --- | --- | --- | --- |
| `repository-map-followup` | analysis | `e753fa9c` | `origin/publish/repository-provenance-map` (Faber2026-analysis); also the gitlink on parent `origin/main` |
| `repository-map-followup` | pipeline | `1d5633c1` | same branch on `jakobtfaber/dsa110-FLITS`; also the gitlink on parent `origin/main` |
| `repository-map-publish` | analysis / pipeline | `e753fa9c` / `1d5633c1` | as above |
| `Faber2026-repository-map` | analysis | `17aca27f` | `origin/publish/repository-provenance-map` in canonical `Faber2026-analysis` |
| `Faber2026-repository-map` | pipeline | `1d5633c1` | `refs/heads/publish/repository-provenance-map` on the `dsa110-FLITS` remote, confirmed by `git ls-remote` |

Note the subtlety worth carrying forward: `1d5633c1` is **absent** from both
canonical pipeline object stores (`Faber2026/.git/modules/pipeline` and
standalone `dsa110-FLITS/.git`) and existed locally only inside the
per-worktree module stores — but it is a branch tip on the GitHub remote, and it
is the pipeline gitlink recorded on parent `origin/main`. A local-object check
alone would have produced a false "unique content" verdict.

**Owner decision, 2026-07-24:** retire both rather than relocate. Rationale
accepted: `git worktree remove` preserves the branch reference, so even the
never-pushed commit `3d50b721` remains reachable locally, and everything else is
on GitHub. External relocation would have added two more removable-drive-
dependent registrations for no preservation gain.

---

## 4. Execution and post-checks

Eight of the ten retired with `git worktree remove` at exit status 0, no
`--force`.

Three refused with `fatal: working trees containing submodules cannot be moved
or removed`. This is a Git limitation keyed on gitlink entries in the index, not
on checkout state — `git submodule deinit -f --all` cleared the checkouts and
the refusal persisted. Fallback used, with an exact nested-status receipt
captured first: `rm -rf <target>` followed by `git worktree prune -v`. A
`git worktree prune --dry-run` immediately before each removal returned empty,
proving no other registration was at risk. No blanket prune and no force at any
point.

**Post-checks — all ten:**

- Target directory absent: 10/10
- Registration absent: 10/10
- Per-worktree admin directory under `.git/worktrees/…` removed: 10/10
- Branch reference preserved at its recorded head: 10/10, verified individually
- Local-only commit `3d50b721` still resolves in the canonical parent: yes

**Five-common census, before → after:**

| Common directory | Before | After |
| --- | ---: | ---: |
| `Faber2026/.git` | 33 | 27 |
| `Faber2026/.git/modules/analysis` | 40 | 36 |
| `Faber2026/.git/modules/pipeline` | 13 | 13 |
| `Faber2026-analysis/.git` | 23 | 23 |
| `dsa110-FLITS/.git` | 7 | 7 |
| **Total** | **116** | **106** |

**Physical bytes removed, reported separately from free-space reporting** (the
handoff's definition-of-done item 7):

- Checkout trees: 5.28 GiB, measured per target before removal.
- Per-worktree submodule object stores under
  `.git/worktrees/<name>/modules/{analysis,pipeline}`: 1.47 GiB each for
  `repository-map-followup`, `repository-map-publish`, and
  `Faber2026-repository-map` — 4.41 GiB total.
- **Physical total: about 9.7 GiB.**

APFS free space did **not** rise correspondingly: it read 12 GiB before and
11 GiB after. Two local Time Machine snapshots
(`…2026-07-24-111829.local`, `…2026-07-24-121826.local`) still retain the
deleted blocks; one older snapshot was purged automatically by macOS during the
wave. **No snapshot was deleted manually.** Do not read the `df` figure as
evidence that the removal failed, and do not thin snapshots without explicit
owner approval.

---

## 5. Safety-rule compliance

| Rule | Result |
| --- | --- |
| #227 stays absent and unregistered | Verified: path absent on disk, and `worktree list` in all five commons contains no `untrack-agent-briefs` entry. |
| Never blanket-prune or force-remove | Honoured. `--force` never used; every `prune` was preceded by an empty `--dry-run`. |
| Refresh state before each action | Done; Section 2. |
| Target-directory markers block | Adjudicated on live evidence; Section 2. No sibling marker was deleted. |
| Lock external registrations | Not applicable — no external relocation occurred. |
| `pipeline/` gitlink is deliberate | No canonical parent or submodule ref was changed. Only linked-worktree registrations and their own admin directories were removed. |
| Preserve rejected host dispersion-measure lane | Parent #204 and analysis #56 untouched and still open drafts. |

---

## 6. Not done — carried forward

1. **#229 cannot close.** Its sub-tickets #242 (ignored/nested payload retains),
   #243 (ten detached retained checkouts), and #244 (operation and lock retains,
   51 items) are open. The handoff's definition of done listed only the
   ten-worktree delta and the census, and did not account for these.
2. **#233 cannot close.** Its body poses an explicit owner choice among "keep all
   until separately audited", "adjudicate bag-by-bag with agent-prepared
   manifests", and "other", and states it is blocked pending manifests. Closing
   it is an owner act, not an agent act.
3. **Receipt hygiene still outstanding**, unchanged from the handoff: the
   external radio-frequency-interference relocation receipt at
   `/Volumes/ArtifexBackupDrive/Faber2026-worktrees/receipts/20260724T190204Z-rfi-route-validation/`
   records a faulty `source_entries=1` and lacks
   `delta/verification-summary.txt`; three relocation final manifests still need
   a SHA-256 seal. Not attempted here — it touches preserved external payloads
   and is a separate lane from the ten-row delta.
4. **Newly discovered post-estate item, not in the handoff's ten rows:**
   `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-worktrees/special-refs-20260724`
   — a **standalone full clone**, 786 MiB, created 2026-07-24 11:33, branch
   `docs/special-ref-maintenance-20260724`, HEAD `3a58378`, clean, submodules
   uninitialized, no open handles. Because it is a standalone clone rather than a
   registered linked worktree, the five-common census cannot see it. Its content
   **has landed**: pull request #245 is merged, and the 30-line
   "Repository maintenance: special refs" section it adds is byte-identical to
   the section at `README.md:39` on `origin/main`. It therefore belongs to the
   orphan-full-clone cohort (#234), not the linked-worktree cohort. Left in
   place — **decision pending**, deliberately outside this session's sanctioned
   scope.
5. **Separate lane preserved, untouched:** the canonical `Faber2026-analysis`
   primary checkout is on `codex/nine-sightline-search-contract`, dirty, with an
   abandoned cherry-pick sequencer and an unresolved conflict in
   `docs/rse/wayfinder/map-apj-submission.md`. It belongs to another agent's
   work; nothing was staged, committed, aborted, or cleaned there.
6. **No test suite ran.** This wave changed no production or scientific code.
   The `pipeline/` gitlink and all canonical refs are untouched, so there is no
   scientific result to reproduce or regression to check.

---

## 7. Recommendations

**Critical — none.** No content loss, no protected-path violation, no
separate-lane contamination.

**Important**

- Work #242, #243, and #244 before attempting to close #229. Those three cohorts
  (ignored/nested payload, detached checkouts, operation/lock retains) cover
  roughly 63 registry entries and are the actual remaining bulk of the map.
- Put `special-refs-20260724` in front of the owner under #234's orphan-clone
  protocol rather than letting it sit unclassified.
- When judging whether a worktree holds unique content, check the **remote**,
  not just local object stores. Pipeline commit `1d5633c1` would have looked
  unique under a local-only check while being a branch tip on GitHub.

**Nice to have**

- The now-empty container
  `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis-worktrees/`
  can be removed whenever convenient; it holds nothing.
- Seal the three relocation manifests and annotate the faulty
  radio-frequency-interference receipt while the drive is mounted.

**Follow-up requiring the owner**

- #233's bag-by-bag adjudication choice.
- Whether local Time Machine snapshots should be thinned to realise the ~9.7 GiB
  on an internal volume that is 99% full. Destructive; not attempted.

---

## References

- [`handoff-2026-07-24-12-40-worktree-content-disposition.md`](handoff-2026-07-24-12-40-worktree-content-disposition.md) — primary handoff validated here
- [`handoff-2026-07-24-12-33-worktree-content-disposition.md`](handoff-2026-07-24-12-33-worktree-content-disposition.md) — operational annex with the ten-row table and safety rules
- Receipts: `~/Developer/scratch/receipts/Faber2026/worktree-retirement/post-estate-delta-20260724T195430Z/`
- Issues: [#229](https://github.com/jakobtfaber/Faber2026/issues/229), [#233](https://github.com/jakobtfaber/Faber2026/issues/233), [#234](https://github.com/jakobtfaber/Faber2026/issues/234), [#242](https://github.com/jakobtfaber/Faber2026/issues/242), [#243](https://github.com/jakobtfaber/Faber2026/issues/243), [#244](https://github.com/jakobtfaber/Faber2026/issues/244)
