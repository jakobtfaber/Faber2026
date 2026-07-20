# Plan: trust-reset re-validation program (§V — V1–V5)

---
**Date:** 2026-07-06
**Status:** Ready for execution (phase structure approved by owner 2026-07-06)
**Governs:** [plan-circulation-readiness.md](plan-circulation-readiness.md) §V
**Grounding:** [research-trust-reset-revalidation.md](research-trust-reset-revalidation.md)
---

## Overview

Owner decisions of 2026-07-06 revoked trust in every analysis product
(CONTEXT.md "Trust reset", three waves — wave 3, same night, took the last
two retained items: TOA association arithmetic and DM_obs). This plan is
the re-validation program that restores trust: it freezes and pins all
provenance (Phase 0), authors the re-trust contract and builds its missing
machinery (Phase 1, V1), runs the scattering-input defect forensics
(Phase 2, V2), re-derives the foreground census (Phase 3, V4), re-verifies
the DM budget implementations (Phase 4, V5), audits the energies chain
(Phase 5, V3), and re-derives the association arithmetic + per-telescope
DM_obs provenance (Phase 6, V6). It does **not** re-run the
scattering/scintillation fits — that is the C lane, gated on this plan
plus A and B.

Why this shape: the five explorations found the systemic hole is
*provenance* (unpinned inputs, off-repo builders, removed scripts,
hand-transcribed tables, two fit generations feeding different manuscript
tables), and that most validation machinery exists but is fragmented (three
rail definitions, a χ²-statistic mislabeled PPC, a verification glob that
misses the joint fits). So the program pins first, unifies second, and only
then re-derives.

## Current State Analysis

Full inventory with file:line anchors:
[research-trust-reset-revalidation.md](research-trust-reset-revalidation.md).
Load-bearing facts (paths relative to `pipeline/` = dsa110-FLITS @ `7e77437`):

- `data-manifest.csv` (repo root): 24 rows, sha256/bytes all `PENDING`.
- No in-repo builder for the CHIME scattering cubes
  (`data/CHIME_bursts/dmphase/*_32000b_cntr_bpc.npy`); the builder lives
  off-repo on h17/arc. `scintillation/DATA_PROVENANCE.md:167` records the
  h17 staging (`/data/research/astrophysics/frbs/chime-dsa-codetections/
  chime_singlebeam/`), `:176` the arc archive
  (`h17:/data/jfaber/arc_archive_2026-06/`).
- Open reconciliation failure: `DATA_SOURCES.md:90-111` (pipeline repo
  root).
- Three rail definitions: `analysis/beta_campaign/grade_beta_campaign.py:65`,
  `analysis/beta_campaign/sim_gate.py:72`,
  `analysis/scattering-refit-2026-06/gate_joint_committed.py:47-55`.
- "PPC" is a per-band OLS-gain χ² statistic:
  `analysis/scattering-refit-2026-06/joint_ppc_multi.py:54`.
- `.claude/workflows/fit-verify.js` globs `**/*_fit_results.json` only; the
  joint gate writes `*_joint_gate.json` (`gate_joint_committed.py:8-10`).
- τ injection recovery linear, not absolute (ratio ≈ 2.47–2.50):
  `simulation/recovery_campaign.py:9-24` (docstring; entry points
  `recovery_curve` `:76`, `dnu_recovery_curve` `:146`), asserted
  linear-only in `tests/test_recovery_campaign.py:38,54`.
- γ hard prior bound (−5, 5): `scattering/scat_analysis/burstfit.py:1403`,
  inherited by `burstfit_joint.py:396-409`; 5/8 energies rows within 0.15
  of −5; relaxation harness `analysis/burst_energies/refit_calibrated.py`
  (RAILED list `:57`, `GAMMA_FLOOR=-10` `:61`; bare `main()`, no CLI).
  The mixed-legacy `*_joint_fit.json` are percentile summaries — no
  posterior samples for that generation exist in-tree.
- Energies read the mixed-legacy generation
  (`analysis/calculate_burst_energies.py:66` → `joint_json/*_joint_fit.json`),
  not the β campaign; three-way chromatica gate inconsistency.
- Census adjudication scripts removed from main (`9096a60`); survive in
  worktrees (`~/Developer/scratch/worktrees/flits-rerun/scratch/codetection/`
  and `…/flits-acf-lag-selector`); four frozen CSVs pinned by SHA-256 in
  `docs/rse/specs/reproducibility-foreground-galaxies.md:56-59`
  (foreground_final / foreground / foreground_validated / bursts).
- Deterministic census tail is tracked: `galaxies/foreground/
  census_registry.py`, `build_unified.py`, `build_artifacts.py`,
  `sightline_budget.py`, `sightline_sensitivity.py`.
- Budget export gap: pipeline emits markdown/CSV only
  (`sightline_budget.py:836-876` `format_budget_table`); manuscript-root
  `budget_table.tex` is a hand transcription.
- Missing external oracle: nothing pins `dm_cosmic_macquart`
  (`sightline_budget.py:130-151`) to an analytic/published value; mNFW has a
  hard oracle (`galaxies/foreground/test_scattering_predict.py:183-187`).

## Desired End State

- Every input consumed by a re-fit or a re-derived product has a pinned
  SHA-256 in a tracked manifest; `pytest tests/test_data_manifest.py` passes
  with no xfail markers.
- ADR-0008 (the re-trust contract) is merged in FLITS; a single rail
  classifier (`flits/fitting/rails.py`) is the only rail definition imported
  anywhere; a true replicated-data PPC exists and is required by the gate;
  fit-verify.js covers joint-gate artifacts.
- A per-burst scattering-input provenance table exists with a wrap/de-chirp
  verdict for all 24 cubes; the DATA_SOURCES.md reconciliation failure is
  closed with a root-cause note.
- The census Tier-1 replay reproduces the tracked registry byte-for-byte
  from the frozen CSVs; Tier-2 re-adjudication of every flippable row is
  recorded with a verdict-flip table and per-sightline audit figures.
- Every DM-budget model term has either an external-oracle test or a written
  audit note; `budget_table.tex` is emitter-generated with a parity test.
- The γ_D ≈ −5 pile-up is explained (rail study run at GAMMA_FLOOR=−10), the
  energies exporter enforces an explicit selection rule, and the chromatica
  gate contradiction has a single recorded resolution.
- A per-burst, per-telescope DM_obs provenance table exists (value, error,
  method, producing artifact, CHIME−DSA agreement in σ) and the TOA
  association arithmetic is re-derived from raw inputs against the
  committed report — the co-detection sample membership is re-certified.
- All of the above lands as FLITS PRs; Faber2026 takes one `build:` pin bump
  at the end.

## What We're NOT Doing

- **No citable re-fits of burst data** (no citable β/τ/Δν_d/c₀/γ posterior
  is produced here) — that is lane C (scattering) and lane B
  (scintillation), gated on this plan. Phase 5's GAMMA_FLOOR=−10 study
  does run an MCMC re-fit, but as a *prior-sensitivity diagnostic* of the
  revoked fits whose outputs are quarantined from the citable artifact
  dirs.
- **No geometry-selection work** (A2/A3 kernels, model averaging) — A-lane,
  pending the A1 lock.
- **No manuscript prose or table-value edits** — F1/F2 are gated on C/D; the
  only manuscript-repo changes here are docs under `docs/rse/specs/`.
- **No full live re-run of the census sky search** — Tier 2 is scoped to
  flippable rows; the historical PS1-STRM HLSP strip extraction is
  documented as not fully repeatable and is audited, not re-executed.
- **No pin bump until the FLITS PRs merge**; no pushes from Faber2026 main
  (Overleaf gate) as part of this plan.
- **No new fitting frameworks** — consolidation of existing machinery only.

## Implementation Approach

**Lanes.** All pipeline code changes are made in the canonical FLITS clone
(`~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS/`) on a feature
branch per phase (`reval/p0-provenance`, `reval/p1-contract`, …), landing as
FLITS PRs. The pinned submodule here is never edited. Python runs via
`conda run -n flits …`; when validating pinned behavior, run from inside
`pipeline/` (cwd shadows the editable install). h17 work (Phase 2) is a data
lane: read-only forensics plus checksum capture, no arc mutations.
Manuscript-repo work is limited to `docs/rse/specs/` deliverables.

**Test-first discipline.** Each task writes the failing test (or the
assertion against a known value) before the implementation. For forensics
tasks where the "test" is a measurement, the pre-registered acceptance
criterion is stated in the task before the measurement runs.

**Visibility.** Every phase ends with at least one figure or table
deliverable (owner preference, 2026-07-06): provenance dashboards, per-burst
thumbnail grids, verdict-flip tables, prior-sensitivity posteriors.

