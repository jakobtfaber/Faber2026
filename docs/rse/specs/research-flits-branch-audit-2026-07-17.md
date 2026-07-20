# FLITS fork branch audit — 2026-07-17

## Scope and decision rule

This audit covers the 29 branches present on
`jakobtfaber/dsa110-FLITS` when the cleanup phase began. During the audit the
remote gained a thirtieth branch, `toa-model-definition-switch`; it is recorded
separately rather than silently changing the requested inventory.

A branch is a deletion candidate only when its tip is protected by at least one
of the following and it has no open PR or occupied worktree:

1. the exact head was merged by a named PR;
2. the tip is an ancestor of a surviving integration ref;
3. the branch's changed paths are already identical on `main`; or
4. a later PR explicitly supersedes or ports the branch's useful content.

`entire/checkpoints/v1` is a retention ref, not a feature branch. Worktree
occupancy and open-PR ownership override apparent staleness. The July history
rewrite means a lack of ancestry with current `main` is not, by itself, proof
of unique content.

## Live-state boundary

- Audit start: 29 remote branches.
- Audit refresh: 30 remote branches after PR #194 appeared.
- Open fork PRs at refresh: #192, #193, and #194.
- Open upstream PR using a fork head: draft dsa110/dsa110-FLITS#49 from
  `agent/revert-dm-phase-v1` to upstream `pin/faber2026`.
- Occupied FLITS worktrees:
  - detached parent submodule checkout at `79b7b0e` (dirty);
  - local-only `feat/remediation-artifacts` at `4e951c8`;
  - `scint/window-tuning-campaign` at local `b815445` (the remote head advanced
    to `eb61267` during this audit).
- After explicit owner confirmation, all 22 deletion candidates were removed
  in one atomic push with exact old-SHA leases. A post-push `ls-remote`,
  fetch/prune, open-PR query, and worktree inventory confirmed the eight-ref
  survivor set documented below.

## Individual dispositions for the original 29

