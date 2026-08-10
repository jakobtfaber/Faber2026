# Decide how to run the two-repository distillation sweep

- Type: `wayfinder:ops`
- Status: open — awaiting owner decision
- Assignee: jakobtfaber
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)

## Fact

**Settled owner decision, 2026-07-27:** Faber2026 carries no `dsa110-FLITS`
runtime, submodule, or external-package dependency. The migration and the
parent cutover landed 2026-07-28. The migrated resources are
`radio_pipeline/resources/scattering_sampler.yaml` and
`radio_pipeline/resources/scattering_telescopes.yaml` (analysis `1512b15e`,
2026-07-28), which current code loads through the packaged resource path — for
example `radio_pipeline/batch/codetection_data.py:58`. Migrate-versus-preserve
is therefore **not open**, and nothing in this ticket reopens it.

The two-repository shape holds. Verified 2026-08-04 against the live checkouts:
the parent `.gitmodules` declares exactly one submodule,
`analysis` → `Faber2026-analysis`; no `pipeline/` directory exists in either
repository; `pyproject.toml` and `uv.lock` here contain no FLITS reference; and
no live Python outside `.archive/` imports `flits`.

What remains is **stale cleanup defects** — pre-migration text that still names
the retired repository, none of it a live dependency:

- `scattering/studies/joint-refits/hpcc/run_burst.sbatch:25,28` and
  `hpcc/run_joint.sbatch:16,18` still default `FLITS_REPO` to a sibling
  `dsa110-FLITS` checkout; `dispersion/studies/scattering-dm-locked/run_joint.sbatch:35`
  still executes `$FLITS_REPO/analysis/...`. Superseded by the migrated
  resources above.
- `hpcc/wilhelm_chime_refit.yaml:4-5`, `joint-refits/wilhelm_chime_refit.yaml:9-10`,
  and further `local_runs/*.yaml` still point at the pre-migration
  `scattering/configs/{sampler,telescopes}.yaml` paths.
- `.archive/superseded-joint-refits/` hardcodes
  `/home/jfaber/flits/dsa110-FLITS` in 45 files, and `repro_manifest.csv` names
  `conda run -n flits` or `cd pipeline &&` in 24 rows.
- `data/catalog/machine_inventory.yaml` records the Mac clone (lines 12, 36,
  42), the quarantined h17 clone and fit outputs (289–301), and an arc copy
  (399–400). This is provenance and stays.

An earlier revision of this ticket read the first two items as evidence that
`dsa110-FLITS` was still load-bearing. That reading was wrong: it checked which
files an old script named, not which files current code loads.

Also enumerated 2026-08-04:

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

- `dsa110-FLITS`, 2.43 GiB, 21 commits behind, one modified file. Retired by
  owner decision 2026-07-27 and superseded by the 2026-07-28 migration; no
  runtime path reaches it. Retirement is gated on a content disposition and
  receipt, as for any clone — not on migration policy.
- `FLITS` (remote `jakobtfaber/flits`), 1.04 GiB, 2 unpushed commits, 4
  untracked paths including `polarimetry/`.
- `dsa110-scat` 1.78 GiB, `FLITS_GBT` 0.09 GiB, `Faber2024` 0.015 GiB,
  `Faber2025` 0.020 GiB, and an empty `frb_analysis` whose upstream branch is
  gone. Total 5.36 GiB. **None of the seven carries runtime coupling** —
  adversarial review found only prose, machine-inventory entries, migration
  path-maps, and reference notebooks.

**Residual coupling inside this repository**

- `.archive/superseded-joint-refits/` hardcodes
  `/home/jfaber/flits/dsa110-FLITS` in 45 files.
- `repro_manifest.csv` still prescribes `conda run -n flits` or
  `cd pipeline &&` in 24 rows.

## Non-result

This enumeration establishes what exists, not what is disposable. It does not
establish that any branch is superseded, that any clone is retirable, or that
the `repro_manifest.csv` rows are stale rather than describing a still-valid
historical environment. Per the standing rule, subject-on-main does not prove
superseded while unique patches remain, and no clone may be retired without a
content disposition and receipt.

It does not establish whether the stale batch scripts and run configurations
should be repointed at the migrated resources or deleted as superseded records.
That is a cleanup scope question, not a dependency question.

## The decision

Both former gates are closed.