**Ordering.** Phase 0 blocks everything (all later phases consume pinned
inputs). Phase 1 blocks the *acceptance* of phases 2–5 outputs (they are
judged under the contract) but its tasks run in parallel with Phase 2
fieldwork. Phases 3→4 are sequential (V5's host-residual re-derivation
needs the V4-verified census); Phase 4's implementation checks (P4.1–P4.4)
can run any time after Phase 0 (P4.3's sensitivity run executes on the
revoked census and is re-emitted on the verified one at P4.5); Phase 5
needs P1.1's rail classifier and otherwise runs any time after Phase 0.

## Phase 0 — Provenance freeze [FLITS]

**Objective:** every input, script, and generated table that later phases
touch is tracked, hashed, and generation-labeled.

### P0.1 Pin the scattering-input manifest

1. Write the failing test `tests/test_data_manifest.py` (new file):

   ```python
   import csv
   import pathlib

   import pytest

   MANIFEST = pathlib.Path(__file__).parents[1] / "data-manifest.csv"


   def _rows():
       with MANIFEST.open() as fh:
           return list(csv.DictReader(fh))


   def test_manifest_parses_and_is_nonempty():
       rows = _rows()
       assert len(rows) == 24


   # xfail removed by P2.2 once the h17-resident rows are hashed.
   @pytest.mark.xfail(reason="h17-resident rows pending P2.2", strict=False)
   def test_manifest_has_no_pending_checksums():
       pending = [r["filename"] for r in _rows()
                  if r["sha256"].strip().upper().startswith("PENDING")]
       assert pending == []
   ```

   Run `conda run -n flits python -m pytest tests/test_data_manifest.py -q`
   — expect 1 passed, 1 xfailed.

