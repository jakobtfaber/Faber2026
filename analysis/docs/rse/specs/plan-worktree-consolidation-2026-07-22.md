# Worktree Consolidation Plan (2026-07-22)

> **Amended 2026-07-25 by owner decision.** The original ">2 days idle" pruning
> clock is **cancelled**. This is a consolidation *review* plan, not a deletion
> schedule. Retirement rules are owned by the authority reconciliation
> (`worktree-reconciliation.md` at the parent repo root): no merging, manuscript
> promotion, or retirement begins until those rules are agreed. Every removal
> needs positive evidence plus an explicit owner decision — never elapsed time.

## 1. Executive Strategy
With **132 cataloged worktrees** across `Faber2026`, `analysis`, `pipeline`, local scratch/tmp, and `h17`, the worktree footprint is far larger than the working set anyone is actually using, which is what makes the material hard to navigate.

The goal is to establish, for every analysis family, one accepted conclusion and one authoritative producing commit — and *then* let the redundant checkouts fall out as a consequence. A small active working set is the expected outcome, not a quota to hit by deleting until the count drops.

---

## 2. Action Tiers & Execution Order

### Tier 1: Triage & Preserve Dirty Worktrees (DO NOT DELETE)
Before any pruning, audit and stash/commit uncommitted work in the **14 dirty worktrees**:

| Repository | Path | Dirty Count | Target Action |
| :--- | :--- | :--- | :--- |
| `Faber2026` | Root (`repos/.../Faber2026`) | 8 files | Keep active main workspace |
| `Faber2026` | `.codex-expanded-foreground-map-closure-20260722` | 2 files | Stash / commit `analysis` & `pipeline` pointers |
| `Faber2026` | `Faber2026-rfi-preservation-prototype` | 15 files | Commit active experimental RFI code |
| `Faber2026` | `Faber2026-rfi-route-validation` | 1 file | Review detached HEAD merge commit |
| `Faber2026` | `Faber2026-ticket14-roster` | 1 file | Commit ticket14 reproduction gate update |
| `Faber2026` | `Faber2026-wayfinder18` | 1 file | Review `.kb/` additions |
| `analysis` | `Faber2026-analysis-host-redshifts` | 3 files | Commit host-redshift claims |
| `analysis` | `Faber2026-analysis-rfi-preservation` | 6 files | Commit RFI preservation limits |
| `analysis` | `Faber2026-analysis-ticket-10` | 1 file | Commit count-audit decision packet |
| `pipeline` | `dsa110-FLITS-joint-scattering-seeded-20260722` | 6 files | Commit joint fit test scripts |
| `h17` | `/home/ubuntu/worktrees/joint-tf-fits` | 1 file | Review joint TF fit outputs |

---

### Tier 2: Evidence-Gated Retirement Review (no idle clock)

**Owner decision, 2026-07-25: the ">2 days idle" clock is cancelled. A date never
makes the removal decision.** Idle time is not evidence about the scientific
value of a checkout, and the retirement rules are set by the authority
reconciliation (`worktree-reconciliation.md`), not by this plan. Nothing below is
a prune list; it is a *review queue*, and no entry leaves it without the proof
gate satisfied and an explicit owner decision recorded.

#### Proof gate — all four required before any `worktree remove`

1. **Authority status assigned.** The checkout's analysis family has an
   accepted conclusion (or an explicit unresolved result) recorded under the
   reconciliation's status scheme, with its authoritative producing commit named.
2. **Working tree clean.** No modified, staged, untracked, deleted, renamed, or
   conflicted files. A dirty checkout is never removed — it goes to Tier 1.
3. **No live pull-request dependency.** `gh pr list --head <branch>` returns
   nothing open.
4. **No unmerged unique delta.** Proven by `git range-diff` or content
   comparison against `origin/main` — **not** `git cherry`. These repos rebase
   and squash-merge, so `git cherry` reports already-upstream commits as unique
   (see the branch-staleness note in project memory).

Removing the checkout must also not be the last copy of a preserved negative or
superseded result the reconciliation wants kept.

#### Review queue — main repo (`Faber2026`)

| Path | Note |
| :--- | :--- |
| `~/Developer/scratch/worktrees/Faber2026-scint-2l` | pending gate |
| `~/Developer/scratch/worktrees/Faber2026-quarantine-20260717` | pending gate |
| `~/Developer/scratch/worktrees/Faber2026-expanded-foreground-phase-two` | pending gate |
| `~/Developer/scratch/worktrees/Faber2026-foreground-redshift-verdicts` | **stale entry — do not action.** As of 2026-07-25 the live registered worktree for `research/foreground-redshift-verdicts` is `/Volumes/ArtifexBackupDrive/Faber2026-worktrees/parent/Faber2026-foreground-redshift-verdicts`, and it is **locked**. Re-verify before any review. |
| `~/Developer/scratch/worktrees/Faber2026-overleaf-native-git-contract` | pending gate |
| `~/Developer/scratch/worktrees/Faber2026-jointtf-grok-revalidation` | pending gate |
| `~/Developer/scratch/worktrees/Faber2026-wayfinder-auto/audit-results-library-conflicts` | pending gate |

#### Review queue — `pipeline` / `dsa110-FLITS`

| Path | Note |
| :--- | :--- |
| `~/Developer/scratch/recovery/flits-window-tuning-ae67bdf` | pending gate; under `recovery/`, treat as preserved until proven duplicated |
| `~/Developer/scratch/worktrees/FLITS-quarantine-20260717` | pending gate |
| `~/Developer/scratch/worktrees/pipeline-archive-historical-diagnostics-20260720` | pending gate; name suggests archival intent |

#### Review queue — `analysis` / `Faber2026-analysis`

25+ ticket worktrees under `~/Developer/scratch/worktrees/Faber2026-analysis-*`
(`close-02`, `close-03`, `converge-*`, `wayfinder-auto/*`). "Merged ticket" is a
claim to be proven per checkout via the gate above, not a batch assumption.

---

### Tier 3: Temp & Orphan Worktree Cleanup
- Review transient checkouts in `/private/tmp/` (`faber2026-analysis-rfi01a.*`,
  `ticket14-review.*`). These are volatile — `/private/tmp` is cleared by the OS —
  so if one holds unique work, it needs preserving, not pruning.
- `git worktree prune` on all 3 repositories is safe **only** for administrative
  refs whose working directories no longer exist. Note it will drop the
  registration for any worktree on an **unmounted** volume: as of 2026-07-25 four
  registered worktrees live on `/Volumes/ArtifexBackupDrive`. Never run it while
  that drive is detached.

---

### Tier 4: Canonical Active Working Set
The expected steady state once reconciliation is done — a description of what
stays hot, **not** a cap that licenses removing everything else. Checkouts
outside this list are retired only through the Tier 2 gate.
1. `Faber2026` root (Manuscript)
2. `Faber2026/analysis` root (Analysis)
3. `Faber2026/pipeline` root (Pipeline)
4. `Faber2026-host-dm-repair` (Active figure repair)
5. `Faber2026-rfi-preservation-prototype` (Active RFI prototyping)
6. Overleaf working copy (`~/Developer/overleaf/Faber2026`)
