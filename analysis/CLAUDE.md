# CLAUDE.md — Faber2026 manuscript

AASTeX631 manuscript for the CHIME/FRB–DSA-110 co-detection dispersion- and
scattering-budget paper. Layout, build, and repo conventions: `README.md`.
Pipeline-pin semantics: `PIPELINE.md`.

**Before editing any prose, read `CONTEXT.md`** — it is the domain-language
contract (β co-model, provisional-citable rows, the per-section sample rule,
energies trust boundary). Its "Avoid" lines are hard constraints on wording.

## Non-negotiables

- **`pipeline/` is a pinned submodule; detached HEAD is intentional.** Every
  number and figure in the tex must be reproducible from the pinned commit.
  Never check out a branch inside `pipeline/` or bump the pin casually; a pin
  bump is a deliberate `build:` commit made only after the corresponding
  pipeline work has merged upstream. `git submodule update` realigns a drifted
  checkout.
- **Pushing `main` publishes.** `.github/workflows/overleaf-sync.yml` mirrors
  every push to `main` into the Overleaf project (one-way; GitHub is the source
  of truth). Treat a push to `main` as outward-facing.
- **Figures are pipeline exports.** Never hand-edit files under `figures/`;
  regenerate in `pipeline/` and re-export. Layout prototypes go in
  `figures/prototypes/` (gitignored).
- **Root `*_table.tex` files are pipeline-derived.** Check provenance before
  hand-editing table values; prose edits to captions live in `sections/`.

## Build & verify

`make` (latexmk, mirrors Overleaf) · `make watch` · `make clean`. Build
artifacts are gitignored. A tex change is not done until `make` exits 0 with no
new warnings in `main.log` (undefined references, citations, overfull boxes).

## Pipeline code — which copy runs

Two dsa110-FLITS clones exist on this machine: the pinned submodule here and
the canonical clone at `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS/`.
The `flits` conda env editable-installs the **canonical clone**, so Python run
from outside a checkout imports that clone's (possibly in-flight) code; run from
inside `pipeline/` the cwd shadows it and you get the pinned code. When
validating pinned behavior, run from inside `pipeline/`; when in doubt, print
`module.__file__` first. Pipeline commands: `conda run -n flits …`.

## Cross-agent notes

- Codex config lives in `.codex/` (entire-tracing hooks, `entire-search` agent);
  keep Claude and Codex hook surfaces in parity when changing either.
- The pipeline repo has its own agent setup (`pipeline/.claude/`,
  `pipeline/.cursor/rules/`); runtime-authoritative fit-validation thresholds
  live there, in the `fit-validation` agent and `fit-verify.js` workflow — not
  in this repo.
