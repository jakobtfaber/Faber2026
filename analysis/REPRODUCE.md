# Reproducing the figures and tables in Faber2026

This maps every manuscript output — each `*_table.tex` and each `figures/…`
graphic — back to the command that regenerates it. It is the reproducibility
spine for the ApJ Data Availability statement.

The machine-readable version is [`repro_manifest.csv`](repro_manifest.csv)
(one row per output). This file is the prose companion: how to read it, how the
two repos relate, and the caveats that a CSV cell can't carry.

## The two-repository structure (read this first)

Faber2026 is **not** a monolith. `pipeline/` is a **git submodule** pointing at
`https://github.com/dsa110/dsa110-FLITS.git` — a separate repository with
its own history, remote, and lifecycle. Outputs therefore fall into two classes:

- **Faber2026-local producers** live under `scripts/` in this repo. Edit and
  run them here.
- **Submodule producers** live under `pipeline/…` (i.e. inside dsa110-FLITS).
  Changing them is a commit to the *shared library*, not to the manuscript.
  Treat those edits with library-grade caution (other consumers inherit them).

The `run_command` column reflects this: `scripts/…` producers run from the repo
root; `pipeline/…` producers run from inside `pipeline/` under the submodule's
own environment.

One wrinkle worth knowing before you go looking for a pipeline commit. The
`.gitmodules` URL above is what a fresh `git submodule update --init` clones,
and it resolves the pinned SHA. **Pipeline development happens on the
`jakobtfaber/dsa110-FLITS` fork.** Since FLITS #151 merged the old divergent
line (`fix/budget-table-data-post-igm-lognormal`) into the fork's `main`, the
pin base is an ancestor of fork `main`; the pin itself sits 1–2 replayed
commits off it. The full pin lineage is published on the fork branch
**`pin/faber2026`** (since 2026-07-09), so pinned SHAs are reachable by ref,
not just as fork-network dangling objects. A pipeline fix is PR'd against fork
`main`, then replayed onto the pin (see FLITS #149 → Faber2026 #71, and
FLITS #156 → the guards pin bump, for the pattern); advance `pin/faber2026` on
every bump, and check `git merge-base --is-ancestor` before ever bumping the
pin.

## Environment

There are **two** environments, and which one you need depends on where the
producer lives.

**Submodule producers (`pipeline/…`)** use the `uv` lock
(`pipeline/uv.lock`, `requires-python >=3.12`), invoked from within `pipeline/`:

```bash
cd pipeline
uv sync            # once, materializes the locked environment
uv run python <producer.py> [args]
```

**Faber2026-local producers (`scripts/…`)** have no lockfile of their own, and
bare `python` is not a defined interpreter for them — on a clean shell it is
simply `command not found`. They run under the conda env named **`flits`**,
whose spec is `pipeline/environment.yml`:

```bash
conda env create -f pipeline/environment.yml   # once; creates `flits`
conda run -n flits python scripts/<producer.py> [args]
```

`flits` is required rather than merely convenient: `plot_ne2025_mw_properties.py`
imports `healpy`, which is in `pipeline/environment.yml` but **not** in
`pipeline/uv.lock`. The older campaign scripts under
`analysis/scattering-refit-2026-06/` were also authored against `flits` and say
so in their docstrings. Prefer `uv run` where the script is `uv`-clean; every
row's `run_command` names the environment it actually needs.

## How to read `clone_verified`

`writer_verified` is a **reading** standard — someone read the `savefig` line.
`clone_verified` is an **execution** standard: on 2026-07-09 every distinct
`run_command` was executed from a fresh `git clone` + `git submodule update
--init` at super-repo `733a369` × pipeline `6c87890`. The two disagree often
enough that the DA statement should rest on the second.

"Executed" here means more than *exit 0*. For each command a marker file is
touched immediately before the run, and the verdict asks which files anywhere
under the clone are newer than that marker. The first pass of this audit instead
compared each output's mtime against `README.md`'s — but `git clone` writes every
file within the same second, so that comparison reported "written" for outputs no
producer had touched. It scored three rows `reproduced` whose producers write
somewhere else entirely. **A generator that exits 0 while writing nothing at the
declared path is the single most common failure here**, and it is invisible to
both a `savefig` read and a return code.

- **reproduced** — the command as written exits 0 and writes the declared
  output into the clone.
- **reproduced_fixed_cmd** — the command *as previously written* did not work;
  the corrected command now in the `run_command` cell was executed and does.
- **wrong_output_path** — the command exits 0 but does not write the declared
  output at the declared path. Exit status alone would have hidden this.
- **blocked_external_data** — the producer needs inputs that exist in neither
  repository (an HPC scratch tree, or a data directory with zero tracked
  files). Not reproducible from a clone by anyone, including the author on a
  fresh machine.
- **no_command** — nothing runnable is recorded.

Result: of the manifest's 28 rows, **12 regenerate from a fresh clone** (5 as
written, 7 only after correcting the command), **4 exit 0 while writing nothing
at the declared path**, 10 are blocked on data outside both repos, and 2 have
no command. The 2026-07-09 execution sweep ran the 25 rows then present. The
compact archival gallery, the Figure 1 data overview, and the
main-text-plus-appendix triptych family were added later with verdicts assigned
by inspection rather than execution. The Figure 1 data grid draws every panel
from the archival `_cntr_bpc.npy` waterfalls (all 24 products, near-native
display grids) and anchors the time axes on the fitted arrival times from the
tracked jointmodel NPZ + joint_fit JSON pairs. The legacy CHIME-minus-DSA
400-MHz timing offsets are re-referenced from their recorded DMs to the adopted
DMs before those anchors are placed; the triptychs require the
eleven local fit-delivery NPZ artifacts plus Chromatica's two archival
waterfall products; the compact gallery remains diagnostic only and requires
all 24 archival waterfalls.