| # | Branch at audited tip | Disposition | Individual evidence |
|---:|---|---|---|
| 1 | `a1/trigger-calibration` `1e58c96` | **delete candidate** | No PR/worktree. Its ten campaign code/test paths are byte-equal to current `main`; PR #174 explicitly consolidated the completed 68-cell A1 campaign and records zero qualified measurements. |
| 2 | `agent/chime-artifact-consolidation` `691dc7d` | **delete candidate** | Exact head merged by PR #174; the merge tree at `91a5120` is tree-identical to this head. |
| 3 | `agent/dm-phase-suite-v1` `5e15f96` | **delete candidate** | Exact ancestor of surviving upstream `pin/faber2026`; the invalid v1 result is being removed by upstream PR #49. The source branch adds no reachability beyond the surviving upstream pin. |
| 4 | `agent/dm-phase-v2` `c07f1f1` | **keep — provenance/landing pending** | Two commits beyond upstream pin, no PR, and explicitly named as the source branch/commit by `analysis/dm-joint-phase-v2/SOURCE.json` and its README. Deleting it would orphan the live provenance ref before a tag or landing decision exists. |
| 5 | `agent/revert-dm-phase-v1` `a08597b` | **keep — active upstream PR** | Head of open draft upstream PR #49, which reverts invalid v1 content from upstream `pin/faber2026`. |
| 6 | `agent/two-band-event-figure-prototype` `d99e98a` | **delete candidate** | Exact head merged by PR #175, which deliberately ports the useful prototype onto clean `main`. |
| 7 | `census/attribution-matrix-parity-20260715` `90d8f2d` | **delete candidate** | Exact PR #188 head; PR merged. Tip is also an ancestor of current `main`. |
| 8 | `census/v4-extension-20260715` `c9d7826` | **delete candidate** | Exact PR #186 head; PR merged. Squash history explains non-ancestry, while the reviewed head is fully represented by the merge. |
| 9 | `entire/checkpoints/v1` `a90492d` | **keep — retention ref** | Entire checkpoint namespace used for agent/session recovery; not a feature-branch cleanup target. |
| 10 | `feat/chime-scint-common-mode-correction` `195479f` | **delete candidate** | PR #160 was intentionally closed after a fail-closed diagnostic result. The qualified recovery stack superseded it through #166, the old pin lane was content-relanded by #171, and #174 consolidated the surviving evidence. |
| 11 | `fix/class-aware-pcc-20260712` `528b21e` | **delete candidate** | Exact ancestor of both surviving upstream and fork pin lineages; no open PR/worktree and no unique reachability. |
| 12 | `fix/dm-locked-joint-figures` `4a07029` | **delete candidate** | Old eight-commit campaign head. PR #173 explicitly landed the expanded 15-commit `fix/dm-locked-joint-figures-v2` campaign on clean `main`; remaining differences are superseded roster/README/checkpoint state. |
| 13 | `fix/scint-component-track-plot` `11a68fb` | **delete candidate** | PR #159 merged the component-track fix. PR #175 explicitly says the disconnected preservation branch was replaced by a clean-main port of the useful one-event layout experiment. |
| 14 | `joint/tf-fit-window-resolution` `d292f4b` | **keep — active fork PR** | Head of open, clean PR #193 with passing checks. |
| 15 | `main` `8e54589` | **keep — default branch** | Fork default/development branch. |
| 16 | `pin/faber2026` `5405e5f` | **keep — integration/provenance ref** | Long-lived Faber2026 integration pin on the pre-rewrite lineage; several old-history branches are safely reachable only through this retained ref. |
| 17 | `reval/p0-provenance` `9b7ebe0` | **delete candidate** | PR #170 merged the P0 head; the current tip is only a merge of that head with PR #173's already-merged main head, with no unique commit payload. |
| 18 | `scint/c1-allpairs-crossgp` `79de266` | **delete candidate** | PR #176 merged C1; this later tip only merges P1 head `72f9dbb`, which separately merged to `main` in PR #179. |
| 19 | `scint/chime-recovery-failclosed` `0f92826` | **delete candidate** | Exact ancestor of surviving upstream `pin/faber2026`; no open PR/worktree or unique reachability. |
| 20 | `scint/chime-recovery-loop` `a8f3df5` | **delete candidate** | Closed PR #163 contains an explicit maintainer comment: superseded by #166, with H2/H3/A1/B1 evidence preserved and unrelated association changes excluded. The lane was subsequently relanded/consolidated by #171/#174. |
| 21 | `scint/eligibility-caveats` `3ef2197` | **delete candidate** | Exact PR #177 head and ancestor of current `main`. |
| 22 | `scint/p1-window-upchan` `72f9dbb` | **delete candidate** | Exact head merged to `main` by PR #179 (and earlier into C1 by #178); current `main` contains the tip. |
| 23 | `scint/p2-routeb-voltage` `c952849` | **delete candidate** | Exact PR #180 head and ancestor of current `main`; canonical program state marks the lane terminal/documented-fail. |
| 24 | `scint/p3-optimal-estimator` `4dcdb8e` | **delete candidate** | Exact PR #181 head and ancestor of current `main`; canonical program state marks the lane done. |
| 25 | `scint/p4-envelope-model` `0cf0558` | **delete candidate** | Exact PR #182 head; merge commit `479d2c8` is tree-identical. Canonical program state records the terminal documented failure. |
| 26 | `scint/recovered-notebook-replay` `7db0d46` | **delete candidate** | Exact ancestor of surviving fork `pin/faber2026`; notebook replay evidence was explicitly consolidated by PR #174. |
| 27 | `scint/reference-arc-rescue` `9237e4c` | **delete candidate** | Exact ancestor of surviving upstream `pin/faber2026`; reviewed rescue content merged through PRs #162/#168 and was carried through the content-level reland PR #171. |
| 28 | `scint/reference-parity` `46429ca` | **delete candidate** | Exact ancestor of surviving upstream `pin/faber2026`; parity extensions were included in the pin lane and content-level reland PR #171. |
| 29 | `scint/window-tuning-campaign` `eb61267` | **keep — active PR/worktree** | Head of open PR #192. The remote advanced during audit; the occupied local worktree remains at `b815445` and must not be removed or rewritten. |

