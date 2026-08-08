# Fast exploratory joint fit — what actually costs time

Owner instruction, 2026-08-05: stop the long-running component-count campaign
and fit the dynamic spectrum at the highest resolution that completes in under
five minutes end to end.

**The measured answer is that resolution is not what costs time.** Fit at the
finest resolution available; buy the five minutes from the sampler instead.

Exploration only. Nothing produced here is admissible as component-count
evidence — see "What this configuration cannot do".

## The recipe that meets the target

Measured on h17 (40 cores, otherwise idle), one uncontended run, exit code 0:

| Setting | Value |
|---|---|
| DSA-110 decimation | `t_factor` 1, `f_factor` 192 → 32 channels × 2500 bins at native 32.768 microsecond sampling |
| CHIME/FRB decimation | `t_factor` 12, `f_factor` 8 → 128 channels × 2666 bins |
| Fitted points | 421,248 — four times the campaign contract's |
| Live points | 40 |
| Processes | 32 |
| Stopping threshold `dlogz` | 1.0 |
| Model scan | off |
| **End-to-end wall clock** | **263.9 s** (141.9 s preparation, 122 s sampling) |

Reproduce with `cost_ladder.py` (see below):

```bash
python cost_ladder.py r1 40 32 500 25 1.0 noscan
```

That is 20 to 40 times faster than the frozen campaign contract's 1.5 to 3
hours per fit, and it fits *more* data, not less.

## Why downsampling does not help

The ladder was run at eight decimations spanning a 260-fold range in fitted
data volume. Wall clock barely moved:

| Row | Fitted points | Processes | Sampler rate | End-to-end |
|---|---|---|---|---|
| `r1` (finest) | 421,248 | 32 | — | 332.3 s |
| `r2` | 210,624 | 32 | — | 332.4 s |
| `r8` | 52,624 | 32 | — | 331.7 s |
| `r256` (coarsest) | 1,640 | 4 | 3.94 it/s | did not converge in 300 s |
| `r2` | 210,624 | 4 | 3.75 it/s | did not converge in 300 s |

Three rows spanning an eightfold data range, all at 50 live points and 32
processes, finished within **one second of each other**. At four processes, a
260-fold data reduction changed the sampler rate by five per cent (3.94 versus
3.75 iterations per second). Both halves of the cost are effectively
data-independent in this regime:

- **Preparation, about 141 s, is fixed.** It did not vary with resolution at
  all (141.9 / 142.4 / 140.7 s across the eightfold range). It is interpreter
  startup, model construction and forking the worker pool, not array work.
- **Sampling cost is set by likelihood *calls*, not by their individual size.**
  The sampler spends `nc` = 36 likelihood evaluations per accepted sample at
  about 2.9 per cent efficiency, and needs of order 10,000 iterations. The
  per-evaluation cost is dominated by fixed Python overhead, so shrinking the
  arrays underneath it changes almost nothing.

## What does buy time

1. **Processes — the largest free win.** Nearly linear and scientifically free:
   4 → 5.62, 8 → 10.9, 32 → 35.7 iterations per second. The campaign contract
   used four processes on a forty-core host.
2. **Live points.** Sets the iteration count, and therefore sampling time,
   roughly proportionally. This is a precision cost, not a free one.
3. **Stopping threshold.** Loosening `dlogz` from 0.5 to 1.0 truncates the
   evidence tail: 191 s of sampling became 122 s. Also a precision cost.
4. **The model scan.** Off in the recipe above. Cheap to restore if wanted.

## A knob that is not currently reachable

The number of random-walk steps per sample is dynesty's `rwalk` default of 25,
which is what puts `nc` at 36. It is **not** settable from any configuration
file on this path: `nlive_walks` in the band run-config is read only by the
single-band pipeline (`scattering/scat_analysis/pipeline/core.py`), and the
`walks: 25` entry under `dynesty:` in
`radio_pipeline/resources/scattering_sampler.yaml` is not consumed by the joint
fit either — editing both left `nc` at 36 in every cell. `run_joint_fit.py`
never passes `walks` to `fit_joint_scattering`, though that function already
forwards `**dynesty_kwargs` straight to `NestedSampler`.

Exposing it would be a one-line optional flag with an unchanged default, and it
is the largest remaining lever: cutting walks from 25 to 8 would cut likelihood
calls per sample by roughly a factor of three. Not done here — it is a change
to a shared entry point and belongs in its own reviewed step.

## What this configuration cannot do

The completed fit reports a log-evidence uncertainty of **±2.63**. The campaign
contract accepts a component-count step only when the log-evidence improvement
exceeds 5 after subtracting *twice* the combined numerical uncertainty. A
single fit at this setting therefore spends the entire budget on its own noise
before any comparison starts.

So this recipe is for looking at morphology, residuals and parameter
plausibility quickly. It is not a cheaper route to the component-count answer,
and its outputs must never be mixed into that comparison.

## `cost_ladder.py`

Runs one cell of the ladder and writes `timing.json` beside the outputs:

```
python cost_ladder.py <row> <nlive> <nproc> <cap_seconds> <walks> <dlogz> [noscan]
```

Rows are defined in the `LADDER` table; `contract` reproduces the campaign
decimation and `r1` is the finest. Each cell gets its own run root via
`FABER2026_RUNS`, so cells never collide — but run them **one at a time** when
timing matters, because concurrent cells contend for cores and the numbers
become meaningless.

The harness reads the source checkout read-only and writes nothing into it.