8 of the 10 rows marked `embedded_in_manuscript = yes` regenerate — **4 of
those 8 needed their `run_command` corrected first**, so the pre-audit manifest
could not have rebuilt the manuscript. The two blocked embedded rows are the
codetection data grid and triptych family; neither can be rebuilt from a fresh
clone until the fit artifacts and Chromatica waterfall products are deposited
(see hazard 6). Every other blocked or
command-less row is a *staged* output waiting on a result SLOT; those cannot
be promoted into the manuscript until their inputs are published alongside the
code.

⚠️ **This is a statement about the manifest, not about the manuscript.** The
manifest does not enumerate every embedded output — see hazard 7. Until it does,
"all embedded outputs reproduce" is *not* a claim the Data Availability statement
can make.

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

The manuscript is mid-draft. Of 29 tracked outputs (24 figures + 5 tables),
ten are currently `\input`/`\includegraphics`'d (the
`embedded_in_manuscript = yes` rows, most recently the Figure 1 data grid and
the redistributed triptych family); the other 18 (seventeen figures + the
staged `beta_table.tex`) are produced and sit in the repo but are not yet
placed — they are waiting on the abstract's bracketed result SLOTs (joint
two-band scattering, scintillation attribution, band-restricted energies). One
of the staged figures, `ne2025_mw_characterization.pdf`, is a true orphan: it
is the default-resolution (`--nside 8`) sibling of the embedded `_nside32`
variant and is not referenced anywhere. Both classes are tracked so nothing is
lost when a SLOT is filled.

## Regenerating the tables

All five manuscript tables have an explicit provenance path. For the verified
DM table, the reviewed source is
`analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv` and parity is enforced by
`tests/test_verified_dm_manuscript.py`. For the DM budget,
the foreground/cosmological columns remain sourced from the pinned pipeline
JSON, while `DM_obs` is overlaid from
`analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv` and `DM_host` from
`scripts/dm_budget_uncertainty.csv`. Run the root renderer after regenerating
the host posterior; do not edit `budget_table.tex` directly.