2. Implement `scripts/fill_data_manifest.py` (new file):

   ```python
   """Fill sha256/bytes in data-manifest.csv from locally reachable files.

   Rows whose file is not reachable under --data-root are left PENDING and
   reported; they are closed on h17 in P2.2.
   """
   import argparse
   import csv
   import hashlib
   import pathlib
   import sys

   MANIFEST = pathlib.Path(__file__).parents[1] / "data-manifest.csv"


   def sha256(path, chunk=1 << 20):
       h = hashlib.sha256()
       with path.open("rb") as fh:
           while blk := fh.read(chunk):
               h.update(blk)
       return h.hexdigest()


   def main():
       ap = argparse.ArgumentParser()
       ap.add_argument("--data-root", required=True,
                       help="e.g. ~/Data/Faber2026")
       args = ap.parse_args()
       root = pathlib.Path(args.data_root).expanduser()
       with MANIFEST.open() as fh:
           reader = csv.DictReader(fh)
           fields = reader.fieldnames
           rows = list(reader)
       missing = []
       for r in rows:
           hits = list(root.rglob(r["filename"]))
           if not hits:
               missing.append(r["filename"])
               continue
           r["sha256"] = sha256(hits[0])
           r["bytes"] = str(hits[0].stat().st_size)
           r["status"] = "HASHED_LOCAL"
       with MANIFEST.open("w", newline="") as fh:
           w = csv.DictWriter(fh, fieldnames=fields)
           w.writeheader()
           w.writerows(rows)
       print(f"filled {len(rows) - len(missing)}/{len(rows)}; "
             f"still pending: {missing}")
       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

3. Run it: `conda run -n flits python scripts/fill_data_manifest.py
   --data-root ~/Data/Faber2026`. Commit manifest + script + test.
   Rows still PENDING after the local fill are exactly the P2.2 work list.

### P0.2 Restore the frozen census inputs and adjudication scripts

1. Failing test `tests/test_frozen_census.py` (new file) — hashes are
   parsed from the reproducibility doc so the test can never drift from the
   pinned record (`docs/rse/specs/reproducibility-foreground-galaxies.md:56-59`):

   ```python
   import hashlib
   import pathlib
   import re

   ROOT = pathlib.Path(__file__).parents[1]
   DOC = ROOT / "docs/rse/specs/reproducibility-foreground-galaxies.md"
   FROZEN = ROOT / "galaxies/foreground/data/frozen_census"


   def pinned():
       pat = re.compile(
           r"^([a-f0-9]{64})\s+scratch/codetection/(\S+\.csv)\s*$",
           re.MULTILINE,
       )
       out = dict()
       for sha, name in pat.findall(DOC.read_text()):
           out[name] = sha
       assert len(out) == 4, out
       return out


   def test_frozen_census_files_match_pinned_hashes():
       for name, sha in pinned().items():
           p = FROZEN / name
           assert p.exists(), f"missing {p}"
           got = hashlib.sha256(p.read_bytes()).hexdigest()
           assert got == sha, f"{name}: {got} != pinned {sha}"
   ```

   Run — fails (`missing …/frozen_census/foreground_final.csv`).

2. Copy the four CSVs from the worktree into the tracked tree:

   ```bash
   mkdir -p galaxies/foreground/data/frozen_census
   for f in foreground_final.csv foreground.csv foreground_validated.csv bursts.csv; do
     cp ~/Developer/scratch/worktrees/flits-rerun/scratch/codetection/"$f" \
        galaxies/foreground/data/frozen_census/
   done
   ```

   Re-run the test — passes (the explorer already verified byte-match; if a
   hash mismatches here, stop: the worktree copy has drifted and the row is
   escalated to the owner before any Phase 3 replay).

3. Restore the adjudication scripts removed by `9096a60` into a tracked
   `galaxies/foreground/adjudication/` package: copy from the worktree
   (`validate_foreground.py`, `ps1_strm_adjudicate.py`, `merge_final.py`,
   `make_catalog_table.py`), add `__init__.py`, and add
   `tests/test_adjudication_imports.py`:

   ```python
   def test_adjudication_modules_import():
       from galaxies.foreground.adjudication import (  # noqa: F401
           validate_foreground, ps1_strm_adjudicate, merge_final,
           make_catalog_table,
       )
   ```

   Fix only import paths, no logic edits — Phase 3 runs these
   byte-equivalent to the frozen era, so any behavioral edit is a defect.
   Commit.

### P0.3 Fit-generation inventory

1. Failing test `tests/test_fit_generations.py` (new file):

   ```python
   import pathlib
   import yaml

   ROOT = pathlib.Path(__file__).parents[1]
   INV = ROOT / "analysis/fit_generations.yaml"


   def test_inventory_exists_and_covers_known_artifacts():
       inv = yaml.safe_load(INV.read_text())
       gens = {g["name"] for g in inv["generations"]}
       assert {"mixed-legacy-2026-06", "beta-campaign-2026-07"} <= gens
       consumers = {c["artifact"]: c["generation"]
                    for c in inv["consumers"]}
       assert consumers["tab:burst-energies"] == "mixed-legacy-2026-06"
       assert consumers["tab:beta"] == "beta-campaign-2026-07"


   def test_generation_paths_exist():
       inv = yaml.safe_load(INV.read_text())
       for g in inv["generations"]:
           for p in g["artifact_globs"]:
               assert list(ROOT.glob(p)), f"{g['name']}: no match for {p}"
   ```

2. Author `analysis/fit_generations.yaml` with two generation entries
   (mixed-legacy: `analysis/scattering-refit-2026-06/joint_json/*_joint_fit.json`
   + `*_joint_gate.json`; β campaign: `analysis/beta_campaign/fits/**` +
   `analysis/beta_campaign/beta_campaign_verdicts.json` — run posteriors
   live outside the repo in `$FLITS_RUNS`, default
   `~/Developer/scratch/flits-local-runs` per
   `grade_beta_campaign.py:35`, recorded as a `runs_store:` note, not a
   glob),
   `trust: revoked-2026-07-06` on both, and a `consumers:` list mapping
   manuscript artifacts (tab:burst-energies, tab:beta, fig:jointmodel_montage,
   fig:scint_screens, tab:budget, tab:foreground, fig:budget) to their
   producing generation. Record the chromatica three-way gate inconsistency
   in a `known_conflicts:` entry (committed gate MARGINAL/χ²=null vs prose
   gate-FAIL 11.6/9.3 — resolution assigned to P5.3). Test passes. Commit.

### P0.4 Table emitters and parity tests

1. Failing test `tests/test_budget_table_emitter.py` (new file):

   ```python
   import pathlib

   from galaxies.foreground.sightline_budget import format_budget_table_tex

   ROOT = pathlib.Path(__file__).parents[1]


   def test_emitter_produces_deluxetable():
       tex = format_budget_table_tex()
       assert r"\begin{deluxetable" in tex


   def test_emitted_tex_matches_committed_copy():
       committed = (ROOT / "exports/budget_table.tex").read_text()
       assert format_budget_table_tex() == committed
   ```

2. Implement `format_budget_table_tex()` in
   `galaxies/foreground/sightline_budget.py` adjacent to
   `format_budget_table` (`:836-876`), reusing its row assembly and emitting
   the AASTeX `deluxetable` markup currently hand-maintained in the
   manuscript root `budget_table.tex` (column set and footnotes copied from
   that file verbatim so the first parity diff isolates *value* drift from
   *markup* drift). Write output to `exports/budget_table.tex` in the FLITS
   tree via an `--emit-tex` flag on the existing CLI entry point.

3. Run the emitter; diff `exports/budget_table.tex` against the manuscript's
   hand-transcribed `budget_table.tex`:
   `delta pipeline/exports/budget_table.tex budget_table.tex`. Any value
   difference is recorded in the Phase 0 deliverable (below) — do not
   silently adopt either side; values are re-derived in Phase 4 anyway.

4. Same pattern for the foreground table: `make_catalog_table.py` (restored
   in P0.2) already emits `foreground_table.tex`; add
   `tests/test_catalog_table_emitter.py` asserting it runs on the frozen
   census and its output matches the manuscript's `foreground_table.tex`.
   If worktree-era drift makes the parity assert fail, mark it xfail with
   the diff attached to the Phase 0 deliverable; that xfail is resolved at
   P4.5 (the post-Phase-3 regeneration replaces the committed copy and the
   parity target). Commit.

**Phase 0 deliverable (visibility):** provenance freeze report in Faber2026
`docs/rse/specs/`: manifest fill count, frozen-census hashes, the generation
map rendered as a table, and the budget/foreground tex parity diffs. One
figure: a provenance flow diagram (inputs → generations → manuscript
artifacts) rendered with matplotlib.

**Verification:** `conda run -n flits python -m pytest
tests/test_data_manifest.py tests/test_frozen_census.py
tests/test_fit_generations.py tests/test_budget_table_emitter.py
tests/test_catalog_table_emitter.py -q` — all pass (2 sanctioned xfails:
manifest-PENDING until P2.2; catalog parity if drift is found and logged).

## Phase 1 — V1 re-trust contract and machinery [FLITS]

**Objective:** one written contract (ADR-0008) and the four pieces of
machinery it requires: rail SSOT, absolute-recovery criterion, true PPC,
fixed verification glob.

### P1.1 Rail classifier SSOT

1. Failing test `tests/test_rails.py` (new file):

   ```python
   import numpy as np

   from flits.fitting.rails import classify_rail


   def test_interior_gaussian_is_interior():
       rng = np.random.default_rng(0)
       s = rng.normal(3.0, 0.1, 8000)
       assert classify_rail(s, lo=2.2, hi=4.0) == "interior"


   def test_edge_pile_at_hi_is_railed():
       rng = np.random.default_rng(1)
       s = np.concatenate([
           rng.uniform(3.96, 4.0, 4000),   # 50% mass in outer 2% of range
           rng.normal(3.5, 0.2, 4000),
       ])
       assert classify_rail(s, lo=2.2, hi=4.0) == "railed-hi"


   def test_three_sigma_proximity_alone_triggers():
       rng = np.random.default_rng(2)
       s = rng.normal(3.98, 0.02, 8000)    # median within 3σ of hi
       assert classify_rail(s, lo=2.2, hi=4.0) == "railed-hi"


   def test_gamma_lo_rail_matches_energies_pileup():
       rng = np.random.default_rng(3)
       s = rng.normal(-4.97, 0.03, 8000)
       assert classify_rail(s, lo=-5.0, hi=5.0) == "railed-lo"


   def test_absolute_proximity_criterion_from_joint_gate():
       # railed under gate_joint_committed's RAIL_EDGE=0.1 (median within
       # 0.1 of a bound) even though 3σ and edge-mass both miss it
       rng = np.random.default_rng(4)
       s = rng.normal(3.92, 0.01, 8000)
       assert classify_rail(s, lo=3.0, hi=4.0) == "railed-hi"
   ```

2. Implement `flits/fitting/rails.py`:

   ```python
   """ADR-0008 single source of truth for prior-rail classification.

   Union of all three prior operational definitions, so a rail under any
   of them is a rail here (nothing previously railed becomes quotable):
   - grade_beta_campaign (:61-62,77-82): 3σ-proximity OR ≥30% mass in an
     absolute 0.05-wide window at the bound (the campaign β prior is
     unit-width, so the fractional band below reproduces it there and is
     strictly wider for any wider prior, e.g. γ's (−5, 5));
   - sim_gate (:72): 3σ-proximity;
   - gate_joint_committed (RAIL_EDGE, :47-55): median within 0.1
     (absolute) of a bound.
   """
   import numpy as np

   EDGE_WIDTH_FRAC = 0.05   # outer fraction of the prior range
   EDGE_MASS_FRAC = 0.30    # mass in that band that flags a rail
   SIGMA_PROX = 3.0
   PROX_ABS = 0.1           # gate_joint_committed's RAIL_EDGE


   def classify_rail(samples, lo, hi, *,
                     sigma=SIGMA_PROX,
                     edge_width=EDGE_WIDTH_FRAC,
                     edge_mass=EDGE_MASS_FRAC,
                     prox_abs=PROX_ABS):
       s = np.asarray(samples, float)
       med, sd = np.median(s), np.std(s)
       band = edge_width * (hi - lo)
       if (med + sigma * sd >= hi or hi - med <= prox_abs
               or np.mean(s >= hi - band) >= edge_mass):
           return "railed-hi"
       if (med - sigma * sd <= lo or med - lo <= prox_abs
               or np.mean(s <= lo + band) >= edge_mass):
           return "railed-lo"
       return "interior"
   ```

   Tests pass. (The fractional edge band deliberately generalizes the
   campaign's absolute 0.05 window: identical on the unit-width β prior,
   at-least-as-strict on wider priors — the union claim holds per
   criterion, per call site.)

3. Wire the three call sites to import it —
   `analysis/beta_campaign/grade_beta_campaign.py:65`,
   `analysis/beta_campaign/sim_gate.py:72`,
   `analysis/scattering-refit-2026-06/gate_joint_committed.py:47-55` —
   deleting the local definitions. Add `tests/test_rails_is_ssot.py`:

   ```python
   import subprocess


   def test_no_shadow_rail_definitions():
       out = subprocess.run(
           ["rg", "-l", "--", "def .*rail", "analysis", "flits"],
           capture_output=True, text=True, cwd=".",
       ).stdout.split()
       assert out == ["flits/fitting/rails.py"], out
   ```

   Run the existing campaign grading on the committed β posteriors and
   confirm the 2/9/1 classification is unchanged (regression guard — the
   union definition must not reclassify any row silently; if it does, the
   change list goes in the PR description). Commit.

### P1.2 Absolute-recovery criterion

1. Add the failing/xfail test to `tests/test_recovery_campaign.py`
   (currently asserts linearity only at `:38,54`):

   ```python
   from simulation.recovery_campaign import recovery_curve


   @pytest.mark.xfail(reason="known ~2.5x offset; P1.2 root-cause",
                      strict=False)
   def test_tau_recovery_is_absolute():
       df = recovery_curve()   # entry point at recovery_campaign.py:76;
                               # returns tau_true_ms / tau_fit_ms / ratio
       assert np.all(np.abs(np.log10(df["ratio"])) < 0.05)
   ```

   (Call signature mirrors the existing linearity tests at
   `tests/test_recovery_campaign.py:38,54` — reuse their fixture/arguments
   verbatim.)

2. Root-cause the offset. Concrete checks, in order:
   (a) print the τ *definition* on each side —
   `simulation/engine.py:766` `calculate_theoretical_observables()` (which
   moment/e-folding of the simulated PBF it reports) vs the fitted τ
   convention in the estimator under test; (b) check the C1 constant
   convention (2πτΔν_d = 1 vs = C₁ ≠ 1 for non-square-law media — the
   paired offsets, τ ratio ≈ 2.50 with Δν_d ratio ≈ 0.29, multiply to
   ≈ 0.72, the signature of a consistent definitional mismatch rather than
   two independent biases); (c) re-run with a delta intrinsic pulse and an
   exponential PBF where the closed-form answer is exact.
3. Outcome A (definitional): fix the estimator or the truth extractor so
   definitions match; xfail marker removed; test passes at |log₁₀| < 0.05.
   Outcome B (genuine estimator bias): the factor and its validity range are
   measured across the injection grid, recorded as a calibration entry in
   ADR-0008, and the test asserts the *calibrated* estimator is absolute.
   Either way the xfail is gone by phase end — an unexplained offset blocks
   the phase, by design. Commit.

### P1.3 True posterior-predictive check

1. Failing test `tests/test_ppc.py` (new file):

   ```python
   import numpy as np

   from analysis.ppc import ppc_pvalues


   def _toy_model(t, tau):
       return np.exp(-t / tau) * (t >= 0)


   def _sim(t, noise_sigma):
       def simulate(tau, rng=None):
           clean = _toy_model(t, tau)
           if rng is None:
               return clean
           return clean + rng.normal(0, noise_sigma, t.size)
       return simulate


   def test_wellspecified_model_gives_central_pvalues():
       rng = np.random.default_rng(0)
       t = np.linspace(0, 10, 400)
       obs = _toy_model(t, 2.0) + rng.normal(0, 0.02, t.size)
       post = rng.normal(2.0, 0.05, 200)        # posterior draws for tau
       p = ppc_pvalues(obs=obs, noise_sigma=0.02,
                       simulate=_sim(t, 0.02),
                       posterior_draws=post, rng=rng)
       assert 0.05 < p["chi2"] < 0.95
       assert 0.05 < p["lag1_acf"] < 0.95


   def test_misspecified_model_fails():
       rng = np.random.default_rng(1)
       t = np.linspace(0, 10, 400)
       obs = (_toy_model(t, 2.0) + 0.3 * _toy_model(t, 0.3)
              + rng.normal(0, 0.02, t.size))    # unmodeled component
       post = rng.normal(2.0, 0.05, 200)
       p = ppc_pvalues(obs=obs, noise_sigma=0.02,
                       simulate=_sim(t, 0.02),
                       posterior_draws=post, rng=rng)
       assert p["lag1_acf"] < 0.05 or p["lag1_acf"] > 0.95
   ```

2. Implement `analysis/ppc.py`:

   ```python
   """Replicated-data posterior predictive checks (ADR-0008 rung iv).

   For each posterior draw theta: evaluate the noiseless model
   (simulate(theta) with rng=None), draw one replicate dataset
   (simulate(theta, rng)), compute each discrepancy statistic on the
   observed residual (obs - model) and the replicate residual
   (rep - model), and return the Bayesian p-value
   P(T(rep) >= T(obs)) per statistic.

   Statistics: residual reduced chi-square; lag-1 residual
   autocorrelation (sensitive to unmodeled temporal structure — the
   two-screen case).
   """
   import numpy as np


   def _chi2(resid, sigma):
       return float(np.mean((resid / sigma) ** 2))


   def _lag1(resid, _sigma):
       r = resid - resid.mean()
       return float(np.dot(r[:-1], r[1:]) / max(np.dot(r, r), 1e-300))


   STATS = {"chi2": _chi2, "lag1_acf": _lag1}


   def ppc_pvalues(*, obs, noise_sigma, simulate, posterior_draws, rng):
       exceed = {k: 0 for k in STATS}
       n = 0
       for theta in posterior_draws:
           model = simulate(theta)              # rng=None -> noiseless
           rep = simulate(theta, rng)
           for k, stat in STATS.items():
               t_obs = stat(obs - model, noise_sigma)
               t_rep = stat(rep - model, noise_sigma)
               exceed[k] += t_rep >= t_obs
           n += 1
       return {k: v / n for k, v in exceed.items()}
   ```

   Tests pass.

3. Adapt to production: add `analysis/ppc_joint.py` wiring `ppc_pvalues` to
   the joint-fit model evaluation used by `joint_ppc_multi.py:54` (same
   data loading, same per-band noise estimate), emitting `*_ppc.json` with
   per-band and combined p-values. Retire the PPC *label* on the old
   statistic: its output fields are already `chi2_chime`/`chi2_dsa` (no
   field literally named `ppc`), so the change is filename/vocabulary-level
   — new emissions write `*_ols_gain_chi2.json`, and gate/docs prose stops
   calling it a PPC (it remains a useful gate input). Commit.

### P1.4 fit-verify.js coverage and stale refs

1. Failing check (run from the FLITS clone; do not execute the workflow —
   it spawns verifier agents): `rg -c "joint_gate"
   .claude/workflows/fit-verify.js` — 0 matches today; the script has a
   single hardcoded `TARGET = "**/*_fit_results.json"` at
   `fit-verify.js:15` and no listing mode.
