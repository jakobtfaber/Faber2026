# Decision packet: trust-registry authority

Date: 2026-07-23  
Status: owner decision accepted 2026-07-23; implementation pending

Scope: authority adjudicated; accepted baseline not yet landed

## Decision boundary

This packet compares the four pinned trust surfaces requested by the Phase 1
authority-reconciliation plan. It does not select an authority, modify a trust
variant, promote a row, or merge a pull request.

Classification used below:

- **Presentation-only:** changes navigation, wording, or the generated human
  view without changing which result is citable or how the registry fails
  closed.
- **Scientific:** changes a trust state, adds or removes a registry row, changes
  the scope of a row, changes trust/provenance semantics, or changes whether an
  unreviewed manuscript claim or artifact is rejected.

## Compared variants

| Variant | Exact commit | Form | Registry snapshot | Material authority state | Agent proposal, not a decision |
|---|---|---|---|---|---|
| Pull request #31 exact | `5292337ffc6c0bb918a763860d70c0575530ae61` | Seven trust commits, then merge with contemporaneous `origin/main` | Schema 6; 62 rows; 13 trusted, 42 pending, 7 revoked; 6 complete and 56 pending provenance records | Exact row inventory; independently reviewed ownership for each numeric manuscript claim; exact artifact ownership; repository-specific full commit provenance; `budget.cluster_column` and `association.toa_offset_figure` pending | **Propose using this as the candidate authority baseline.** It is the strongest fail-closed implementation, but the two pending rows still require owner judgment. |
| `trust-publish` | `a9ac20cd007be5964db0219e5bb71afb3378679e` | Initial one-commit registry publication | Schema 2; 61 rows; 14 trusted, 40 pending, 7 revoked; provenance absent on 36 input-certificate rows | Separates scientific trust from provenance for manuscript rows, but has no compiled-manuscript coverage and no timing-offset row | **Propose superseded-preserved.** No unique valid work needs extraction; its useful registry/view foundation is incorporated and hardened in `5292337`. |
| `trust-publish-v2` | `ef3211be5745d5eb512694e823ea134ac8242750` | Initial publication plus one fail-closed successor commit | Schema 3; 62 rows; 15 trusted, 40 pending, 7 revoked; 7 complete and 55 pending provenance records | Adds compiled numeric-line and artifact coverage; adds `association.toa_offset_figure` as trusted; retains the old trusted `budget.cluster_column` conclusion | **Propose superseded-preserved.** Its coverage work is valid and is incorporated more strictly in `5292337`; its two citeability conclusions need explicit owner review, not implicit carry-forward. |
| Closed pull request #35 row audit | `75b9d5f62bbf8bf0526ad733add64a395ca8444d` | Review document only; registry unchanged from its schema-1 parent | Audit reads 61 rows and recommends one future trust change | Recommends `budget.host_dm_posteriors` pending→trusted after tickets 06 and 07; recommends no other trust-state change | **Propose retaining as review evidence, not as an implementation variant.** Its host-dispersion-measure release condition and cluster snapshot are superseded by newer evidence. |

## Comparison method

All commands used the objects at the exact commits above. The four supplied
worktrees were clean and their `HEAD` values matched the requested pins.

The publication histories diverge. The comparison therefore used
`git range-diff` on the related trust-only patch series:

```text
a9c96bd..a9ac20c  versus  06d21dc^..ef3211b
a9c96bd..a9ac20c  versus  8df98ba^..2e0fbd9
06d21dc^..ef3211b versus  8df98ba^..2e0fbd9
```

The row-audit commit is a separate one-file child of `dfcd1d5`; it is not a
publication series. Comparisons involving `75b9d5f` therefore used content
diffs of:

```text
docs/rse/control/results-registry.toml
docs/rse/control/results-registry-claim-owners.toml
docs/rse/specs/review-trust-ledger-2026-07-22.md
docs/rse/wayfinder/tickets/13-overhaul-trust-assessment.md
CONTEXT.md
RESULTS.md
scripts/generate_results_coverage.py
scripts/render_results_registry.py
tests/test_results_registry.py
Makefile
```

Direct whole-tree endpoint diffs were not treated as trust deltas because the
branches contain unrelated contemporaneous work. Registry rows were also
parsed by stable `id` and compared field by field.