Both are safe to regenerate at the currently pinned submodule (`0e0f58b`);
regenerating reproduces the committed `.tex` byte-for-byte. This was briefly
untrue — see hazard 1 for what went wrong and why the pin matters. (The pin
reached `14e0d1f` in three steps: `6c87890 → 334cc74` as Faber2026 #68, then
`334cc74 → 79eaf7e` as Faber2026 #71, a single commit promoting the `zach`
C2D4 beta fit, then `79eaf7e → 14e0d1f` as the guards pin-bump PR, a single
commit promoting the CHIME artifact-control guards (FLITS #156; scintillation
lane only). It then advanced to `fba48c6` — `3435ba0 → fba48c6`, Faber2026
#21 of the relinked repo, 2026-07-13, reconciling the scintillation and DM
lanes. On 2026-07-13 the submodule was retargeted from the org upstream to
the personal fork `jakobtfaber/dsa110-FLITS` (`f08c973`) and pinned to the
fork's rewritten `main` at `0e0f58b` (`c5e83d2`). **`0e0f58b` is NOT a
descendant of `fba48c6`** — the fork history was rewritten (author scrub +
force-push), so the `merge-base --is-ancestor` bump check does not apply
across that boundary, and every pre-rewrite SHA in this document resolves
only via the org upstream `dsa110/dsa110-FLITS`, not via the fork. A content
diff `fba48c6 → 0e0f58b` (2026-07-13) touches no `*_table_data.json` and
neither table emitter, so the byte-exact regeneration of `budget_table.tex`
and `foreground_table.tex` is unchanged from the earlier verification, and
the `table-parity` CI job is green at `c5e83d2`. The same diff, however,
**drops ~221 files** that `fba48c6` carried — `scintillation/scint_analysis`,
the `dispersion/dm_phase_suite` + DM-campaign results trees, and the
2026-07-12/13 CHIME recovery/baseband-calibration analyses — content from the
canonical `pin/faber2026` lane that never reached the rewritten fork `main`.
Whether to re-land that lane (cherry-picks onto the rewritten history) is an
open decision; tables are unaffected. `beta_table.tex` is a separate matter —
see the note below.)

`#71` did change the submodule's `analysis/beta_campaign/beta_table_rows.tex`
(the `zach` row moved from `_C1D1` to `_C2D4_cwin`). The root `beta_table.tex`
is hand-maintained, is not `\input` by the manuscript, and is deliberately left
untouched: `tab:beta` is deferred. Do not treat that file as regenerable-and-current.

```bash
conda run -n flits python scripts/dm_budget_uncertainty.py
conda run -n flits python scripts/render_budget_table.py
conda run -n flits python scripts/render_budget_table.py --check

cd pipeline
# foreground census: values in galaxies/foreground/foreground_table_data.json
uv run python -m galaxies.foreground.foreground_table_emitter --out ../foreground_table.tex
# verify (byte-exact vs exports/ + value cross-checks against upstream products)
uv run pytest galaxies/foreground/test_foreground_table_emitter.py
# ^ green at pipeline pin 6c87890 (verified 2026-07-09).
```

The pipeline emitters also write canonical copies to `pipeline/exports/<table>.tex` (the
byte-exact regression anchor) and supports `--check` (non-zero exit on drift).
**`--check` is not a sufficient CI gate on its own** — it compares the emitter's
output to `exports/<table>.tex`, and both are derived from the *same*
submodule-local data file, so it cannot see the cross-repository drift of
hazard 1. Measured at pin `f9e1c24`: both emitters' `--check` exited 0 while
`test_dm_host_matches_forward_model` failed. (That test's row loop uses a bare
`assert`, so one run reports only the first mismatching sightline —
FRB 20220207C; replaying the comparison without short-circuiting shows all nine
differed.) CI must run the **parity tests**, not just `--check`.
The root budget renderer is now the authoritative cross-repository parity gate;
the pipeline-local budget test predates the adopted phase-DM catalog and is not
run against the manuscript table. The `\input{budget_table}` /
`\input{foreground_table}` paths
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
  over the 9 non-placeholder sightlines. Green at pin `6c87890` (9/9), verified
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
   is part of the result. (RESOLVED 2026-07-09 by PRs #48 and #53 — recorded as
   a standing trap.)**

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

   Note what did *not* fire: throughout that window both emitters' `--check`
   exited 0, because the emitter and its `exports/` anchor were regenerated from
   the same stale `budget_table_data.json`. A drift guard that compares a
   generator to its own output is blind by construction to an upstream input
   going stale. Only the parity test, which reaches across into the super-repo's
   CSV, could see it.

   **PRs #48 and #53 closed it** by bumping the pin to a commit that carries a
   regenerated `budget_table_data.json`. Verified at pin `6c87890`: the parity
   test is 9/9 green, `--check` exits 0, and the emitter's output is
   byte-identical to the committed `budget_table.tex`. This still holds at the
   current pin `0e0f58b` (verified 2026-07-13, by content diff across the
   fork-history rewrite — see the pin narrative above): no
   `budget_table_data.json` or table-emitter changes anywhere in
   `6c87890 → fba48c6 → 0e0f58b`, so the 9/9
   parity result carries over unchanged. The `parity` CI job re-ran the emitters
   against the super-repo at each pin bump and was green on both.

   Closing it took two tries, and the misfire is the more useful half of the
   story. **`f9e1c24` — the pin this repo had carried since #39 — is not an
   ancestor of `dsa110-FLITS` `main`.** It sits on `agent/sightline-halo-grid-figure`,
   22 commits divergent since the fork at `6647753`, and the budget-table emitter
   exists *only* on that line; `main` has never carried it. #48 bumped to
   `c69d043`, a squash produced by merging the pin's branch into FLITS `main` —
   which silently dragged the whole 127-file fork delta upstream, rolled back an
   unrelated `johndoeII` promotion, and turned FLITS CI red. FLITS #145 reverted
   it; #53 re-pinned here to `6c87890` = `f9e1c24` + the three intended files.

   Second lesson, then: **before bumping the pin, check that the new commit is a
   descendant of the old one** (`git merge-base --is-ancestor <old> <new>`).
   A submodule pin that lives off the upstream default branch — as this one does —
   makes "just merge it upstream" the wrong reflex.

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
   `MANUSCRIPT_OUTDIR` was `/Users/jakobfaber/Developer/overleaf/Faber2026/figures/association_cards`
   (`b19a3d3`) — worked on one laptop only. `ae67f4f` replaced it with a
   **repo-relative default derived from the file location**
   (`ROOT.parent/figures/association_cards`), overridable with
   `--manuscript-dir`; `--no-manuscript-copy` skips the copy entirely for a
   standalone submodule checkout. No absolute machine path remains *in this
   script*; it survives a clone to any location.

   (An earlier revision of this file said the constant passed through a
   "repo-absolute path" on its way to repo-relative. It did not: no version of
   `plot_association_cards.py` in any ref of `dsa110-FLITS` ever held a
   `/Users/jakobfaber/Developer/repos/...` literal. The fix went from the
   Overleaf absolute path straight to `ROOT.parent`. Corrected 2026-07-09 —
   and note that the fix was never carried across to the two `galaxies/v2_0/`
   modules that share the same defect. See hazard 5.)

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

