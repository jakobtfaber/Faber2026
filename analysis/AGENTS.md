# AGENTS.md

Agent brief for the **Faber2026-analysis** research-control repository.

## Repository boundary

- This repository is mounted at `Faber2026/analysis/`.
- The manuscript authority is the parent checkout (`../main.tex`, `../sections/`,
  generated root tables, and final `../figures/` assets).
- Reusable fitting and plotting code lives in `radio_pipeline/`; the former
  sibling pipeline and FLITS repositories are retired provenance only.
- Run analysis tools from this repository unless they explicitly require the
  parent pair; use `FABER2026_ROOT=..` or the provided Makefile targets then.
- Do not copy analysis/control material back into the manuscript repository.

## Response style (required for all responses in this repo)

- Be extremely concise. Sacrifice grammar for the sake of concision;
  telegraphic fragments are fine.
- No shorthand or unnecessary jargon. Write the plain term instead of an
  acronym or project codename; expand any unavoidable acronym at first use.
  Explain domain statistics (e.g. confidence bounds, order statistics) in
  plain English when they appear.

## Orient with the knowledge base before grepping

Before exploratory `grep`/`glob`/file-reading to reconstruct context, run
`python3 scripts/kb search "<topic>"` — hybrid keyword+semantic search over
manuscript docs, wayfinder tickets, parent and analysis git history, analysis
code, configs, and cited references, with ranked
cross-source results. Filter with `--source tickets|docs|git|code|config|refs`.
Refresh after changes with `make kb-index` (incremental, seconds when
embeddings are current). See
[`docs/rse/ops/knowledge-base.md`](docs/rse/ops/knowledge-base.md).
Fall back to grep for exhaustive sweeps (every call site, every match).

## Live analysis and the Jupyter surface

Interactive analysis follows
[`docs/rse/ops/live-analysis.md`](docs/rse/ops/live-analysis.md): which
workspace to open, which repository may be written, the five-line task header,
where exploratory notebooks live, and how an accepted result reaches the
manuscript.

The repository-owned Jupyter surface — environment and lock, kernel
specification, notebooks, data mounts, generated-output policy, bind address
and port, start/stop commands, owner, recovery procedure, and admission smoke
test — is defined in
[`docs/rse/ops/jupyter-surface.md`](docs/rse/ops/jupyter-surface.md), written
to the admission bar set by
[`authority-10-choose-operational-ownership.md`](docs/rse/wayfinder/tickets/authority-10-choose-operational-ownership.md).
Owner-ratified 2026-08-07 (admission ticket
`docs/rse/wayfinder/tickets/jupyter-surface-admission-2026-08-05.md`):
agents may start and stop a kernel for bounded local work under the
definition's own start, stop, and recovery instructions.

## Owner queue walkthrough

On "walk me through my queue": follow
[`docs/rse/control/owner-queue-ritual.md`](docs/rse/control/owner-queue-ritual.md) —
regenerate via `python3 scripts/owner_queue.py`, verify heuristics, present
one item at a time with its evidence, record every decision at its source.
Never scheduled; owner-triggered only. Science/domain context and the
trust-reset state lives in [`CONTEXT.md`](CONTEXT.md); this file carries
operational standing instructions only.

## Standing authorization — git push / PR (owner grant, 2026-07-08)