## Pairwise delta classification

| Pair | Presentation-only delta | Scientific delta | Overall classification |
|---|---|---|---|
| `a9ac20c` → `ef3211b` | Regenerated `RESULTS.md`; stronger ticket, map, and standing-context wording | Adds the timing-offset row as **trusted**; gives all 36 input-certificate rows explicit pending provenance; adds compiled numeric-line and artifact coverage; rejects stale coverage, missing paths, unresolved pins, and new unregistered numbers or figures | Scientific successor with presentation changes |
| `ef3211b` → `5292337` | Refines the generated view and closure wording | Demotes timing-offset figure trusted→pending; demotes stale cluster-column result trusted→pending and replaces old `p50=252` scope with current `DM_int=255 (+67/-52); host DM p50=62`; adds exact canonical inventories and schemas; individually owns every numeric claim; separates association cards from the timing-offset figure; verifies full repository-specific commits and paths at those commits; rejects duplicate/nested-schema collapse and unresolved ownership; gates validation in `Makefile` | Scientific successor; two incompatible citeability conclusions |
| `a9ac20c` → `5292337` | Initial renderer and ticket/map presentation are superseded by the later generated view and wording | Combines the coverage hardening above with the timing-offset and cluster fail-closed dispositions; adds one row; reduces trusted rows from 14 to 13; makes all provenance explicit | Scientific; `a9ac20c` has no unique additional work |
| `75b9d5f` ↔ `a9ac20c` | Audit prose versus generated registry view | Audit proposes a future host-posterior promotion while `a9ac20c` leaves it pending; otherwise it endorses the trust states it reviewed. It does not implement schema-2 trust/provenance separation | Scientific recommendation only; no registry implementation |
| `75b9d5f` ↔ `ef3211b` | Audit prose versus expanded generated view | Audit does not review the new timing-offset row or compiled-coverage contract. It recommends host-posterior promotion, while `ef3211b` leaves it pending. It retains the old trusted cluster conclusion | Scientific recommendation plus omissions; no registry implementation |
| `75b9d5f` ↔ `5292337` | Audit prose versus hardened generated view and closure wording | Audit agrees that the gallery remains pending and that revoked/pending fit lanes remain fail-closed. It recommends host-posterior promotion under an older gate, omits the timing-offset row, and recommends keeping the old cluster result trusted; `5292337` instead demotes the cluster row against the current probabilistic values | Useful review evidence, but scientifically incomplete and partly superseded |

## Variant-specific answers

### Does `trust-publish` add valid work beyond pull request #31?

No unique valid addition remains. `a9ac20c` introduced the useful separation of
scientific trust from provenance completeness, a deterministic `RESULTS.md`
view, and basic consistency tests. Those are valid foundations, but
`5292337` incorporates and substantially hardens them.

Its presentation changes are superseded. Its scientific snapshot is
incompatible with `5292337` where it keeps the stale
`budget.cluster_column` result trusted and has no separately governed
`association.toa_offset_figure` row.

### What does `trust-publish-v2` add relative to `trust-publish`?

It adds valid scientific control work:

- coverage of compiled numeric manuscript lines and artifacts;
- fail-closed tests for new numbers and figures;
- explicit pending provenance for all input-certificate rows;
- stronger checks for complete provenance;
- a new `association.toa_offset_figure` row.

It also makes a new scientific conclusion: that timing-offset figure is
trusted even though its exact rendering receipt remains incomplete.
`5292337` reverses that conclusion to pending. `ef3211b` also retains the old
trusted cluster-column values; `5292337` reverses that state after the
probabilistic update. Thus `ef3211b` is valid additional work relative to
`a9ac20c`, but it is not an authority-equivalent substitute for `5292337`.

### What does the `75b9d5f` row audit add or contradict?

It adds an explicit independent row-by-row review and proportionate re-entry
recommendations. It supports keeping association, census, and the then-current
budget rows trusted; keeping the gallery and input certificates pending; and
keeping scattering, scintillation, energy, and attribution rows revoked or
pending.

It is not a registry variant: the commit adds only
`docs/rse/specs/review-trust-ledger-2026-07-22.md`.

Two recommendations are no longer sufficient as written:

