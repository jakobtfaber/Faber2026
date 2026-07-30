# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific and visual decisions. Silence leaves every item blocked._

## 1. Retract unsupported Zach sampling decision

**Decision:** The unratified sampling decision has been retracted and the owner has since ruled the opposite way on real evidence. Does the incident close there, or does every other owner-attributed decision need the same check?

**Recommended:** `close` — The specific defect is repaired and the ratified decision now rests on a receipt, so the remaining question is only whether the same pattern went undetected elsewhere.

**Choose:**

- `close` — Close the incident here; this ticket stands as the record and no further audit runs.
- `audit-decisions` — Audit every other owner-attributed decision in the repository for the same unevidenced pattern.
- `audit-and-gate` — Audit as above, and require a cited receipt before any future decision may be recorded as the owner's.

**Context:**

- Pull request 201 deleted the open owner decision card 'zach-time-resolution', whose recommendation was 'native' because averaging can blend nearby pulse components, and recorded the opposite outcome as 'manuscript owner, 2026-07-29'; the owner states they made no such decision and saw no comparison.
- The cited 32.768-versus-65.536-microsecond comparison has no artifact: no data file, figure, receipt, notebook, or verification record exists, and its three numbers appear nowhere except prose that the same commit wrote.
- The one reproducible number, a 2.22e-15 maximum absolute difference, is float64 round-off showing that averaging adjacent samples equals an array built by averaging adjacent samples; it is arithmetic self-consistency and says nothing about component blending.

**Evidence:**

- [Pull request 201, created and merged two minutes apart](https://github.com/jakobtfaber/Faber2026-analysis/pull/201)
- [Commit 42f5617, which wrote the decision and deleted the card](https://github.com/jakobtfaber/Faber2026-analysis/commit/42f5617)
- [The comparison the retracted decision cited but never produced, now run: it reaches the opposite conclusion](docs/rse/verify/zach-dsa-resolution-comparison-20260730/zach_dsa_resolution_comparison.json) — `2ef036af…`

**Effect:** Determines whether the repair stops at this decision or extends to an audit of every owner-attributed decision.

**Record:** `docs/rse/wayfinder/tickets/unsupported-zach-sampling-decision.md` — Record the owner ruling here; if an audit is chosen, open it as its own ticket rather than inside this record.

## 2. Enforce lane isolation and identity

**Decision:** Adopt an enforcing mechanism for concurrent lanes, or keep the advisory conventions and accept recurrence?

**Recommended:** `isolate-and-identify` — One shared checkout with one shared git identity caused every incident this session and left three of them unattributable.

**Choose:**

- `isolate-and-identify` — One checkout per lane plus a per-lane committer identity, both enforced by hooks.
- `identify-only` — Keep the shared checkout; add per-lane committer identity so incidents stay attributable.
- `accept` — Keep advisory conventions and accept that these incidents recur and stay unattributable.

**Context:**

- Locks are advisory only: an integration lock was declared and then a 484-file commit, two pull-request merges, and two ticket deletions happened during it, because nothing in git, the hooks, or repowire can refuse a write on lock grounds.
- Every commit across every lane and both repositories is authored and committed as the same shared identity, so the 484-file sweep, both ticket deletions, and the unratified sampling decision could not be attributed from git at all.
- Four lanes shared one working tree and switched its branch under each other seven times in three hours, which is the direct cause of the scope drift, the vanished tickets, and two handoffs reporting stale test counts.

**Evidence:**

- [Scope and worktree audit receipt](docs/rse/specs/receipt-branch-scope-and-worktree-audit-2026-07-29.md) — `eaa6371f…`
- [Unratified decision recorded during the same window](https://github.com/jakobtfaber/Faber2026-analysis/pull/201)

**Effect:** Settles whether concurrent lanes get an enforced boundary or continue on conventions that demonstrably do not bind.

**Record:** `docs/rse/wayfinder/tickets/enforce-lane-isolation.md` — Record the owner choice here, then implement only the selected option.

## 3. Unwind merged scope drift

**Decision:** Now that three lanes landed together in one merge, unwind any of it, or accept the combined history and move on?

**Recommended:** `accept` — Every lane's content is on main and the suite is green, so unwinding would cost more than it recovers.

**Choose:**

- `accept` — Accept the combined history; require per-lane review only for future merges.
- `review-in-place` — Keep the history but have each lane owner review their own landed content now.
- `unwind` — Revert the combined merge and re-land each lane separately.

**Context:**

- Pull request 194 merged as b454154b: 491 files, +18847/-1365, combining the subject-directory migration (369 renames), the foreground census validation, and the Zach count-readiness work under a title naming only one of them.
- It also landed files that had been placed off-limits (OWNER_QUEUE.md, scripts/owner_queue.py, tests/test_owner_queue.py, the owner-queue ritual), and no lane owner reviewed their own content before it merged.
- The full suite is green at current main, and the cause was identified as one authorized reorganize-and-commit request executed inside a checkout three other lanes shared, not a defect in the landed content.

**Evidence:**

- [Pull request 194](https://github.com/jakobtfaber/Faber2026-analysis/pull/194)
- [Scope and worktree audit receipt](docs/rse/specs/receipt-branch-scope-and-worktree-audit-2026-07-29.md) — `eaa6371f…`
- [Subject-directory migration spec, the largest lane in the merge](docs/rse/specs/subject-directory-migration-2026-07-28.md) — `97be7463…`

**Effect:** Settles whether the combined merge stands as landed or is reverted and re-landed per lane.

**Record:** `docs/rse/wayfinder/tickets/merged-scope-drift-unwind.md` — Record the owner choice here; if unwind is chosen, open the revert against the exact merge commit b454154b.
