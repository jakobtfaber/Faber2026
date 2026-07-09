# Reproducing the figures and tables in Faber2026

This maps every manuscript output — each `*_table.tex` and each `figures/…`
graphic — back to the command that regenerates it. It is the reproducibility
spine for the ApJ Data Availability statement.

The machine-readable version is [`repro_manifest.csv`](repro_manifest.csv)
(one row per output). This file is the prose companion: how to read it, how the
two repos relate, and the caveats that a CSV cell can't carry.

## The two-repository structure (read this first)

Faber2026 is **not** a monolith. `pipeline/` is a **git submodule** pointing at
`https://github.com/jakobtfaber/dsa110-FLITS.git` — a separate repository with
its own history, remote, and lifecycle. Outputs therefore fall into two classes:

- **Faber2026-local producers** live under `scripts/` in this repo. Edit and
  run them here.
- **Submodule producers** live under `pipeline/…` (i.e. inside dsa110-FLITS).
  Changing them is a commit to the *shared library*, not to the manuscript.
  Treat those edits with library-grade caution (other consumers inherit them).

The `run_command` column reflects this: `scripts/…` producers run from the repo
root; `pipeline/…` producers run from inside `pipeline/` under the submodule's
own environment.

## Environment

The pipeline pins its environment with `uv` (`pipeline/uv.lock`,
`requires-python >=3.12`). The reproducible invocation is `uv run` from within
`pipeline/`:

```bash
cd pipeline
uv sync            # once, materializes the locked environment
uv run python <producer.py> [args]
```

A few older campaign scripts under `analysis/scattering-refit-2026-06/` were
authored against a conda env named `flits` and their docstrings say
`conda run -n flits python …`. Both paths are recorded per-row in the manifest;
prefer `uv run` where the script is `uv`-clean.

## How to read `writer_verified`

- **yes** — I read the actual `write_text` / `fig.savefig(...)` line that emits
  this exact filename. The command is trustworthy.
- **candidate** — the producing *module or function* is identified, but I did
  not confirm a single trustworthy command for this exact stem. Two sub-cases:
  (a) the file is emitted by a multi-figure script (e.g. `systems_figures.py`,
  `scint_census/figbank.py`, `crossmatching/plotting.py`) where I did not
  isolate the one savefig call for this stem — the command regenerates the
  figure *set*; or (b) the producing function is confirmed but no committed CLI
  caller passes this stem (e.g. `freya_dsa_gamma_summary`). Confirm the
  individual target before relying on it in the DA statement.
- **unresolved** — no producer found anywhere in the current tree.

(The **hand** status used in earlier versions is now retired: the two
hand-maintained tables were converted to generated emitters — see the table
regeneration section below.)

## Status: what's embedded now vs. staged

The manuscript is mid-draft. Of 25 tracked outputs (21 figures + 4 tables),
nine are currently `\input`/`\includegraphics`'d (the
`embedded_in_manuscript = yes` rows); the other 16 (fifteen figures + the
staged `beta_table.tex`) are produced and sit in the repo but are not yet
placed — they are waiting on the abstract's bracketed result SLOTs (joint
two-band scattering, scintillation attribution, band-restricted energies). One
of the staged figures, `ne2025_mw_characterization.pdf`, is a true orphan: it
is the default-resolution (`--nside 8`) sibling of the embedded `_nside32`
variant and is not referenced anywhere. Both classes are tracked so nothing is
lost when a SLOT is filled.

## Regenerating the tables

Three of the four tables are generated from a data file + an emitter; edit the
**data file**, never the `.tex`. Each root `.tex` also carries a
`% !! GENERATED FILE` banner with its own regenerate line.

Both are safe to regenerate at the currently pinned submodule (`c69d043`);
regenerating reproduces the committed `.tex` byte-for-byte. This was briefly
untrue — see hazard 1 for what went wrong and why the pin matters.

