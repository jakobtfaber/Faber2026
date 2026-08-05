# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific and visual decisions. Silence leaves every item blocked._

## 1. Zach campaign per-fit sampler cost

**Decision:** The frozen contract costs 1.5 to 3 hours per fit and the owner has judged that too long. How should the campaign proceed?

**Recommended:** `measure-then-decide` — Every cheaper option trades log-evidence precision for wall clock, and the acceptance rule compares a step against a threshold of 5 after subtracting twice the combined numerical uncertainty — so a sampler that halves the cost but widens that uncertainty can make the comparison unresolvable rather than faster. The trade is currently an expectation, not a measurement: the only timing in hand is a 50-live-point feasibility fit. A short diagnostic scan at reduced live points on the already-complete C2D3 s2 = 1 rung costs minutes, not hours, and returns a measured curve of wall clock against reported log-evidence error, which turns this decision into a numerical one. It commits to nothing and touches no contract.

**Choose:**

- `measure-then-decide` — Keep the contract frozen and run a short diagnostic live-point scan first; decide the sampler question against measured cost and precision.
- `amend-halve-nlive` — Halve the live points now under an amended contract; roughly twice as fast per fit, but all 27 rungs restart and the five completed receipts are invalidated.
- `drop-stability-seeds` — Keep the sampler unchanged and cut the schedule to the nine-cell single-seed grid; four fits remain, but the seed spread that feeds the acceptance test's numerical uncertainty is lost.

**Context:**

- Wave 1 was stopped by the owner 52 minutes in on 2026-08-04; all processes are dead, all artifacts preserved, and the campaign stands at 5 of 27 rungs — exactly where it stood before the wave. Stopping outright here also remains available and needs no card.
- The per-fit cost is the contract's own cost, not a scheduling defect: at 1000 live points a rung is of order 100,000 iterations, so reordering launches cannot change it. Any sampler amendment breaks the uniformity the contract requires, restarting all 27 rungs and invalidating the five completed receipts.
- Live points set the log-evidence precision the acceptance rule spends: the rule requires a step above 5 with the same sign at every fixed gain-prior variance, after subtracting twice the sampler error added in quadrature with the seed spread — so dropping the stability seeds also weakens the test, leaving only the sampler's own reported error to bound it.

**Evidence:**

- [Wave-1 launch, owner stop, verified-dead processes and preserved artifacts](docs/rse/verify/zach-count-relaunch-20260804/README.md) — `fde405a6…`
- [Frozen contract, acceptance rules and the measured cost basis](scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md) — `765ecbb1…`

**Effect:** Determines whether the component-count experiment continues under the frozen contract, continues under an amended one, continues with a weaker acceptance test, or stops. Nothing runs on h17 until this is answered.

**Record:** `docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md` — Record the chosen option in this ticket's Current state section, then act on it; do not relaunch any rung before it is recorded.
