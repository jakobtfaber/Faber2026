# One-event absolute dispersion measure workflow

Dry-run any reviewed event configuration:

```bash
python scripts/run_one_event_absolute_dm_workflow.py \
  --config analysis-configs/absolute-dm/casey.json \
  --dry-run
```

The configuration supplies all event-specific paths, hashes, channel support,
dispersion measures, crop, frequency order, geometry, and gates. The scripts
contain no Casey-specific branch. Execution fails closed unless the reviewed
configuration explicitly sets `workflow.execution_authorized` to `true`.

Casey is the approved regression fixture. Its authoritative packet is
`results/absolute-dm/casey/approval-packet.svg`.

## Phase B

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

Current write-free example:

```bash
python scripts/run_one_event_absolute_dm_workflow.py \
  --config analysis-configs/absolute-dm/phase-b/oran/workflow-config.json
```