1. It recommends promoting `budget.host_dm_posteriors` after tickets 06 and 07.
   The newer aperture-recompute handoff requires an owner receipt naming the
   exact current fiducial PDF hash before a separate promotion change.
2. It recommends keeping `budget.cluster_column` trusted against the old
   `p50=252` snapshot. `5292337` records the current probabilistic values and
   fails closed pending integrated producer, input, and artifact receipts.

It neither supports nor contradicts the timing-offset decision because that row
did not exist in its reviewed registry.

## Host-dispersion-measure trust-row question

Source: host-dispersion-measure handoff at analysis commit
`ac58513b1086e6c2c6eddbc148332368c1e85ac7`.

For `budget.host_dm_posteriors`, **trusted** would mean that the exact current
fiducial posterior product and the claims derived from it are scientifically
citable within the row's named scope. It would certify the fiducial producer,
inputs, posterior values, PDF bytes, and all three declared consumers as one
authority chain. It would not promote the alternate `1.5 R500` sensitivity
scenario into the fiducial census, figure, or appendix table.

The exact release identity is:

```text
SHA-256 652559148bde627acd036626e5f838b20251c73e09d0c4b18997a9d18c3a994a
artifact figures/dm_host_posteriors.pdf md5:2ee24966
consumers sections/appendix.tex
          sections/results.tex
          budget_table.tex
```

Promotion therefore requires a durable owner receipt naming that exact
SHA-256, followed by a separate change that:

```toml
trust = "trusted"
cleared_by = "<durable owner receipt>"
artifact = "figures/dm_host_posteriors.pdf md5:2ee24966"
consumed_by = ["sections/appendix.tex", "sections/results.tex", "budget_table.tex"]
```

Until then, `trust = "pending"` is the fail-closed state.

## Concrete owner questions

1. Should pull request #31's exact `5292337` state be the authority baseline,
   or should a specific older semantic choice be restored explicitly?
2. Is `association.toa_offset_figure` scientifically citable under legacy V6
   association validation despite the missing exact rendering receipt, or must
   it remain pending until explicit scientific and byte-level review?
3. Should `budget.cluster_column` remain pending against the current
   probabilistic `DM_int=255 (+67/-52); host DM p50=62` values until the
   integrated producer/input/artifact chain is re-receipted, or is there
   authority to trust that exact current chain now?
4. For `budget.host_dm_posteriors`, does the owner approve the exact fiducial
   PDF identified by SHA-256
   `652559148bde627acd036626e5f838b20251c73e09d0c4b18997a9d18c3a994a`
   for all three consumers?
5. Is the host-posterior trust scope explicitly limited to the fiducial result,
   leaving the `1.5 R500` calculation sensitivity-only?
6. Should the closed row audit be retained as supporting review evidence while
   its host release condition and old cluster snapshot are marked superseded?

## Proposed disposition summary

These are agent proposals, not decisions:

- `5292337`: present to the owner as the candidate baseline; do not land until
  the timing-offset, cluster-column, and host-posterior questions are answered.
- `a9ac20c`: superseded-preserved; do not land or cherry-pick.
- `ef3211b`: superseded-preserved; retain its coverage work as ancestry, but do
  not carry its timing-offset or cluster trust states without an explicit
  owner decision.
- `75b9d5f`: retain as review evidence; do not treat it as a registry
  implementation or as sufficient authorization for host-posterior promotion.

No recommendation in this packet authorizes a merge, trust promotion, variant
branch edit, or manuscript/pipeline gitlink change.

## Owner decision receipt

Accepted as written by the owner on 2026-07-23:

- adopt exact commit `5292337ffc6c0bb918a763860d70c0575530ae61` as
  the registry authority baseline;
- keep `association.toa_offset_figure` pending until scientific and exact-byte
  review;
- keep `budget.cluster_column` pending until its current producer, inputs, and
  artifact are receipted;
- keep `budget.host_dm_posteriors` pending because the exact PDF named by the
  proposed release receipt is absent from both live manuscript copies;
- when host-posterior trust is later approved, limit it to the fiducial result
  and keep the `1.5 R500` calculation sensitivity-only;
- retain `75b9d5f` as supporting review evidence while marking its old host
  release condition and cluster snapshot superseded.

This decision authorizes integration and validation of the accepted baseline.
It does not promote any pending or revoked result.