The repository owner has granted a **standing, cross-session authorization**: an
agent may **push branches and open/merge pull requests** on this repo (and the
owner's other configured repos) **without asking for per-action approval**.

Scope and guardrails — this authorization is not a licence to be careless:

- **One-way doors stay careful.** Before merging, confirm the branch is
  fast-forwardable (or the merge is intended) and scoped to the correct repo.
  Never force-push a branch that has concurrent writers.
- **Prefer the clean path.** Land figure/section updates via a focused branch +
  PR that mirrors existing precedent (e.g. the `ms/…` jointmodel-panel PRs),
  not a divergent-branch merge that drags in unrelated submodule-pointer bumps.
- **Never delete or rewrite shared history** (`push --force`, branch deletion on
  `main`, `reset --hard` on a shared ref) without an explicit, separate request.
- **The parent `analysis/` pin is deliberate** — update it only as a focused,
  reviewed manuscript integration step.

> Note: a repo file records the *preference* so future sessions inherit it. The
> platform's enforced no-approval **gate** is understood to live in the agent's
> Managed-Agent `permission_policy` (should be set to `always_allow`) plus the
> per-session GitHub token — control-plane config, not writable from inside a
> session. These field names are unverified against the live Managed-Agents
> schema (confirm before relying on them). See the handoff in `docs/rse/specs/`
> if the approval prompt reappears.

## Learned User Preferences

- Prefer pathspec-only commits; never sweep unrelated dirty-lane or submodule-pointer changes into a manuscript/figure task commit.
- Manuscript figures should omit plot titles (captions carry the title) and match existing manuscript figure style (SciencePlots / shared formatting), not ad-hoc styling.
- Prefer math notation on figure axes/labels, with prose explanation in the caption or body text rather than spelled-out descriptive axis text alone.
- Keep claim wording tight on science readiness and open gates — do not overstate what is certified vs provisional.
- When reporting science or manuscript status, answer whether work is science-ready and vetted and whether it is in the manuscript draft (plus a one-line section status); do not lead with campaign progress metrics.
- Prefer plain verification vocabulary over L#/Tier codes: data chain = Raw Data → Input Data Products → Measurements and Fits → Analyses and Interpretations → In-Manuscript Claims; checks = Equation / Calculation / Model/Fit / Reference / No-Context Review.
- Owner spot-check is required before closing raw-layer certification; agents must not mark that layer trusted without owner sign-off.
- Prefer separating analysis results from reusable fitting code inside this repository, funneling products into a clear navigable results inventory; put analysis/diagnostic review under `docs/analysis/` as MkDocs/HTML prose plus SVG plot panels — not PNG assets or matplotlib text sidebars.
- For heavy parallel work, orchestrate via headless Codex/Claude CLI so ChatGPT and Claude Max subscriptions are used, then guide and merge locally; route author Running Notes sorting through headless Claude Code (`claude -p`), not a Cursor agent.
- When scrubbing `docs/`, prioritize accuracy and concision over historical record; prefer deleting obsolete or misleading material over archiving it.
- Structure in-manuscript figure production as a declarative catalog/workflow (`figures/catalog.yaml` / ax) so regeneration does not require agents to rediscover plot scripts.
- For dual-band dispersion-measure fits: use band-specific on-pulse envelopes (owner eye-set is fine when automated widths under-cut); multi-component events span first through last component (not only the brightest); before DM-phase, center the burst with band-specific off-pulse padding and visually check crops on the dynamic spectra.

## Learned Workspace Facts

- The local Overleaf working copy is retired (2026-07-25); Overleaf pulls from GitHub in the browser. Land manuscript changes through the normal branch → PR flow in the canonical repos, and still respect Overleaf/GitHub merge order so prose sync does not revert git-only edits.
- Project data and provenance span jakob-mbp, h17, and CANFAR/arc; treat machine inventory as part of provenance, not only “active data stores.”
- Session handoffs, science-gate plans, and RSE specs live under `docs/rse/specs/` as markdown-only workflow artifacts; PNGs and other binaries belong elsewhere (e.g. decks, figures, verify trees).
- Raw data on h17 are twelve CHIME/FRB singlebeam voltage `.h5` files plus
  twelve DSA-110 Stokes-I `.fil` files; intensity cubes are derived input
  products (authority on h17; jakob-mbp copies under `~/Data/Faber2026/`),
  not raw. CANFAR is not the fit-input authority.
- Dispersion measures are not frozen in those raw voltage `.h5` files; they are applied when dynamic-spectrum products are built, so derived CANFAR vs h17 arrays can disagree on dispersion measure without the raw archive being wrong.
- Dual-band codetection / dynamic-spectrum figures label the bands as CHIME/FRB and DSA-110; CHIME–DSA time alignment depends on measured ToA offsets (e.g. `geometric_delay_ms`), not arbitrary visual spacing.
- Author-facing manuscript pulse / Running Notes live as standalone local HTML under `docs/rse/ops/running-notes/` (also at `https://faber2026.jakobtfaber.com`; not a Cursor canvas).
- Oran does not get a dedicated in-manuscript figure; treat any doc that assigns one as a mistake to remove.
- Local burst products live under `~/Data/Faber2026/dsa110/` (DSA-110; Stokes-I cubes in `DSA_bursts/`) and `~/Data/Faber2026/chimefrb/` (CHIME/FRB; Stokes-I cubes in `CHIME_bursts/`); do not mix instruments across those trees or paper over layout drift with compatibility symlinks — fix referencing paths universally instead.
- Product dispersion measures in `_cntr_bpc.npy` filenames are per-band archival referral values and can differ between CHIME and DSA for the same event.