## Concurrent remote drift after the 29-branch freeze

| Branch | Disposition | Evidence |
|---|---|---|
| `toa-model-definition-switch` `c4edc1a` | **keep — active fork PR** | New head of open PR #194. It appeared after the requested 29-branch snapshot and is not part of the deletion batch. |

## Executed deletion batch

The following 22 refs were deleted with exact old-SHA leases in one atomic
`git push origin --atomic` request after owner confirmation.

```text
a1/trigger-calibration                         1e58c96e6cdea034ecc20f3b6d658d95ec977d81
agent/chime-artifact-consolidation             691dc7d355e7506cceea621818309934904fb2d1
agent/dm-phase-suite-v1                        5e15f96b29f53dae42d7cff928ab4887f1bd3b7c
agent/two-band-event-figure-prototype          d99e98ab0ee00a076edd9d0bc21a9cbf95d36b86
census/attribution-matrix-parity-20260715      90d8f2dadb36c2cbcd6caf2cbe0919797a577ff0
census/v4-extension-20260715                    c9d78260aa38734971e1e2df38ea0140aa667f61
feat/chime-scint-common-mode-correction         195479fd0df16bd6654bdc31202a3d67f46edb0b
fix/class-aware-pcc-20260712                    528b21eab0681d9b5d2fd195764a8ec3d48def3c
fix/dm-locked-joint-figures                     4a070294f817a106ea9176462dd73f72ed5416e2
fix/scint-component-track-plot                  11a68fb577353719b752948ea91597c92365fe97
reval/p0-provenance                             9b7ebe02c33e64987ab3685388e8af851c1ff33a
scint/c1-allpairs-crossgp                       79de266130583a12933631bbd2115c1ec7061721
scint/chime-recovery-failclosed                 0f9282616112c731a0d58a7d721db835dbd5b65d
scint/chime-recovery-loop                       a8f3df54370a6b2cf5d420e16cbb148d3c58b8a7
scint/eligibility-caveats                       3ef219780a59ed2c2e59fa68bde02312ccf16902
scint/p1-window-upchan                          72f9dbb48af65c211e753085a7a10b7c1f20ead7
scint/p2-routeb-voltage                         c952849e5e7a692b4fc043f3559d5f2edade83b9
scint/p3-optimal-estimator                      4dcdb8ead3b66b7b216f3a4c29aa0e4e7acc8140
scint/p4-envelope-model                         0cf0558f9b35f6f8c1c810b9e972efe5b20b4d40
scint/recovered-notebook-replay                 7db0d4633c11b60dcdac8cd260ebbb5334243265
scint/reference-arc-rescue                      9237e4c982b46f1993363cb3242298a81f3b7dd2
scint/reference-parity                          46429ca37ba93a1c43c86f5c5f3892d658965893
```

Verified post-batch fork branches: eight — `main`, `pin/faber2026`,
`entire/checkpoints/v1`, `agent/dm-phase-v2`,
`agent/revert-dm-phase-v1`, `joint/tf-fit-window-resolution`,
`scint/window-tuning-campaign`, and the newly arrived
`toa-model-definition-switch`.

Post-push verification also confirmed that fork PRs #192, #193, and #194 are
open, clean, and passing, and that all three pre-existing FLITS worktree
checkouts remain present.

## Follow-up decisions outside deletion authority

1. Resolve upstream PR #49; do not close or delete its head as clutter.
2. Decide whether `agent/dm-phase-v2` should land, be tagged as a provenance
   snapshot, or be retired only after its Faber2026 source references are
   updated.
3. Reconcile the occupied `scint/window-tuning-campaign` worktree with its
   advanced remote head through its active owner/PR workflow.
4. Preserve the dirty detached submodule and local-only
   `feat/remediation-artifacts` worktree; neither is remote-branch clutter.
