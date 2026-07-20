# JointTF v2 harvest evidence

Independent, read-only re-harvest of h17 jobs 169–182. This directory preserves
the two reviewed figures and a machine-readable manifest. It supports candidate
count dispositions; it does not record owner adoption.

## Contents

- `manifest.json`: hashes and metadata for 14 logs, 14 result JSON files, 14
  sample archives, six run configurations, six input arrays, executed code,
  package environment, comparison arithmetic, and fit-window checks.
- `v2_harvest_vet.png`: component-time, ζ, and evidence-step overview.
- `zach_v2_ladder_vet.png`: DSA-110 data/model and residual ladder.

## Integrity

| File | SHA-256 |
|---|---|
| `v2_harvest_vet.png` | `9c01505c9ec8f9600d3d69142a6312952ab2dc7ec8ebcb385ee5e98cf6f06169` |
| `zach_v2_ladder_vet.png` | `3cddc2f96afeb75dc3a71418f414d289cb05680cd1acfcaeb2b87fdbf0c317fd` |

Both match the remote h17 files under
`/home/ubuntu/flits-runs/data/joint/_v2_harvest_20260719/`.

## Reproduce the harvest

From the Faber2026 repository with live SSH access to h17:

```bash
python3 -m py_compile scripts/revalidate_jointtf_v2_harvest.py
python3 scripts/revalidate_jointtf_v2_harvest.py \
  --output docs/rse/decks/jointtf-v2-harvest-2026-07-19/manifest.json
python3 -m json.tool \
  docs/rse/decks/jointtf-v2-harvest-2026-07-19/manifest.json >/dev/null
```

The script sends itself to h17 worker mode and performs read-only inspection.
It does not submit jobs or modify remote files.

## Boundary

The harvest is reproducible from existing artifacts. The fits are not exactly
rerunnable: no sampler seeds were recorded, and executed code includes modified
and untracked files. See the validation report for the scientific reading and
owner gates.

## Reference

- `docs/rse/specs/validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md`
