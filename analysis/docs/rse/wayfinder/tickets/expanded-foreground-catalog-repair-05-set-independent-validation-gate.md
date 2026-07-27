# Set the independent validation and release gate

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Independent reviewer
- Blocked by: [Set the Figure 3 regeneration and promotion gate](expanded-foreground-catalog-repair-04-set-figure-3-gate.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `blocked`

## Question

What evidence demonstrates that the rebuilt catalog, classifications, physics,
and Figure 3 are correct without trusting the builder or its prose summary?

## Acceptance decision

The reviewer starts from committed source inputs and paper equations, implements
independent calculations, rechecks every selected identifier and separation,
compares counts and hashes, and records row-level differences. Validation fails
on any unexplained mismatch, query-error collapse, missing input, stale figure,
unapproved figure, or classification drift. The final report names the parent
commit and pipeline commit and may say `Verified` only when all gates pass.

## Current state

The technical release gate is installed at
`docs/rse/specs/validation-expanded-foreground-independent-release-gate.json`
and enforced by
`scripts/validate_expanded_foreground_independent_release_gate.py`.

It independently replays the 52 source identities from pinned pipeline bytes,
recomputes exact hashes for the catalog, Figure 3 input, source artifacts, and
review candidate, and byte-compares the staged candidate with the installed
manuscript figure. The gate does not certify the expanded catalog, does not
promote scientific trust, and does not promote Figure 3. The installed
manuscript Figure 3 bytes and the pipeline gitlink were not changed.

The seven adversarial-review blockers recorded on 2026-07-24 were discharged
independently on 2026-07-26 against parent commit `ac004ece` and its pipeline
gitlink `78b448f0`. Evidence:
[`../../specs/receipt-independent-release-gate-discharge-2026-07-26.md`](../../specs/receipt-independent-release-gate-discharge-2026-07-26.md).

Three corrections came out of that work:

- The gate was bound to pipeline commit `c913175e`, which is **not** an
  ancestor of the pipeline main line. It is a pre-landing form of the change
  that landed as `f5c1d1f3`. The gate is now bound to the current parent
  commit and pipeline pin, and the validator checks both at run time against
  the manuscript checkout.
- The earlier statement that "current source replay verifies 52/52 rows" was
  true only at that unreachable commit and is **STALE**. Replayed at the
  pinned `78b448f0`, source verification is **46 of 52 with 6 discrepancy
  rows**; it is 52/52 at pipeline main `f5c1d1f3`. Verdict and budget replays
  are clean at every binding tested.
- Recomputing the Figure 3 provenance showed the candidate was built from
  registry snapshot `f35dd8be` rather than the pinned `96bfd323`. The
  snapshots differ only in transient identifiers for seven rows, but both the
  candidate and the installed manuscript figure still print `FRB 20230913A`
  and `FRB 20240203A`, which the pinned registry supersedes.

The validator exits nonzero on four recorded blockers:
`expanded-catalog-gate-not-passed`, `source-verification-incomplete`,
`figure3-registry-snapshot-stale`, and `figure3-owner-approval-missing`.

## Owner decisions required

None of the four blockers is dischargeable by verification. Two are owner
calls that this ticket cannot make:

1. Whether to bump the pipeline pin from `78b448f0` to `f5c1d1f3` or later,
   which is what would make source verification 52/52 at the pinned commit.
2. Whether Figure 3 must be regenerated from the pinned registry snapshot
   before submission, given that the figure currently installed in the
   manuscript carries two superseded transient identifiers.
