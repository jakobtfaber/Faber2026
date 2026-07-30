# Geometry-constrained one-event workflow

One public command plans or runs one event:

```bash
python scripts/run_one_event_absolute_dm_workflow.py \
  --config analysis-configs/absolute-dm/casey.json
```

Without `--execute`, the command is write-free and reports every blocker.
Formal inference has one shared absolute dispersion measure and one geocentric,
unscattered 400 MHz arrival time per matched component. CHIME/FRB and DSA-110
remain on separate reviewed grids.

Before authorization, the same command can build only the auditable pre-fit
products and print the exact proposed crop, resolution, frequency, support, and
off-pulse locks:

```bash
python scripts/run_one_event_absolute_dm_workflow.py \
  --config analysis-configs/absolute-dm/casey.json \
  --prepare-reviewed-inputs
```

This mode cannot sample, run posterior oracles, or render an approval packet.
It requires reviewed clock and station-delay uncertainties before touching
data. Casey now carries provisional owner-adopted Gaussian priors: a 1 ms
standard deviation on the inter-site clock difference, split equally between
independent station terms, and a 0.5 us standard deviation per station for the
geometric-delay calculation. The latter is not the independent-projection
mismatch. These are analysis priors, not
measurements of either station's absolute UTC accuracy. CHIME/FRB preparation
performs one coherent anchor evaluation; the three
fully coherent checks run only after formal inference.
Its proposed locks remain unapproved until the owner records them in the event
configuration.

Preparation is incremental. The first pass writes a high-resolution component
diagnostic and an inert resolution template. The reviewed template must specify
independent frequency-averaging factors, retain time factor 1, require complete
rectangular support, and carry the analytic residual-smearing receipt. The
second pass materializes separate fit-grid products, then writes
`component-proposal.json`, `component-proposal.pdf`,
`resolution-lock-proposal.json`, and `review-decision-template.json`.
Component windows therefore always use fit-grid sample coordinates.

Review and execution authorization are separate, source-preserving operations:

```bash
python scripts/run_one_event_absolute_dm_workflow.py \
  --config analysis-configs/absolute-dm/casey.json \
  --apply-review-decision /path/to/approved-review-decision.json \
  --component-proposal /path/to/component-proposal.json \
  --resolution-proposal /path/to/resolution-lock-proposal.json \
  --output-config /path/to/casey-reviewed.json

python scripts/run_one_event_absolute_dm_workflow.py \
  --config /path/to/casey-reviewed.json \
  --authorize-reviewed-config \
  --authorization-note "explicit science-execution authorization" \
  --output-config /path/to/casey-authorized.json
```

Neither command overwrites its source. Review produces a fully locked but
execution-disabled configuration. Authorization creates another binding.
Execution must rebuild preflight through geometry and deterministically
recreate the approved fit grids under that binding before sampling.

The declared runtime is Python 3.12 or newer. On h17 use the locked environment:

```bash
uv run --locked python scripts/run_one_event_absolute_dm_workflow.py \
  --config analysis-configs/absolute-dm/casey.json
```

Execution requires both `workflow.execution_authorized` and
`joint_fit.execution_authorized`. Event configuration binds paths, hashes,
support, crop, resolution, components, associations, geometry, clock
uncertainty, priors, and acceptance thresholds. See
`docs/analysis/geometry-constrained-joint-fitting.md`.
After sampling, mandatory CHIME/FRB coherent and DSA-110 exactly-once oracle
stages evaluate the posterior lower bound, median, and upper bound before the
PDF review packet can be written.

Time averaging is currently forbidden because the likelihood samples bin
centers rather than integrating across averaged time bins. Frequency averaging
must keep residual intra-bin smearing below 0.10 fit sample and 0.05 of the
narrowest reviewed component width. A post-fit factor-versus-half-factor
comparison is mandatory; its dispersion measure, arrival-time, interval-width,
and model-weight thresholds are explicit in every event configuration.

Casey remains blocked before execution. Its timing bounds are recorded;
component windows and associations and strict regenerated observation products
still require review. Historical Casey products remain immutable
provenance; they are not inputs to the formal fit.

## Historical Phase B compatibility

Phase B is paused and execution-disabled after fail-closed Oran and Isha
failures. No Phase B output is science authority or a manuscript claim.

Configs and the campaign receipt are under `phase-b/`. The tracked receipt has
no authorized bindings. All event configs and the Casey regression fixture set
`workflow.execution_authorized` to `false`.

The added controls:

- inventory all CHIME/FRB and DSA-110 inputs;
- reconstruct DSA-110 input dispersion-measure state with held-out checks;
- retain a conservative uncertainty bound when a nonzero residual is not
  established;
- propagate low, nominal, and high input-state endpoints through the DSA-110
  products;
- require timing, morphology, independent-review, config-hash, and campaign
  authorization gates before launch;
- persist failed-stage receipts and require explicit failed-stage retry.

Historical event configurations remain readable for provenance but are not
accepted by the active geometry-constrained execution stages.

Write-free example:

```bash
python scripts/run_one_event_absolute_dm_workflow.py \
  --config analysis-configs/absolute-dm/phase-b/oran/workflow-config.json
```
