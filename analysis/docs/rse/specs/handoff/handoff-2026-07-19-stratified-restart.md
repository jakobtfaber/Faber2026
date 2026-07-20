# Handoff: Stratified restart — data integrity first, then DM → TOA → upchan → scattering → scintillation

---
**Date:** 2026-07-19 (supersedes the *plan* of handoff-2026-07-19-14-56;
that document's technical content — formulas, sign tests, casey state —
remains authoritative and is consumed by stratum 2)
**Status:** Handoff — master resume document
**Everything referenced is committed to origin/main.**

---

## What changed

Owner strategic decision: repeated backtracking (three trust-reset waves,
R5/R6 rejection, two failed remediations, one sign bug) had a single root
cause — issues structured by analysis topic while trust flows along the
data DAG. The cure is codified in **verification-protocol.md** as the
**data chain** (Raw Data → Input Data Products → Measurements and Fits →
Analyses and Interpretations → In-Manuscript Claims), plus per-burst data
cards, input-authority table, executable convention tests, and mechanical
downstream invalidation. All open work is restructured under it.

## The route (work strictly in this order)

| # | Ticket | What it is | Owner involvement |
|---|--------|-----------|-------------------|
| 1 | wayfinder ticket 17 | stratum 0: certify the twelve CHIME singlebeam voltage `.h5` files on h17 (only raw CHIME data; see `definition-raw-chime-data-2026-07-19.md`). Intensity `.npy` products are derived, not raw. | spot-check |
| 2 | ticket 18 | DM analysis redo — casey-first calibration (pick pending: 491.148 / 491.178 / finer strip), codified structure metric, all 12 both telescopes, input-authority table | heavy, figure-driven |
| 3 | ticket 19 | TOA analysis redo on certified DMs | moderate |
| 4 | ticket 20 | Upchan rebuild at adjudicated DMs + aggressive RFI + 12 hash-bound data cards | card approvals |
| 5 | ticket 21 | Scattering re-anchor on certified inputs (folds free-α reporting + count remediation decisions) | moderate |
| 6 | ticket 22 → 02 | Scintillation campaign re-run on certified Input Data Products → CHIME-method ratification | ratification grilling |

Map: `docs/rse/wayfinder/map-apj-submission.md` (resume pointer encodes the
chain). Execution board: `docs/rse/control/BOARD.md`. Claim trust:
`docs/rse/control/results-registry.toml`.

## Pinned state (as of this handoff)

- **Technical detail for stratum 2** (formulas, corrected-sign transform +
  test, disqualified metrics, casey figures incl.
  `decks/casey-dm-calibration-2026-07-19/casey_dm_strip_CORRECTED.png`,
  RFI recipe requirements, sandbox gotchas):
  `handoff-2026-07-19-14-56-scint-input-remediation-casey-dm-calibration.md`.
- **Data defects of record:** `owner-data-review-findings-2026-07-18.md`.
- **Review galleries (durable, in-repo):** `decks/waterfall-review-2026-07-18/`
  (36 inputs), `decks/acf-review-2026-07-18/` (both-band ACFs),
  `decks/remediation-preview-2026-07-18/` (rejected attempt 1),
  `decks/scint-validation-2026-07-18/` (ratification deck — pre-defect,
  historical).
- **Open PRs:** #140 pin bump + scint figures — DO-NOT-MERGE until stratum 6.
- **Rejected/superseded on disk:** `~/Data/Faber2026/dsa110/
  upchan_codetections_remediated_20260718/` (attempt 1); v2 dir contains one
  sign-bugged scan json — discard.
- **Parallel lanes unaffected:** jointtf scattering campaign (h17),
  fig1 decide pair, budget-priors sign-off (wf-07), phineas prescription
  (wf-06), trust overhaul (wf-13 — its row-by-row adjudication now happens
  naturally per stratum), two-screen forward-model charter (3ef33c80).

## For the next session

> /wayfinder — work the map at `docs/rse/wayfinder/map-apj-submission.md`.
> Ticket 17 is open again. Raw CHIME data = the twelve singlebeam `.h5`
> voltage files on h17 only (`definition-raw-chime-data-2026-07-19.md`).
> Certify those before ticket 18. The earlier 36-product `.npy` inventory is
> derived-product work, not raw-layer closeout.

---

**Handoff created by AI Assistant on 2026-07-19**
