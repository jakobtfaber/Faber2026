# Zach component-count contract — staged, not executed

Strict C2D3 / C2D4 / C2D5 comparison at fixed gain-prior variances 1, 10 and
100 for [issue #205](https://github.com/jakobtfaber/Faber2026/issues/205).
Twenty-seven controlled fits under one hash-bound contract.

Nothing here has been run. The readiness audit that explains why is
[`../../../docs/rse/verify/joint-scattering-controlled-rerun-07-zach-count-readiness-20260729/README.md`](../../../docs/rse/verify/joint-scattering-controlled-rerun-07-zach-count-readiness-20260729/README.md).

## Contents

| File | What it is |
|---|---|
| `rungs.json` | The frozen schedule and the adjudication contract. Machine-readable. |
| `stage_zach_count.py` | Builds each rung's contract and drives the controlled entrypoint. |

## Before this can run

Four things must be true. None of them is true today.

1. **The sampler must be a declared dependency.** `dynesty` is imported by
   `scattering/scat_analysis/burstfit_joint.py` and demanded by the
   controlled-run environment-identity gate, but it appears nowhere in
   `analysis/pyproject.toml` or `analysis/uv.lock`. Add it and re-lock. Until
   then every rung fails with `required runtime distribution is missing:
   dynesty`.
2. **The checkout must be clean.** The controlled entrypoint refuses a dirty
   source tree, untracked files included. `stage_zach_count.py` checks this
   first and stops with the offending path.
3. **The retired pipeline package must not shadow the analysis one.** On the
   workstation an editable install record, `__editable__.flits-0.1.0.pth`,
   maps the top-level `scattering` package to the retired `dsa110-FLITS` clone
   and wins. The driver sets `PYTHONPATH` to the analysis root on every
   subprocess, which is verified to defeat it, but removing the editable
   install is the durable fix.
4. **The time resolution is decided; the code does not yet deliver it.** The
   owner fixed native 32.768 microseconds on 2026-07-30, matching what issue
   #205 requires. The preparation code still delivers 65.5 microseconds, and no
   configuration setting changes it, so the cap below must be raised before any
   rung runs.

   The decision rests on a like-for-like comparison of the same archival
   product at time factors 1 and 2:
   `docs/rse/verify/zach-dsa-resolution-comparison-20260730/`. Six components
   above five standard deviations survive at native resolution and four survive
   after adjacent-pair averaging, the two lost ones sitting at +2.195 and
   +2.785 milliseconds from the peak at 5.8 and 8.1 standard deviations. A
   2026-07-29 record selecting 65.536 microseconds was retracted as unratified.

   `choose_resolution` does pick native resolution for DSA-110 from its own
   41-sample on-pulse window. The coarsening happens later, in band
   reconciliation: `_common_peak_relative_window` unions the two bands'
   windows, CHIME/FRB's own window is 9280 native CHIME samples, so the common
   span becomes 23.8 milliseconds — 726 native DSA-110 samples — and
   `_build_model` (`joint_tf_prep.py:439-442`) re-applies the `MAX_TIME_BINS`
   cap of 512 to that reconciled window, doubling the decimation.

   So DSA-110 is coarsened because CHIME/FRB's window is long, not because
   DSA-110 needs it, and `t_factor: 1` in the band configuration cannot help
   because the cap runs after the per-band choice. Raising `MAX_TIME_BINS` to
   1024 restores 32.8 microseconds, at roughly double the DSA-110 sample count.
   See `resolution_contract` in `rungs.json`.

## Running it

From a **clean** checkout, in `analysis/scattering/studies/joint-refits`:

```bash
ANALYSIS=/path/to/Faber2026/analysis
DATA=/path/to/Faber2026-data

python zach_count_20260729/stage_zach_count.py \
  --runs-root  /path/to/run/root \
  --dsa-input   "$DATA/dsa110/DSA_bursts/zach_dsa_I_262_368_2500b_cntr_bpc.npy" \
  --chime-input "$DATA/chimefrb/CHIME_bursts/zach_chime_I_262_3621_32000b_cntr_bpc.npy" \
  --python "$ANALYSIS/.venv/bin/python" \
  --plan-only
```

`--plan-only` prints the 27 rung labels and stops. Drop it to execute. Restrict
to individual rungs with `--rung C2D4:s2-100:seed-20220207`, repeatable — this
is how the work is spread across parallel workers on a compute host.

The run root must be outside the repository. The driver creates
`configs/`, `contracts/`, `receipts/` and `data/joint/` beneath it.

**Do not add `-B` or `PYTHONDONTWRITEBYTECODE` yourself.** Two interacting
traps, both hit and fixed during staging:

- Importing from the checkout writes `__pycache__` into it, which makes the
  tree dirty, which the controlled entrypoint refuses. Left alone, the first
  rung's freeze pass poisons the tree and every pass after it fails. Reproduced:
  one subprocess created seven `__pycache__` directories.
- The obvious fixes both break the run. `-B` lands in the recorded argv and the
  runner rejects interpreter flags it cannot replay. Setting
  `PYTHONDONTWRITEBYTECODE` in an already-running process leaves that process's
  `sys.flags` untouched but is inherited by children — including the reference
  interpreter the runner spawns to check its own flags — so the two disagree
  and every run dies with "interpreter flags or options cannot be replayed".

The driver handles this: `sys.dont_write_bytecode` for its own imports, and the
variable set only in the subprocess environment, where the child sees it from
startup and its reference interpreter agrees. Verified: three consecutive
driver subprocesses leave the tree clean and preflight still passes.

## How each rung executes

The controlled entrypoint will not sample until its contract already carries
the resolved fit identity, which is a hash of the resolved priors, support and
sampler settings — knowable only after preparation. So each rung runs twice:

1. **Freeze pass.** A contract with a placeholder identity passes preflight,
   preparation runs, the runner writes the resolved identity and aborts before
   constructing the sampler.
2. **Real pass.** The identity is written into the contract, the incomplete
   freeze receipt is removed, and the same command runs to completion.

Both passes bind the same inputs, configurations, source files, source
revision, environment lock, runtime environment, command and working
directory. Any drift between them fails closed.

## What is held identical across all 27 rungs

Both input waterfalls, both band configurations, the telescope and sampler
configurations, the bad-channel masks and surviving frequency channels, the
fitted window in each band, the prior version and every prior endpoint, the
environment lock and runtime identity, and every executed source file.

Only three things vary: the DSA-110 component count (3, 4, 5), the fixed
gain-prior variance (1, 10, 100), and the seed (20220207, 20220208, 20220209).

The three seeds exist only to measure the sampler's own log-evidence scatter,
which enters the acceptance test as a numerical uncertainty. `20220207` is the
seed the deleted 2026-07-23 C2D4 run used; the other two are its immediate
increments. This lane chose that schedule as a reversible default and recorded
it so it is reproducible.

## Acceptance and rejection

A step from N to N+1 components is accepted only if every one of these holds:

1. All three fits complete, reach the stopping threshold, and produce the
   complete five-artifact output set.
2. The log-evidence improvement exceeds 5 with the **same sign at every** fixed
   gain-prior variance, after subtracting twice the combined numerical
   uncertainty — the sampler's reported error added in quadrature with the
   spread across the three seeds.
3. Every component's posterior arrival time lies strictly inside the fitted
   window of its own band.
4. Neighbouring counts occupy the same scattering mode: overlapping
   pulse-broadening exponent posteriors, none against a prior edge.
5. The added component is bounded and non-null, coincides with an
   owner-identified candidate feature, and improves local residuals.
6. Per-band visual residual diagnostics are acceptable in both bands.

Off-window components, mode changes between neighbouring counts, unconverged
runs and nonphysical parameters are rejections, not caveats. A previous Zach
result of `+3550` was an off-window artefact and a `+1425` step was a mode jump;
both were correctly discarded, and this contract exists to make that automatic.

A statistical failure does **not** reinstate C2D3 as the physical morphology. It
leaves the owner-confirmed morphology recorded with fitted parameters and count
evidence unaccepted. Scattering time times scintillation bandwidth stays
downstream of acceptance. The inner-scale power-law pulse-broadening model is a
conditional sensitivity test only, at a single accepted count, and is never
mixed into component-count evidence.

## Cost

Measured on the workstation: a reduced feasibility fit at 50 live points
converged in 5658 iterations over 4 minutes 34 seconds on four cores. Iteration
count scales roughly linearly with live points, so a contract rung at 1000 live
points is of order 100,000 iterations — **about 1.5 to 3 hours per fit**, or 40
to 80 hours for all 27 run one after another. Run them in parallel on a compute
host. Raising `MAX_TIME_BINS` to reach native DSA-110 resolution roughly doubles
the sample count and will increase this further.

## Note on the uncontrolled entrypoint

`run_joint_fit.py` writes only the fit summary and the weighted samples. The
model grid, residual diagnostics and panel come from the controlled
finalization path. The issue requires reconstructable model products for every
evidence rung, so the controlled entrypoint is mandatory — the uncontrolled one
cannot satisfy the contract even if it converges.
