# Wayfinder first-wave closeout

Date: 2026-07-21

## Outcome

All five first-wave endpoints are resolved and landed on `main`:

| Ticket | Landed evidence | Outcome |
|---|---|---|
| Fail-close the invalid expanded-catalog validation | [PR #166](https://github.com/jakobtfaber/Faber2026/pull/166), [PR #167](https://github.com/jakobtfaber/Faber2026/pull/167) | Superseded validation fails closed. |
| Freeze candidate-redshift source evidence | [PR #168](https://github.com/jakobtfaber/Faber2026/pull/168) | 52 registry rows frozen; 46 adopted redshifts have source evidence; six remain explicitly without an adopted redshift. |
| Adjudicate the results-library real-byte conflicts | [PR #163](https://github.com/jakobtfaber/Faber2026/pull/163), [PR #169](https://github.com/jakobtfaber/Faber2026/pull/169) | Preserve all four trees; no movement, deletion, authority promotion, or broad materialization. |
| Correct the census-aperture description | [PR #170](https://github.com/jakobtfaber/Faber2026/pull/170) | Prose describes the frozen census without rerunning or re-adjudicating it. |
| Replace letter+number stage names | [PR #171](https://github.com/jakobtfaber/Faber2026/pull/171) | Active planning uses descriptive names; historical codes remain resolvable through a validated glossary. |

## Controller reconciliation

The durable ticket and map records are authoritative. Two controller terminal
labels do not describe unresolved scientific work:

- `audit-results-library-conflicts` remains `review_ready` because its manifest
  mode intentionally stops at review readiness; the reviewed work subsequently
  merged and the research ticket is resolved.
- `freeze-candidate-redshifts` remains `needs_attention` because its worker
  receipt recorded PR #168's merge commit while the verifier expected its head
  commit. The landed pipeline pin, ledger coverage, preserved verdicts, tests,
  and resolved ticket were independently checked. This is receipt-identity
  bookkeeping, not a scientific disagreement.

The interrupted stage-name worker was recovered without discarding its work.
Its changes were reviewed, validated, committed, and landed through PR #171.

## Scope preserved

This wave did not promote Figure 3, scientific trust, or manuscript submission;
re-adjudicate a foreground redshift or budget flag; delete or move data; alter
services; or change coauthors.
