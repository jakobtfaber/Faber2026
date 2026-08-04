# AGENTS.md

Agent brief for the **Faber2026** manuscript repo.

## Response style (required for all responses in this repo)

- Be extremely concise. Sacrifice grammar for the sake of concision;
  telegraphic fragments are fine.
- No shorthand or unnecessary jargon. Write the plain term instead of an
  acronym or project codename; expand any unavoidable acronym at first use.
  Explain domain statistics (e.g. confidence bounds, order statistics) in
  plain English when they appear.

## Exploratory fits

Report scientific results and diagnostic figures before provenance packaging.
Keep audit evidence available but out of the foreground. A publication-only
provenance gap does not block an exploratory fit unless it could change the
scientific interpretation.

## Orient with the knowledge base before grepping

Before exploratory `grep`/`glob`/file-reading to reconstruct context, run
`python3 analysis/scripts/kb search "<topic>"` — hybrid keyword+semantic search over
manuscript docs, wayfinder tickets, git history, analysis code, retired FLITS
provenance, configs, and cited references, with ranked
cross-source results. Filter with `--source tickets|docs|git|code|config|refs`.
Refresh after changes with `make kb-index` (incremental, seconds when
embeddings are current). See [`analysis/docs/rse/ops/knowledge-base.md`](analysis/docs/rse/ops/knowledge-base.md).
Fall back to grep for exhaustive sweeps (every call site, every match).

## Owner queue walkthrough

On "walk me through my queue": follow
[`analysis/docs/rse/control/owner-queue-ritual.md`](analysis/docs/rse/control/owner-queue-ritual.md) —
regenerate via `python3 analysis/scripts/owner_queue.py`, verify heuristics, present
one item at a time with its evidence, record every decision at its source.
Never scheduled; owner-triggered only. Science/domain context and the
trust-reset state lives in [`analysis/CONTEXT.md`](analysis/CONTEXT.md); this
file carries operational standing instructions only.

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
  Standing exception (owner, 2026-07-27): a merged-PR head branch may be
  deleted by default once patch equivalence with the base is proven
  (`git cherry`/`range-diff` for squash merges); `overleaf-*` sync branches
  are never deleted.
- **The `analysis/` submodule pin is deliberate** — do not bump the gitlink as
  a side effect of a manuscript change; that is its own reviewed step.
- **Land by default** (owner, 2026-07-27): a mechanical, narrowly scoped,
  cheaply reversible pull request (revert restores the previous state; no
  scientific judgment, no data or pin change) merges immediately — do not
  leave it open for review.
- **Queue quietly** (owner, 2026-07-27): owner-facing requests go into a
  queue source (ticket, figure-review batch, board line, pull request), not
  into chat as standing asks; the reply states only how many items were
  queued. Low-stakes items may carry a stated default and deadline, after
  which the default applies.

> Note: a repo file records the *preference* so future sessions inherit it. The
> platform's enforced no-approval **gate** is understood to live in the agent's
> Managed-Agent `permission_policy` (should be set to `always_allow`) plus the
> per-session GitHub token — control-plane config, not writable from inside a
> session. These field names are unverified against the live Managed-Agents
> schema (confirm before relying on them). See the handoff in `analysis/docs/rse/specs/`
> if the approval prompt reappears.

## Learned User Preferences

