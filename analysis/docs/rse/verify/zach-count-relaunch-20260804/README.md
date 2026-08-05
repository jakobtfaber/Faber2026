# Zach component-count campaign — wave 1 relaunch record (2026-08-04)

- Objective: restart the stopped 27-rung controlled component-count campaign
  for [issue #205](https://github.com/jakobtfaber/Faber2026/issues/205) under
  the schedule the manuscript owner chose on 2026-08-04.
- Scientific phase: exploration. No fit value, table, figure or results-library
  pointer is promoted by this record.
- Operational phase: capture (campaign execution). Adjudication is a separate
  later phase and is not started here.
- May change: the h17 run tree `~/zach_count_20260731/runs/`, this receipt, the
  ticket and lane state.
- Must not change: the frozen contract
  (`scattering/studies/joint-refits/zach_count_20260729/`), the five completed
  seed-20220207 receipts, both input waterfalls, the campaign clone and its
  environment.
- Done when: nine relaunched rungs carry `outputs_complete: true` receipts and
  the five-artifact output set, giving 14 of 27 rungs and a complete nine-cell
  seed-20220207 grid.

## Owner decision this record executes

Restart as **seed-1 grid plus seed-2 backfill**: relaunch the four unfinished
seed-20220207 rungs together with five seed-20220208 rungs, concurrently, with
the contract unchanged. Recorded in
[ticket 07](../../wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md).

The 2026-07-31 queue card recommended `finish-seed1-grid` (four rungs). That
option occupies 16 of h17's 40 cores. Nine rungs at four processes each occupy
36 cores, which is the occupancy the original nine-launcher schedule already
assumed, so the nine-cell single-seed grid arrives in the same wall clock and
five stability-seed rungs arrive with it. Launch order is not fixed by the
contract, so this is a contract-identical reordering and the five completed
receipts stay valid. Nothing about the sampler, priors, windows, masks,
resolution or environment was amended.

## Snapshot identity verified before launch

| Item | Value |
|---|---|
| Host | h17, 40 cores, load average 0.19 before launch (idle) |
| Campaign tree | `~/zach_count_20260731/` |
| Source clone | `~/zach_count_20260731/src/analysis`, revision `894a1d2`, `git status --porcelain` empty |
| Interpreter | `~/zach_count_20260731/src/analysis/.venv/bin/python`, CPython 3.13.12 |
| Sampler library | dynesty 3.1.0 |
| DSA-110 input | `/home/ubuntu/flits-runs/data/dsa/zach_dsa_I_262_368_2500b_cntr_bpc.npy`, SHA-256 begins `be917e94d89134f6` |
| CHIME/FRB input | `/home/ubuntu/flits-runs/data/zach_chime_I_262_3621_32000b_cntr_bpc.npy`, SHA-256 begins `bf317648879936ce` |
| Free disk | 114 GiB on `/` (campaign tree was 2.3 GiB) |

Both input hashes agree with the values bound at the 2026-07-31 launch and
recorded in `docs/rse/specs/handoff-2026-07-31-20-23-zach-campaign-replan.md`,
so the relaunched rungs bind the same data as the five completed ones.

## Rungs relaunched

Seed-20220207 completion (four):

- `C2D4:s2-100:seed-20220207`
- `C2D5:s2-1:seed-20220207`
- `C2D5:s2-10:seed-20220207`
- `C2D5:s2-100:seed-20220207`

Seed-20220208 backfill (five):

- `C2D3:s2-1:seed-20220208`
- `C2D3:s2-10:seed-20220208`
- `C2D3:s2-100:seed-20220208`
- `C2D4:s2-1:seed-20220208`
- `C2D4:s2-10:seed-20220208`

Untouched, already complete with `outputs_complete: true`:
`C2D3:s2-1`, `C2D3:s2-10`, `C2D3:s2-100`, `C2D4:s2-1`, `C2D4:s2-10`, all at
seed-20220207.

Not yet launched (thirteen): `C2D4:s2-100` and the three `C2D5` rungs at
seed-20220208, plus all nine seed-20220209 rungs.

## Superseded partial run directories

`stage_zach_count.py` refuses a rung namespace that already holds a contract,
receipt or joint output ("rung directory is not empty; use a new run root").
Each relaunched rung's killed partial directory was therefore **moved, not
deleted**, to `~/zach_count_20260731/runs/rungs-superseded-20260804/` under its
own label. Nine directories moved; the five completed rung directories were not
touched. No campaign artifact was deleted at any point.

## Commands

Preparation, on h17:

```bash
R=~/zach_count_20260731
mkdir -p $R/runs/rungs-superseded-20260804
for L in C2D4_s2-100_seed-20220207 C2D5_s2-1_seed-20220207 \
         C2D5_s2-10_seed-20220207 C2D5_s2-100_seed-20220207 \
         C2D3_s2-1_seed-20220208 C2D3_s2-10_seed-20220208 \
         C2D3_s2-100_seed-20220208 C2D4_s2-1_seed-20220208 \
         C2D4_s2-10_seed-20220208; do
  mv $R/runs/rungs/$L $R/runs/rungs-superseded-20260804/$L
done
```

Launch, one detached driver per rung, all nine concurrent — script preserved on
h17 as `~/zach_count_20260731/relaunch-20260804.sh`:

```bash
R=$HOME/zach_count_20260731
A=$R/src/analysis
PY=$A/.venv/bin/python
DSA=/home/ubuntu/flits-runs/data/dsa/zach_dsa_I_262_368_2500b_cntr_bpc.npy
CHIME=/home/ubuntu/flits-runs/data/zach_chime_I_262_3621_32000b_cntr_bpc.npy
cd $A/scattering/studies/joint-refits
for L in <the nine labels above>; do
  T=$(echo $L | tr ":" "-")
  nohup $PY zach_count_20260729/stage_zach_count.py \
    --runs-root $R/runs --dsa-input $DSA --chime-input $CHIME --python $PY \
    --rung $L > $R/logs/relaunch-20260804-$T.log 2>&1 &
  sleep 2
done
```

Per-rung logs: `~/zach_count_20260731/logs/relaunch-20260804-<label>.log`.
Launcher record: `~/zach_count_20260731/logs/relaunch-20260804-wave1.log`.

## Launch verification

Immediately after launch (2026-08-04 22:55–23:00 PDT):

- All nine drivers reported a process identifier; none exited early.
- `pgrep -fc run_controlled_joint_fit` returned ten, so the controlled
  entrypoint is live in every rung; load average climbed 0.19 → 21.1 → toward
  the expected 36-process occupancy.
- Sampler progress lines appear in the per-rung logs, which means each rung
  cleared its freeze pass and is in the real pass. Every log also carries
  exactly one `ControlledRunError` traceback from the freeze pass — that abort
  is the contract protocol, **never** a failure signal.
- All nine rungs wrote a real-pass receipt with `outputs_complete: false`; the
  five completed rungs still read `outputs_complete: true`.

## Verification to repeat when wave 1 finishes

Re-runnable check for completion, on h17:

```bash
cd ~/zach_count_20260731/runs/rungs
for d in */; do
  printf "%-34s %s\n" "$d" \
    "$(grep -o '"outputs_complete": *[a-z]*' $d/receipts/*.json | head -1)"
done
```

Fourteen rungs must read `true`, and each must carry the complete five-artifact
output set. Only then may the provisional adjudication phase begin, against the
acceptance rules in
[`scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md`](../../../../scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md).

## Owner stop, 2026-08-04 23:47 PDT

The owner stopped wave 1 about 52 minutes in: "1-3 hours per fit is too long,
if fits are running now, kill them." No further wave was started.

- Kill sequence: the launcher, then the nine `stage_zach_count.py` drivers,
  then the `run_controlled_joint_fit.py` children, with a final signal 9 sweep.
  It ran from a script file on the host rather than an inline command, because
  an inline `pkill -f stage_zach_count` matches the killing command's own
  command line and terminates the invoking shell before the later kills run —
  the first attempt failed exactly that way and left all nine rungs alive.
- Verified dead: `pgrep -fc '[s]tage_zach_count'`,
  `pgrep -fc '[r]un_controlled_joint_fit'` and `pgrep -fc '[r]elaunch-20260804'`
  all return zero; no campaign Python process survives (`pgrep -af python`
  shows only unrelated system services). Load average drains from 30.
- **Nothing was deleted.** All nine partial run directories, their contracts,
  their incomplete receipts and every per-rung log remain in place, as do the
  nine directories under `runs/rungs-superseded-20260804/` (580 KiB).
- Rung state after the stop, re-read from the receipts: unchanged at 5 of 27
  complete. The five seed-20220207 receipts (C2D3 at s2 = 1/10/100, C2D4 at
  s2 = 1/10) still read `outputs_complete: true`; all nine killed rungs read
  `false`. No rung of this wave reached its stopping threshold, so no rung of
  this wave produced usable evidence.

## What the stop implies

The per-fit cost is the frozen contract's own cost, not a scheduling defect.
At 1000 live points a rung is of order 100,000 iterations, which the MANIFEST
already measured as 1.5 to 3 hours. Reordering launches, which is what the
2026-08-04 restart decision did, cannot reduce it: the wall clock per fit is
set by the sampler settings the contract fixes.

Reducing it therefore requires amending the contract — the
`amend-contract-cheaper-sampler` option from the 2026-07-31 card. That is not a
mechanical change. Live points set the evidence precision, and the acceptance
rule compares log-evidence steps against a threshold of 5 after subtracting
twice the combined numerical uncertainty, so a cheaper sampler widens exactly
the uncertainty the comparison must overcome. It also breaks the uniformity the
contract requires, invalidating the five completed receipts and restarting all
27 rungs. This is a scientific decision for the manuscript owner and is queued
as a decision card in
[ticket 07](../../wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md).

## Still prohibited

- Promoting any fit value, table, figure or results-library pointer.
- Mixing the superseded Mac tree `~/Data/Faber2026/zach_count_20260731/` or the
  quarantined `zach-count-20260730-r3` receipts into adjudication.
- Amending the contract, including a sampler change, without the owner's
  recorded decision on the queued card.
- Relaunching any rung before that decision is recorded.
- Deleting anything under `runs/rungs-superseded-20260804/` or under the nine
  killed rung directories.

## Status

STATUS: VERIFIED — wave 1 launched, ran about 52 minutes, and was stopped by
the owner; all processes verified dead and all artifacts preserved. The campaign
stands at 5 of 27 complete rungs. No scientific claim follows from this record.
