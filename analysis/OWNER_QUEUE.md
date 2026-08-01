# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific and visual decisions. Silence leaves every item blocked._

## 1. Zach campaign restart schedule

**Decision:** Restart the stopped 27-rung component-count campaign under which schedule?

**Recommended:** `finish-seed1-grid` — Relaunching only the four unfinished seed-20220207 fits, concurrently and contract-unchanged, yields a full nine-cell single-seed grid in roughly four hours, keeps the five completed receipts valid, and defers the eighteen stability-seed fits until after a provisional adjudication shows where they matter.

**Choose:**

- `finish-seed1-grid` — Relaunch the four unfinished first-seed fits concurrently; adjudicate provisionally on the nine-cell grid; run remaining seeds afterward.
- `amend-contract-cheaper-sampler` — Halve nlive under an amended hash-bound contract and restart all 27 rungs; invalidates the five completed receipts.
- `resume-original-schedule` — Relaunch the original nine-launcher, three-serial-seed schedule unchanged (about twelve hours).

**Context:**

- Five of 27 rungs are receipt-complete (C2D3 s2 1/10/100, C2D4 s2 1/10, seed-20220207); the owner stopped the campaign for wall-clock, processes were killed cleanly, and all artifacts are preserved on h17.
- The bottleneck is the serial seed dimension: three ~4-hour waves; full nine-cell single-seed coverage needs only four more fits run concurrently.
- A contract-identical reordering preserves completed receipts; any sampler amendment restarts all 27 rungs because the contract requires uniform environment and settings.

**Evidence:**

- [Stop-state handoff (exact rung inventory and environment identity)](docs/rse/specs/handoff-2026-07-31-20-23-zach-campaign-replan.md) — `e0a7fa33…`
- [Frozen campaign contract and acceptance rules](scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md) — `765ecbb1…`

**Effect:** Sets the relaunch schedule for the component-count campaign; adjudication (this ticket's core work) begins only after the chosen schedule delivers its rungs.

**Record:** `docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md` — Record the chosen restart schedule in this ticket's Current state section, then relaunch on h17 accordingly.