2. Edit `.claude/workflows/fit-verify.js`: (a) replace the single `TARGET`
   with a glob list adding `**/*_joint_gate.json` and `**/*_ppc.json`;
   (b) implement a `--list-coverage` dry-run mode that prints the matched
   artifact paths and spawns no agents; (c) update the stale
   `burstfit.py:1342-1386` references at `fit-verify.js:18` and
   `.claude/agents/fit-validation.md:13` to `classify_fit_quality` at
   `:1464` (re-verifying the other line refs both files cite).
3. Check: `node .claude/workflows/fit-verify.js --list-coverage | rg -q
   joint_gate` succeeds. Commit.

### P1.5 Author ADR-0008 (the contract)

1. Write `docs/adr/0008-re-trust-validation-contract.md` in FLITS with the
   five rungs, each bound to now-existing machinery:
   (i) input lineage — row in `data-manifest.csv` with `HASHED_*` status or
   frozen-census hash test; (ii) injection recovery — absolute criterion of
   P1.2 under each candidate geometry, through the production fit path
   (sim_gate pattern, `sim_gate.py:47-52`); (iii) rail behavior —
   `classify_rail` verdict `interior` required for quotability; a rail is
   model-family rejection (ADR-0006/0007 cross-ref); (iv) PPC —
   `analysis/ppc.py` p-values in [0.05, 0.95] for all registered statistics;
   (v) independent cross-check — sub-band slope or τ·Δν_d consistency,
   itself produced under rungs i–iv, never inherited from a revoked
   campaign, and a gate verdict is bound to its generation (cross-generation
   quoting forbidden; see P5.3). Include the P1.2 calibration table (or its
   definitional-fix note), the fleet-status reconciliation (P1.6), and the
   explicit statement that gate constants live in `burstfit.py:81-86`;
   delete the dead `CHI_SQ_RED_MARGINAL_MAX` from
   `flits/fitting/VALIDATION_THRESHOLDS.py:30`.
2. Verification: every path cited in the ADR resolves (`rg --files | rg`
   each); FLITS PR review. Commit.

### P1.6 Fleet-status reconciliation

1. `analysis/beta_campaign/fleet_status.json` reports whitney_fine and
   phineas rc=−15 while the campaign narrative says complete. Re-derive:
   check for later successful runs of those two targets in
   `analysis/beta_campaign/fits/` (committed fit JSONs, e.g.
   `whitney_fine_joint_fit_C2D2.json`, `phineas_joint_fit_C3D3.json`) and
   the `$FLITS_RUNS` store (`grade_beta_campaign.py:35`, default
   `~/Developer/scratch/flits-local-runs`) — run ids/timestamps vs
   fleet_status timestamps; write the finding into
   `analysis/beta_campaign/CAMPAIGN_REPORT.md` as an erratum section —
   either "superseded by successful rerun <id>" or "row invalid, target
   re-queued in lane C". No fit is re-run here. Commit.

**Phase 1 deliverable (visibility):** contract one-pager figure — the five
rungs as a ladder diagram with the machinery file names, plus the rail
demonstration: `classify_rail` applied to the (revoked) β-campaign
posterior samples from `$FLITS_RUNS`, rendered as a strip plot colored by
verdict. (γ_D has no stored samples for the mixed-legacy generation —
its CI-based verdicts arrive in P5.1 as point-interval marks, not here.)

**Verification:** `conda run -n flits python -m pytest tests/test_rails.py
tests/test_rails_is_ssot.py tests/test_ppc.py tests/test_recovery_campaign.py -q`
all pass (no xfail on absolute recovery by phase end); fit-verify coverage
listing includes joint gates; ADR-0008 merged.

## Phase 2 — V2 scattering-input forensics [data: h17 + local]

**Objective:** a wrap/de-chirp verdict and pinned checksum for all 24
scattering cubes; the DATA_SOURCES.md reconciliation failure closed.

### P2.1 Locate and audit the cube builder on h17

1. Pre-registered acceptance: the builder script(s) that wrote
   `*_32000b_cntr_bpc.npy` are found and their dedispersion call is
   inspected for the `time_shift` wrap footgun
   (`crossmatching/chime_singlebeam.py:111` documents the safe convention:
   `time_shift=False` + explicit roll).
2. Commands (read-only):

   ```bash
   ssh h17 'rg -l "cntr_bpc" /data/jfaber /data/research/astrophysics/frbs \
            --max-depth 6 -g "*.py" 2>/dev/null'
   ssh h17 'rg -n "coherent_dedisp|time_shift|np.roll" <each hit>'
   ```

   Starting points recorded in `scintillation/DATA_PROVENANCE.md:167,176`
   (`/data/research/astrophysics/frbs/chime-dsa-codetections/chime_singlebeam/`,
   `/data/jfaber/arc_archive_2026-06/`, `/data/jfaber/upchan_codetections/`).
3. Capture each builder file verbatim into the FLITS tree under
   `scattering/scat_analysis/builders_h17/` (with an `ORIGIN.md` noting
   host, path, mtime, sha256) — closing the "no in-repo builder" gap.
   If the builder is *not found*, that fact is the finding: the cubes drop
   to `UNVERIFIED_BUILDER` status in the manifest, and rung (i) can only be
   satisfied by the direct-data checks of P2.3 plus regeneration in lane B.

### P2.2 Checksum capture (closes P0.1)