```bash
cd pipeline
# budget table: values in galaxies/foreground/budget_table_data.json
uv run python -m galaxies.foreground.budget_table_emitter     --out ../budget_table.tex
# foreground census: values in galaxies/foreground/foreground_table_data.json
uv run python -m galaxies.foreground.foreground_table_emitter --out ../foreground_table.tex
# verify (byte-exact vs exports/ + value cross-checks against upstream products)
uv run pytest galaxies/foreground/test_budget_table_emitter.py \
              galaxies/foreground/test_foreground_table_emitter.py
# ^ green at pipeline pin c69d043 (verified 2026-07-09).
```

Each emitter also writes a canonical copy to `pipeline/exports/<table>.tex` (the
byte-exact regression anchor) and supports `--check` (non-zero exit on drift),
suitable for CI. The `\input{budget_table}` / `\input{foreground_table}` paths
in `sections/` are unchanged: the emitters overwrite the manuscript's root
`.tex` files in place, so the Overleaf lane (which has no `pipeline/` submodule)
keeps building. `sample_table.tex` uses its own generator
(`scripts/make_sample_table.py`); `beta_table.tex` uses
`analysis/beta_campaign/export_beta_table.py`.

The parity tests are the substantive guarantee — they tie each table to a
*recomputable* upstream product, not just to its own export. They have already
earned their keep once: they are what caught the drift described in hazard 1.
- **budget** — the DM_host `median^{+p84}_{-p16}` column is cross-checked
  value-for-value against the forward-model posteriors in
  `scripts/dm_budget_uncertainty.csv` (emitted by `scripts/dm_budget_uncertainty.py`),
  over the 9 non-placeholder sightlines. Green at pin `c69d043` (9/9), verified
  2026-07-09. Note the test spans **both repositories**: it reads a super-repo
  CSV from a submodule test, so it is only meaningful for a matched
  (super-repo commit, submodule pin) pair.
- **foreground** — every numeric object ID's verdict is cross-checked against
  the census registry `pipeline/galaxies/foreground/data/intervening_census_registry.csv`
  (27/27 registry-resident rows). The table is a curated subset of the registry's
  confirmed+inconclusive systems (refuted candidates omitted; the cluster row's
  ID comes from the WenHan2024 catalog, not the registry).

## Caveats and hazards (the things worth fixing)

1. **The budget-table parity test spans two repositories, so the submodule pin
   is part of the result. (RESOLVED 2026-07-09 by PR #48 — recorded as a
   standing trap.)**

   `test_dm_host_matches_forward_model` lives in the submodule but reads
   `scripts/dm_budget_uncertainty.csv` from the **super-repo**. Its verdict is
   therefore a property of the *pair* (super-repo commit, `pipeline` pin), not
   of either repo alone. That let a drift open up silently:

   - **PR #40** re-based the cosmic DM term on the TNG-calibrated IGM log-normal
     (Connor 2025), rewriting `dm_budget_uncertainty.csv`.
   - **PR #42** further corrected the low-z IGM spline.
   - `budget_table.tex` was updated to follow. `budget_table_data.json`, in the
     submodule, was not — and the pin stayed at `f9e1c24`.

   For a window on 2026-07-09 the emitter was therefore *behind* the manuscript:
   at pin `f9e1c24` all 9 non-placeholder sightlines mismatched, and running the
   documented regenerate command would have rewritten 35 lines of
   `budget_table.tex`, reverting the DM_host column to pre-#40 values. The
   `% !! GENERATED FILE -- do not edit by hand` banner pointed exactly the wrong
   way: for that window, the hand edits were the correct ones.

   **PR #48 closed it** by bumping the pin to `c69d043`, which carries a
   regenerated `budget_table_data.json`. Verified at `c69d043`: the parity test
   is 9/9 green, `--check` exits 0, and the emitter's output is byte-identical
   to the committed `budget_table.tex`.

   The lesson worth keeping: **a green parity test in the submodule proves
   nothing until the super-repo pins the commit that made it green.** When you
   change `dm_budget_uncertainty.py` / `.csv`, regenerate
   `budget_table_data.json` in `dsa110-FLITS` and bump the gitlink in the same
   breath, or the next person to run the "safe" regenerate command silently
   reverts your numbers.

   (Two sightlines — FRB 20220310F and FRB 20221203A, both $z\approx0.5$ — carry
   *negative* DM_host medians. This is intended, not a defect: their posteriors
   are consistent with zero, `P(DM_host<0)≈0.5`, and `budget_table.tex`'s own
   `\tablecomments` explains that the marginally negative medians reflect scatter
   about the cosmological normalization. Do not "fix" them by censoring at zero.)

