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

## Current state (2026-08-04)

Wave 1 of the owner-chosen restart is running on h17 in the preserved campaign
tree `~/zach_count_20260731/` (clone at `894a1d2`, clean; CPython 3.13.12 with
dynesty 3.1.0; both input hashes re-verified as `be917e94…` and `bf317648…`).
Nine rungs launched 2026-08-04 22:55 PDT:

- seed-20220207 completion: `C2D4:s2-100`, `C2D5:s2-1`, `C2D5:s2-10`,
  `C2D5:s2-100`;
- seed-20220208 backfill: `C2D3:s2-1`, `C2D3:s2-10`, `C2D3:s2-100`,
  `C2D4:s2-1`, `C2D4:s2-10`.

The five completed seed-20220207 receipts (C2D3 at s2 = 1/10/100, C2D4 at
s2 = 1/10) were left untouched. Each relaunched rung's killed partial run
directory was moved, not deleted, to `runs/rungs-superseded-20260804/`, because
the driver refuses a non-empty rung namespace. Launch record and verification
commands: `docs/rse/verify/zach-count-relaunch-20260804/README.md`.

This ticket is `(AFK)` while the campaign executes: the restart decision is
recorded and no owner decision is pending. It returns to `(HITL)` with an
evidence-bound decision card when adjudication produces exact candidate
artifacts for hash-bound review.

Stop-state history: `docs/rse/specs/handoff-2026-07-31-20-23-zach-campaign-replan.md`.

## Owner decision card — resolved 2026-08-04

Retained for provenance. The owner answered this card on 2026-08-04 with a
fourth option, recorded above; it is no longer a queue item.

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
