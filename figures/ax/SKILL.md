# Skill: manuscript figure regeneration

**Consult this skill + `analysis/figures/catalog.yaml` before opening any plot script.**

## Goal

Regenerate science-ready manuscript figures without re-ingesting producer
source. The LLM must never draw or restyle figures.

## Source of truth

| Artifact | Role |
|----------|------|
| [`analysis/figures/catalog.yaml`](../../analysis/figures/catalog.yaml) | Declarative DAG: producer argv, inputs, outputs, deps, approval slots |
| [`analysis/scripts/figure_flow.py`](../../analysis/scripts/figure_flow.py) | Deterministic runner (no API keys) |
| [`repro_manifest.csv`](../../repro_manifest.csv) | Broader inventory (tables + historical notes) |
| [`analysis/figure_review/definitions/slots.json`](../../analysis/figure_review/definitions/slots.json) | Hash-bound approval for protected targets |

## Commands

```bash
# Inventory
python3 analysis/scripts/figure_flow.py list
python3 analysis/scripts/figure_flow.py stale

# Clone-safe embedded set (same as `make figures`)
python3 analysis/scripts/figure_flow.py regen --manuscript --clone-ok
make figures

# One figure (fails closed if inputs missing)
python3 analysis/scripts/figure_flow.py regen --id toa_offset_decomposition
python3 analysis/scripts/figure_flow.py regen --id clusters_icm   # runs sightline_budget first

# Fig. 1 — external waterfalls; staging only
python3 analysis/scripts/figure_flow.py regen --id fig1_gallery
# then follow the approval hint to analysis/scripts/figure_review.py
```

## Agent rules

1. Prefer `analysis/scripts/figure_flow.py` / `make figures` over reading plot scripts.
2. Open producer source **only** after a typed `PRODUCER_FAILED` / `MISSING_INPUTS`
   error and only the failing node.
3. Never copy staging PDFs onto `figures/` for slots with `approval_slot`.
4. `manuscript: false` catalog rows are discoverable but must not be promoted
   into the compiled manuscript without an explicit owner request.
5. Optional Ax front door (needs `pip install axllm`):
   `python3 figures/ax/agent.py --help`

## Environments

- Analysis producers: `uv run --project analysis --frozen …`.
