# Decide how to run the two-repository distillation sweep

- Type: `wayfinder:ops`
- Status: open — awaiting owner decision
- Assignee: jakobtfaber
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)

## Fact

The two-repository shape holds at the **import and dependency** layer only.
Verified 2026-08-04 against the live checkouts: the parent `.gitmodules`
declares exactly one submodule, `analysis` → `Faber2026-analysis`; no
`pipeline/` directory exists in either repository; `pyproject.toml` and
`uv.lock` here contain no FLITS reference; and no live Python outside
`.archive/` imports `flits`.

It does **not** hold at the executable, reproducibility, or publication layer.
Adversarial review the same day established three refutations:

- **`dsa110-FLITS` is currently load-bearing, not merely named.** Live batch
  scripts outside `.archive/` set `FLITS_REPO` to a sibling `dsa110-FLITS`
  checkout and `cd` into it — `scattering/studies/joint-refits/hpcc/run_burst.sbatch:25,28`
  and `hpcc/run_joint.sbatch:16,18`. Declared run configurations point at
  `scattering/configs/telescopes.yaml` and `scattering/configs/sampler.yaml`
  (`hpcc/wilhelm_chime_refit.yaml:4-5`, `joint-refits/wilhelm_chime_refit.yaml:9-10`,
  and further `local_runs/*.yaml`). **Neither config file exists in this
  repository**; both exist only in the sibling clone. Those runs cannot be
  reproduced from the two repositories alone.
- **The manuscript publishes `dsa110-FLITS` as the code release.**
  `main.tex:116` states the reduction and fitting pipeline is publicly
  available at `https://github.com/jakobtfaber/dsa110-FLITS` and that the
  accepted version of the manuscript corresponds to a tagged release of that
  repository; `main.tex:131` repeats the URL in `\software{}`. This is a
  publication commitment, not operational residue.
- **Machine inventory records it across hosts.**
  `data/catalog/machine_inventory.yaml` names the Mac clone (lines 12, 36, 42),
  quarantined h17 clone and fit outputs (289–301), and an arc copy (399–400).
  Inventory alone is provenance, but it shows the coupling is not confined to
  `.archive/` and `repro_manifest.csv`.

What remains beyond those three, enumerated the same day:

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

- `dsa110-FLITS`, 2.43 GiB, 21 commits behind, one modified file. Owner-retired
  2026-07-28 as a *dependency*; nothing imports it, but the batch scripts and
  run configurations above still execute out of it, so it is not inert.
- `FLITS` (remote `jakobtfaber/flits`), 1.04 GiB, 2 unpushed commits, 4
  untracked paths including `polarimetry/`.
- `dsa110-scat` 1.78 GiB, `FLITS_GBT` 0.09 GiB, `Faber2024` 0.015 GiB,
  `Faber2025` 0.020 GiB, and an empty `frb_analysis` whose upstream branch is
  gone. Total 5.36 GiB. **None of these six carries runtime coupling** —
  adversarial review found only prose, machine-inventory entries, migration
  path-maps, and reference notebooks. Only `dsa110-FLITS` is load-bearing.

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

It also does not establish what should replace the manuscript's `dsa110-FLITS`
citation, nor whether the batch-script runs that depend on the sibling checkout
are still live science or historical records. Those are the two questions that
decide whether literal two-repository distillation is reachable at all.

## The decision

Two gates come before any sweep, and neither is operational:

1. **`dsa110-FLITS` must be migrated or explicitly preserved before any clone
   retirement.** `scattering/configs/sampler.yaml` and `telescopes.yaml` exist
   only there, and live batch scripts execute out of it. Migrating them here
   makes the runs reproducible from two repositories; preserving the clone
   keeps them reproducible but abandons literal distillation. Deleting it
   without either silently breaks declared runs.
2. **The manuscript's code-availability wording is a separate scientific-owner
   change.** `main.tex:116` and `:131` publish `dsa110-FLITS` as the pipeline
   and as the accepted tagged release. Either the manuscript repoints to
   `Faber2026-analysis`, or `dsa110-FLITS` stays public and frozen as the cited
   artifact. This is a publication commitment and is not covered by any
   operational sweep.

Only after those does the remaining work split by cost. Enumeration is
deterministic and already done — a handful of Git commands, not an agent
fan-out. Per-item **disposition judgment** is the expensive part: roughly 40
independent items, each needing "unique work, superseded, or preserve?" backed
by a `range-diff` or content comparison rather than a branch-tip glance. That
part does parallelise, one agent per item, with an adversarial verifier on
every non-obvious "superseded" verdict, because that is the claim that is cheap
to assert and expensive to get wrong.

The owner's call is the method and scope for that remaining work, given the two
gates above.

```json
{
  "id": "two-repo-distillation-sweep",
  "kind": "operational",
  "title": "Two-repository distillation sweep",
  "decision": "How should the remaining ~40 branch, clone, and residual-coupling items be dispositioned so the project reduces to Faber2026 and Faber2026-analysis alone?",
  "recommended": {
    "choice": "gates-first-then-sweep",
    "reason": "Retiring dsa110-FLITS before migrating scattering/configs would silently break declared runs, and the manuscript still cites it as the accepted release. Close both gates first, then fan out the remaining ~40 items with adversarial verification of every superseded verdict."
  },
  "choices": [
    {
      "id": "gates-first-then-sweep",
      "label": "Close the two gates first — migrate scattering/configs (sampler.yaml, telescopes.yaml) and the referenced run data into this repository, and decide the main.tex citation — then run one multi-agent workflow over the remaining items, one agent per item with adversarial verification of superseded verdicts. Deletions stay gated on owner approval."
    },
    {
      "id": "preserve-flits-publicly",
      "label": "Abandon literal two-repository distillation: keep dsa110-FLITS public and frozen as the manuscript's cited tagged release, leave main.tex unchanged, and sweep only the branches, dead refs, and the five siblings that carry no runtime coupling."
    },
    {
      "id": "branches-only-now",
      "label": "Disposition only the branches, pull requests, and dead remote-tracking refs now; defer both gates and every clone decision to a separate ticket."
    },
    {
      "id": "defer",
      "label": "Defer the whole sweep. Note this leaves declared runs dependent on a sibling checkout and the manuscript citing a retired repository."
    }
  ],
  "context": [
    "Verified 2026-08-04: .gitmodules declares only analysis; no pipeline/ directory; no FLITS in pyproject.toml or uv.lock; no live import of flits outside .archive. The two-repository shape holds at the import layer only.",
    "Adversarial review 2026-08-04 refuted the stronger claim: hpcc/run_burst.sbatch:25,28 and hpcc/run_joint.sbatch:16,18 execute out of a sibling dsa110-FLITS checkout; dispersion/studies/scattering-dm-locked/run_joint.sbatch:35 runs $FLITS_REPO/analysis/...; run configs point at scattering/configs/sampler.yaml and telescopes.yaml, which exist only in the sibling clone.",
    "main.tex:116 and :131 publish https://github.com/jakobtfaber/dsa110-FLITS as the reduction and fitting pipeline and as the accepted tagged release — a publication commitment, not operational residue.",
    "Of the seven sibling clones (5.36 GiB total), only dsa110-FLITS carries runtime coupling; dsa110-scat, FLITS, FLITS_GBT, Faber2024, Faber2025 and frb_analysis appear only in prose, machine inventory, migration path-maps, and reference notebooks.",
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
