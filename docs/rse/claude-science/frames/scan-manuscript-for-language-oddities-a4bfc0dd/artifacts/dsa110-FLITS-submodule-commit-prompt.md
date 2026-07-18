# Task: commit & push work in the `dsa110-FLITS` repo, then let me know the new commit SHA

You are working on my machine (outside a sandbox), so you have full git write
access. I need you to commit some uncommitted work in a repository and report
back the results. **Do not force-push, do not rebase, do not delete anything.**

## Repository

```
/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/dsa110-FLITS
```

This is the `pipeline/` git submodule of my manuscript repo `Faber2026`. It is
currently on branch `agent/sightline-halo-grid-figure` at HEAD `92b4fdf`
(already pushed to `origin`). Remote: `https://github.com/jakobtfaber/dsa110-FLITS.git`.

> Note: you can reach it either as the standalone path above, or as
> `Faber2026/pipeline`. Use the standalone path to avoid submodule-pointer
> confusion.

## Step 0 — orient (report this back verbatim)

```bash
cd /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/dsa110-FLITS
git rev-parse --abbrev-ref HEAD          # expect: agent/sightline-halo-grid-figure
git rev-parse --short HEAD               # expect: 92b4fdf
git status -s
```

If HEAD is **not** `92b4fdf` or the branch differs, **stop and report** — the
state has changed since this prompt was written and the steps below may not fit.

## Step 1 — commit the table-emitter feature (the one ready, coherent unit)

These 7 files are a single self-contained feature: they make the manuscript's
`budget_table.tex` and `foreground_table.tex` *generated* from single-source
JSON instead of hand-transcribed. `sightline_budget.py` gains only a thin
re-export wrapper (`format_budget_table_tex`) pointing at the new emitter.

```bash
cd /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/dsa110-FLITS

git add galaxies/foreground/budget_table_emitter.py \
        galaxies/foreground/foreground_table_emitter.py \
        galaxies/foreground/budget_table_data.json \
        galaxies/foreground/foreground_table_data.json \
        galaxies/foreground/test_budget_table_emitter.py \
        galaxies/foreground/test_foreground_table_emitter.py \
        galaxies/foreground/sightline_budget.py

# sanity: run the emitter tests before committing, if pytest is available
python -m pytest galaxies/foreground/test_budget_table_emitter.py \
                 galaxies/foreground/test_foreground_table_emitter.py -q || \
  echo "(tests failed or pytest unavailable — report output, do NOT commit if they fail)"

git commit -m "Add generated-table emitters for budget_table.tex and foreground_table.tex

Make the manuscript's budget_table.tex and foreground_table.tex generated
rather than hand-transcribed (the DR8/DR9 survey-release drift caught in
language_audit.md was a symptom of hand-editing). Values now live in
single-source JSON; the AASTeX markup is assembled by dedicated emitters.

- budget_table_emitter.py + budget_table_data.json
- foreground_table_emitter.py + foreground_table_data.json
- test_budget_table_emitter.py, test_foreground_table_emitter.py
- sightline_budget.py: thin re-export of format_budget_table_tex so the
  canonical import path sits next to format_budget_table"
```

## Step 2 — the REST of the uncommitted work (needs your judgment — describe, don't auto-commit)

There is additional uncommitted work in this repo beyond the emitters. **Do not
commit these blindly** — instead, for each group, show me the diff/summary and
ask whether it should go in the same push, a separate commit, or be left alone:

Modified (tracked):
- `crossmatching/plot_association_cards.py`  (note: shows as `MM` — staged+unstaged; check both)
- `analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py`
- `analysis/scintillation-dsa-lorentzian-2026-07-07/results/figures/dsa_lorentzian_summary.{png,svg}`
- `uv.lock`  (large regeneration — confirm it's an intended dependency change, not incidental)

Untracked:
- `exports/`  (contains `budget_table.tex`, `foreground_table.tex` — exported copies)
- `analysis/scattering-refit-2026-06/refit-2026-07-07/configs/` and `.../scripts/`
- `scintillation/HANDOFF_SCINT_DATA_PRODUCTS.md`

For each, run e.g. `git diff -- <file>` (tracked) or `head -40 <file>` / `ls -R
<dir>` (untracked) and summarize. Check `.gitignore` before adding anything
under `analysis/scattering-refit-2026-06/` — some paths there are intentionally
ignored (`*.npz`, `*.json`, `*.png`, etc.).

## Step 3 — push

```bash
git push origin agent/sightline-halo-grid-figure
```

## Step 4 — report back to me

Please paste back:
1. The output of Step 0.
2. The **new commit SHA** from Step 1 (`git rev-parse HEAD` after committing) —
   I need this to bump the submodule pointer in `Faber2026`.
3. The test output from Step 1 (pass/fail).
4. Your Step-2 summary of the remaining WIP + your recommendation on each.
5. Confirmation the push in Step 3 succeeded (`git status` showing
   "up to date with origin/agent/sightline-halo-grid-figure").

---

### Why this hand-off exists (context for you)

The agent that prepared this runs in a sandbox where the submodule git store
(`.git/modules/pipeline/`) is write-protected — object writes (`git hash-object
-w`) and a bare `touch` on `objects/`, `refs/`, and the `.git/modules` dirs all
return "Operation not permitted" — so it cannot commit inside the submodule.
Everything else (the manuscript-side commits, PRs #31/#33/#34) it did itself.
Once you report the new SHA in Step 4.2, it will open the follow-up PR on
`Faber2026` that bumps the `pipeline` pointer to your new commit and carries the
regenerated `budget_table.tex`/`foreground_table.tex` provenance headers that
reference these emitters.
