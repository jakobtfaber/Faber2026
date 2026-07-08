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
- **hand** — no generator exists; the file is hand-maintained. This is a
  reproducibility hazard, not a verified writer (see caveats 1 and 2).
- **unresolved** — no producer found anywhere in the current tree.

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

## Caveats and hazards (the things worth fixing)

1. **Two manuscript tables are hand-maintained — no generator emits them.**
   - `foreground_table.tex` — its own header says so. Values transcribed by
     hand from the dsa110-FLITS foreground validation (LS DR9 / DESI DR1 / NED /
     PS1-STRM; WenHan2024 cluster catalog).
   - `budget_table.tex` — its header says "regenerate, not by hand," but
     `docs/rse/specs/plan-trust-reset-revalidation.md` confirms it is *currently
     a hand transcription*; the emitter (`exports/budget_table.tex` with a
     parity test against the manuscript copy) is planned, not built. The
     upstream numbers exist — `sightline_budget.py` emits
     `sightline_dm_scattering_budget.md`/`.csv` (markdown, **not** `.tex`), and
     `scripts/dm_budget_uncertainty.py` supplies the skew-corrected
     uncertainties — but the `.tex` itself is assembled by hand. Its measured
     `tau_obs` column is withheld pending the V1 re-validation ladder.

   These are the least reproducible objects in the manuscript: a referee cannot
   regenerate them, and a hand edit can silently drift from the pipeline (the
   `language_audit.md` already caught a DR8/DR9 drift in `budget_table.tex`).
   *Recommendation:* build the planned `budget_table.tex` emitter + parity test,
   and add an equivalent exporter for `foreground_table.tex`, both mirroring the
   existing `export_beta_table.py` pattern.

2. **`plot_association_cards.py` hardcoded a machine-specific output path.**
   `MANUSCRIPT_OUTDIR` pointed at `/Users/jakobfaber/Developer/overleaf/Faber2026/...`
   (L40) — worked on one laptop only. **Fixed 2026-07-08** to the repo-local
   `figures/association_cards`. *Remaining recommendation:* promote it to a CLI
   arg / repo-relative path so it survives a clone to any location.

3. **Producer resolution for the two burst-nickname figures:**
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
- Fix hazards (1) and (2) — both are small and both directly serve the DA
  statement.
- Once producers are confirmed, this manifest can back a top-level `Makefile`
  target (`make figures`) that regenerates the embedded set end-to-end.
