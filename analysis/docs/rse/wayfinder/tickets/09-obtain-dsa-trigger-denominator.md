# Obtain the exact DSA-110 detection denominator

- Type: `wayfinder:task` (HITL)
- Status: resolved (2026-07-22)
- Assignee: Codex
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

The chance-coincidence trials paragraph quotes the look-elsewhere denominator
only by order of magnitude ("of order 10²–10³ DSA-110 events across the
two-year window"). The exact count of independent DSA-110 triggers searched
for a CHIME counterpart over the 2022-Feb–2024-Feb overlap is not derivable
from any local artifact (2026-07-08 evidence pass: candidate sheets hold the
12 accepted pairs + 4 near-misses, not the denominator; no local trigger-DB
client exists). Owner checklist: query the DSA-110 trigger database (or
supply the count from collaboration records) for the overlap window with the
trigger-class definition the search actually used; record the count, the
generating rule (time range + trigger class + required data products), and
ideally a machine-readable trigger list for the reproducibility supplement
the technical review requested. Resolution = the number + rule recorded here;
the one-line prose edit is execution. Note: the published bound holds for any
count ≲10³, so this is rigor, not a result change. (Legacy code: referee item
B3; review item S1.)

## Resolution (owner-approved, 2026-07-22)

The denominator is **64 DSA-110 FRB detections**. The authoritative trial-set
rule is every catalog row with a finite Modified Julian Date in the half-open
interval `59611 <= MJD < 60370` (2022 February through 2024 February). No
localization, host, voltage, or CHIME-match field is required for inclusion.

The machine-readable source is
[`dsa110_frb_catalog.csv`](../../claude-science/frames/resolve-dsa-110-trial-count-denominator-27fa6148/artifacts/dsa110_frb_catalog.csv),
SHA-256
`f2558f7ca7782fcb173b6ac0c83c584a6bc59c3f303916680a384c3f6f09ef94`.
The exact clean-environment reproduction is:

```bash
env -i PATH=/usr/bin:/bin /usr/bin/python3 -c 'import csv; p="docs/rse/claude-science/frames/resolve-dsa-110-trial-count-denominator-27fa6148/artifacts/dsa110_frb_catalog.csv"; rows=csv.DictReader(open(p, encoding="utf-8")); print(sum(bool(r["mjd"]) and 59611 <= float(r["mjd"]) < 60370 for r in rows))'
```

It prints `64`. Reproduced against analysis commit
`bc76d7371041353d13f9634ac77ace7e22edf264`.

The candidate-name date is not an independent confirmation. It also returns
64 only because two missing-data cases cancel: the authoritative MJD rule
includes the candname-less `johndoe` detection at MJD `60123.490223`, while a
candidate-name rule instead includes the unmeasured `240204aacb` stub with no
MJD. Parent commit `1871ef2c50b563c5b07a174f30060fe46ab31565`
records the same adjudication.

The trial-set objects are detections, not raw single-pulse triggers. Current
manuscript prose has regressed to “triggers”; restoring “FRB detections” is a
separate one-line execution task. The denominator and scientific conclusion do
not change.
