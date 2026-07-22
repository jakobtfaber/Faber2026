# Handoff: dsa110-FLITS pipeline commits (table emitters → Lorentzian refresh), plus live-lane repo state

---
**Date:** 2026-07-08 22:49 PDT
**Author:** AI Assistant
**Status:** Handoff — my pipeline lane is complete, verified, and pushed. **Two `claude` sessions are sharing one working tree**; the repo is mid-flight in another lane.
**Branch:** `Faber2026` on `main` at `4a00aa0` (behind `origin/main` `64158aa` by 4, ahead by 1) *(note: a later rebase at 23:01 replayed `4a00aa0` to `681cfe2`, same content; `4a00aa0` is now reachable only via `backup/main-pre-rebase-20260708`. Its content has since landed on `main` via PR #46 (squash `f7fcbb2`), with PR #51 correcting a stale hazard note.)*
**Commit:** pipeline `agent/sightline-halo-grid-figure`, my last commit `e223b90`; **branch tip is now `f9e1c24`** (not mine)

---

## Read this first

This handoff overlaps with **`handoff-2026-07-08-18-42-submodule-roundtrip-figure-refresh.md`** (untracked), which another
concurrently-running agent wrote about the *same* pipeline round-trip and which already cites my SHAs
(`386e886`, `1e2c507`, `5258aa7`, `e223b90`, `f9e1c24`). Read it before acting so you do not redo its work.

This document is deliberately scoped to what only *this* session can attest to: the per-commit verification evidence,
the concurrency incident that silently dropped a commit, and a correction to two claims I made earlier in the session.
Everything I describe about the *other* lane is **observed, not verified** — it is labelled as such throughout.

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Commit table-emitter feature (7 files) | ✅ Complete | `386e886`, pushed. Prior session. |
| Commit A — association cards: FLITS style + derived manuscript dir | ✅ Complete | `ae67f4f` |
| Commit B — Lorentzian fits: mathtext/PDF fonts, `--band`, regenerate 26 figures | ✅ Complete | `1e2c507` |
| Commit C — resync `uv.lock` to `requires-python>=3.12` | ✅ Complete | `5258aa7` |
| Commit D — refit-2026-07-07 configs+scripts, scint data-products handoff | ✅ Complete | `a3d3dc4` |
| Follow-up — rename per-burst results to band-prefixed names | ✅ Complete | `e223b90`, 12 git-detected renames |
| Bump `Faber2026` submodule gitlink | 📋 **Blocked/pending** | gitlink still records `386e886`; tip is `f9e1c24` |
| Reconcile two live agents on one worktree | 📋 **Open — needs a human** | See "Known-broken" |
| Harmonic-mask edit to `run_dsa_lorentzian_fits.py` | 🔄 In progress — **other lane, not mine** | Uncommitted, +127/−4 |

**Current Workflow Phase:** Validate (my lane is implemented and verified; what remains is repo/lane reconciliation)

## Workflow Artifacts

**Handoff documents (both untracked, written by the other live agent):**
- [handoff-2026-07-08-18-42-submodule-roundtrip-figure-refresh.md](../handoff/handoff-2026-07-08-18-42-submodule-roundtrip-figure-refresh.md) — the other lane's account of this same submodule round-trip and figure refresh. **Overlaps this document.**
- [handoff-2026-07-08-18-12-b7-cgm-census-resolved.md](../handoff/handoff-2026-07-08-18-12-b7-cgm-census-resolved.md) — B7 / CGM-intersection census. Unrelated lane.

**Related prior artifacts (tracked):**
- [validation-sightline-halo-grid.md](../validation/validation-sightline-halo-grid.md) — validation for the branch this work sits on.
- [handoff-2026-07-05-23-24-flits-130-harmonic-mask-merge.md](../handoff/handoff-2026-07-05-23-24-flits-130-harmonic-mask-merge.md) and [validation-harmonic-mask-chime-sweep.md](../validation/validation-harmonic-mask-chime-sweep.md) — prior art for the harmonic mask the other lane is now porting into the fresh-fit driver.
- [handoff-2026-07-08-07-26-figure-resolution-font-standardization.md](../handoff/handoff-2026-07-08-07-26-figure-resolution-font-standardization.md) — the font-standardization lane that Commit B continues.

## Critical References

- `docs/rse/specs/handoff/handoff-2026-07-08-18-42-submodule-roundtrip-figure-refresh.md` — the other agent's overlapping handoff. Read before touching the submodule pointer.
- `pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py` — carries **both** my committed change (`1e2c507`) *and* the other lane's uncommitted harmonic-mask edit. Any work here collides.
- `pipeline/CLAUDE.md` — documents the Stop gates and the **"one agent per git worktree; never run two live agents in the main checkout"** rule that the current setup is violating.

## Recent Changes

All in the `dsa110-FLITS` submodule (`git@github.com:jakobtfaber/dsa110-FLITS.git`), branch `agent/sightline-halo-grid-figure`.

**`ae67f4f` — association cards**
- `crossmatching/plot_association_cards.py:17-22` — replaced `plt.style.use("default")` with `from flits.plotting import use_flits_style` + `use_flits_style()`.
- `crossmatching/plot_association_cards.py:50` — `DEFAULT_MANUSCRIPT_OUTDIR = ROOT.parent / "figures" / "association_cards"`, replacing a hardcoded `/Users/.../overleaf/Faber2026/...` path that pointed at the Overleaf **sync target** (which lags `main`).
- `crossmatching/plot_association_cards.py:286-296` — new `--manuscript-dir` and `--no-manuscript-copy` flags; `:309-321` guards the copy.

**`1e2c507` — DSA Lorentzian fits + 26 regenerated figures**
- `analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py:411-421, 693-703` — `mathtext.fontset="stix"`, `pdf.fonttype=42`.
- `…:617-619, 892-894` — emit `.pdf` beside `.png`/`.svg` (PDFs are gitignored at `.gitignore:108`).
- `…:1253-1259` — new `--band dsa|chime`.
- `…:1286` — `config_path = Path("scintillation/configs/bursts")/f"{burst}_{args.band}.yaml"` — **relative to CWD**.
- `…:911, 1043` — `stem.removesuffix("_dsa")` → `stem.split("_")[0]`.

**`5258aa7`** — `uv.lock`: `requires-python` `>=3.10` → `>=3.12`, collapsing per-Python duplicate pins (116 → 108 packages).

**`a3d3dc4`** — added `analysis/scattering-refit-2026-06/refit-2026-07-07/{configs/*.yaml (8), scripts/*.py (4)}` and `scintillation/HANDOFF_SCINT_DATA_PRODUCTS.md`.

**`e223b90`** — `results/{burst}_lorentzian_fits.json` → `{burst}_dsa_lorentzian_fits.json` (12 files, git-detected renames at 89–98% similarity) + regenerated top-level `dsa_lorentzian_fits.json`.

**Not mine, on the same branch:** `e0039c6` (committed `exports/*.tex` as emitter-parity regression fixtures, 17:36) and `f9e1c24` (scint handoff `DATA_PROVENANCE.md` mark-complete, 18:28).

## Reproducibility & Data State

- **Seeds:** none set explicitly. The Lorentzian ACF fits are deterministic least-squares + BIC selection; re-runs are reproducible for every *selected* fit. See the degeneracy caveat under Learnings.
- **Environment:** conda env `flits` (the repo's canonical env); the run above executed under `py312` / Python 3.12.13. Lockfile `pipeline/uv.lock`, `requires-python>=3.12`, 108 packages, `uv lock --check` exit 0.
- **Data:** `FLITS_ROOT` defaults to `~/Data/Faber2026/dsa110`; `scintillation/data/*.npz`, 36 files present. 12 `*_dsa.yaml` burst configs.
- **Partial results / checkpoints:** none. `results/cache/` was **not** created by the re-run.
- **In-flight jobs:** none of mine. The other lane has an uncommitted working-tree edit (below), not a running job.

**To reproduce Commit B's figures — run from the *repo root*, not the analysis directory:**
```bash
cd <…>/Faber2026/pipeline
python analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py
```

## Verification State / Known-Broken

**Verified by this session (evidence, not assertion):**
- Emitter tests: `pytest test_budget_table_emitter.py test_foreground_table_emitter.py -q` → `9 passed`, **exit 0**.
- `plot_association_cards.py`: `ast.parse` exit 0, *and* the module was actually imported so `use_flits_style()` executed — proving the post-edit autoformatter did not strip the new import.
- `uv lock --check` → `Resolved 108 packages`, **exit 0**.
- Fit re-run → **exit 0**, 12/12 bursts, no traceback.
- **Fit results did not change where it matters.** `dsa_lorentzian_components.csv` and `DSA_LORENTZIAN_FITS.md` are byte-identical pre/post. A structural deep-diff of `dsa_lorentzian_fits.json` found 79 numeric diffs, **all inside `all_fit_summaries[2]`** (the BIC-rejected 3-component candidate) and **zero** in any selected fit. Same for each of the 12 per-burst renames.
- **Figures visually reviewed**, not just regenerated: `dsa_lorentzian_summary.png` renders γ correctly in the axis label and the `γ ∝ ν⁴` legend — the exact glyph that was mapping to U+00B0.
- **Nothing reads the renamed-away files.** Grep across both repos, run with a positive control to prove the search executed.
- The 14 modified `Faber2026/figures/**.pdf` are **byte-identical** to my regenerated pipeline PDFs (spot-checked `casey`, `zach`) — the round-trip already happened.

**Known-broken / unresolved:**

1. **Two live `claude --dangerously-skip-permissions` sessions share the `Faber2026/pipeline` working tree.** PIDs `20316` and `58357` (mine was `21369`); `lane-liveness` reports `verdict: "live"` on `Faber2026`. This violates `pipeline/CLAUDE.md`'s one-agent-per-worktree rule. **It already caused a real failure**: my first Commit-A attempt died on `index.lock` while the other session committed `e0039c6`, and both my `git add` and `git commit` were silently dropped. Only one worktree holds this branch, so the two sessions share one index. **This needs a human to arbitrate before more commits land.**

2. **The `[entire]` git hook is broken and dangerously noisy.** On every `add`/`commit`/`push` in the pipeline it tries to push `entire/checkpoints/v1` to remotes literally named `0`, `1`, `preparing`, `prepared`, `committed`, `aborted`, and once to a `.git/modules/pipeline/COMMIT_EDITMSG` path — emitting `fatal: Could not read from remote repository` each time. It is **non-fatal** (exit status unaffected), but it looks exactly like a failed push. **Always verify pushes with `git ls-remote`, never with push output.** Note `core.hooksPath` is `~/.git-hooks-global`, so the `.githooks/post-commit.pre-entire` documented in `pipeline/CLAUDE.md` is **not running** — `docs/entire-tracing-checkpoints.md` is not being appended, contrary to that doc.

3. **`Faber2026` submodule gitlink is stale**: records `386e886`, tip is `f9e1c24`. Five+ commits behind.

4. **`Faber2026` `main` is behind `origin/main`** by 4, ahead by 1 (`4a00aa0` vs `64158aa`) *(later rebased to `681cfe2`, same content; `4a00aa0` now lives only on `backup/main-pre-rebase-20260708`. Its content has since landed on `main` via PR #46 (squash `f7fcbb2`), with PR #51 correcting a stale hazard note.)*. The other lane's handoff cites yet another origin SHA (`700f231`) — the remote is moving fast.

5. **Uncommitted, not mine, in the pipeline worktree** *(observed, unverified)*: `run_dsa_lorentzian_fits.py`, +127/−4, adding `_harmonic_keep_mask()` — a de-comb for the CHIME upchannelization ripple (400 MHz / 1024 = 0.390625 MHz). It is **opt-in per config**: all 12 `*_chime.yaml` set `harmonic_mask`, **no** `*_dsa.yaml` does. So it does **not** invalidate the DSA figures in `1e2c507`. I did not run, test, or review it.

6. **Uncommitted in `Faber2026`** *(mostly not mine)*: 14 modified figure PDFs/PNGs, `docs/rse/protocols/journal.jsonl`, `docs/rse/control/board/readiness.html`, ` M pipeline` (the stale gitlink), untracked `scripts/__pycache__/`, and the two untracked handoffs above. **This document is also untracked, by request.**

7. **Unidentified provenance:** I never determined *which* session produced `e0039c6`, only that it was a real writer (author == committer, no auto-commit hook on the active `hooksPath`).

## Learnings

- **`git commit -- <paths>` (`--only`) was mandatory here.** `crossmatching/plot_association_cards.py` was `MM` — it had a *staged* hunk in the index. A plain `git add <files> && git commit` would have swept that unrelated staged change into the emitter commit. Check `git status` for `MM` before any scoped commit in this repo.
- **`run_dsa_lorentzian_fits.py` must run from the repo root.** `main()` resolves `Path("scintillation/configs/bursts")` relative to CWD (`:1286`). Running it from inside its own analysis directory finds zero configs.
- **The `--band` rename does *not* touch figures.** Per-burst figures are `{burst}_{band}_acf_lorentzian_fits.*`, which at `band="dsa"` reproduces the tracked names exactly, and the summary name is hardcoded. The orphans were the per-burst **results JSONs**. Don't assume the rename surface from the commit message.
- **The 3-component candidate fits are degenerate.** Their `m_err`/`dnu_err` are ~1e8–1e9 (unconstrained), and re-runs permute component labels — two `m` values swapped `0.677 ↔ 0.853`. When checking reproducibility of this analysis, **compare selected fits, `components.csv`, and `DSA_LORENTZIAN_FITS.md`** — never raw equality of `dsa_lorentzian_fits.json`, which will always differ.
- **The `uv.lock` diff looks alarming and is not.** It shows `numpy`/`scipy`/`astropy` entries disappearing and −854 lines. The cause is `requires-python` catching up to `pyproject.toml`'s already-declared `>=3.12`, collapsing the Python-3.10-specific duplicate pins. **The committed lock was the stale artifact**, not the regenerated one.
- **`exports/*.tex` regenerate byte-identically from the emitters** (verified by regenerating in-process). That property is what makes them usable as the parity fixtures `e0039c6` committed them as.
- **`Faber2026/figures/` is the manuscript's figure home; `~/Developer/overleaf/Faber2026` is a downstream sync target that lags `main`.** Scripts that write figures should derive the path from the repo root, never hardcode the Overleaf copy (this is what `ae67f4f` fixed).

## Action Items & Next Steps

1. [ ] **Arbitrate the concurrent sessions first.** Identify PIDs `20316` / `58357`, stop the duplicate, and give each remaining agent its own worktree per `pipeline/CLAUDE.md`. Nothing below is safe while two agents share one index.
2. [ ] Reconcile `Faber2026` `main`: it is behind `origin/main` by 4 and ahead by 1. Fast-forward or merge before bumping anything.
3. [ ] **Bump the submodule gitlink** from `386e886` to the *then-current* pipeline tip — re-check with `git ls-remote`, it was `f9e1c24` at 22:49 and has moved twice already today.
4. [ ] Decide the fate of the three untracked handoffs in `docs/rse/specs/` (18-12, 18-42, and this one) — commit or discard.
5. [ ] Other lane: finish, test, and commit the harmonic-mask edit to `run_dsa_lorentzian_fits.py`, then regenerate the **CHIME** figures (`--band chime`). DSA figures need no re-run.
6. [ ] Fix or disable the `[entire]` hook — it fabricates `fatal:` push errors on every git write.
7. [ ] Reconcile `pipeline/CLAUDE.md`'s claim that `.githooks/post-commit.pre-entire` appends `docs/entire-tracing-checkpoints.md`; with `core.hooksPath` set globally, it does not run.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` — my lane is implemented and its evidence is recorded above; what remains is verifying the submodule round-trip end-to-end (gitlink → manuscript figures → build) and validating the other lane's harmonic-mask change before it lands. If instead you pick up the harmonic-mask work directly, use `ai-research-workflows:implementing-plans`.

## Other Notes

- **Two corrections to claims I made earlier in this session, recorded so they don't propagate:**
  1. I described the removals in `e223b90` as "12 orphans" while the glob I quoted matched **13** files — it swept in `dsa_lorentzian_fits.json`, which the script *does* still write (`f"{band}_lorentzian_fits.json"` at `band="dsa"` reproduces the same name). It was never an orphan; it was committed as a modification.
  2. The original hand-off I was given claimed the standalone clone at `repos/github.com/jakobtfaber/dsa110-FLITS` and `Faber2026/pipeline` were interchangeable views of one repo. **They are not** — separate git dirs, separate checkouts. The standalone clone sits on `main`, clean, and has never contained this branch. All work must happen in `Faber2026/pipeline`.
- Nothing was deleted, force-pushed, or rebased in this session. The 12 "deletions" in `e223b90` are git-recorded renames; content is preserved in history regardless.
- Every push in this session was verified with `git ls-remote`, not push output, because of the `[entire]` hook (item 2 above).

---

**Handoff created by AI Assistant on 2026-07-08 22:49 PDT**