5. **Two `galaxies/v2_0/` modules defaulted their output to a hardcoded personal
   Overleaf path — and one of them was not saved by its `run_command`. FIXED at
   the current pin. (Code fix landed as FLITS #148, first reaching this repo at
   pin `334cc74` via the `6c87890 → 334cc74` bump, Faber2026 #68. The current
   pin `0e0f58b` carries the fix unchanged (re-verified directly at `0e0f58b`,
   since descendant-of-`334cc74` reasoning does not survive the 2026-07-13
   fork-history rewrite).)**

   Hazard 3 fixed `plot_association_cards.py`. It did not fix its neighbours:

   - `galaxies/v2_0/sightline_halo_grid.py:59`
   - `galaxies/v2_0/systems_figures.py:76`

   both set `DEFAULT_OUT_DIR = "/Users/jakobfaber/Developer/overleaf/Faber2026/figures"`.
   `sightline_halo_grid.py` is harmless *only* because its `run_command` passes
   `--out-dir ../figures` explicitly. `systems_figures.py`'s command did not, so
   running it as documented exits **0** while writing `clusters_icm.*` and
   `galaxies_cgm.*` into a directory that exists on exactly one laptop — silently
   outside the repository, and on any other machine into a freshly `makedirs`'d
   path nobody will look in. This was found on 2026-07-09 by executing the
   command and then noticing the six modified files in the *Overleaf* checkout
   (restored). **FLITS PR #148** replaced both defaults with
   `os.path.join(os.path.dirname(_REPO), "figures")` — the same `_REPO`-derived
   form hazard 3 used — and that fix is now in the pinned submodule (present
   since `334cc74`, verified again at the current pin `0e0f58b`:
   `DEFAULT_OUT_DIR` is repo-derived at
   `sightline_halo_grid.py:63` and `systems_figures.py:80`). A bare run therefore
   lands `clusters_icm.*` / `galaxies_cgm.*` inside the repository. The manifest's
   `run_command` still passes `--out-dir ../figures` explicitly, so the documented
   invocation was already safe and remains so. The undeclared ordering dependency
   below is unaffected by #148 and still stands.

   The same run exposed an **undeclared ordering dependency**: `systems_figures.py`
   reads `pipeline/results/sightline_dm_scattering_budget.csv`, which nothing in
   the manifest produced before it. That CSV comes from `sightline_budget`, which
   in turn only runs in **module** form — as a script its direct-execution import
   fallback (`galaxies/foreground/sightline_budget.py:61-65`) imports
   `MASS_PRIORITY` but drops `build_unified_records`, so line 494 raises
   `NameError`. Both are fixed in the manifest's commands and neither was
   detectable by reading a `savefig` line.

