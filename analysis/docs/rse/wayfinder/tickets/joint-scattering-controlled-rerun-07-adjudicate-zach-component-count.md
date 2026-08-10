# Adjudicate the bounded-window Zach component count

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Orchestrator
- Blocked by: [Regenerate Zach C2D4](joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- GitHub: [Issue #205](https://github.com/jakobtfaber/Faber2026/issues/205)
- Authorization: manuscript-owner approval, 2026-07-22

## Owner decision

- Decision: use 65.536-microsecond DSA-110 sampling for the controlled
  component-count experiment.
- Recorded: manuscript owner, 2026-07-30, after direct visual comparison of the
  32.768- and 65.536-microsecond profiles.
- Exact scope: the owner found the profiles nearly identical and accepted the
  coarser sampling, then requested the component-count experiment. This is not
  approval of a component count or proof that the two resolutions recover the
  same physical components.
- Diagnostic evidence:
  `docs/rse/verify/zach-dsa-resolution-comparison-20260730/`. A threshold-only
  one-dimensional peak finder reports six local maxima at native sampling and
  four after averaging. Requiring each peak to rise by two noise standard
  deviations above neighbouring troughs gives four in both arms. The diagnostic
  therefore identifies two low-prominence shoulders; it does not establish six
  physical or fitted components.
- Input: `zach_dsa_I_262_368_2500b_cntr_bpc.npy`, SHA-256
  `be917e94d89134f699c456b9185422e8cfdbf3d935bbcf4d8b2e798d0ea12b01`.
- Effect: all 27 controlled fits use the same accepted 65.536-microsecond
  sampling. Their model evidence and residuals—not the profile peak finder—must
  adjudicate the component count.

## Owner decision — restart schedule

- Decision: restart the stopped campaign as **seed-1 grid plus seed-2
  backfill** — relaunch the four unfinished seed-20220207 rungs together with
  five seed-20220208 rungs, concurrently, with the contract unchanged.
- Recorded: manuscript owner, 2026-08-04, choosing against the three cards
  offered on 2026-07-31 (`finish-seed1-grid`, `resume-original-schedule`,
  `amend-contract-cheaper-sampler`).
- Why this rather than the recommended `finish-seed1-grid`: that option would
  have left 24 of h17's 40 cores idle. Nine concurrent fits at four processes
  each occupy 36 cores — the same occupancy the original schedule already
  assumed — so the full nine-cell seed-20220207 grid still arrives in one
  wave, and a third of the stability seeds arrives with it.
- Contract status: unchanged. No sampler, prior, window, mask, resolution or
  environment amendment. Only launch order differs, which the contract does
  not fix, so the five completed receipts stay valid.
- Effect: 14 of 27 rungs complete after wave 1; provisional adjudication may
  begin on the nine-cell single-seed grid; the remaining thirteen rungs run in
  waves 2 and 3.

## Current state (2026-08-04, after the owner stop)

Wave 1 of the restart launched at 22:55 PDT and the owner stopped it at 23:47,
about 52 minutes in: the per-fit cost was too long. Nine rungs were killed
(`C2D4:s2-100` and the three `C2D5` rungs at seed-20220207; `C2D3:s2-1/10/100`
and `C2D4:s2-1/10` at seed-20220208). All processes are verified dead and every
artifact is preserved; nothing was deleted. No rung of this wave reached its
stopping threshold, so this wave produced no usable evidence.

**The campaign stands where it stood before wave 1: 5 of 27 rungs complete** —
C2D3 at s2 = 1/10/100 and C2D4 at s2 = 1/10, all seed-20220207, receipts still
`outputs_complete: true`. Stop record, kill sequence and re-runnable state
check: `docs/rse/verify/zach-count-relaunch-20260804/README.md`.

The per-fit cost is the frozen contract's own cost, not a scheduling defect: at
1000 live points a rung is of order 100,000 iterations, which the MANIFEST
already measured as 1.5 to 3 hours. Reordering launches — what the earlier
restart decision did — cannot change it, because the wall clock per fit is set
by the sampler settings the contract fixes.

Stop-state history: `docs/rse/specs/handoff-2026-07-31-20-23-zach-campaign-replan.md`.

## Owner decision — retire the campaign plan, pivot to fast fitting (2026-08-05)

- Decision: stop the long-running component-count campaign and instead fit the
  dynamic spectrum at the highest resolution that completes in under five
  minutes end to end.
- Recorded: manuscript owner, 2026-08-05. This supersedes the queued
  `zach-campaign-sampler-cost` card, which asked how to make the campaign
  cheaper; the owner's answer was to stop running it.
- Campaign disposition: **parked, not deleted.** The five completed
  seed-20220207 receipts, the nine killed partial directories, the superseded
  directories, the frozen contract and the campaign clone all remain exactly as
  the stop record leaves them. Reviving the campaign needs no recovery work,
  only a decision.
- What is retired is the *plan* to run 27 contract rungs on the current
  schedule. The contract itself stays valid and untouched, so nothing about the
  five completed receipts is invalidated.

### What the pivot measured

Result: **263.9 seconds end to end, exit code 0, at the finest resolution on
the ladder** — DSA-110 at native 32.768-microsecond sampling with 32 channels,
CHIME/FRB at 128 channels, 421,248 fitted points, four times the campaign
contract's data volume. Recipe, harness and full timing table:
`scattering/studies/joint-refits/fast_fit_20260805/` and
`docs/rse/verify/zach-fast-fit-cost-ladder-20260805/`.

The premise of the instruction did not survive measurement, in a useful
direction. **Downsampling buys no time at all.** Three ladder rows spanning an
eightfold range in fitted data volume, at identical sampler settings, finished
within one second of each other (332.3 / 332.4 / 331.7 s). At four processes a
260-fold data reduction moved the sampler rate by five per cent. Preparation is
about 141 seconds of fixed overhead regardless of resolution, and sampling cost
is set by the number of likelihood calls — 36 per accepted sample at about 2.9
per cent efficiency — not by the size of each call.

So the answer to "the highest resolution that runs in under five minutes" is
*the highest resolution available*. The five minutes came from processes
(4 → 5.62, 8 → 10.9, 32 → 35.7 iterations per second, nearly linear and
scientifically free; the contract used four on a forty-core host), live points,
a looser stopping threshold, and switching off the model scan.

### What this does not deliver

The fast configuration reports a log-evidence uncertainty of ±2.63. The
acceptance rule needs a step above 5 after subtracting *twice* the combined
numerical uncertainty, so one such fit spends the whole budget on its own
noise. This is a fast route to morphology, residuals and parameter
plausibility — not a cheap route to the component-count answer, and its outputs
must never be mixed into that comparison. The component-count question remains
open and unanswered.

## Queued next steps (agent work, no owner decision pending)

Item 2 below is **done** — that is the pivot's cost ladder, recorded above.
Item 1 stays queued and still costs no compute. Item 3 is new.

3. **Expose the random-walk step count.** It is the largest untouched lever and
   currently unreachable: `nc` is dynesty's `rwalk` default of 25, and neither
   `nlive_walks` in the band run-config (read only by the single-band pipeline)
   nor `walks` under `dynesty:` in the sampler resource is consumed by the
   joint fit. `run_joint_fit.py` never passes it, though `fit_joint_scattering`
   already forwards `**dynesty_kwargs` to `NestedSampler`. A one-line optional
   flag with an unchanged default would let a future fit cut likelihood calls
   per sample by roughly threefold. It touches a shared entry point, so it
   belongs in its own reviewed change, not in a timing study.

1. **Build the adjudicator.** No code yet applies the six MANIFEST acceptance
   rules to the rung receipts; the campaign directory holds only the contract,
   the schedule and the driver. Write it under
   `scattering/studies/joint-refits/zach_count_20260729/`, developed against
   the five completed seed-20220207 receipts. It must read receipts and joint
   products only, and report per rule: output completeness and stopping
   threshold; log-evidence step against the threshold of 5 after subtracting
   twice the combined numerical uncertainty, evaluated at every fixed
   gain-prior variance; every component posterior arrival time inside its own
   band's fitted window; overlapping pulse-broadening exponent posteriors
   between neighbouring counts with none at a prior edge; bounded non-null
   amplitude for the added component. It decides nothing on its own — the
   per-band visual residual review and the owner's morphology review stay
   separate, and no value is promoted.
2. **Measure the cost-versus-precision trade directly.** The decision below
   currently rests on the MANIFEST's 50-live-point feasibility timing and the
   general expectation that log-evidence precision degrades as live points
   fall. A short, explicitly non-contract scan at reduced live points on the
   already-complete C2D3 s2 = 1 rung would replace that expectation with a
   measured curve of wall clock and reported log-evidence error, which is what
   the owner needs to judge whether a cheaper sampler can still clear a
   threshold of 5. Its outputs are diagnostic only and must never enter
   adjudication.

Also corrected 2026-08-04: issue #205's body still specified native
32.768-microsecond DSA-110 sampling, which the owner's 2026-07-30 decision
superseded. The issue body now states 65.536 microseconds and cites this ticket
and the frozen contract. The contract and the running campaign were already
correct; only the issue text was stale.

## Owner decision card — sampler cost, resolved 2026-08-05

Retained for provenance. The owner answered it by retiring the campaign plan
rather than choosing among its three options; see the pivot decision above. It
is no longer a queue item, and the ticket is `(AFK)` because no owner decision
is pending.

```json
{
  "id": "zach-campaign-sampler-cost",
  "kind": "scientific",
  "title": "Zach campaign per-fit sampler cost",
  "decision": "The frozen contract costs 1.5 to 3 hours per fit and the owner has judged that too long. How should the campaign proceed?",
  "recommended": {
    "choice": "measure-then-decide",
    "reason": "Every cheaper option trades log-evidence precision for wall clock, and the acceptance rule compares a step against a threshold of 5 after subtracting twice the combined numerical uncertainty — so a sampler that halves the cost but widens that uncertainty can make the comparison unresolvable rather than faster. The trade is currently an expectation, not a measurement: the only timing in hand is a 50-live-point feasibility fit. A short diagnostic scan at reduced live points on the already-complete C2D3 s2 = 1 rung costs minutes, not hours, and returns a measured curve of wall clock against reported log-evidence error, which turns this decision into a numerical one. It commits to nothing and touches no contract."
  },
  "choices": [
    {
      "id": "measure-then-decide",
      "label": "Keep the contract frozen and run a short diagnostic live-point scan first; decide the sampler question against measured cost and precision."
    },
    {
      "id": "amend-halve-nlive",
      "label": "Halve the live points now under an amended contract; roughly twice as fast per fit, but all 27 rungs restart and the five completed receipts are invalidated."
    },
    {
      "id": "drop-stability-seeds",
      "label": "Keep the sampler unchanged and cut the schedule to the nine-cell single-seed grid; four fits remain, but the seed spread that feeds the acceptance test's numerical uncertainty is lost."
    }
  ],
  "context": [
    "Wave 1 was stopped by the owner 52 minutes in on 2026-08-04; all processes are dead, all artifacts preserved, and the campaign stands at 5 of 27 rungs — exactly where it stood before the wave. Stopping outright here also remains available and needs no card.",
    "The per-fit cost is the contract's own cost, not a scheduling defect: at 1000 live points a rung is of order 100,000 iterations, so reordering launches cannot change it. Any sampler amendment breaks the uniformity the contract requires, restarting all 27 rungs and invalidating the five completed receipts.",
    "Live points set the log-evidence precision the acceptance rule spends: the rule requires a step above 5 with the same sign at every fixed gain-prior variance, after subtracting twice the sampler error added in quadrature with the seed spread — so dropping the stability seeds also weakens the test, leaving only the sampler's own reported error to bound it."
  ],
  "evidence": [
    {
      "label": "Wave-1 launch, owner stop, verified-dead processes and preserved artifacts",
      "path": "docs/rse/verify/zach-count-relaunch-20260804/README.md",
      "sha256": "fde405a6dd8e682992a290f52266e575079a90c0cf7277b15b144f6f20f55ccb"
    },
    {
      "label": "Frozen contract, acceptance rules and the measured cost basis",
      "path": "scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md",
      "sha256": "765ecbb152c1aa7af448c51aafbff50ae410bb5dc2f1335b2b6993249e03d677"
    }
  ],
  "effect": "Determines whether the component-count experiment continues under the frozen contract, continues under an amended one, continues with a weaker acceptance test, or stops. Nothing runs on h17 until this is answered.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md",
    "action": "Record the chosen option in this ticket's Current state section, then act on it; do not relaunch any rung before it is recorded."
  },
  "priority": 30
}
```

## Owner decision card — restart schedule, resolved 2026-08-04

Retained for provenance. The owner answered this card on 2026-08-04 with a
fourth option, recorded above. The wave it authorised was then stopped for
per-fit cost, which the card above now addresses.

```json
{
  "id": "zach-campaign-restart-schedule",
  "kind": "scientific",
  "title": "Zach campaign restart schedule",
  "decision": "Restart the stopped 27-rung component-count campaign under which schedule?",
  "recommended": {
    "choice": "finish-seed1-grid",
    "reason": "Relaunching only the four unfinished seed-20220207 fits, concurrently and contract-unchanged, yields a full nine-cell single-seed grid in roughly four hours, keeps the five completed receipts valid, and defers the eighteen stability-seed fits until after a provisional adjudication shows where they matter."
  },
  "choices": [
    {
      "id": "finish-seed1-grid",
      "label": "Relaunch the four unfinished first-seed fits concurrently; adjudicate provisionally on the nine-cell grid; run remaining seeds afterward."
    },
    {
      "id": "amend-contract-cheaper-sampler",
      "label": "Halve nlive under an amended hash-bound contract and restart all 27 rungs; invalidates the five completed receipts."
    },
    {
      "id": "resume-original-schedule",
      "label": "Relaunch the original nine-launcher, three-serial-seed schedule unchanged (about twelve hours)."
    }
  ],
  "context": [
    "Five of 27 rungs are receipt-complete (C2D3 s2 1/10/100, C2D4 s2 1/10, seed-20220207); the owner stopped the campaign for wall-clock, processes were killed cleanly, and all artifacts are preserved on h17.",
    "The bottleneck is the serial seed dimension: three ~4-hour waves; full nine-cell single-seed coverage needs only four more fits run concurrently.",
    "A contract-identical reordering preserves completed receipts; any sampler amendment restarts all 27 rungs because the contract requires uniform environment and settings."
  ],
  "evidence": [
    {
      "label": "Stop-state handoff (exact rung inventory and environment identity)",
      "path": "docs/rse/specs/handoff-2026-07-31-20-23-zach-campaign-replan.md",
      "sha256": "e0a7fa33991a32800df27043e8fe173932a46d8dad44e9911ba72f425f37bc0c"
    },
    {
      "label": "Frozen campaign contract and acceptance rules",
      "path": "scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md",
      "sha256": "765ecbb152c1aa7af448c51aafbff50ae410bb5dc2f1335b2b6993249e03d677"
    }
  ],
  "effect": "Sets the relaunch schedule for the component-count campaign; adjudication (this ticket's core work) begins only after the chosen schedule delivers its rungs.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md",
    "action": "Record the chosen restart schedule in this ticket's Current state section, then relaunch on h17 accordingly."
  },
  "priority": 25
}
```

## What to build

Run a new, reproducible Zach C2D3/C2D4/C2D5 comparison after the clean C2D4
morphology rerun. This is a new experiment, not recovery of job 180 and not a
substitute for the injection-calibrated sample-wide statistic in ticket 20.

Use the canonical all-exponential exponentially modified Gaussian family,
65.536-microsecond DSA-110 time resolution, unchanged prepared CHIME/FRB
resolution, identical masks, channels, fitted support, prior version, and a
frozen multi-seed schedule. Compare fixed gain-prior variances
`s2 = {1, 10, 100}` only within the same pulse-broadening family and sampler
contract.

## Acceptance criteria

- [ ] C2D3, C2D4, and C2D5 complete under one frozen schedule, with one
  hash-bound controlled-run contract per rung.
- [ ] Every fitted window contains all owner-identified candidate components.
- [ ] Every component-time prior and posterior remains inside the fitted window.
- [ ] Neighboring counts occupy the same scattering and nuisance-parameter mode.
- [ ] An evidence improvement above 5 has the same direction at every fixed gain-prior variance after numerical uncertainty.
- [ ] Added components coincide with candidate features, have bounded non-null amplitude, and improve local residuals.
- [ ] Reconstructable model products and per-band visual residual diagnostics exist for every rung.
- [ ] Owner morphology review and numerical guards agree before any fitted value or count is promoted.

Statistical failure does not promote a visibly wrong C2D3 fit. It leaves the
owner-confirmed morphology recorded while fitted parameters and count evidence
remain unaccepted. Keep `tau * delta_nu` downstream of fit acceptance.

The inner-scale power-law pulse-broadening model is a conditional sensitivity
test only, at a fixed accepted count, if the canonical fit retains tail-shaped
residuals or boundary behavior.

## Blocked by

- [Regenerate Zach C2D4](joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md)
