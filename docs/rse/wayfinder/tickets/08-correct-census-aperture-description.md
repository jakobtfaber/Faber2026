# Correct the census-aperture description to match the pipeline

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: Codex
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

The observations-section prose describes the galaxy-census search aperture,
but the evidence pass (2026-07-08) showed no single number is honest: the
live replay code uses a 100 kpc default that would *not* recover the frozen
manuscript census (budget-eligible halos span 102–243 kpc; retained rows
reach 281 kpc; eligibility is actually set by confirmation/provenance
columns, not an impact cut). Author call: what does the prose describe — the
frozen census as-built (state the envelope and the eligibility logic), or a
re-run under the documented live-search aperture (which changes the census)?
Given the deadline, describing the frozen census accurately is the cheap
path; the ticket closes with the exact wording decision and the numbers it
quotes. (Legacy code: referee item B7 / handoff item 2.)

## Resolution

Resolved 2026-07-21 under the standing delegated decision authority.

Decision: describe the frozen manuscript census as built. Do not rerun the
census, do not adopt the current live-search `100 kpc` replay default, and do
not treat a single impact-parameter cut as the eligibility rule.

The observations prose now states:

- budget-eligible frozen halo rows span `b=101.7--242.7 kpc`;
- the retained halo envelope reaches `b=281.4 kpc`;
- eligibility follows confirmation and provenance fields from validation, not
  a `100 kpc` impact-parameter cut.

Evidence used:

- `docs/rse/specs/handoff/handoff-2026-07-08-08-55-open-author-decisions.md`
  records the live default and the frozen-census mismatch.
- `pipeline/galaxies/foreground/data/intervening_census_registry.csv` carries
  the frozen row-level `impact_kpc`, `final_verdict`, `classification`,
  `best_z_source`, and `budget_eligible` fields.
- `docs/rse/specs/handoff/handoff-2026-07-08-18-12-b7-cgm-census-resolved.md`
  records the B7 foreground-census correction and the warning that assumed-mass
  or hard-cut replays produce fake census churn.

Validation:

- Red first:
  `uv run --project pipeline --frozen python -m pytest -q tests/test_consistency_audit.py::test_committed_foreground_census_wording_matches_frozen_registry`
  failed before `check_foreground_census_wording` existed.
- `uv run --project pipeline --frozen python -m pytest -q tests/test_consistency_audit.py::test_committed_foreground_census_wording_matches_frozen_registry tests/test_consistency_audit.py`
- `python3 scripts/consistency_audit.py`
- `rtk make test-science`
- `rtk make all`
