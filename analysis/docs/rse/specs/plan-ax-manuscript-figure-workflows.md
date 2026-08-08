# Plan: Ax-structured manuscript figure workflows

**Status:** implemented 2026-07-20 — catalog + `scripts/figure_flow.py` + `make figures` + `figures/ax/`  
**Goal:** agents (and humans) regenerate science-ready manuscript figures from a
typed, prescriptive graph — without re-reading plot scripts each time.

Stack: [ax-llm/ax](https://github.com/ax-llm/ax) via **Python `axllm`**
(`flow`, `agent`, signatures). TypeScript `@ax-llm/ax` is equivalent if we later
want a Node entrypoint; science producers stay Python.

---

## Problem

Today producers are scattered across `scripts/`, `pipeline/`, and notes in
`repro_manifest.csv` + `figure_review/slots.json`. Regen is possible for some
figures but not as one declarative workflow. Agents spend tokens rediscovering
commands, envs (`flits` / `uv` / conda), input roots, and approval steps.

## Non-goals

- Do **not** use an LLM to draw or restyle figures.
- Do **not** replace SciencePlots producers or the hash-bound
  `figure_review.py` gate.
- Do **not** put PNGs in `docs/rse/specs/` (markdown-only).

## Architecture

```text
figures/catalog.yaml          ← single declarative source of truth
        │
        ├─► AxFlow (axllm)    ← typed DAG: deps → run → hash → optional review batch
        │         │
        │         └─► existing producers (subprocess; flits / uv as declared)
        │
        └─► AxAgent + skill   ← agent entry: "regen fig:X" / "list stale figures"
                              consults catalog; never opens plot scripts by default
```

| Layer | Role |
|-------|------|
| **Catalog** | Per-figure: id, tex label, producer argv, env, inputs, outputs, depends_on, approval_slot, clone_ok |
| **AxFlow** | Deterministic orchestration of catalog nodes (parallel where safe) |
| **AxAgent** | Thin LLM layer for discovery/QA wording only; tools call the flow |
| **Producers** | Unchanged Python scripts |
| **Approval** | Existing `figure_review` slots for protected paths |

### Catalog schema (sketch)

```yaml
figures:
  - id: dm_host_posteriors
    tex: fig:dm_host_posteriors
    manuscript: true
    producer:
      argv: ["conda", "run", "-n", "flits", "python", "scripts/dm_budget_uncertainty.py"]
      cwd: .
    inputs:
      - analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv
      # … budget json, census as needed
    outputs:
      - figures/dm_host_posteriors.pdf
    depends_on: []
    approval_slot: null
    clone_ok: true

  - id: clusters_icm
    tex: fig:clusters_icm
    manuscript: true
    producer:
      argv: ["uv", "run", "python", "galaxies/v2_0/systems_figures.py", "--out-dir", "../figures"]
      cwd: pipeline
    depends_on: [sightline_budget]   # explicit edge (today undeclared)
    outputs:
      - figures/clusters_icm.pdf
    approval_slot: null
    clone_ok: true

  - id: fig1_gallery
    tex: fig:codetection-data-grid
    manuscript: true
    producer:
      argv: ["python", "scripts/plot_codetection_data_grid.py", "--out", "candidates/fig1/"]
      cwd: .
    inputs:
      - data_root: ~/Data/Faber2026/dsa110/DSA_bursts
      - analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv
    outputs:
      - figures/codetection_data_grid.pdf   # after promote
    approval_slot: fig1-gallery
    clone_ok: false   # needs external waterfalls
```

Seed the catalog from `repro_manifest.csv` rows with `type=figure` and
`embedded_in_manuscript=yes`, plus `figure_review/slots.json` approval_slot
links. Keep `repro_manifest.csv` generated or dual-written until CI migrates.

### AxFlow (deterministic)

```python
# figures/ax_flow.py  (sketch)
from axllm import flow

regen = (
    flow[dict]()
    .description("Manuscript figures", "Run catalog nodes; fail closed on missing inputs.")
    .n("load_catalog", "path:string -> nodes:json")
    .n("topo_sort", "nodes:json -> order:string[]")
    .n("run_node", "node_id:string, dry_run:boolean -> receipt:json")
    # wire: load → sort → for each id run_node (native loop / parallel fan-out)
    .r(lambda s: {"receipts": s.run_results})
)
```

Practical first cut: **AxFlow wraps a small Python runner** that already
implements topo-sort + subprocess + SHA-256 receipts. Ax signatures type the
I/O; GEPA later can optimize *agent* prompts, not plot code.

CLI:

```bash
python -m figures.ax_cli list
python -m figures.ax_cli regen --id dm_host_posteriors
python -m figures.ax_cli regen --manuscript   # all manuscript:true ∧ inputs present
python -m figures.ax_cli stale                # outputs older than inputs / missing
make figures                                  # → regen --manuscript
```

### AxAgent (agent-facing)

Skill body (loaded via `consult` / static `skills:`):

- Point at `figures/catalog.yaml` and the CLI above.
- Rule: **do not open producer source** unless the flow fails with a typed error.
- Tools: `list_figures`, `regen_figure`, `figure_status`, `open_approval_batch`
  (shell to CLI / `figure_review.py`).

Signature sketch:

```text
request:string -> action:class "list, regen, status, explain", figure_ids:string[], notes:string
```

---

## Live manuscript figure inventory (seed set)

| Catalog id | TeX | Producer | One-command today? | Approval |
|------------|-----|----------|--------------------|----------|
| `fig1_gallery` | `fig:codetection-data-grid` | `scripts/plot_codetection_data_grid.py` | needs `~/Data` waterfalls | `fig1-gallery` |
| `ne2025_mw` | `fig:ne2025_mw` | `scripts/plot_ne2025_mw_properties.py --nside 32` | `conda run -n flits …` | — |
| `sightline_halo_grid` | `fig:sightline_halo_grid` | `pipeline/.../sightline_halo_grid.py` | `uv run` in pipeline | — |
| `toa_offset_decomposition` | `fig:toa-offset-decomposition` | `scripts/plot_toa_offset_decomposition.py` | yes | — |
| `assoc_cards_grid` | `fig:assoc-cards-grid` | `pipeline/.../plot_association_cards.py` | yes | — |
| `clusters_icm` | `fig:clusters_icm` | `systems_figures.py` after `sightline_budget` | 2-step; declare dep | — |
| `dm_host_posteriors` | `fig:dm_host_posteriors` | `scripts/dm_budget_uncertainty.py` | `flits` | — |

Placeholders / suppressed (catalog `manuscript: false` until promoted):
association summary, joint scint summary, jointmodel / DSA ACF families.

---

## Phased delivery

1. **Catalog** — `figures/catalog.yaml` for the seven live figures; validate
   against TeX `\includegraphics` set.
2. **Runner CLI** — topo-sort, env/argv from catalog, input existence checks,
   output SHA receipts under `figures/.receipts/`.
3. **`make figures`** — manuscript subset.
4. **AxFlow + AxAgent thin wrap** — `axllm` package in repo (`figures/ax/`);
   skill for agents.
5. **Wire approval** — nodes with `approval_slot` emit to candidate root +
   print `figure_review.py new-batch` command (never silent promote).
6. **Migrate** — generate `repro_manifest` figure rows from catalog; retire
   duplicate prose in wishlist where superseded.

## Success criteria

- `make figures` regenerates every `manuscript: true` figure whose inputs exist,
  without opening producer source.
- An agent with only the Ax skill + catalog can answer “how do I remake Fig. 1?”
  in one tool call.
- Protected slots still require owner `decide` / `promote`.
- Missing external data fails with a named catalog error, not a stack trace hunt.

## Open choice (default locked)

**Python `axllm`** in-repo under `figures/ax/` — matches producer language and
conda/`uv` runners. Revisit TypeScript only if we want a shared Node agent host.
