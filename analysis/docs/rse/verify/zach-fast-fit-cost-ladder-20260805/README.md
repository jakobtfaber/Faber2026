# Zach fast-fit cost ladder — receipt (2026-08-05)

- Objective: find the highest dynamic-spectrum resolution whose joint fit
  completes end to end in under five minutes, per the owner's 2026-08-05
  instruction to stop the long-running component-count campaign and pivot.
- Scientific phase: exploration.
- Operational phase: discovery. No promotion, no adjudication, no contract.
- May change: the h17 scratch tree `~/zach_fast_20260805/`, this receipt, the
  study directory `scattering/studies/joint-refits/fast_fit_20260805/`.
- Must not change: the frozen campaign contract, the five completed campaign
  receipts, the campaign clone, both input waterfalls.
- Done when: one configuration completes with exit code 0 in under 300 s and
  the cost structure is measured well enough to say what bought the time.

**Done.** 263.9 s end to end, exit code 0, at the finest resolution on the
ladder.

## Result

| Setting | Value |
|---|---|
| DSA-110 | `t_factor` 1, `f_factor` 192 → 32 channels × 2500 bins, native 32.768 microsecond sampling |
| CHIME/FRB | `t_factor` 12, `f_factor` 8 → 128 channels × 2666 bins |
| Fitted points | 421,248 (four times the campaign contract) |
| Live points / processes | 40 / 32 |
| `dlogz` / model scan | 1.0 / off |
| Wall clock | 263.9 s = 141.9 s preparation + 122 s sampling |

Fitted values from that run, exploratory and not for promotion: pulse-broadening
exponent 5.333 (5.309–5.352), turbulence index 3.200 (3.193–3.209),
scattering time at 1 GHz 0.1705 ms (0.1689–0.1725), log-evidence
28466.13 ± 2.63 over 200,112 likelihood calls.

Two component arrival times sit near the edges of their fitted windows —
`t0_D1` at 0.045 ms (interval 0.011–0.104) and `t0_D4` at 22.46 ms (interval
21.02–23.40). At forty live points that is not evidence of anything; it is
flagged because boundary behaviour is exactly what the contract's rejection
rules watch for, and it should be re-checked before anyone reads morphology off
this configuration.

## The finding that matters

Downsampling does not buy time. Three rows spanning an eightfold range in
fitted data volume, all at 50 live points and 32 processes, finished within one
second of each other:

| Row | Fitted points | End-to-end | Preparation | Sampling |
|---|---|---|---|---|
| `r1` | 421,248 | 332.3 s | 141.9 s | 191 s |
| `r2` | 210,624 | 332.4 s | 142.4 s | 190 s |
| `r8` | 52,624 | 331.7 s | 140.7 s | 191 s |

At four processes, a 260-fold data reduction moved the sampler rate by five per
cent: the coarsest row (`r256`, 1,640 points) ran at 3.94 iterations per second
against 3.75 for a row with 128 times more data. Both components of the cost
are effectively data-independent here — preparation is fixed overhead, and
sampling is set by the *number* of likelihood calls (36 per accepted sample at
about 2.9 per cent efficiency, of order 10,000 iterations), not by the size of
each one.

What does buy time: processes (4 → 5.62, 8 → 10.9, 32 → 35.7 iterations per
second, nearly linear and scientifically free — the contract used four on a
forty-core host), live points, the stopping threshold, and switching off the
model scan.

A false lead worth recording: the random-walk step count is dynesty's `rwalk`
default of 25 and is not settable from any configuration file on this path.
Editing `nlive_walks` in the band run-config (read only by the single-band
pipeline) and `walks` under `dynesty:` in the sampler resource both left `nc`
at 36 in every cell. Exposing it through `run_joint_fit.py` is the largest
remaining lever and is deliberately not done here.

## Snapshot identity

| Item | Value |
|---|---|
| Host | h17, 40 cores, idle before and between cells |
| Source | `~/zach_count_20260731/src/analysis`, revision `894a1d2`, read-only, tree clean |
| Interpreter | CPython 3.13.12, dynesty 3.1.0 |
| Scratch tree | `~/zach_fast_20260805/` (outside any repository) |
| DSA-110 input | `zach_dsa_I_262_368_2500b_cntr_bpc.npy`, SHA-256 begins `be917e94` |
| CHIME/FRB input | `zach_chime_I_262_3621_32000b_cntr_bpc.npy`, SHA-256 begins `bf317648` |

Same inputs and same source revision as the campaign, so the timings are
comparable to it. The harness reads the checkout read-only and writes nothing
into it; each cell gets its own run root through `FABER2026_RUNS`.

## Method and its limits

`scattering/studies/joint-refits/fast_fit_20260805/cost_ladder.py`, one cell per
invocation, each capped by wall clock so a cell that misses the target is
recorded as a failure rather than left to run. Every raw row is in
`timings.json` beside this file.

Limits worth knowing before reusing these numbers:

- Early cells were run several at a time and contended for cores. Those rows
  are marked by their process counts and are used here only for the
  resolution-versus-rate comparison at fixed process count, never for
  end-to-end wall clock. Every end-to-end number quoted above comes from an
  uncontended single-cell run.
- One rung directory was written twice by concurrent cells before the cell
  naming included the process count, so its `timing.json` reflects the last
  writer. It is excluded from the conclusions.
- Timings are for one burst, one component count (C2D4) and one gain-prior
  variance. The scaling arguments should hold across the grid but were not
  measured across it.
- `prep_seconds` is derived by subtracting the sampler's own progress clock
  from the wall clock, so it absorbs any post-sampling finalisation.

## Status

STATUS: VERIFIED — one configuration completes in 263.9 s with exit code 0 at
the finest resolution on the ladder, and the cost structure is measured. The
fitted values above are exploratory and must not be promoted; this
configuration's log-evidence uncertainty of ±2.63 makes it unusable for
component-count evidence, where the acceptance rule requires a step above 5
after subtracting twice the combined numerical uncertainty.
