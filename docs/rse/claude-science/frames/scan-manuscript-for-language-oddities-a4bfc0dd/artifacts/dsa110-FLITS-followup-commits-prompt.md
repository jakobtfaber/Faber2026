# Task: four more commits in `dsa110-FLITS`, then report the new SHA(s)

Follow-up to the table-emitter commit you already made (`386e886`, pushed). The
author has now reviewed the remaining WIP and made decisions. Work in the
**submodule working tree**, same as last time:

```
/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline
```

Branch `agent/sightline-halo-grid-figure`, HEAD should be `386e886`.
**No force-push, no rebase, no deletions.** Remote: `origin` =
`https://github.com/jakobtfaber/dsa110-FLITS.git`.

> Reminder from last time: a broken repo hook spams `fatal: Could not read from
> remote repository` and tries to push to remotes named `0`/`1`/etc. It's
> non-fatal noise. **Verify every push with `git ls-remote origin
> refs/heads/agent/sightline-halo-grid-figure`, not the push output.**

## Step 0 — orient (report back)

```bash
cd /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline
git rev-parse --short HEAD                    # expect 386e886
git rev-parse --abbrev-ref HEAD               # expect agent/sightline-halo-grid-figure
git status -s
```
If HEAD ≠ `386e886`, **stop and report**.

---

## Commit A — `plot_association_cards.py`: keep BOTH the style fix and the path fix

This file is `MM`. The staged half adds `use_flits_style()`; the unstaged
(worktree) half **reverts that line back** to `plt.style.use("default")` AND
adds the good path-de-hardcoding + `--manuscript-dir`/`--no-manuscript-copy`
argparse changes. **The author's decision: keep both fixes.** So take the
worktree content (path fix) but restore `use_flits_style()`.

Concretely — in the worktree file, **line 17** currently reads:

```python
plt.style.use("default")
```

