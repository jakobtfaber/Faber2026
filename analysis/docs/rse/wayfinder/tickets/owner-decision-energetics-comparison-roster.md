# Choose the energetics comparison and roster

- Type: `wayfinder:grilling` (HITL)
- Status: resolved — owner selected methods-only 2026-07-31
- Assignee: manuscript owner
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)

## Owner decision card

```json
{
  "id": "energetics-comparison-roster",
  "kind": "scientific",
  "title": "Choose energetics comparison and roster",
  "decision": "What scientific comparison, if any, should the band-energy analysis test, and what exact event roster is required before execution?",
  "recommended": {
    "choice": "methods-only",
    "reason": "No accepted event-band receipt exists, so keeping the section method-only avoids inventing a population question or minimum roster before the owner defines one."
  },
  "choices": [
    {
      "id": "complete-paired-roster",
      "label": "Compare paired CHIME/FRB and DSA-110 band energies for every redshift-eligible event; require every paired event-band receipt."
    },
    {
      "id": "predeclared-subset",
      "label": "Use an owner-named comparison and exact named subset; record the minimum event count and exclusions before any calibration work."
    },
    {
      "id": "methods-only",
      "label": "Run no population comparison; retain only the measurement method until a later owner decision."
    }
  ],
  "context": [
    "The candidate table has 24 event-band rows, seven failed window gates, and no accepted row.",
    "The builder fails closed unless window, calibration, correlated-noise, and owner-review gates pass.",
    "No current authority defines the population comparison or the minimum acceptable roster."
  ],
  "evidence": [
    {
      "label": "Fit-independent energetics workflow and admission rules",
      "path": "energetics/studies/burst-energies/README.md",
      "sha256": "79035b1154bbe1d733d304e9a9f30510a85daf0568afa4bd8b282b1630b04418"
    },
    {
      "label": "Remaining-science evidence probe",
      "path": "docs/rse/specs/research/research-remaining-science-questions-2026-07-31.md",
      "sha256": "0615403457950b538a5d641a16a229f063db9413ca3a54eab04381b72cf7c508"
    }
  ],
  "effect": "Defines whether energetics remains method-only or may begin a predeclared comparison, and fixes the roster gate that measurement receipts must satisfy.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/owner-decision-energetics-comparison-roster.md",
    "action": "Record the selected comparison; for a population comparison, also record the exact named roster, minimum count, and exclusions. For methods-only, record roster none, minimum count 0, and exclusions not applicable."
  },
  "priority": 34
}
```

## Fact

`energetics/studies/burst-energies/README.md` defines a fail-closed path from
candidate fluences to accepted receipts. The current evidence probe records 24
candidate event-band rows, seven window failures, and no accepted row.

## Non-result

Those mechanics do not define a scientific comparison, minimum event count, or
permitted exclusions. They establish no energy value or population claim.

## Scientific falsifier

After the owner predeclares a comparison and roster, that future claim is
falsified if accepted measurements fail its stated test. No such test exists
before this decision, so current failed or missing rows are admission blockers,
not evidence for or against a population result.

## Admission blocker

Execution requires, for every admitted event-band row: dynamic-spectrum identity
and checksum; burst-epoch or justified transferred system-equivalent flux
density; per-event beam response and independently reviewed beam-gain receipt;
reviewed calibration systematic; stable integration window; correlated-noise
validation; owner visual review; accepted fluence receipt; frozen redshift source;
and independent energy-calculation verification. For a population comparison,
the owner must first record the comparison, exact named roster, minimum count,
and exclusions. For methods-only, record roster none, minimum count 0, and
exclusions not applicable.

## Prerequisite check

The existing candidate inventory is read-only and executable:

```bash
python - <<'PY'
import csv
rows = list(csv.DictReader(open(
    "energetics/studies/burst-energies/data_fluences.candidate.csv"
)))
print(len(rows), sum(row["window_status"] != "candidate" for row in rows))
print(sorted({row["calibration_status"] for row in rows}))
print(sorted({row["noise_status"] for row in rows}))
print(sorted({row["review_status"] for row in rows}))
PY
```

Expected current inventory: 24 rows, seven non-passing windows, and only pending
calibration, noise, and review states. This inventories blockers; it authorizes
no energy calculation.

## Resolution

Owner decision, 2026-07-31: **methods-only for now**. Run no population
comparison. Record roster `none`, minimum event count `0`, and exclusions `not
applicable`. Retain only the measurement method until a later owner decision.
This resolution admits no fluence, energy, calibration, event roster, or
population claim.