6. **Seven staged figures are not reproducible from a clone by anyone.**
   `chime_subband_compare.py`, `joint_ladder/_subband_tau_validation.py` and
   `plot_jointmodel_montage.py` read from `/central/scratch/jfaber/flits-runs/…`,
   an HPC scratch tree; `scint_census/figbank.py` reads
   `scint_census/data/scint/…`, a directory with **zero tracked files**. All seven
   are `embedded_in_manuscript = no`. Any of them that later enters the
   manuscript must have its inputs published — a committed data file, or a
   deposited archive — before the DA statement can cover it.

   **2026-07-11 update (revised 2026-07-13): this class has one embedded
   member.** The codetection Figure 1 data grid reads all 24 archival CHIME/DSA
   `_cntr_bpc.npy` waterfalls (near-native display grids); the triptych family
   reads the 11 fit-delivery NPZ artifacts plus Chromatica's two archival
   waterfalls. Both rows are `embedded_in_manuscript = yes` while
   `blocked_external_data`; the compact gallery uses the same 24 archival
   waterfalls but is diagnostic and non-embedded. The archival waterfalls and
   fit artifacts must be part of the data release before the DA statement
   can cover Figures 1--2 and the morphology-audit appendix.

7. **The manifest does not enumerate every embedded output. (OPEN — this is the
   weakest link in the DA statement.)**

   `repro_manifest.csv` is treated as the authoritative list of manuscript
   outputs, but the built manuscript `\includegraphics` two families for which it
   has **no rows at all**:

   - `figures/dsa_lorentzian_summary.pdf` — `sections/results.tex:157`
   - `figures/dsa_scint_acf/*_dsa_acf_lorentzian_fits.pdf` — 12 committed panels,
     pulled in via `sections/appendix.tex:193` → `sections/dsa_scint_acf.tex`

   That is **13 embedded files with zero reproducibility evidence.** A producer
   does exist in the submodule —
   `pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py`
   — but it has never been given a manifest row, a `run_command`, or a
   `clone_verified` verdict, and this audit did **not** execute it.

   The consequence is worse than a gap: because the manifest defines the set it
   audits, a green sweep over its 28 rows reads as "the manuscript reproduces"
   while silently skipping the scintillation figures. Any future coverage check
   must derive the output set from the manuscript's `\includegraphics` and
   `\input` directives, not from the manifest's own row list. Until these rows
   exist and are executed, the DA statement can claim only that *the outputs the
   manifest tracks* regenerate.

## Suggested next steps

- **Close hazard 7 first.** Add rows for `dsa_lorentzian_summary.pdf` and the 12
  `dsa_scint_acf/` panels, run their producer from a fresh clone, and record a
  `clone_verified` verdict. Nothing else in this file matters to the DA statement
  as much as this.
- Deposit the 24 archival CHIME/DSA `_cntr_bpc.npy` waterfalls and the 11
  fit-delivery artifacts: the Figure 1 grid (archival waterfalls) and triptych
  family (fit artifacts plus Chromatica's waterfalls) are the two embedded
  rows the DA statement cannot cover, and data deposition is the only way to
  close them.
- Fill the two unresolved producers (author knowledge) and promote their rows
  to `writer_verified = yes`.
- Hazards (1) and (2) are both **done**: the two tables are generated + tested,
  and `plot_association_cards.py`'s output path is now a repo-relative default
  with `--manuscript-dir` / `--no-manuscript-copy` overrides.
- **Hazard (5) is partly closed; (6) is open.** (5)'s `DEFAULT_OUT_DIR` half is
  **done** — FLITS #148 made it repo-relative in the two `galaxies/v2_0/` modules,
  in the pinned submodule since `334cc74` (Faber2026 #68) and still present at the
  current pin `0e0f58b` (verified 2026-07-13). Still open in (5): add
  the missing `build_unified_records` to `sightline_budget.py`'s fallback import
  (the module now lives at `galaxies/foreground/sightline_budget.py` after the
  `v2_0 → foreground` rename; confirmed still absent at `0e0f58b` — the
  `except ImportError` branch at line 65 imports only `MASS_PRIORITY`). (6) is a data-deposition decision,
  not a code fix.
- Once producers are confirmed, this manifest can back a top-level `Makefile`
  target (`make figures`) that regenerates the embedded set end-to-end. The
  `clone_verified = reproduced*` rows are exactly the set that target can cover
  today.