The migration gate was already closed before this ticket: the owner decided on 2026-07-27 that
Faber2026 carries no `dsa110-FLITS` dependency, and the migration landed
2026-07-28. The manuscript gate is resolved to **Faber2026-only citation** —
the manuscript is to cite no GitHub repository except `jakobtfaber/Faber2026`
(landed in Faber2026 pull request #308, merged as `fc8f042b`..`4c27101d`), and
`Faber2026-analysis` is represented by the pinned `analysis/` submodule rather
than a second citation. Clone retirement is gated on a content disposition and
receipt, the same standard as any clone, and not on migration policy.

What is left is ordinary cleanup, split by cost. Enumeration is deterministic
and already done — a handful of Git commands, not an agent fan-out. Per-item
**disposition judgment** is the expensive part: roughly 40 independent items,
each needing "unique work, superseded, or preserve?" backed by a `range-diff`
or content comparison rather than a branch-tip glance. That part does
parallelise, one agent per item, with an adversarial verifier on every
non-obvious "superseded" verdict, because that is the claim that is cheap to
assert and expensive to get wrong.

The owner's call is the method and scope for that remaining work.

```json
{
  "id": "two-repo-distillation-sweep",
  "kind": "operational",
  "title": "Two-repository distillation sweep",
  "decision": "How should the remaining ~40 branch, clone, and residual-coupling items be dispositioned so the project reduces to Faber2026 and Faber2026-analysis alone?",
  "recommended": {
    "choice": "workflow-with-adversarial-verify",
    "reason": "No dependency or publication gate remains open. The items are independent and each judgment is small but must be evidence-backed, so a per-item fan-out with adversarial verification of every superseded verdict covers them in one pass without an agent swarm touching the deterministic enumeration."
  },
  "choices": [
    {
      "id": "workflow-with-adversarial-verify",
      "label": "Run one multi-agent workflow over the remaining items: one agent per item producing a land/superseded/preserve disposition with range-diff or content evidence, then an adversarial verifier on each superseded verdict, then a single receipt. Deletions stay gated on owner approval."
    },
    {
      "id": "stale-references-first",
      "label": "Clean the stale FLITS/pipeline references first — repoint or delete the joint-refit batch scripts and run configs and the repro_manifest rows — then disposition the branches and clones in a second pass."
    },
    {
      "id": "branches-only-now",
      "label": "Disposition only the branches, pull requests, and dead remote-tracking refs now; defer the clones and the stale references to a separate ticket."
    },
    {
      "id": "defer",
      "label": "Defer the sweep. The residue is inert — no runtime path reaches it — but it keeps naming a retired repository."
    }
  ],
  "context": [
    "Owner decision 2026-07-27: Faber2026 carries no dsa110-FLITS runtime, submodule, or external-package dependency. Migration and parent cutover landed 2026-07-28; the migrated resources are radio_pipeline/resources/scattering_sampler.yaml and scattering_telescopes.yaml (analysis 1512b15e), loaded via the packaged resource path (radio_pipeline/batch/codetection_data.py:58). Migrate-versus-preserve is not open.",
    "Manuscript gate resolved to Faber2026-only citation: the manuscript is to cite no GitHub repository except jakobtfaber/Faber2026, with Faber2026-analysis represented by the pinned analysis/ submodule. Landed in Faber2026 pull request #308, rebase-merged 2026-08-04.",
    "Verified 2026-08-04: .gitmodules declares only analysis; no pipeline/ directory; no FLITS in pyproject.toml or uv.lock; no live import of flits outside .archive.",
    "Stale cleanup defects, not dependencies: hpcc/run_burst.sbatch:25,28, hpcc/run_joint.sbatch:16,18 and dispersion/studies/scattering-dm-locked/run_joint.sbatch:35 still name FLITS_REPO; several run configs still point at the pre-migration scattering/configs paths; .archive/superseded-joint-refits hardcodes the old path in 45 files; repro_manifest.csv names 'conda run -n flits' or 'cd pipeline &&' in 24 rows.",
    "Of the seven sibling clones (5.36 GiB total), none carries runtime coupling; they appear only in prose, machine inventory, migration path-maps, and reference notebooks. Retirement is gated on content disposition and receipt.",
    "31 local branches ahead of origin/main, 5 unmerged remote branches, 5 dead remote-tracking refs, 3 dependabot pull requests, plus pull request #237 which needs scientific reconciliation.",
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