- Prefer pathspec-only commits; never sweep unrelated dirty-lane or submodule-pointer changes into a manuscript/figure task commit.
- Manuscript figures should omit plot titles (captions carry the title) and match existing manuscript figure style (SciencePlots / shared formatting), not ad-hoc styling.
- Prefer math notation on figure axes/labels, with prose explanation in the caption or body text rather than spelled-out descriptive axis text alone.
- Keep claim wording tight on science readiness and open gates — do not overstate what is certified vs provisional.
- When reporting science or manuscript status, answer whether work is science-ready and vetted and whether it is in the manuscript draft (plus a one-line section status); do not lead with campaign progress metrics.
- Prefer plain verification vocabulary over L#/Tier codes: data chain = Raw Data → Input Data Products → Measurements and Fits → Analyses and Interpretations → In-Manuscript Claims; checks = Equation / Calculation / Model/Fit / Reference / No-Context Review.
- Owner spot-check is required before closing raw-layer certification; agents must not mark that layer trusted without owner sign-off.
- Prefer separating analysis results from reusable fitting code, funneling products into a clear navigable results inventory; put analysis/diagnostic review under `analysis/docs/analysis/` as MkDocs/HTML prose plus SVG plot panels — not PNG assets or matplotlib text sidebars.
- For heavy parallel work, orchestrate via headless Codex/Claude CLI so ChatGPT and Claude Max subscriptions are used, then guide and merge locally; route author Running Notes sorting through headless Claude Code (`claude -p`), not a Cursor agent.
- When scrubbing `analysis/docs/`, prioritize accuracy and concision over historical record; prefer deleting obsolete or misleading material over archiving it.
- Structure in-manuscript figure production as a declarative catalog/workflow (`analysis/figures/catalog.yaml` driving `analysis/scripts/figure_flow.py` / `make figures`) so regeneration does not require agents to rediscover plot scripts.
- For dual-band dispersion-measure fits: use band-specific on-pulse envelopes (owner eye-set is fine when automated widths under-cut); multi-component events span first through last component (not only the brightest); before DM-phase, center the burst with band-specific off-pulse padding and visually check crops on the dynamic spectra.

## Learned Workspace Facts

- The former separate Overleaf working copy at `~/Developer/overleaf/Faber2026` was retired 2026-07-25 and deleted 2026-07-26 (history bundled at `~/Data/Faber2026/preservation/Faber2026-overleaf-20260725/`); Overleaf now pulls from GitHub via its browser GitHub Sync integration. `AGENTS.md` and `CLAUDE.md` are tracked; `GEMINI.md` and `CODEX.md` are gitignored — `.olignore` keeps agent briefs out of Overleaf sync.
- Project data and provenance span jakob-mbp, iacobus, h17, CANFAR/arc, and Google Drive; treat machine inventory as part of provenance, not only “active data stores.”
- Session handoffs, science-gate plans, and RSE specs live under `analysis/docs/rse/specs/` as markdown-only workflow artifacts; PNGs and other binaries belong elsewhere (e.g. decks, figures, verify trees).
- Raw CHIME data means only the twelve singlebeam voltage `.h5` files on h17; intensity and upchannelized `.npy` products are derived, not raw.
- Dispersion measures are not frozen in those raw voltage `.h5` files; they are applied when dynamic-spectrum products are built, so derived CANFAR vs h17 arrays can disagree on dispersion measure without the raw archive being wrong.
- Dual-band codetection / dynamic-spectrum figures label the bands as CHIME/FRB and DSA-110; CHIME–DSA time alignment depends on measured ToA offsets (e.g. `geometric_delay_ms`), not arbitrary visual spacing.
- Author-facing manuscript pulse / Running Notes live as standalone local HTML under `analysis/docs/rse/ops/running-notes/` (also at `https://faber2026.jakobtfaber.com`; not a Cursor canvas).
- Oran does not get a dedicated in-manuscript figure; treat any doc that assigns one as a mistake to remove.
- Local burst products live under `~/Data/Faber2026/dsa110/` (DSA-110; Stokes-I cubes in `DSA_bursts/`) and `~/Data/Faber2026/chimefrb/` (CHIME/FRB; Stokes-I cubes in `CHIME_bursts/`); do not mix instruments across those trees or paper over layout drift with compatibility symlinks — fix referencing paths universally instead.
- Product dispersion measures in `_cntr_bpc.npy` filenames are per-band archival referral values and can differ between CHIME and DSA for the same event.
- Retained Mac worktrees and orphan clones need an explicit content disposition — land/integrate, superseded/obsolete, or preserve — with a receipt before retirement; subject-on-main alone does not prove superseded when unique patches remain.
- The parent manuscript pins one submodule: `analysis/` is the research-control repository, and it also houses all fitting code. Its lockfile no longer references FLITS; `dsa110-FLITS` is retired provenance and must not be imported at runtime.
