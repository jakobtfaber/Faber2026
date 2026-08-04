# Decide how to run the two-repository distillation sweep

- Type: `wayfinder:ops`
- Status: open — awaiting owner decision
- Assignee: jakobtfaber
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)

## Fact

The project's code already has the intended two-repository shape. Verified
2026-08-04 against the live checkouts: the parent `.gitmodules` declares exactly
one submodule, `analysis` → `Faber2026-analysis`; no `pipeline/` directory
exists in either repository; `pyproject.toml` and `uv.lock` here contain no
FLITS reference; and no live Python outside `.archive/` imports `flits`.

What remains is residue around that shape, enumerated the same day:

**Branches and pull requests, this repository**

- 31 local branches ahead of `origin/main`, from `codex/host-dm-repair-v2`
  (9 commits) and `codex/auto-set-expanded-independent-validation` (7) down to
  20 branches 1 commit ahead.
- 5 unmerged remote branches: `codex/casey-exact-likelihood-acceleration`,
  `codex/geometry-constrained-joint-fit`, `codex/oran-isha-gates`,
  `receipts-dsa-timing-20260728`, and
  `codex/casey-fit-performance-recovery` (pull request #237).
- 5 remote-tracking refs under `local/` and `local-owner/` whose remotes no
  longer exist.
- `pin/pipeline-f5c1d1f3`, a branch from the retired submodule era.
- 3 open dependabot pull requests (#231, #232, #233).

**Clones on disk that are neither repository**

- `dsa110-FLITS`, 2.4 GB, 21 commits behind, one modified file. Owner-retired
  2026-07-28; nothing imports it.
- `FLITS` (remote `jakobtfaber/flits`), 1.0 GB, 2 unpushed commits, 4 untracked
  paths including `polarimetry/`.
- `dsa110-scat` 1.8 GB, `FLITS_GBT` 92 MB, `Faber2024` 15 MB, `Faber2025`
  20 MB, and an empty `frb_analysis` whose upstream branch is gone.

**Residual coupling inside this repository**

- `.archive/superseded-joint-refits/` hardcodes
  `/home/jfaber/flits/dsa110-FLITS` in nine files.
- `repro_manifest.csv` still prescribes `conda run -n flits` and
  `cd pipeline &&` as reproduction commands for five rows.

## Non-result

This enumeration establishes what exists, not what is disposable. It does not
establish that any branch is superseded, that any clone is retirable, or that
the `repro_manifest.csv` rows are stale rather than describing a still-valid
historical environment. Per the standing rule, subject-on-main does not prove
superseded while unique patches remain, and no clone may be retired without a
content disposition and receipt.

## The decision

The disposition work splits cleanly in two, and the split determines the cost.

Enumeration is deterministic and already done — it took a handful of Git
commands and must not be fanned out to agents. Per-item **disposition
judgment** is the expensive part: roughly 40 independent items, each needing
"unique work, superseded, or preserve?" backed by a `range-diff` or content
comparison rather than a branch-tip glance. That part does parallelise, one
agent per item, with an adversarial verifier on every non-obvious "superseded"
verdict, because that is the claim that is cheap to assert and expensive to get
wrong.

The owner's call is whether to spend a large multi-agent run on it, or to walk
the items in smaller owner-reviewed batches.

```json
{
  "id": "two-repo-distillation-sweep",
  "kind": "operational",
  "title": "Two-repository distillation sweep",
  "decision": "How should the remaining ~40 branch, clone, and residual-coupling items be dispositioned so the project reduces to Faber2026 and Faber2026-analysis alone?",
  "recommended": {
    "choice": "workflow-with-adversarial-verify",
    "reason": "The items are independent and the judgment per item is small but must be evidence-backed; a per-item fan-out with adversarial verification of every superseded verdict covers them in one pass without an agent swarm touching the deterministic enumeration."
  },
  "choices": [
    {
      "id": "workflow-with-adversarial-verify",
      "label": "Run one multi-agent workflow: one agent per item producing a land/superseded/preserve disposition with range-diff or content evidence, then an adversarial verifier on each superseded verdict, then a single receipt. Deletions stay gated on owner approval."
    },
    {
      "id": "batched-owner-review",
      "label": "Walk the items in owner-reviewed batches through the queue, starting with the 31 local branches, without a multi-agent run."
    },
    {
      "id": "scope-to-branches-only",
      "label": "Disposition only the branches and pull requests now; leave the non-Faber2026 clones and the archive/manifest coupling for a separate later decision."
    },
    {
      "id": "defer",
      "label": "Defer the whole sweep; the residue is inert and the two-repository shape already holds in code."
    }
  ],
  "context": [
    "Verified 2026-08-04: .gitmodules declares only analysis; no pipeline/ directory; no FLITS in pyproject.toml or uv.lock; no live import of flits outside .archive.",
    "31 local branches ahead of origin/main, 5 unmerged remote branches, 5 dead remote-tracking refs, 3 dependabot pull requests, plus pull request #237 which needs scientific reconciliation.",
    "5.4 GB of non-Faber2026 clones on disk (dsa110-FLITS, FLITS, dsa110-scat, FLITS_GBT, Faber2024, Faber2025, frb_analysis).",
    "The 2026-08-04 worktree consolidation is already complete and receipted; this ticket covers only what it deliberately left out of scope."
  ],
  "evidence": [
    {
      "label": "Worktree consolidation receipt",
      "path": "docs/rse/specs/receipt-worktree-consolidation-2026-08-04.md"
    },
    {
      "label": "Rescued joint-fit work awaiting reconciliation",
      "path": "https://github.com/jakobtfaber/Faber2026-analysis/pull/237"
    }
  ],
  "effect": "Selects the method and scope for retiring the remaining branches, clones, and residual FLITS/pipeline references. Records no disposition by itself; every deletion still needs separate owner approval naming exact paths.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/owner-decision-two-repo-distillation-sweep.md",
    "action": "Record the owner's chosen method and scope in a Resolution section, then execute only that scope."
  },
  "priority": 30
}
```

## Prerequisite check

The enumeration exists and is current as of 2026-08-04. No disposition
evidence — `range-diff` or content comparison per branch, content disposition
per clone — has been produced yet, so no retirement command is prescribed here.

Pull request #237 is a prerequisite for retiring
`codex/casey-fit-performance-recovery` and its rescue tag, and it needs
scientific reconciliation rather than an operational disposition.
