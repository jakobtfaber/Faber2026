# Zach component-count readiness audit (issue #205)

Status: **BLOCKED**. The strict C2D3/C2D4/C2D5 by `s2 = {1, 10, 100}` contract is
staged and runnable, but it cannot be executed today. Five blockers were found,
four of them verified by running the code rather than reading it. No fit was
adjudicated, no value was promoted, nothing was committed.

- Objective: audit readiness of the frozen C2D4 baseline, then execute or stage
  the strict component-count contract required by
  [issue #205](https://github.com/jakobtfaber/Faber2026/issues/205) and ticket
  `joint-scattering-controlled-rerun-07`.
- Phase: discovery and staging only. No repair, no consolidation, no retirement.
- Audit date: 2026-07-29.
- Parent repository revision: `d4eebe4f` (`main`).
- Analysis submodule revision: `a762ece30da414e1dacf72c730bcc2cc5a08c5c5`,
  worktree **dirty** (shared checkout; other workers hold the foreground,
  figure-review, and wayfinder-tooling lanes).
- Machine-readable evidence: [`readiness-audit.json`](readiness-audit.json).
- Staged contract: [`../../../../scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md`](../../../../scattering/studies/joint-refits/zach_count_20260729/MANIFEST.md).

## Verdict on the frozen C2D4 baseline

**The frozen C2D4 baseline no longer exists as a reusable comparator.** It
cannot be reproduced, re-hashed, or compared against. Only its hashes and its
rendered panel survive.

The 2026-07-23 verification receipt
([`joint-scattering-controlled-rerun-05-zach-c2d4-20260723`](../joint-scattering-controlled-rerun-05-zach-c2d4-20260723/README.md))
names the run root `/home/ubuntu/flits-controlled/joint-scattering-2026-07-23-v4/zach`
on h17. That directory and its entire parent are gone. A filesystem-wide search
of h17's single root device found no trace of the bundle, and no local copy
exists on the workstation or in the results library. What survives is the
verification receipt, the reviewed panel scalable-vector graphic in the ticket-6
owner-review receipt, and the source worktree the run was executed from.

The practical consequence: **C2D4 must be re-run as one of the three rungs.** It
cannot be carried forward as a frozen comparator, and the ticket's "after the
clean C2D4 morphology rerun" premise no longer holds. This does not invalidate
the earlier reproducibility verdict — that verdict was true of a snapshot that
has since been deleted, so it is now stale rather than wrong.

## Blockers

Ordered by how hard they are to clear.

### 1. The required time resolution is unreachable in the preparation code

Issue #205 requires DSA-110 at its native 32.768 microsecond time resolution.
Under the frozen controlled-run processing environment the preparation step
actually delivers **65.5 microseconds**, and no configuration setting changes
that.

Observed directly from a run on the real Zach data:

```
[zach] AUTO-TF DSA  : 24 ch x 7.8 MHz, dt=65.5 us (f256/t2); window 23.8 ms; peak S/N 38/px
```

The mechanism was re-derived directly from the real Zach data rather than read
off the log line, and it is **not** where it first appears to be.

`joint_tf_prep.choose_resolution` picks **native resolution for DSA-110 on its
own merits**: from the DSA band's own on-pulse window of 41 native samples it
returns a time decimation of 1, that is 32.768 microseconds. Nothing is wrong
with the DSA-110 data or its per-band resolution choice.

The decimation happens afterwards, during band reconciliation.
`_common_peak_relative_window` takes the union of the two bands' on-pulse
windows in peak-relative time. CHIME/FRB's own window is 9280 native CHIME
samples wide, so the union spans 23.8 milliseconds, which is **726 native
DSA-110 samples**. `_build_model` then re-applies the `MAX_TIME_BINS` cap
against that reconciled window (`joint_tf_prep.py:439-442`):

```python
t_factor = p.t_factor
span = max(1, win_native[1] - win_native[0])
while span // t_factor > MAX_TIME_BINS:
    t_factor *= 2
```

With `MAX_TIME_BINS = 512`, 726 // 1 exceeds the cap, so the decimation doubles
to 2 and DSA-110 lands at 65.5 microseconds. Verified by re-running the same
arithmetic on the real probes: at a cap of 512 the loop yields 2 (65.5
microseconds), at 1024 it yields 1 (32.8 microseconds).

So the DSA-110 band is coarsened **because CHIME/FRB's window is long**, not
because DSA-110 needs it. Setting `t_factor: 1` in the band configuration
cannot help, because this cap runs after the per-band choice.

Reaching native resolution therefore means raising `MAX_TIME_BINS` to at least
1024, which roughly doubles the DSA-110 sample count in the joint likelihood.
That changes the frozen processing contract and raises the sampler cost. **This
is a scientific and contract-design decision and belongs to the owner** — it is
exactly the resolution family that produced the earlier collapsed C2D4 result at
coarse binning, so it should not be resolved silently by an agent.

### 2. The nested sampler is not a declared dependency of the analysis package

`dynesty` is imported by the joint-fit path
(`scattering/scat_analysis/burstfit_joint.py`, inside `fit_joint_scattering`)
and is required by the controlled-run environment-identity gate, which checks
NumPy, SciPy, `dynesty`, PyYAML, and Matplotlib against their installed wheel
records. It appears **nowhere** in `analysis/pyproject.toml` and **zero times**
in `analysis/uv.lock`. The repository's own virtual environment fails the gate:

```
ControlledRunError: required runtime distribution is missing: dynesty
```

Until `dynesty` is declared and locked, **no controlled joint fit can run
analysis-only on any machine.** This is a gap left by the retirement of the
former pipeline submodule, where the sampler used to be provided.

`pyproject.toml` is currently modified by another worker in this shared
checkout, so this lane did not edit it.

### 3. The runtime silently imports retired pipeline code

In the workstation's default interpreter, running the analysis-housed runner
resolves `scattering.scat_analysis` to the **retired** `dsa110-FLITS` clone:

```
File ".../jakobtfaber/dsa110-FLITS/scattering/scat_analysis/controlled_run.py", line 715
```

An editable install record, `__editable__.flits-0.1.0.pth`, maps the top-level
`scattering` package to the retired repository and wins over the analysis
checkout. This directly violates the analysis-only requirement and would have
bound retired source paths into the contract.

Verified workaround: prepend the analysis root to `PYTHONPATH`. With
`PYTHONPATH=<analysis>` the import resolves inside the analysis submodule. The
staged manifest sets this on every command. The durable fix is either removing
the editable install or having the runner place the repository root on the
module search path itself — it currently adds only `<repo>/scattering`, which
makes the package name resolvable only by accident.

### 4. The controlled entrypoint cannot run from this shared checkout

The controlled runner fails closed on any dirty source tree, including untracked
files. Verified by running it:

```
ControlledRunError: source worktree is dirty: M LOCAL_CODE_PROVENANCE.md
```

This checkout is shared with other workers and is heavily modified. A clean
source snapshot at a fixed revision is required. The assignment for this lane
forbids creating a worktree, so **choosing the clean-checkout mechanism is an
owner or orchestrator decision.**

### 5. No compute host is prepared

h17 is reachable (`lxd110h17`, two RTX 2080 Ti, 131 gigabytes free) and both
Zach inputs are already staged there under `/home/ubuntu/flits-runs/data`. But
its `Faber2026` clone sits at an old revision with **no `analysis` submodule
checked out**, so it cannot run the analysis-only contract until refreshed and
given a locked environment that includes the sampler.

## What is ready

Everything except the five items above.

- Both Zach inputs are present locally and hash-stable: the DSA-110 waterfall
  (123 megabytes) and the CHIME/FRB waterfall.
- The fitting code is fully migrated into `analysis/` with no import of the
  retired pipeline package.
- The telescope and sampler configurations are migrated to
  `analysis/radio_pipeline/resources/`.
- The controlled-run contract machinery is intact and its gates demonstrably
  fail closed in the intended order.
- The code path runs end to end on the real Zach data. A reduced-live-point
  feasibility run (50 live points, four workers, C2D4, fixed gain-prior variance
  100) prepared both bands and drove the sampler from a log-evidence gap of
  about 114,000 down to about 21 in roughly 100 seconds on the workstation.

## Cost estimate for the full contract

The frozen schedule is 27 controlled fits: three component counts, three fixed
gain-prior variances, three seeds.

The feasibility run converged in 5658 sampler iterations over 4 minutes 34
seconds at 50 live points on four workstation cores. Iteration count scales
roughly linearly with live points, so a contract rung at 1000 live points is of
order 100,000 iterations — about **1.5 to 3 hours per fit**, or 40 to 80 hours
for all 27 run one after another. They must be run in parallel on a compute
host. Raising `MAX_TIME_BINS` to reach native resolution roughly doubles the
DSA-110 sample count and will increase this further.

A separate constraint: the uncontrolled entrypoint `run_joint_fit.py` writes
only the fit summary and the weighted samples. The model grid, residual
diagnostics and panel come from the controlled finalization path. Issue #205
requires reconstructable model products for every evidence rung, so the
controlled entrypoint is mandatory — the uncontrolled one cannot satisfy the
contract even when it converges.

## Adjudication contract (staged, not yet applied)

A count step from N to N+1 components is accepted only if **all** of the
following hold, and is rejected otherwise:

1. All three fits complete with the contract's stopping threshold reached and a
   complete output set.
2. The log-evidence improvement exceeds 5 with the **same sign at every** fixed
   gain-prior variance, after subtracting twice the combined numerical
   uncertainty (the sampler's own error added in quadrature with the spread
   across the three seeds).
3. Every component's posterior arrival time lies strictly inside the fitted
   window in its own band — any off-window component voids the comparison.
4. Neighbouring counts occupy the same scattering mode: the pulse-broadening
   exponent posteriors must overlap and must not sit against a prior edge.
5. The added component is physical: bounded, non-null amplitude, coinciding with
   an owner-identified candidate feature, and improving local residuals.
6. Per-band visual residual diagnostics are acceptable in both bands.

A statistical failure does **not** reinstate C2D3 as the physical morphology. It
leaves the owner-confirmed morphology recorded with its fitted parameters and
count evidence unaccepted. Scattering-time times scintillation-bandwidth
products stay downstream of acceptance.

## Adjudication verdict

**None. Null and positive adjudication are both unavailable**, because no rung
was executed. Reporting any component-count verdict from existing artifacts
would mean reusing the deprecated job-180 numbers or the deleted v4 bundle, both
of which are explicitly barred.

## What this audit did not do

No commit, no push, no issue closure, no change to any shared control registry,
no edit to any path held by another worker, and no promotion of any fitted
value, table, figure, or results-library pointer.