2. **The two hand-maintained tables are now generated. (RESOLVED 2026-07-08,
   with the caveat in hazard 1.)**
   Both `budget_table.tex` and `foreground_table.tex` — previously the least
   reproducible objects in the manuscript — are now emitted from structured
   single-source data files with parity tests. See *Regenerating the tables*
   below. What used to be the hazard, for the record:
   - `budget_table.tex` had a "regenerate, not by hand" header but was in fact
     a hand transcription; a DR8/DR9 drift had already slipped through
     (`language_audit.md`).
   - `foreground_table.tex`'s own header stated no generator existed.

   Now each `.tex` carries a `% !! GENERATED FILE` banner naming its data source
   and regenerate command, and a hand edit that drifts from the source data is
   caught by the parity tests. `budget_table.tex`'s measured `tau_obs` column is
   still withheld pending the V1 re-validation ladder (a data-content decision,
   independent of the emitter).

3. **`plot_association_cards.py` machine-specific output path. (RESOLVED 2026-07-08.)**
   `MANUSCRIPT_OUTDIR` was a hardcoded absolute path (originally an
   `overleaf/Faber2026/...` mirror, then a repo-absolute path) — worked on one
   laptop only. It is now a **repo-relative default derived from the file
   location** (`ROOT.parent/figures/association_cards`), overridable with
   `--manuscript-dir`, and `--no-manuscript-copy` skips the copy entirely for a
   standalone submodule checkout. No absolute machine path remains; the script
   survives a clone to any location.

4. **Producer resolution for the two burst-nickname figures:**
   - `freya_dsa_gamma_summary.pdf` (freya = FRB 20230325A) — **resolved** to the
     producing function `plot_subband_gamma_summary` in
     `scintillation/scint_analysis/plotting.py`, confirmed by commit `18fbe98`
     ("freya DSA gamma(nu) summary — manuscript export", FLITS #130, run at
     pinned submodule `25b8cc6` against `scintillation/configs/bursts/freya_dsa.yaml`
     Lorentzian fits). The function takes a caller-supplied `save_path` and no
     committed CLI script passes the `freya_dsa_gamma_summary` stem, so it is
     `candidate`, not `yes` — the author should confirm/commit the driver.
   - `whitney_multiplicity.pdf` (whitney = FRB 20220310F) — **unresolved.** It
     was committed as a binary copy-in (commit `438825f`), not by any script in
     the tree. Commit `b96aa29` frames it as whitney's 1-component multiplicity
     demo (α rails to 1.5 under the [1.5, 6.0] prior; whitney stays 2-component
     canonical at α≈5.1). Almost certainly a local/HPC `burstfit` run that was
     never committed. Needs author confirmation.

## Suggested next steps

- Fill the two unresolved producers (author knowledge) and promote their rows
  to `writer_verified = yes`.
- Hazards (1) and (2) are both **done**: the two tables are generated + tested,
  and `plot_association_cards.py`'s output path is now a repo-relative default
  with `--manuscript-dir` / `--no-manuscript-copy` overrides.
- Once producers are confirmed, this manifest can back a top-level `Makefile`
  target (`make figures`) that regenerates the embedded set end-to-end.