1. On h17: `ssh h17 'cd <cube dir> && sha256sum *_cntr_bpc.npy'` for every
   directory holding manifest-listed cubes; same locally under
   `~/Data/Faber2026`. Fill the remaining PENDING rows with
   `scripts/fill_data_manifest.py` (P0.1), extended with a `--from-listing
   <file>` mode that parses `sha256sum` output text (same row-update path;
   test extended with a listing-parse case).
2. Cross-check: where a cube exists on both hosts, hashes must match; a
   mismatch is a hard stop escalated to the owner (it would mean the local
   fits consumed different bytes than the archived inputs).
3. Remove the xfail marker from
   `tests/test_data_manifest.py::test_manifest_has_no_pending_checksums`;
   run; passes. Commit (FLITS).

### P2.3 Direct wrap/defect tests on the cubes

1. Pre-registered acceptance criteria (per cube; the cubes are ~29–36%
   NaN from channel masking, so all reductions are NaN-aware): (a) **edge
   significance**: no time sample above 5σ (robust MAD noise scale) in the
   outer 2% of the time axis — a wrapped scattering tail puts significant
   flux at an array edge; (b) **centering**: the S/N-weighted centroid of
   the >5σ samples lies within the central 20% of the 32000-bin window
   (the `cntr` convention); (c) **cross-lineage**: for targets with an
   independent gen-2/gen-3 CHIME regeneration — casey, whitney, phineas,
   mahi, isha (the 2026-07-06 de-chirped rebuilds,
   `scintillation/DATA_PROVENANCE.md:90-98`) and freya (gen-3 lane) — the
   cube's band-averaged profile cross-correlates with the regenerated
   profile at a lag consistent with 0 (|lag| < 5 time bins after TOA
   alignment). wilhelm and chromatica have no independent CHIME
   regeneration yet (`DATA_PROVENANCE.md:247-252`: pre-regeneration
   up-channelized spectra existed only for casey); their cross-lineage
   cell reads `no-independent-reference` pending lane B.
2. Failing test first — `tests/test_cube_integrity.py` (new file), running
   only when the data root is present:

   ```python
   import os
   import pathlib

   import numpy as np
   import pytest

   DATA = pathlib.Path(
       os.environ.get("FLITS_DATA", "~/Data/Faber2026")
   ).expanduser()
   CUBES = sorted(DATA.rglob("*_32000b_cntr_bpc.npy"))

   pytestmark = pytest.mark.skipif(not CUBES, reason="data root absent")


   def _snr_profile(cube):
       arr = np.load(cube, mmap_mode="r")
       prof = np.nanmean(np.asarray(arr, float), axis=0)
       base = np.nanmedian(prof)
       noise = 1.4826 * np.nanmedian(np.abs(prof - base))
       return (prof - base) / max(noise, 1e-12)


   @pytest.mark.parametrize("cube", CUBES, ids=lambda p: p.stem)
   def test_no_edge_significance_and_centered(cube):
       snr = _snr_profile(cube)
       n = snr.size
       hot = snr > 5.0
       assert hot.any(), "no burst detected above 5 sigma"
       edge = n // 50
       assert not hot[:edge].any() and not hot[-edge:].any()
       idx = np.flatnonzero(hot)
       centroid = float((snr[idx] * idx).sum() / snr[idx].sum())
       assert 0.4 * n < centroid < 0.6 * n
   ```

   Run against the local cubes; any failure is a per-burst finding
   triaged in the phase report (an isolated >5σ edge spike may be RFI —
   the triage distinguishes RFI from a wrapped tail by its bandpass
   footprint), not a threshold to loosen — the criteria were
   pre-registered above.
3. Implement the cross-lineage check as `scripts/cube_crosscheck.py`
   producing a per-burst lag table and a thumbnail-grid figure
   (band-averaged profile per cube, verdict annotated) — the phase's
   visibility deliverable.

### P2.4 Close the DATA_SOURCES reconciliation failure

1. Reproduce the failure exactly as documented at `DATA_SOURCES.md:90-111`
   (pipeline repo root; stored scintillation products vs current arc files
   + committed joint fits); record the minimal command sequence and its
   output.
2. Adjudicate with the P2.2 hashes: if the arc files' hashes differ from
   what the stored products' provenance records (or the records are
   absent), the verdict is "arc files re-generated post-hoc; stored
   products orphaned — superseded by lane-B regeneration"; update
   `DATA_SOURCES.md:90-111` in place with the verdict, evidence hashes,
   and date. The stored scintillation products are already wave-1 revoked
   either way; this task converts an open mystery into a closed, evidenced
   note.

### P2.5 Per-burst provenance table (V2 deliverable)

1. Write `docs/rse/specs/experiment-scattering-input-forensics.md`
   (Faber2026 repo) — per burst × band: filename, sha256, builder
   (path@h17 or UNVERIFIED_BUILDER), `time_shift` verdict, edge-leakage /
   centering / cross-lineage results, and a trust status feeding ADR-0008
   rung (i). Embed the P2.3 thumbnail grid and lag table.
2. Verification: every one of the 24 manifest rows appears; no row has an
   empty verdict cell; statuses match the manifest `status` column.

## Phase 3 — V4 census re-validation [FLITS + live TAP]

**Objective:** Tier-1 byte-reproduction of the census from frozen inputs;
Tier-2 live re-adjudication of every flippable row; per-candidate provenance
and per-sightline audit figures.

### P3.1 Tier-1 deterministic replay

1. Failing test `tests/test_census_replay.py` (new file):

   ```python
   import filecmp
   import pathlib
   import subprocess
   import sys

   ROOT = pathlib.Path(__file__).parents[1]


   def test_registry_rebuilds_bytewise(tmp_path):
       out = tmp_path / "intervening_census_registry.csv"
       subprocess.run(
           [sys.executable, "-m",
            "galaxies.foreground.census_registry",
            "--from-frozen",
            str(ROOT / "galaxies/foreground/data/frozen_census"),
            "--out", str(out)],
           check=True, cwd=ROOT,
       )
       tracked = (ROOT / "galaxies/foreground/data/"
                         "intervening_census_registry.csv")
       assert filecmp.cmp(out, tracked, shallow=False)
   ```

2. Add the `--from-frozen`/`--out` CLI to `census_registry.py` (it already
   builds the registry — `census_registry.py:76-82` computes
   budget_eligible; the flags only redirect input/output paths, no logic
   change). Run; if the bytes differ, the diff is a Phase 3 finding (frozen
   inputs → tracked registry is supposed to be deterministic) and is
   resolved before continuing — the registry is the root of every
   downstream product.
3. Replay the rest of the deterministic tail and diff each tracked
   artifact:

   ```bash
   conda run -n flits python -m galaxies.foreground.adjudication.merge_final \
     --inputs galaxies/foreground/data/frozen_census --check-only
   conda run -n flits python -m galaxies.foreground.build_artifacts
   git diff --stat -- galaxies/foreground/data/
   ```

   `merge_final` must reproduce 49/29/7/13 (its own hard assert,
   `merge_final.py:88-96`); `git diff` must be empty. (`--check-only` is a
   new flag: run, assert, write nothing — added alongside the import-path
   fixes of P0.2.) Commit (test + CLIs).

### P3.2 Per-candidate provenance audit

1. Failing test `tests/test_census_audit.py` (new file):

   ```python
   import csv
   import pathlib

   ROOT = pathlib.Path(__file__).parents[1]
   AUDIT = ROOT / "galaxies/foreground/data/census_audit.csv"

   REQUIRED = {"nickname", "objid", "ra", "dec", "sep_arcsec",
               "z_value", "z_class", "z_source", "strm_class",
               "strm_reliability", "verdict", "verdict_basis"}


   def test_audit_covers_all_49_candidates():
       rows = list(csv.DictReader(AUDIT.open()))
       assert len(rows) == 49
       assert REQUIRED <= set(rows[0])
       assert all(r["verdict_basis"] for r in rows)
   ```

2. Implement `galaxies/foreground/adjudication/build_audit.py`: join the
   frozen CSVs with the registry, emitting one row per candidate with the
   redshift class/source priority actually used
   (`validate_foreground.py:169-192` priority: DESI spec-z → LS-DR9 z_spec →
   z_phot±std → NED), the PS1-STRM class/reliability consumed by
   `ps1_strm_adjudicate.py:34-47`, and a `verdict_basis` sentence naming
   the discriminating datum. Test passes.
3. Per-sightline audit figures (visibility): 12 panels — candidates plotted
   at (separation, z) with the host-z line and 1σ straddle band, colored by
   verdict; emitted to `galaxies/foreground/data/figures/audit_<nick>.png`
   by `build_audit.py --figures`.

### P3.3 Independent re-derivation of impact parameters

