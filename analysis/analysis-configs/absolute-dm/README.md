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