Replace that single line with this block (mirrors exactly what the staged half
of this same file already contains — that half was authored against this tree,
so `from flits.plotting import use_flits_style` is the intended import; I could
**not** verify it resolves from my environment (no matplotlib there), so run the
`ast.parse` check below and, if you can, an actual import in the repo's venv):

```python
from flits.plotting import use_flits_style

# Adopt the shared FLITS style (Computer Modern serif, cmr10) so these cards
# match every other manuscript figure and the paper body font; then re-pin the
# card-specific small sizes and TrueType embedding the standard doesn't set.
use_flits_style()
```

Leave **all** the other worktree changes in place (the `DEFAULT_MANUSCRIPT_OUTDIR
= ROOT.parent / "figures" / "association_cards"` derivation, the two new
argparse flags, and the `copy_to_manuscript` guarding).

Then sanity-check and commit **just this file**:

```bash
python -c "import ast; ast.parse(open('crossmatching/plot_association_cards.py').read()); print('parse OK')"
# optional but nice: python crossmatching/plot_association_cards.py --no-manuscript-copy  (should run without writing to the manuscript dir)

git add crossmatching/plot_association_cards.py
git commit -m "association cards: adopt shared FLITS style + derive manuscript dir from repo root

Keep the shared use_flits_style() (Computer Modern serif matching the paper
body) and replace the hardcoded Overleaf-sync output path
(/Users/.../overleaf/Faber2026/figures/association_cards, which lags main) with
DEFAULT_MANUSCRIPT_OUTDIR = ROOT.parent/figures/association_cards, resolved from
the file location so a fresh clone works. Add --manuscript-dir override and
--no-manuscript-copy for standalone submodule checkouts."
```

Confirm afterward: `git show --stat HEAD` lists exactly one file, and
`grep -n use_flits_style crossmatching/plot_association_cards.py` finds it.

---

## Commit B — `run_dsa_lorentzian_fits.py`: RE-RUN first so figures match, then commit script + figures together

The script has been edited (font/PDF fix: `mathtext.fontset="stix"`,
`pdf.fonttype=42`, emit `.pdf`; plus a `--band dsa|chime` generalization), but
the tracked figures are stale — the script is newer than the committed
`.png`/`.svg`. **Do not commit the script without regenerating**, or the tracked
figures won't match the code.

```bash
cd analysis/scintillation-dsa-lorentzian-2026-07-07
# regenerate all DSA-band figures with the current script (default band = dsa)
python run_dsa_lorentzian_fits.py            # adjust args if the script needs an input/config path — inspect --help first
cd -
git status -s analysis/scintillation-dsa-lorentzian-2026-07-07/
```

Then stage the script **and** the regenerated tracked figures (26 tracked files
live in `results/figures/`: 12 per-burst `.png` + 12 per-burst `.svg` + summary
`.png` + `.svg`; note `*.pdf` is gitignored at .gitignore line 108, so PDFs
won't and shouldn't be added):

```bash
git add analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py \
        analysis/scintillation-dsa-lorentzian-2026-07-07/results/figures/
git status -s   # confirm: script + only .png/.svg staged, no .pdf, no stragglers
git commit -m "DSA Lorentzian fits: fix mathtext/PDF fonts, add --band, regenerate figures

Use STIX mathtext + TrueType (pdf.fonttype=42) so the gamma glyph stops mapping
to U+00B0 and corrupting the PDF text layer; emit .pdf alongside png/svg. Add
--band dsa|chime. Per-burst output renames to {burst}_dsa_lorentzian_fits.* at
the default band. Regenerated all tracked figures to match the new code."
```

**Heads-up to flag if you hit it — orphan check (do NOT assume a specific
rename pattern).** The currently tracked per-burst figures are named
`{burst}_dsa_acf_lorentzian_fits.{png,svg}` (12 bursts × 2 = 24 files, plus
`dsa_lorentzian_summary.{png,svg}`) — I verified this against `git ls-files`.
The `--band` generalization *may* change the output basename, but I have not
confirmed what the new script actually writes. So after the re-run, compare the
new output filenames against the tracked set:

```bash
cd analysis/scintillation-dsa-lorentzian-2026-07-07/results/figures
echo "TRACKED:"; git ls-files . | sed 's#.*/##' | sort
echo "ON DISK:"; ls -1 *.png *.svg 2>/dev/null | sort
cd -
```

If the re-run wrote files under a *different* basename than the tracked ones,
the old tracked figures are now orphaned. **Report both lists rather than
deleting or `git rm`-ing anything** (no deletions per the ground rules); the
author will decide what to do with any orphans.

---

## Commit C — `uv.lock`: dependency resync (safe, its own commit)

Not incidental. `pyproject.toml` already declares `requires-python = ">=3.12"`,
so the committed lock was stale; regenerating collapses the per-Python duplicate
pins (116 → 108 packages; nothing dropped). Verify then commit:

```bash
uv lock --check          # expect exit 0 against the worktree lock
git add uv.lock
git commit -m "Resync uv.lock to requires-python>=3.12 (collapse per-Python duplicate pins)"
```
If `uv lock --check` does **not** exit 0, stop and report — do not commit.

---

## Commit D — refit configs/scripts + scint handoff doc (docs/config, its own commit)

`refit-2026-07-07/HANDOFF.md` is already committed and points at these files;
this closes that out. `.gitignore` already excludes the heavy/`.pyc` paths, so
adding the two dirs picks up exactly **8 YAML configs + 4 `.py` scripts** (the
`__pycache__/*.pyc` are correctly ignored). The scint handoff doc is docs-only.

```bash
git add analysis/scattering-refit-2026-06/refit-2026-07-07/configs/ \
        analysis/scattering-refit-2026-06/refit-2026-07-07/scripts/ \
        scintillation/HANDOFF_SCINT_DATA_PRODUCTS.md
git status -s   # confirm: 8 .yaml + 4 .py (refit_runner, refit_chunk, inspect_profiles, dump_plot) + 1 .md; NO .pyc
git commit -m "Add refit-2026-07-07 configs+scripts and scintillation data-products handoff

Ships the runner/chunk/inspect/dump scripts and 8 per-burst run configs that the
already-committed refit-2026-07-07/HANDOFF.md documents, plus the 174-line
scintillation data-products handoff. (The latter notes DATA_PROVENANCE.md is
stale on storage paths — h17:/data/jfaber/ was emptied ~2026-06-27, contents
moved to h17:/data/research/astrophysics/frbs/chime-dsa-codetections/ — an open
follow-up, not addressed here.)"
```

---

## Step E — push and verify

```bash
git push origin agent/sightline-halo-grid-figure
git ls-remote origin refs/heads/agent/sightline-halo-grid-figure   # THIS is the source of truth
git status -sb                                                     # expect: up to date with origin/...
```

## Step F — report back

1. Step 0 output.
2. For **each** of commits A–D: the commit SHA (`git log --oneline -5`), and for
   B, C the sanity-check results (`ast.parse` / `uv lock --check` exit codes) and
   whether the figure re-run produced any orphaned old-named figures.
3. The final `git ls-remote` SHA after push.
4. Anything you stopped on or deviated from.

I need the **final HEAD SHA** (after all four commits) to bump the `Faber2026`
submodule pointer again — the pointer currently on `Faber2026` main is `386e886`,
so it will need a second bump to whatever these four commits produce.