1. Failing test `tests/test_impact_params_independent.py` (new file) —
   independent implementation, not a call into `utils.py`. The registry
   carries no FRB coordinates (header: `nickname,type,obj,tns,
   host_z_spec,survey,ra_deg,dec_deg,impact_kpc,b_over_r500,…,best_z,
   best_z_err,best_z_source,…`), so FRB positions are joined from
   `galaxies/foreground/config.py`'s per-target table by nickname:

   ```python
   import csv
   import pathlib

   import astropy.units as u
   import numpy as np
   from astropy.coordinates import SkyCoord
   from astropy.cosmology import Planck18

   from galaxies.foreground import config

   ROOT = pathlib.Path(__file__).parents[1]
   REG = ROOT / "galaxies/foreground/data/intervening_census_registry.csv"


   def _frb_coord(nickname):
       t = config.TARGETS[nickname]   # attribute names confirmed against
       return SkyCoord(t["ra"] * u.deg, t["dec"] * u.deg)  # config.py at
                                                           # impl. time


   def test_impact_kpc_matches_independent_calc():
       rows = list(csv.DictReader(REG.open()))
       checked = 0
       for r in rows:
           if not r.get("best_z") or float(r["best_z"]) <= 0:
               continue
           gal = SkyCoord(float(r["ra_deg"]) * u.deg,
                          float(r["dec_deg"]) * u.deg)
           theta = _frb_coord(r["nickname"]).separation(gal)
           d_a = Planck18.angular_diameter_distance(float(r["best_z"]))
           b = (theta.radian * d_a).to(u.kpc).value
           assert np.isclose(b, float(r["impact_kpc"]), rtol=1e-3), r["obj"]
           checked += 1
       assert checked > 0
   ```
2. Run. A systematic offset indicts `utils.py:18-35` or the registry's
   cosmology; a per-row miss indicts that row's coordinates. Findings feed
   the audit table (an `audit_flag` column added to `census_audit.csv`).
   Same pattern for b/R_vir (`build_unified.py:277-282`) and the frozen
   cluster b/R500 (`census_registry.py:111-113`), comparing against the
   audit's independently computed values.

### P3.4 Tier-2 live re-adjudication (flippable rows)

1. Enumerate the flippable set from the audit table: rows whose verdict
   rests on (a) a photo-z 1σ straddle, or (b) a PS1-STRM class with
   UNSURE/extrapolated reliability. Emit
   `galaxies/foreground/data/flippable_rows.csv` from `build_audit.py
   --flippable`; the set size is a reported number, not assumed.
2. Re-query live services for exactly those rows:

   ```bash
   conda run -n flits python -m galaxies.foreground.adjudication.validate_foreground \
     --only "$(cut -d, -f2 galaxies/foreground/data/flippable_rows.csv | tail +2 | paste -sd, -)"
   ```

   and the same `--only` filter for `ps1_strm_adjudicate.py` (input filter
   only, no verdict-logic change). All network results are cached to
   `galaxies/foreground/data/tier2_cache/` with retrieval dates.
