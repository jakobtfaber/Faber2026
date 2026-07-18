# Correct the census-aperture description to match the pipeline

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)

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
