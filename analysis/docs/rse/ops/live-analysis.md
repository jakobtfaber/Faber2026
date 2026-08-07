# Live analysis operator guide

Where to do live analysis work, what a task declares before it starts, where
exploratory notebooks live, and how a result becomes a manuscript claim.
Structural background — which repository owns what — is in
[`repository-map.md`](repository-map.md). This page covers the working loop.

## Two workspaces

Analysis and manuscript integration are separate workspaces. Open the one that
matches the work; do not run both at once.

**Workspace A — the analysis laboratory.** The `Faber2026-analysis` checkout is
primary and is the only repository you write to. The parent `Faber2026`
checkout is read-only reference: consult `main.tex`, `sections/`, and the
installed figures to see what a result would have to support, but do not edit
them. Work that belongs here: inspecting data, building and fitting models,
statistical experiments, diagnostic figures, scientific validation, and
reviewing results.

**Workspace B — manuscript integration.** The parent `Faber2026` checkout is
primary and is the repository you write to; `analysis/` sits at the accepted
commit — the commit whose result you are integrating, not whatever happens to
be checked out — and you do not develop in it here. Work that belongs in this
workspace: advancing the `analysis` gitlink, regenerating approved tables and
figures, editing manuscript claims, compiling, and cross-repository
verification.

The rule that keeps the two honest:

- A manuscript edit must not quietly advance the analysis pin. Advancing the
  pin is its own change, with its own reason and its own pull request.
- An analysis change must not immediately rewrite manuscript conclusions. A new
  number is a candidate until it has cleared the promotion chain below.

## The five-line task header

Every task — yours or an agent's — states its boundary before the first
command, in this form:

```text
Scientific phase: <exploration | scientific validation | publication>
Objective:      <the result being pursued>
May change:     <exact paths>
Must not change:<data, accepted results, manuscript, other campaigns>
Done when:      <the condition that ends the phase>
```

Worked example:

```text
Scientific phase: exploration
Objective:      see whether a second scattering screen improves the casey
                dual-band residuals relative to the accepted single-screen fit
May change:     ~/Data/Faber2026/workbench/casey-two-screen/
Must not change:config/bursts.yaml, the accepted casey fit artifacts,
                docs/rse/control/, the parent Faber2026 checkout
Done when:      one- and two-screen residual panels exist side by side for both
                bands and the comparison is written down
```

## Scientific phase ladder

exploration → scientific validation → publication.

- **Exploration** — obtain and inspect the scientific result, doing only the
  checks needed to interpret it and distinguish it from an execution artifact.
- **Scientific validation** — test the result's assumptions, sensitivity,
  convergence, and model adequacy.
- **Publication** — produce immutable provenance, independent reruns, final
  receipts, and repository integration.

Two rules
apply at the bench: a phase never changes implicitly — a task that starts in
exploration stays there until its header is rewritten — and promotion to
publication is an explicit owner decision, never the momentum of a session
that is going well.

## Where notebooks live

Exploratory notebooks live under `~/Data/Faber2026/workbench/<slug>/`, with
`scratch/` for intermediates and `exports/` for figures and tables worth
keeping. New exploratory notebooks are never tracked in Git. The notebooks
already tracked in this repository predate this policy: they are grandfathered
in place, are not part of the admitted live-analysis surface, and no new
tracked notebook joins them (the allowlist in
`config/grandfathered-notebooks.txt` is enforced by
`tests/test_notebook_policy.py`). The kernel and environment are
described in [`jupyter-surface.md`](jupyter-surface.md).

A notebook is visually persuasive, which is exactly why it must never become an
accidental authority. The notebook is a mutable view for exploration and
inspection. Maintained code, fixed inputs, tests, result records, and review
evidence establish the result. The manuscript states only the accepted result
selected by the pinned analysis commit.

A notebook may load input data products, import maintained modules, launch a
bounded exploratory fit, load completed outputs from a finished run, display
dynamic spectra and model-and-residual panels and posterior summaries, compare
parameterizations, and hold your own annotations.

A notebook must not be the only implementation of any of the following:

- a likelihood;
- a fit model;
- a calibration;
- an uncertainty calculation;
- a manuscript figure;
- a catalog query;
- an acceptance criterion.

Those live in maintained modules with tests. When a cell has quietly become the
definition of one of them, move it into the repository before the result goes
any further.

## How a result reaches the manuscript

The promotion chain, in order. Every step is a gate, not a formality.

1. Local notebook observation.
2. Maintained analysis code, with tests, in this repository.
3. A subject-local study or result packet.
4. Scientific validation against
   [`verification-protocol.md`](../protocols/verification-protocol.md).
5. Independent read-only review, by someone or something that did not write
   the result.
6. Independent reproduction where the claim warrants it.
7. A trusted entry in the
   [results registry](../control/results-registry.toml).
8. **Merge the `Faber2026-analysis` pull request.**
9. **A separate parent pull request advancing the `analysis` gitlink.**
10. Regenerate the approved figure or table at the new pin.
11. The manuscript prose change that states the claim.
12. `make check-provenance`, `make test-science`, and `make` from the parent.

Stated plainly, so none of it is inferred:

- Exploratory outputs do not enter the results registry.
- A file existing does not make it trusted.
- A visually approved figure does not clear the scientific claim it carries.
- A trusted analysis result does not automatically enter the manuscript; steps
  8 through 12 are separate work with their own review.

## Correction — what `make observations|fit|verify|review` really is

These four targets read like the project's general analysis entry point. They
are not. What they actually are:

- They are `.PHONY` wrappers around
  `scripts/run_dualband_burst_model.py --stage <stage>`, invoked as
  `make observations|fit|verify|review EVENT=<event>`.
- They drive the **synthetic dual-band burst-model vertical slice**
  (`workflows/dualband_burst_model.py`, a hash-bound synthetic slice) — not a
  general analysis interface, and not a way to fit a real burst.
- They are prerequisite-chained: `review: verify`, `verify: fit`,
  `fit: observations`. Asking for `review` runs all four in order.
- They run in a **separate virtual environment**, `analysis/.venv-dualband`,
  selected through `UV_PROJECT_ENVIRONMENT` and invoked as
  `uv run --locked --no-sync --group dualband`. This is not the environment
  the rest of the repository's targets and scripts use.
- Only `observations` guards `EVENT`; `fit`, `verify`, and `review` inherit the
  guard through the chain, so a missing `EVENT` fails at the first link rather
  than where you typed it.

Real analysis runs use the producer named in the figure catalog, the repro
manifest, or the subject's own documentation. Start from
[`repository-map.md`](repository-map.md) to find it, and from
[`knowledge-base.md`](knowledge-base.md) to search for prior work on the same
question.