3. Flip protocol (the frozen inputs are the immutable historical record —
   they are never mutated, so `tests/test_frozen_census.py` and the
   reproducibility doc's pinned hashes stay valid): each verdict flip is
   recorded as a row in a new tracked
   `galaxies/foreground/data/tier2_overrides.csv` (obj, old verdict, new
   verdict, datum that moved, retrieval date, cache path).
   `census_registry.py` gains an `--overrides <csv>` input applied after
   the frozen-input load; the tracked registry and downstream artifacts
   are regenerated with overrides; `tests/test_census_replay.py`'s
   invocation adds the same `--overrides` argument in the same commit. If
   the 49/29/7/13 partition changes, `merge_final.py`'s hard assert
   (`:88-96`) is updated in that commit too, and the change is surfaced to
   the owner in the phase report.
4. Deliverable: the verdict-flip table (rendered from
   `tier2_overrides.csv`), reviewed by the owner. Verification:
   `pytest tests/test_frozen_census.py tests/test_census_replay.py -q`
   passes with the overrides in place.

### P3.5 Halo-mass proxy provenance

1. Failing test first — extend `tests/test_census_audit.py`:

   ```python
   def test_mass_provenance_recorded():
       rows = list(csv.DictReader(AUDIT.open()))
       assert all(r["mass_source"] in {"MEASURED", "PREDICTED"}
                  for r in rows)
       fallback = [r for r in rows if r["mass_fallback_logm10"] == "1"]
       assert all("logM*=10" in r["verdict_basis"] for r in fallback)
   ```

2. Extend `build_audit.py` to emit `mass_source`
   (MEASURED/PREDICTED per `build_unified.py:415`), the mass-ladder branch
   taken (`build_unified.py:117-154`), a `mass_fallback_logm10` flag for
   the assumed logM*=10.0 fallback (`:154`), and the cluster M200=1.3·M500
   override (`:430-460`). Test passes.
3. Deliverable: the count and identity of PREDICTED-mass and fallback-mass
   systems among the 15 budget-eligible rows (`census_registry.py:76-82`)
   — these carry into V5's uncertainty discussion.

**Phase 3 deliverable (visibility):** census re-validation report
(`docs/rse/specs/` in Faber2026): Tier-1 replay result, audit table summary,
flip table, 12 audit figures, mass-provenance census.

## Phase 4 — V5 DM-budget re-validation [FLITS]

**Objective:** every model term externally oracled or explicitly
audit-noted; budget artifacts regenerated from the V4-verified census
through the P0.4 emitter.

### P4.1 Macquart-relation oracle

1. Failing test `tests/test_macquart_oracle.py` (new file) — independent
   inline implementation against `dm_cosmic_macquart`
   (`sightline_budget.py:130-151`, F_IGM=0.84 `:97`, CHI_E=0.875 `:98`,
   Planck18 per `galaxies/foreground/config.py:6`):

   ```python
   import numpy as np
   from astropy import constants as const, units as u
   from astropy.cosmology import Planck18

   from galaxies.foreground import sightline_budget as sb


   def _dm_cosmic_ref(z, n=20000):
       zs = np.linspace(0, z, n)
       ez = Planck18.efunc(zs)
       rho_b = Planck18.critical_density0 * Planck18.Ob0
       n_e0 = (sb.F_IGM * sb.CHI_E * rho_b / const.m_p).to(u.cm ** -3)
       integrand = (1 + zs) / ez
       dm = (const.c * n_e0 / Planck18.H0
             * np.trapezoid(integrand, zs)).to(u.pc / u.cm ** 3)
       return dm.value


   def test_macquart_matches_analytic_within_0p5pct():
       for z in (0.1, 0.3, 0.5):
           ours = sb.dm_cosmic_macquart(z)
           ref = _dm_cosmic_ref(z)
           assert abs(ours / ref - 1) < 5e-3, (z, ours, ref)


   def test_macquart_low_z_slope_is_standard():
       # all-baryon d<DM>/dz ≈ 930–990 pc cm^-3 as z→0 for Planck-like
       # parameters; the implementation includes F_IGM=0.84 and
       # CHI_E=0.875, so the expected slope is that band × F_IGM·χ_e
       # (measured 824.8 at the pin) — bracket set around the diluted
       # value, wide enough for parameter-set variation only
       slope = sb.dm_cosmic_macquart(0.02) / 0.02
       assert 780 < slope < 900
   ```

2. Run. A mismatch beyond 0.5% is a real V5 finding (implementation or
   constant drift); resolve before any budget regeneration. If the module
   applies a helium-ionization step in χ_e(z) that the flat-χ_e reference
   deliberately omits, the reference is upgraded to match the *stated*
   model in the manuscript methods — the test pins implementation to
   stated model, whichever way the discrepancy resolves. Commit.

### P4.2 Galactic terms: direct pygedm comparison

1. Script `galaxies/foreground/scripts/galactic_terms_check.py`: for each
   of the 12 sightlines, call `pygedm.dist_to_dm` directly (both NE2001
   and YMW16, 30 kpc) and diff against the budget chain's
   `galactic_dm_tau` pass-through (`sightline_budget.py:265-285`). Emit a
   12-row table and a paired-bar figure (visibility).
2. Acceptance: identity within float noise (it *is* a pass-through — any
   difference means the chain mutates the value somewhere, and that is the
   finding). The existing live bound test
   (`galaxies/foreground/test_sightline_budget.py:359-368`) stays as the
   CI guard.

### P4.3 Priors audit: MW halo, interior cap, mNFW lump constants

1. These are priors, not derivable facts — the deliverable is a written
   audit note in the phase report, per constant: the 40 pc cm⁻³ MW halo
   prior (`sightline_budget.py:90-92`) against the published 30–60
   plausible bracket; the 0.1 R_vir interior cap (`:73-77`, applied
   `:592-614`); A=1e-6 ms, COOL_CLUMP_BOOST=10, k_eff=0.3
   (`scattering_predict.py:163-194,208-243,64-90`). Each note names the
   source of the adopted value and what observable would move it.
2. Plus one computation: re-run the host-residual column with the halo
   prior at 30 and 60 (`--halo-prior` flag added to the `sightline_budget`
   CLI, default 40 — pass-through to the constant, no logic change) and
   report which sightlines' negative-residual status flips. Figure:
   residual per sightline with 30/40/60 whiskers. Run pre-Phase-3 this
   executes on the revoked census (useful for spotting implementation
   sensitivity early); the citable version is re-emitted at P4.5 on the
   V4-verified census — that one is what F1's budget-prose rewrite
   consumes.

### P4.4 mNFW second oracle point

1. The existing hard oracle pins one value
   (`galaxies/foreground/test_scattering_predict.py:183-187`,
   350.875 pc cm⁻³). Add a second, independently sourced point to the same
   file: the ProchaskaZheng2019 Milky-Way-like case (bib key at
   `bib/refs.bib:200`; M_halo = 10^12.18 M_sun profile at f_hot=0.75, α=2,
   y0=2 — the paper's own parameter choice). First step of the task:
   digitize the b = 50 kpc point from their Fig. 5 (fetch the published
   figure; do not trust a remembered value) and set the assertion bracket
   to digitized ± 15%. Test shape (bracket numbers replaced by the
   digitized band):

   ```python
   def test_mnfw_prochaska_zheng_mw_point():
       dm = dm_mnfw_projected(m_halo_msun=10**12.18, z_gal=0.0,
                              impact_kpc=50.0)
       assert LO_DIGITIZED < dm < HI_DIGITIZED
   ```

   (Entry point `dm_mnfw_projected` at `scattering_predict.py:369`;
   digitized bracket recorded in the test docstring with the figure
   panel/axis noted.)
2. Run; a failure indicts profile normalization (c=7.67, y0, f_hot
   handling) and blocks budget regeneration until explained. Commit.

### P4.5 Budget regeneration and parity

1. After Phase 3 lands: regenerate the budget from the V4-verified registry
   through the full chain
   (`conda run -n flits python -m galaxies.foreground.sightline_budget
   --emit-tex`), producing `exports/budget_table.tex` via the P0.4 emitter.
2. `tests/test_budget_table_emitter.py::test_emitted_tex_matches_committed_copy`
   passes against the *new* committed export; the diff against the old
   hand-transcribed manuscript table is attached to the phase report (the
   manuscript-side swap of `budget_table.tex` itself happens at the C3 pin
   bump, not here).
3. Re-run `sightline_sensitivity.py` (P(DM_host<0), `:277,306-308`) on the
   regenerated budget; figure: prior-predictive negative-residual
   probability per sightline, old vs new, side by side.

**Phase 4 deliverable (visibility):** budget re-validation report — oracle
results, pygedm parity table+figure, priors audit with the 30/40/60
sensitivity figure, regenerated-vs-old budget diff, sensitivity re-run.

## Phase 5 — V3 energies audit [FLITS]

**Objective:** the γ_D pile-up explained, the exporter's selection rule
explicit and enforced, the chromatica gate contradiction resolved. (Citable
energies still wait on lane-C re-fits; this phase makes the chain
trustworthy so those re-fits can flow through it.)

### P5.1 γ prior-rail study

1. Classify first (no new fits). The mixed-legacy generation stores no
   posterior samples — `joint_json/*_joint_fit.json` are percentile
   summaries — so sample-based `classify_rail` cannot run on it. Add a
   CI-based companion to the SSOT, `flits/fitting/rails.py`:

   ```python
   def classify_rail_from_ci(median, ci_lo, ci_hi, lo, hi, *,
                             prox_abs=PROX_ABS):
       """Percentile-summary variant: rail if the median is within
       prox_abs of a bound, or the quoted CI touches it (the CI plays
       the 3σ-proximity role; edge-mass is unavailable without samples).
       """
       if hi - median <= prox_abs or ci_hi >= hi:
           return "railed-hi"
       if median - lo <= prox_abs or ci_lo <= lo:
           return "railed-lo"
       return "interior"
   ```

   Failing test first (extend `tests/test_rails.py`): chromatica's γ_D
   summary (lower CI −4.9937) must classify `railed-lo` at bounds (−5, 5);
   a summary with median −3.0, CI (−3.4, −2.6) must classify `interior`.
   Then run it over γ_C and γ_D of all 11 committed joint fits
   (`analysis/scattering-refit-2026-06/joint_json/`), bounds (−5, 5) from
   `burstfit.py:1403`. Deliverable table: per burst × band, verdict +
   distance of median from −5, rendered as point-interval marks.
2. Run the relaxation harness on the RAILED list
   (`analysis/burst_energies/refit_calibrated.py` — RAILED `:57` =
   chromatica, oran, phineas, zach, freya; `GAMMA_FLOOR=-10` `:61`). The
   script is currently a bare `main()` with outputs hardwired to
   `analysis/burst_energies/`; first add a minimal CLI — `--targets
   <comma-list|railed>` and `--outdir` (default the new
   `analysis/burst_energies/gamma_floor_study/`) — touching only target
   selection and output paths, no likelihood/model change. Then:

   ```bash
   conda run -n flits python analysis/burst_energies/refit_calibrated.py \
     --targets railed --outdir analysis/burst_energies/gamma_floor_study
   ```

   Diagnostic run — outputs never land in `joint_json/` or the citable
   `burst_energies` artifacts; these are not citable fits, per What We're
   NOT Doing.
3. Pre-registered read-out: for each target, does the γ posterior move off
   −5 and become interior at the wider bound (⇒ the −5 bound was binding
   and the committed γ_D values are prior artifacts), or does it pile at
   −10 (⇒ the spectral model itself is degenerate for that burst)? Figure
   (visibility): per-burst γ_D posterior violins at floor −10 (samples
   exist for these new diagnostic runs) against the committed −5-floor
   point-interval summaries.
4. Record the verdict per burst in `analysis/fit_generations.yaml` (P0.3)
   under the mixed-legacy generation's `known_conflicts:`.

### P5.2 Exporter selection-rule enforcement

1. Failing test `tests/test_energies_selection_rule.py` (new file):

   ```python
   import json
   import pathlib

   ROOT = pathlib.Path(__file__).parents[1]
   OUT = ROOT / "analysis/burst_energies/burst_energies.json"
   PROV = ROOT / "analysis/burst_energies/burst_energies.provenance.json"


   def test_provenance_states_selection_rule():
       prov = json.loads(PROV.read_text())
       rule = prov["selection_rule"]
       assert rule["requires_spec_z"] is True
       assert rule["requires_both_band_fluxcal"] is True
       assert rule["scattering_gate_used"] == "informational"


   def test_no_railed_gamma_row_without_flag():
       rows = json.loads(OUT.read_text())["bursts"]
       for r in rows:
           if r["gamma_rail_verdict"] != "interior":
               assert r["quality_flags"]["gamma_railed"] is True
   ```

2. Implement in `analysis/calculate_burst_energies.py`: (a) emit the
   explicit `selection_rule` block into the provenance JSON (`:544`) —
   codifying what `load_joint_params`/`compute` already do
   (`:182-190,237-239,248,269`): spec-z + both-band fluxcal + physical
   amplitudes, scattering gate informational; (b) call
   `classify_rail_from_ci` (P5.1) on each consumed γ percentile summary
   and stamp `gamma_rail_verdict` + `gamma_railed` quality flag per row;
   (c) exit nonzero if any railed-γ row lacks the flag. Re-run the exporter on the committed (revoked)
   inputs to regenerate the JSON artifacts with flags; tests pass. This
   also settles the F1 wording question: the table's stated criterion
   becomes the selection rule and "quality-passing" language is retired —
   the 20240203A contradiction dissolves (its inclusion basis is spec-z +
   fluxcal, gate status disclosed, γ flagged).

### P5.3 Chromatica gate resolution

1. Root-cause the three-way inconsistency: read
   `joint_json/chromatica_joint_gate.json` (MARGINAL, χ²=null) and the β
   campaign's gate artifact for chromatica; diff their producing scripts'
   inputs (which fit JSON each consumed, per `gate_joint_committed.py:8-10`
   and the β campaign's grading in `grade_beta_campaign.py`). Expected
   resolution shape: the committed gate ran on the mixed-legacy fit where
   τ·Δν_d was unevaluable (capped MARGINAL per
   `gate_joint_committed.py:93-100`), while the prose's FAIL 11.6/9.3 comes
   from the β-campaign fit — two generations, two verdicts, both revoked.
   If the evidence contradicts that shape, the actual chain found is
   recorded instead; the deliverable is the evidenced chain, not the guess.
2. Record the resolution in `fit_generations.yaml` `known_conflicts:` with
   both artifact paths and the rule going forward: *a gate verdict is
   bound to its generation; cross-generation quoting is forbidden* (also
   written into ADR-0008 rung (v), per P1.5). No manuscript edit here
   (F1's job).

### P5.4 Flux-scale audit

1. Verify the two instrument constants against their sources: CHIME SEFD
   34.5 Jy and DSA per-element 8016.2 Jy / 48 antennas
   (`analysis/calculate_burst_energies.py:77` `BAND_SYS_DEX`, folded
   `:279-288`; radiometer path `analysis/flux_cal.py:271`). Check against
   the CHIME/FRB system paper and the DSA-110 system description (both
   already cited in the manuscript bib); record page/section in a comment
   at the constant definitions and in the phase report. Acceptance: each
   constant either matches a citable source or the discrepancy is flagged
   to the owner (these numbers scale every energy linearly).

**Phase 5 deliverable (visibility):** energies audit report — γ rail table
and violin figure, the enforced selection rule, the chromatica resolution
note, flux-constant citations.

## Phase 6 — V6 association + DM_obs re-validation [FLITS] (wave 3)

**Objective:** per-burst, per-telescope DM_obs provenance with quantified
CHIME↔DSA agreement; TOA association arithmetic re-derived from raw
inputs. Re-certifies the co-detection sample membership. Runs any time
after Phase 0; no dependence on Phases 1–5 beyond ADR-0008 acceptance.

### P6.1 Anchor inventory (read-only exploration)

1. The V1–V5 phases were grounded by five explorer reports; wave 3 arrived
   after that sweep, so Phase 6 starts with its own scoped exploration.
   Known anchors going in: `crossmatching/association.py`,
   `toa_crossmatch.py`, `chime_singlebeam.py`;
   `crossmatching/chime_side_inputs.json` (per-burst `dm_dsa`, `dm_chime`,
   `dm_chime_err` — both-telescope DMs already exist here);
   `crossmatching/association_report.json` (keys: `inputs`,
   `expected_chance_associations`, `bursts`); tests
   `tests/test_association.py`, `tests/test_chime_dm.py`,
   `tests/test_chime_singlebeam_toa.py`,
   `tests/test_crossmatching_notebook_reproduction.py`.
2. The exploration answers, with file:line: (a) where each burst's DSA-side
   DM comes from (which pipeline, which dedispersion criterion) and where
   the CHIME-side values in `chime_side_inputs.json` were produced;
   (b) which manuscript surfaces quote DM_obs and TOA
   residuals/P_cc (sections/toa.tex, the budget table's DM_obs column,
   observations §2); (c) whether the association arithmetic in
   `association.py`/`toa_crossmatch.py` reproduces
   `association_report.json` at the pin. Findings appended to
   [research-trust-reset-revalidation.md](research-trust-reset-revalidation.md)
   as a V6 section.

### P6.2 Per-burst DM provenance table + agreement figure

1. Failing test `tests/test_dm_provenance.py` (new file):

   ```python
   import csv
   import pathlib

   ROOT = pathlib.Path(__file__).parents[1]
   TAB = ROOT / "crossmatching/dm_provenance.csv"

   REQUIRED = {"nickname",
               "dm_dsa", "dm_dsa_err", "dm_dsa_method", "dm_dsa_source",
               "dm_chime", "dm_chime_err", "dm_chime_method",
               "dm_chime_source", "delta_dm", "delta_dm_sigma"}


   def test_dm_provenance_covers_all_twelve():
       rows = list(csv.DictReader(TAB.open()))
       assert len(rows) == 12
       assert REQUIRED <= set(rows[0])
       assert all(r["dm_dsa_method"] and r["dm_chime_method"]
                  for r in rows)
       assert all(r["dm_dsa_source"] and r["dm_chime_source"]
                  for r in rows)
   ```

2. Implement `scripts/build_dm_provenance.py`: join
   `chime_side_inputs.json`'s per-burst `dm_chime`/`dm_chime_err` with the
   DSA-side DM source located in P6.1; `*_method` states the dedispersion
   criterion (structure-maximizing vs S/N-maximizing vs catalog value),
   `*_source` cites the producing artifact (path or DOI); `delta_dm` and
   `delta_dm_sigma` quantify per-burst CHIME−DSA agreement. Where a value
   has no locatable producer, the method/source cells read
   `UNDOCUMENTED` and the row is a finding — the test still passes
   (cells non-empty) while the report flags it.
3. Figure (visibility): per-burst ΔDM with error bars, zero line, and a
   σ-agreement axis — the direct answer to "by how much do they agree."

### P6.3 TOA association re-derivation

1. Failing check first: run the existing oracles at the pin —
   `conda run -n flits python -m pytest tests/test_association.py
   tests/test_chime_singlebeam_toa.py
   tests/test_crossmatching_notebook_reproduction.py -q` — record
   pass/fail as the baseline.
2. Re-derive: execute `crossmatching/toa_crossmatch.py` and
   `association.py` from their raw inputs (positions, timestamps,
   `chime_side_inputs.json`) and diff the regenerated report against the
   committed `crossmatching/association_report.json` (per-burst residuals,
   `expected_chance_associations`). Byte/value parity ⇒ the arithmetic is
   reproducible at the pin; any mismatch is a finding resolved before the
   sample membership is re-certified.
3. Deliverable: re-derived association table (per burst: TOA residual,
   chance-association expectation, verdict) with the P6.2 figure in a
   `docs/rse/specs/` report (Faber2026), closing V6.

**Phase 6 deliverable (visibility):** association + DM report — the
provenance table, the ΔDM agreement figure, the re-derived association
table, and the list of `UNDOCUMENTED` cells (if any) as named findings.

## Success Criteria

### Automated

- FLITS clone, all new tests green, no xfail markers remaining (single
  sanctioned exception: the P0.4 catalog-parity xfail may persist until
  P4.5 replaces the committed copy, with its diff logged in the Phase 0
  deliverable):
  `conda run -n flits python -m pytest tests/test_data_manifest.py
  tests/test_frozen_census.py tests/test_fit_generations.py
  tests/test_budget_table_emitter.py tests/test_catalog_table_emitter.py
  tests/test_adjudication_imports.py tests/test_rails.py
  tests/test_rails_is_ssot.py tests/test_ppc.py
  tests/test_recovery_campaign.py tests/test_census_replay.py
  tests/test_census_audit.py tests/test_impact_params_independent.py
  tests/test_macquart_oracle.py tests/test_energies_selection_rule.py
  tests/test_dm_provenance.py -q`
- `FLITS_DATA=~/Data/Faber2026 conda run -n flits python -m pytest
  tests/test_cube_integrity.py -q` green on jakob-mbp.
- `node .claude/workflows/fit-verify.js --list-coverage | rg -q joint_gate`.
- Full existing suite still green:
  `conda run -n flits python -m pytest tests/ galaxies/ -q`.
- `rtk grep -c PENDING data-manifest.csv` returns no matches.
- Faber2026: `make` exits 0 (docs-only changes must not break the build).

### Manual

- Owner reviews and accepts: the Tier-2 verdict-flip table (P3.4), the
  halo-prior 30/40/60 sensitivity figure (P4.3), the γ floor study
  verdicts (P5.1), and the budget tex parity diff (P0.4/P4.5).
- ADR-0008 merged via FLITS PR review.
- Per-burst provenance table (P2.5) spot-checked against h17 by the owner
  (or via the h17-ssh-troubleshooter lane if h17 is unreachable).
- Each phase's visibility deliverable exists and is legible without this
  plan open beside it.

## Testing Strategy

- **Unit:** rails classifier, PPC p-values, manifest / frozen-census /
  generation-inventory invariants, emitter markup — plain pytest, no
  network, no data root.
- **Oracle:** Macquart analytic reference, mNFW published points, pygedm
  pass-through identity, independent astropy impact parameters — external
  truth, tight tolerances, run in CI.
- **Data-gated:** cube integrity and cross-lineage tests skip without
  `FLITS_DATA`; run explicitly on jakob-mbp and h17.
- **Replay/regression:** census Tier-1 byte-parity; β-campaign rail
  reclassification guard (P1.1 step 3); the existing suite as backstop.
- **Manual:** owner review of every judgment-bearing deliverable (flip
  table, sensitivity figures, γ study) — these are decisions, not checks.

## References

- [research-trust-reset-revalidation.md](research-trust-reset-revalidation.md)
  — the five exploration inventories (V1–V5) with all file:line anchors.
- [plan-circulation-readiness.md](plan-circulation-readiness.md) — parent
  plan; this document is its §V expansion.
- `CONTEXT.md` "Trust reset" — the governing owner decision.
- `pipeline/docs/adr/0006-beta-coherent-scattering-comodel.md`,
  `0007-extended-medium-pbf-for-shallow-alpha.md` — the model-selection
  frame ADR-0008 plugs into.
- `pipeline/docs/rse/specs/reproducibility-foreground-galaxies.md` — pinned
  census input/output hashes (Tier-1 ground truth).
- `pipeline/scintillation/DATA_PROVENANCE.md` — h17/arc geography for
  Phase 2.
- [handoff-2026-07-06-14-50-chime-sample-regeneration.md](handoff-2026-07-06-14-50-chime-sample-regeneration.md)
  — gen-2 regeneration state consumed by P2.3's cross-lineage check.
