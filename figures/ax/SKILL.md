# Skill: manuscript figure regeneration

**Consult this skill + `figures/catalog.yaml` before opening any plot script.**

## Goal

Regenerate science-ready manuscript figures without re-ingesting producer
source. The LLM must never draw or restyle figures.

## Source of truth

| Artifact | Role |
|----------|------|
| [`figures/catalog.yaml`](../catalog.yaml) | Declarative DAG: producer argv, inputs, outputs, deps, approval slots |
| [`analysis/scripts/figure_flow.py`](../../analysis/scripts/figure_flow.py) | Deterministic runner (no API keys) |
| [`analysis/repro_manifest.csv`](../../analysis/repro_manifest.csv) | Broader inventory (tables + historical notes) |
| [`analysis/figure_review/slots.json`](../../analysis/figure_review/slots.json) | Hash-bound approval for protected targets |

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
# then follow the APPROVAL_REQUIRED hint → analysis/figure_review.py new-batch / decide / promote
```

## Agent rules

1. Prefer `figure_flow.py` / `make figures` over reading `analysis/scripts/plot_*.py`.
2. Open producer source **only** after a typed `PRODUCER_FAILED` / `MISSING_INPUTS`
   error and only the failing node.
3. Never copy staging PDFs onto `figures/` for slots with `approval_slot`.
4. `manuscript: false` catalog rows are discoverable but must not be promoted
   into the compiled manuscript without an explicit owner request.
5. Optional Ax front door (needs `pip install axllm`):
   `python3 figures/ax/agent.py --help`

## Environments

- Faber2026-local producers: `conda run -n flits …` (healpy, SciencePlots).
- Pipeline producers: `cd pipeline && uv run …` (declared as `cwd: pipeline` in catalog).
