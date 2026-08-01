# Handoff — Zach component-count campaign stopped; restart plan pending owner choice

- Date: 2026-07-31 20:23 PDT
- Session scope: owner queue walkthrough (completed), Zach 27-rung campaign
  supervision (owner-stopped mid-run), restart replanning (owner decision
  pending).
- Repository: Faber2026-analysis, `main`. This handoff landed together with the
  restart decision card in
  [ticket 07](../wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md).

## Completed this session (all merged to main)

- Owner queue walked to empty. Item 1: owner **upheld** the 2026-07-29
  `needs_revision` on the installed Figure 3 bytes (SHA-256 `281e4bf4…`);
  recorded via `figure_review/decisions/batch_dispositions.json` (PR #228).
  The 2026-07-31-fig3-installed-approval batch had re-queued an
  already-decided candidate and is now suppressed with the reason recorded.
  Item 2: owner selected **accept-restricted** for the predicted-delay
  second-screen escalation trigger; ticket
  `04-close-scint-scattering-coupling-design.md` resolved with binding
  restrictions (PR #229): threshold 4.65 at the 1 per cent false-escalation
  envelope, valid only for `tau2/tau1 >= 1` on CHIME-like geometry; measured
  zero power below ratio 0.3, so a quiet trigger is never evidence against a
  weaker near screen.
- Earlier in the session (pre-compaction): PRs #221–#226 — figure_review
  `--pipeline-revision` optional; Figure 3 batch; predicted-delay trigger
  calibration plan, implementation, driver, and committed campaign results
  under `simulation/experiments/predicted-delay-trigger/`.

## Zach campaign: exact stop state (h17)

The owner stopped the campaign at ~4.5 h ("too slow — we need a new plan").
All processes were killed and verified gone (no `stage_zach_count` /
`run_controlled_joint_fit` survivors; load draining). **Nothing was deleted.**

- Campaign tree: h17 `~/zach_count_20260731/` — clone of Faber2026-analysis at
  `894a1d2`, uv-frozen environment (CPython 3.13.12, dynesty 3.1.0). Runner:
  `scattering/studies/joint-refits/zach_count_20260729/stage_zach_count.py`
  driven per the contract in `MANIFEST.md` / `rungs.json` (same directory).
- Inputs (hash-verified at launch): DSA
  `/home/ubuntu/flits-runs/data/dsa/zach_dsa_I_262_368_2500b_cntr_bpc.npy`
  (`be917e94…`), CHIME
  `/home/ubuntu/flits-runs/data/zach_chime_I_262_3621_32000b_cntr_bpc.npy`
  (`bf317648…`).
- Design: 27 rungs = {C2D3, C2D4, C2D5} × s2 ∈ {1, 10, 100} × 3 seeds
  (20220207/08/09), nlive 1000, nproc 4. Schedule was 9 parallel launchers,
  each running its 3 seeds serially (~4 h per fit → 3 waves ≈ 12 h).
- **Completed, receipts `outputs_complete: true` (5 of 27), all seed-20220207:**
  `C2D3_s2-1`, `C2D3_s2-10`, `C2D3_s2-100`, `C2D4_s2-1`, `C2D4_s2-10`
  (receipts under `~/zach_count_20260731/runs/rungs/<rung>/receipts/`).
- Killed mid-sampling (seed-20220207): `C2D4_s2-100`, `C2D5_s2-1`,
  `C2D5_s2-10`, `C2D5_s2-100`. Seeds 20220208/09: barely started anywhere;
  partial run directories exist and are superseded on relaunch.
- Every launcher log shows exactly one expected freeze-pass
  `ControlledRunError` traceback per started rung ("resolved likelihood,
  priors, or fitted support do not match contract") — that abort is part of
  the contract protocol, **never** a failure signal.
- Mac predecessor tree `~/Data/Faber2026/zach_count_20260731/` remains
  SUPERSEDED evidence only (owner kill-and-switch 13:55 PT); not mixable into
  adjudication (environment uniformity).

## Pending owner decision (queued in ticket 07)

Restart schedule — card `zach-campaign-restart-schedule` in ticket 07:

1. `finish-seed1-grid` (recommended): relaunch only the 4 unfinished
   seed-20220207 fits, concurrently, contract unchanged (~4 h to a full
   9-cell single-seed grid); adjudicate provisionally; run the remaining 18
   seed fits afterward. Keeps the 5 receipts valid.
2. `amend-contract-cheaper-sampler`: halve nlive → ~2× faster, but amends the
   hash-bound contract and invalidates the 5 completed rungs (uniformity).
3. `resume-original-schedule`: relaunch the as-was 9×3-serial schedule
   (~12 h).

## Known-broken / unverified

- The 5 completed rung receipts are receipt-verified only; no adjudication or
  visual vetting has happened (that is ticket 07's separate phase, after all
  rungs complete under whichever schedule the owner picks).
- Installed Figure 3 is **not reproducible** from any current environment:
  bytes were rendered with matplotlib 3.10.9 (retired FLITS env); the frozen
  analysis lock pins 3.10.6; renders at the pinned revision differ from the
  installed 52 576-byte file, and the committed staging render is a third
  hash (`8c7d2e92…`). Any future Figure 3 candidate must be regenerated from
  the current pipeline (new bytes) — which the required revision implies
  anyway.
- Local disk on jakob-mbp is at 99 % (16 GiB free) — one clone of this repo
  failed with `fetch-pack: invalid index-pack output` until a blob-filtered
  clone was used. Watch this before large local work.
- Journal appends to `docs/rse/journal.jsonl` were deferred all session (the
  shared checkout `Faber2026/analysis` sits on the Codex lane branch
  `codex/propagation-authority-figure3`; never commit through it).

## Critical files for the next session

1. `docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md`
   — the decision card, acceptance criteria, and owner sampling decision.
2. `scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md` — the
   frozen contract and acceptance rules the relaunch must not violate.
3. This handoff.

## Next steps (priority order)

1. Owner records the restart-schedule choice (queue walkthrough or directly
   in ticket 07); relaunch on h17 accordingly — reuse the existing
   `~/zach_count_20260731` tree and environment for a contract-identical
   restart; only rungs without a complete receipt need launching.
2. After 27/27 receipts: verify `outputs_complete` and the five artifacts per
   rung, then start the adjudication phase per MANIFEST acceptance rules +
   owner visual review (separate phase; do not mix).
3. Figure 3 revision lane (from the upheld needs_revision): infer
   dispersion-measure-based redshift distributions for the three hostless
   sightlines, extend the foreground search, produce a new exact-byte
   candidate from the current pipeline. Needs its own plan
   (`ai-research-workflows:planning-implementations`).

Recommended next skill: `ai-research-workflows:implementing-plans` for the
campaign relaunch once the owner picks a schedule; `planning-implementations`
for the Figure 3 revision lane.
