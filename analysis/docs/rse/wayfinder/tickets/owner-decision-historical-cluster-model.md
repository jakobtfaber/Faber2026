# Choose the historical FRB 20230307A cluster model

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: manuscript owner + cluster-model source expert
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)

## Owner decision card

```json
{
  "id": "historical-cluster-model",
  "kind": "scientific",
  "title": "Choose the historical FRB 20230307A cluster model",
  "decision": "Which fully specified historical model, if any, should govern the FRB 20230307A intervening-dispersion result?",
  "recommended": {
    "choice": "defer",
    "reason": "The arithmetic lineage is known, but no historical state has both the required producer/environment receipt and independent scientific acceptance of its cluster prescription."
  },
  "choices": [
    {
      "id": "ticket-06-model",
      "label": "Adopt the ticket-06 probabilistic-crossing model. Only 203/255/322 pc cm^-3 may become quotable, and only after its exact producer/environment receipt and scientific review are accepted."
    },
    {
      "id": "corrected-historical-model",
      "label": "Adopt the later equal-weight modified-NFW/beta mixture, revised beta calculation, and c200=4 NFW M500c-to-M200c conversion together. Only 217/281/354 pc cm^-3 may become quotable, and only after its exact producer/environment receipt and scientific review are accepted."
    },
    {
      "id": "defer",
      "label": "Quote no historical cluster-budget result pending source-expert review and complete receipts."
    }
  ],
  "context": [
    "Ticket 06 records 203/255/322 pc cm^-3 at commit be2131b76771d6291dfd18784eaa1c3f08636272.",
    "The later profile-mixture and beta revision, before the mass-conversion correction, yields 202/260/329 pc cm^-3; this is a version-lineage checkpoint, not an accepted result and is not quotable under any offered choice.",
    "Commit c8ec78ceeeb37505b5343aeb0ad0a51671658640 changes the cluster point from 183.674227906529 to 224.719617368599 pc cm^-3 under a c200=4 NFW M500c-to-M200c conversion; 9890aa8 restores the producing artifacts without changing the resulting 217/281/354 row."
  ],
  "evidence": [
    {
      "label": "Resolved probabilistic-crossing ticket",
      "path": "docs/rse/wayfinder/tickets/06-adjudicate-phineas-halo-mass-prescriptions.md",
      "sha256": "fc077afb02ad40b1970076366ab72de811ae64ffc2ed75f1e239b74873cad67a"
    },
    {
      "label": "Historical 217/281/354 output at 9890aa8",
      "path": "https://github.com/jakobtfaber/Faber2026-analysis/blob/9890aa8cc299fc2696348327a1c2efe14c80fdbe/scripts/dm_budget_uncertainty.csv"
    },
    {
      "label": "Evidence probe and version reconciliation",
      "path": "docs/rse/specs/research/research-remaining-science-questions-2026-07-31.md",
      "sha256": "0615403457950b538a5d641a16a229f063db9413ca3a54eab04381b72cf7c508"
    }
  ],
  "effect": "Selects a model state for later receipt construction and scientific review; the decision alone admits no number.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/owner-decision-historical-cluster-model.md",
    "action": "Record the chosen model, source-expert rationale, accepted profile mixture, beta revision, mass-conversion prescription, and receipt identity; resolve only when every admission blocker is discharged."
  },
  "priority": 36
}
```

## Fact

Git history reproduces the numerical lineage. Ticket 06 at `be2131b` records
`203/255/322 pc cm^-3`. The later profile-mixture and beta-model revision with
the old cluster point gives `202/260/329 pc cm^-3`. The `c8ec78c` correction
changes the cluster point from `183.674227906529` to `224.719617368599`
`pc cm^-3` using an NFW conversion from `M500c` to `M200c` at declared
`c200=4`; the output becomes `217/281/354 pc cm^-3` and remains so at
`9890aa8`.

## Non-result

This confirms arithmetic and version lineage only. It does not establish that
equal weighting of the modified-NFW and beta profiles is physical, that the
revised beta implementation should govern, that `c200=4` or this mass
conversion is appropriate, or that any of the three percentile sets is
manuscript-admissible. The intermediate `202/260/329` state is a diagnostic
boundary between changes, not an accepted scientific result.

## Scientific falsifier

The chosen historical result is falsified if an independent reproduction from
the exact selected producer, inputs, environment, profile prescription, and
mass conversion differs from its stated percentiles beyond the producer's
rounding rule. Its scientific interpretation is also falsified if source-expert
review rejects any model ingredient that defines that selected state.

## Admission blocker

No option becomes quotable from the owner choice alone. Admission requires an
immutable receipt binding the selected Git revision; exact producer bytes and
invocation; runtime environment; every input and output hash; the profile
mixture and beta-model definition; the `M500c`-to-`M200c` prescription and
concentration; an independent reproduction; and explicit owner/source-expert
scientific acceptance. Until then, quote none.

## Prerequisite check

The read-only history comparison is executable because all named Git objects
exist locally:

```bash
git show be2131b76771d6291dfd18784eaa1c3f08636272:scripts/dm_budget_uncertainty.csv \
  | rg 'FRB 20230307A'
git show c8ec78ceeeb37505b5343aeb0ad0a51671658640^:scripts/dm_budget_uncertainty.csv \
  | rg 'FRB 20230307A'
git show c8ec78ceeeb37505b5343aeb0ad0a51671658640:scripts/dm_budget_uncertainty.csv \
  | rg 'FRB 20230307A'
```

These commands establish only the committed lineage. No producer rerun is
prescribed because the exact historical runtime environment and invocation
receipt are absent.
