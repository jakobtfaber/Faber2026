# Set the independent validation and release gate

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Independent reviewer
- Blocked by: [Set the Figure 3 regeneration and promotion gate](expanded-foreground-catalog-repair-04-set-figure-3-gate.md)
- Map: [ApJ submission](../map-apj-submission.md) (folded from the expanded-foreground-catalog-repair map, 2026-07-27)
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

## Current state (2026-07-29)

The pipeline-bound release gate is **retired and superseded**. It declared
every replay against the `dsa110-FLITS` repository at pipeline commit
`99e60c3a`, reached through a `pipeline/` git submodule the manuscript no
longer carries — `.gitmodules` records `analysis/` as the only submodule. It
also bound a superseded parent commit, a superseded installed Figure 3
SHA-256, and a review batch path since moved. Run as it stood, it raised
`FileNotFoundError` rather than refusing a release.

Its replacement is `scripts/validate_foreground_census_analysis_only.py`,
which reads only `analysis/` and **passes**. Six checks, each recomputing
rather than reading:

1. Every adopted redshift carries a source-bearing record — 12 of 12 host
   redshifts trace to the frozen extracts, 46 of 46 adopted candidate
   redshifts to frozen, hashed catalog rows.
2. Redshiftless systems and the three sightlines with no established host
   redshift fail closed everywhere, and each recorded fail-closed reason is
   checked against the data rather than trusted.
3. The Figure 3 input rebuilds byte-identically from committed sources; all 7
   cross-listing deduplications reproduce from coordinates; 192 catalog
   cross-matches carry a separation, candidate count, response hash, retrieval
   time, and — where more than one candidate was returned — the runner-up.
4. All 12 sightlines carry coverage across 5 surveys, with coordinates
   matching the roster and both footprint files hashing as recorded.
5. Halo and cluster mass and radius conventions are declared, distinct, and
   never mixed; all 25 halo radii reproduce from their masses at 200 times the
   critical density under Planck18 to better than 0.1 per cent.
6. The twelve-sightline census and the installed Figure 3 describe the same
   systems.

Every check is paired with mutation tests that corrupt one input and assert
the check rejects it, so a passing run is evidence rather than an assertion.

Evidence:
[`../../specs/receipt-foreground-census-analysis-only-2026-07-29.md`](../../specs/receipt-foreground-census-analysis-only-2026-07-29.md)
and
`../../specs/evidence/foreground-census-analysis-only-2026-07-29/validation.json`.

Nothing was promoted. Scientific trust in the census is not asserted here, and
Figure 3 is not approved.

The two 2026-07-26 owner decisions recorded below are **closed by
obsolescence**: the pipeline pin cannot be bumped because the repository it
pinned is retired, and Figure 3 was rebuilt from the consolidated census by
pull request #282, which removed the superseded transient identifiers. Both
now read `FRB 20230913G` and `FRB 20240203D`.

## Owner decision required

One, and it is the one the retired gate also carried.

**Approve the installed Figure 3 bytes, or return `needs_revision`.** The
review is bound to SHA-256
`281e4bf4c9d910c070cb822195a743920a7ecf14e249c924521e359a9d788a75`, the bytes
`figures/sightline_halo_grid.pdf` actually carries, with a rendered preview of
those exact bytes at
`../../specs/evidence/foreground-census-analysis-only-2026-07-29/installed-figure3-preview.png`.
The binding record is `owner-review.json` in the same directory.

This rebinding matters: the retired gate bound approval to candidate
`3dece7e3…`, which is not what the manuscript installs, so approving that
candidate would not have approved the published figure.

The validation above cannot make this call. It establishes that the figure
shows the census correctly; it cannot judge whether the figure reads well, or
whether nine drawn panels — three sightlines are omitted for having no
established host redshift — is the right presentation for the paper.

**Blocked, needs an owner call before a review batch can exist:**
`scripts/figure_review.py new-batch` still requires `--pipeline-revision`,
naming the retired repository. Until that argument is made optional, a batch
for this candidate cannot be created without supplying a dead revision.

## Superseded record (2026-07-26)

The seven adversarial-review blockers recorded on 2026-07-24 were discharged
independently on 2026-07-26 against parent commit `ac004ece` and its pipeline
gitlink `78b448f0`. Evidence:
[`../../specs/receipt-independent-release-gate-discharge-2026-07-26.md`](../../specs/receipt-independent-release-gate-discharge-2026-07-26.md).
That work, and the pipeline pin bumps that followed it, are kept for the record
but no longer describe a reachable lineage.
