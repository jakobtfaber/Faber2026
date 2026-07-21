# Implementation Plan: Expanded foreground catalog repair

---
**Date:** 2026-07-20
**Author:** Codex
**Status:** In progress — blocked by authoritative host-redshift evidence
**Related Documents:**
- [Wayfinder map](../wayfinder/map-expanded-foreground-catalog-repair.md)
- [Invalid validation](validation-expanded-foreground-photometry-and-morphology-catalog.md)
- [Current catalog description](expanded_foreground_photometry_and_morphology_catalog.md)
- [Figure validation](validation-sightline-halo-grid.md)

---

## Overview

Repair the catalog without allowing the expanded crossmatch product to replace
the adjudicated foreground census. First fail-close the false validation. Then
make matching deterministic and inspectable, correct the physics interfaces and
applicability gates, rebuild versioned catalog and Figure 3 inputs, stage Figure
3, and repeat validation through an independent calculation path.

**Goal:** A committed, reproducible catalog and Figure 3 whose inputs, equations,
quality states, uncertainties, and approval receipts can be checked offline.

**Motivation:** The current builder selects arbitrary response rows, hides query
errors, passes linear stellar mass to a logarithmic interface, misstates Cluver
and Stern, reports incomplete catalog coverage as 52/52, and leaves the plotted
input outside version control.

## Current State Analysis

**Existing implementation:**

- `scripts/build_expanded_foreground_provenance.py:31-60` computes diagnostic
  masses, including the linear-versus-logarithmic Moster input error.
- `scripts/build_expanded_foreground_provenance.py:63-125` requests five rows,
  takes row zero, and suppresses all exceptions.
- `scripts/build_expanded_foreground_provenance.py:154-191` treats Stern color as
  a starlight proof and emits physics without applicability or error states.
- `pipeline/galaxies/foreground/generate_galaxy_plots.py:42-86` contains a fixed
  redshift-zero Moster relation and an approximate Dutton-Macciò evolution.
- `pipeline/galaxies/foreground/vo/halos.py:39-77` already contains the correct
  redshift-dependent Moster parameterization and a linear-mass interface.
- `pipeline/galaxies/foreground/census_registry.py:220-300` records duplicate,
  mass, and owner adjudications; these remain authoritative.
- `figures/catalog.yaml:55-73` declares no input or review gate for Figure 3.
- `pipeline/galaxies/v2_0/sightline_halo_grid.py:54-94` defaults to an external,
  unversioned CSV.
- `docs/rse/specs/validation-expanded-foreground-photometry-and-morphology-catalog.md:1-38`
  currently says Ready/Verified despite the defects.

**Observed audit facts:**

- Live 3-arcsecond queries returned GSC 48/52, ALLWISE 47/52, CatWISE 49/52,
  and unWISE 48/52; only 46 rows had all four, not 52.
- Nearest-match selection differs from stored selection in 10 GSC, 4 CatWISE,
  and 10 unWISE rows. Four GSC differences change the morphology code.
- Three ALLWISE W2 values are upper-limit or invalid-quality measurements;
  11 sources carry extended-source flags.
- Only 21 of 47 ALLWISE matches satisfy the Stern `W2 <= 15.05` depth condition.
- The stored radii are roughly 2.5-3.0 Mpc because the builder exponentiates
  `log(M*)` before passing it to an interface that expects `log(M*)`.
- The expanded CSV copies all 52 census verdicts exactly; it does not independently
  validate them.

## Desired End State

The pipeline owns normalized query snapshots, deterministic matching, corrected
physics helpers, the rebuilt CSV, and a versioned Figure 3 input. The parent repo
owns the rendered catalog description, validation reports, figure workflow, and
manuscript artifact. Parent and pipeline commits are recorded together.

**Success looks like:**

- Every catalog has identifier, status, separation, candidate count, second
  separation, errors, native quality flags, release, retrieval time, and snapshot
  hash columns.
- Every derived field has value, uncertainty, method, source authority, units,
  and status. Inapplicable values are null, never silently substituted.
- Candidate verdicts and budget eligibility equal the census registry byte for
  byte unless a separate adjudication changes them.
- Figure 3 reads only the checked-in corrected input and is promoted only through
  an approval receipt.
- An independent report reproduces the equations and row-level match checks.

## What We're NOT Doing

- [ ] Reclassifying candidates from GSC morphology alone.
- [ ] Changing a foreground redshift or budget flag without a separate,
      evidence-backed adjudication record. Independent verification remains in
      scope and blocks Figure 3.
- [ ] Replacing owner-adjudicated masses with fresh WISE estimates.
- [ ] Converting cluster `M500/R500` to `M200c/R200c` without a separately named
      and validated cluster profile model.
- [ ] Treating a non-Stern-selected object as proven starlight-dominated.
- [ ] Silently bumping the `pipeline/` submodule during unrelated manuscript work.

## Implementation Approach

**Technical strategy:** Put the scientific and catalog logic in pure pipeline
functions. Make network refresh a separate command that writes normalized,
hashable snapshots. Build products offline from those snapshots. Keep the
catalog description generated from the CSV schema and summary, not as an
independent truth surface.

**Key decisions:**

1. **Census authority is immutable in this lane.** Crossmatches are evidence,
   not verdict generators. This prevents morphology or WISE artifacts from
   undoing redshift adjudication.
2. **Use `R200c`, not “virial radius.”** Compute it directly from
   `M200c = (4π/3) 200 ρcrit(z) R200c^3`. Concentration only supplies `r_s`.
3. **Cluver is conditional.** Implement Equation 2 (`-2.54`, `-0.17`) with an
   explicit rest-frame-color flag. Do not compute it from invalid/upper-limit
   photometry or use a colorless fallback.
4. **Stern is a selection, not a decomposition.** Emit
   `selected_by_stern12`, `not_selected_within_depth`,
   `outside_validated_depth`, or `insufficient_color`.
5. **Network-independent build.** Tests and normal regeneration consume committed
   fixtures; only `refresh` contacts VizieR.

**Patterns to follow:**

- Nearest angular match: `pipeline/galaxies/foreground/adjudication/validate_foreground.py:50-65`.
- Redshift-dependent Moster inversion: `pipeline/galaxies/foreground/vo/halos.py:39-77`.
- Census deduplication and mass authority: `pipeline/galaxies/foreground/census_registry.py:220-300`.
- Fail-closed figure staging and receipts: `scripts/figure_review.py:98-258,394-469`.

## Implementation Phases

### Phase 1: Fail-close existing validation

**Objective:** Make the present artifact unusable as accepted evidence before
repair work starts.

**Tasks:**

- [x] Add `tests/test_expanded_catalog_validation.py` first:

  ```python
  def test_expanded_catalog_validation_is_fail_closed():
      text = Path("docs/rse/specs/validation-expanded-foreground-photometry-and-morphology-catalog.md").read_text()
      assert "FAILED — superseded; do not use" in text
      assert "Ready / Verified" not in text
  ```

- [x] Run and observe failure:
  `uv run pytest tests/test_expanded_catalog_validation.py -q`.
- [x] Rewrite the validation header and verdict. Add a defect table with affected
  formula, rows/count, scientific effect, and required repair. Add
  `docs/rse/specs/validation-expanded-foreground-catalog.json` with
  `status: failed`, parent commit, pipeline commit, and defect identifiers.
- [x] Add a validator assertion that any non-pass defect makes the command exit 1.
- [x] Run and observe pass:
  `uv run pytest tests/test_expanded_catalog_validation.py -q`.
- [x] Commit only the fail-close files:
  `git commit --only tests/test_expanded_catalog_validation.py docs/rse/specs/validation-expanded-foreground-photometry-and-morphology-catalog.md docs/rse/specs/validation-expanded-foreground-catalog.json -m "docs: fail-close expanded foreground validation"`.

**Verification:** `! rg -n "Ready / Verified|52 / 52.*matched" docs/rse/specs/validation-expanded-foreground-photometry-and-morphology-catalog.md`.

### Phase 2: Fix matching and physics

**Objective:** Establish tested pure functions before rebuilding any artifact.

**Tasks:**

- [x] Add `pipeline/galaxies/foreground/test_expanded_catalog.py` with failing
  tests for nearest-row order independence, unmatched versus query error,
  ambiguity, quality retention, Cluver applicability, Stern depth, Moster units,
  `R200c`, and Dutton-Macciò concentration:

  ```python
  def test_match_is_nearest_not_first():
      rows = fixture_rows(separations_arcsec=[2.1, 0.2, 1.0])
      match = select_match(rows, radius_arcsec=3.0, ambiguity_arcsec=0.3)
      assert match.selected_index == 1
      assert match.candidate_count == 3
      assert match.separation_arcsec == pytest.approx(0.2)

  def test_moster_and_r200c_reference_case():
      m200 = mstar_to_mhalo(1.0e10, z=0.2)
      assert np.log10(m200) == pytest.approx(11.5997073, abs=1e-6)
      r200 = m200c_to_r200c(m200, z=0.2)
      enclosed = 4 * np.pi / 3 * r200**3 * 200 * rho_critical_msun_kpc3(0.2)
      assert enclosed == pytest.approx(m200, rel=1e-10)

  def test_stern_depth_is_required():
      assert stern12_status(0.9, w2=15.2) == "outside_validated_depth"
      assert stern12_status(0.7, w2=14.0) == "not_selected_within_depth"
  ```

- [x] Run and observe failure:
  `cd pipeline && uv run pytest galaxies/foreground/test_expanded_catalog.py -q`.
- [x] Add `pipeline/galaxies/foreground/expanded_catalog.py` with typed match
  records and these exact public interfaces:

  ```python
  select_match(rows, target, radius_arcsec, ambiguity_arcsec) -> CatalogMatch
  cluver14_log_mstar(w1, w2, distance_modulus, *, rest_frame, valid_photometry) -> DerivedValue
  stern12_status(w1_minus_w2, w2, *, color_valid) -> str
  m200c_to_r200c(m200c_msun, z) -> float
  dutton_maccio14_c200c(m200c_msun, z, h) -> float
  ```

  `dutton_maccio14_c200c` uses
  `b=-0.101+0.026z` and
  `a=0.520+(0.905-0.520) exp(-0.617 z^1.21)`, with
  `log10(c200)=a+b log10(M200 h / 10^12 M_sun)`.
- [x] Reuse `vo.halos.mstar_to_mhalo(mstar, z)`; remove the exponentiation plus
  logarithmic-helper path from the expanded builder. Deprecate the approximate
  helper for catalog use; do not rewrite unrelated plot products in this phase.
- [x] Run and observe pass:
  `cd pipeline && uv run pytest galaxies/foreground/test_expanded_catalog.py galaxies/foreground/test_census_registry.py -q -k 'not scratch_codetection_exists'`.
- [x] Commit in `pipeline/`:
  `git commit --only galaxies/foreground/expanded_catalog.py galaxies/foreground/test_expanded_catalog.py galaxies/foreground/vo/halos.py -m "fix: correct foreground matching and halo physics"`.

**Verification:** Tests must compare published coefficients and an independently
computed enclosed-mass invariant, not values produced by the same helper.

### Phase 3: Rebuild catalog with quality and error columns

**Objective:** Produce a versioned, offline-rebuildable 52-row audit table.

**Tasks:**

- [x] Extend the failing tests with a schema fixture. Required per-catalog fields:
  `status`, `id`, `separation_arcsec`, `candidate_count`,
  `second_separation_arcsec`, `release`, `retrieved_at_utc`, `snapshot_sha256`.
  Require GSC class; ALLWISE W1/W2 values, errors, `qph`, `ccf`, `ex`; CatWISE
  profile magnitudes/errors, `pmQual`, `abf`, `ccf`; unWISE flux/errors,
  `q_W1`, `q_W2`, `fFW1`, `fFW2`. Require every derived field's value, error,
  method, units, authority, and status.
- [x] Run and observe schema failure:
  `cd pipeline && uv run pytest galaxies/foreground/test_expanded_catalog.py -q -k schema`.
- [x] Add normalized fixtures under
  `pipeline/galaxies/foreground/data/catalog_crossmatch_snapshots/` and a refresh
  CLI `pipeline/galaxies/foreground/refresh_expanded_catalog.py`. Use a 3-arcsecond
  cone, exact spherical separation, stable sorting by separation then identifier,
  and one recorded response per catalog/candidate. A failed catalog query exits
  nonzero unless `--allow-partial-refresh` is explicit; it never overwrites the
  last complete snapshot.
- [x] Add offline builder
  `pipeline/galaxies/foreground/build_expanded_catalog.py`. Join census keys as
  strings, assert exactly 52 unique registry rows, copy verdict fields unchanged,
  apply overrides before Moster, recompute `M200c/R200c`, leave inadmissible
  Cluver and unknown errors null with a status, and preserve cluster `M500/R500`.
- [x] Write outputs atomically:
  `pipeline/galaxies/foreground/data/expanded_catalog_cross_references.csv` and
  `pipeline/galaxies/foreground/data/expanded_catalog_build.json`.
- [x] Replace `scripts/build_expanded_foreground_provenance.py` with a parent-side
  renderer that reads the pinned CSV and build manifest but never writes into the
  submodule. Regenerate
  `docs/rse/specs/expanded_foreground_photometry_and_morphology_catalog.md`.
- [x] Run and observe pass:
  `cd pipeline && uv run python galaxies/foreground/build_expanded_catalog.py --offline && uv run pytest galaxies/foreground/test_expanded_catalog.py -q`.
- [x] Verify deterministic bytes:
  `shasum -a 256 galaxies/foreground/data/expanded_catalog_cross_references.csv > /tmp/expanded.before && uv run python galaxies/foreground/build_expanded_catalog.py --offline && shasum -a 256 -c /tmp/expanded.before`.
- [ ] Commit pipeline code, fixtures, and outputs; then make a separate parent
  commit for the deliberate submodule pin and regenerated documentation.

**Verification:** An integration test asserts 52 registry rows, unique composite
keys, exact verdict equality, no silent query errors, no finite derived value
with a non-pass status, and no legacy `R_vir` column.

### Phase 4: Re-render Figure 3 through review staging

**Objective:** Make the figure consume only corrected, checked-in data without
overwriting the manuscript artifact before approval.

**Tasks:**

- [x] Add failing pipeline tests for a new
  `pipeline/galaxies/foreground/data/sightline_halo_grid.csv`: only confirmed,
  deduplicated systems may be drawn; `budget_eligible` controls the contributor
  overlay rather than admission to the environment plot; each halo uses corrected
  `M200c/R200c`; each cluster uses explicitly sourced cluster geometry; the host
  roster includes empty sightlines.
- [x] Add a generator `pipeline/galaxies/foreground/build_sightline_halo_grid_input.py`
  and change `pipeline/galaxies/v2_0/sightline_halo_grid.py` to require
  `--halo-csv`. Remove `DEFAULT_HALO_CSV` and rename plot labels/fields to
  `M200c` and `R200c`.
- [x] Run pipeline tests:
  `cd pipeline && uv run pytest galaxies/foreground/test_expanded_catalog.py galaxies/v2_0/test_sightline_halo_grid.py -q`.
- [x] Add `fig3-halo-grid` with family `foreground-halo-grid` to
  `figure_review/slots.json`. Extend `scripts/figure_review.py` so that family
  requires and copies the expanded-catalog build manifest, independent validation
  JSON, and Figure 3 input hash. Change
  `figures/catalog.yaml` so its declared input is the versioned figure CSV, its
  output is
  `figure_review/staging/fig3_halo_grid/figures/sightline_halo_grid.pdf`, its
  `candidate_root` is `figure_review/staging/fig3_halo_grid`, and its
  `approval_slot` is `fig3-halo-grid`.
- [x] Test the workflow first (approval test intentionally remains closed pending receipt):
  `uv run pytest tests/test_figure_flow.py tests/test_figure_review_cli.py tests/test_figure_approval.py -q`.
- [x] Dry-run, then render staging bytes:
  `python3 scripts/figure_flow.py regen --id sightline_halo_grid --dry-run` and
  `python3 scripts/figure_flow.py regen --id sightline_halo_grid`.
- [ ] Create and render a review batch only after Phase 5 passes:
  `python3 scripts/figure_review.py new-batch 2026-07-20-fig3-halo-grid --title "Figure 3: foreground halo sightlines" --candidate fig3-halo-grid --candidate-root figure_review/staging/fig3_halo_grid --pipeline-revision $(git -C pipeline rev-parse HEAD)`;
  `python3 scripts/figure_review.py render 2026-07-20-fig3-halo-grid`.
- [ ] After manuscript-owner approval, record and promote:
  `python3 scripts/figure_review.py decide 2026-07-20-fig3-halo-grid fig3-halo-grid approved --reviewer "Jakob Faber" --note "Approved corrected Figure 3 after visual inspection"`;
  `python3 scripts/figure_review.py promote 2026-07-20-fig3-halo-grid fig3-halo-grid`;
  `python3 scripts/figure_review.py verify`.

**Verification:** Before approval, `git diff -- figures/sightline_halo_grid.pdf`
must be empty. After promotion, candidate, target, and receipt hashes must match.
Compile the manuscript and confirm the current numbering is Figure 3 rather than
relying on the stale “Figure 2” validation text.

### Phase 5: Repeat independent validation

**Objective:** Validate source-to-claim correctness without importing builder
result functions or trusting its prose.

**Tasks:**

- [ ] Add `scripts/validate_expanded_foreground_catalog_independent.py`. It may
  read snapshots, census inputs, and paper constants; it must not import
  `expanded_catalog.py`, the old builder, or generated result columns as expected
  values.
- [ ] Build
  `docs/rse/specs/validation-expanded-foreground-redshifts.csv` independently
  from the registry. For every row record host and candidate source/release,
  identifier, spectroscopic or photometric kind, redshift, uncertainty, retrieval
  date, recomputed verdict, stored verdict, budget eligibility, and disposition.
  Do not treat the registry value itself as verification evidence.
- [ ] Recompute each verdict using the documented census rule: secure redshift
  below the host is foreground; secure redshift above the host is refuted;
  overlapping photometric uncertainty or missing host evidence is inconclusive.
  Verify duplicate removal and the separate budget gate. Any unexplained mismatch
  exits nonzero and blocks Figure 3; any correction requires a dedicated
  adjudication record and manuscript-owner approval.
- [ ] Add failing tamper tests in
  `tests/test_validate_expanded_foreground_catalog_independent.py` for wrong match
  identifier, swapped W1 error, linear/log Moster error, wrong `R200c`, invalid
  Stern depth, changed verdict, stale figure-input hash, and missing approval.
- [ ] Run and observe failures:
  `uv run pytest tests/test_validate_expanded_foreground_catalog_independent.py -q`.
- [ ] Implement independent spherical separations, Cluver applicability checks,
  redshift-dependent Moster inversion, critical-density `R200c`, Dutton-Macciò
  concentration, Stern categories, row/count reconciliation, and figure-input
  hash checks. Emit JSON plus Markdown with every mismatch.
- [ ] Run and observe pass:
  `uv run python scripts/validate_expanded_foreground_catalog_independent.py --catalog pipeline/galaxies/foreground/data/expanded_catalog_cross_references.csv --json docs/rse/specs/validation-expanded-foreground-catalog.json --markdown docs/rse/specs/validation-expanded-foreground-photometry-and-morphology-catalog.md`;
  `uv run pytest tests/test_validate_expanded_foreground_catalog_independent.py -q`.
- [ ] Re-run all scoped checks from a clean worktree at the recorded parent and
  pipeline commits. Record Python lockfile hash, snapshot hashes, commands,
  counts, tolerances, and output hashes.
- [ ] Only then change the report to `Verified`, create the Figure 3 review batch,
  request owner visual approval, promote, compile, and rerun the validator with
  `--require-approved-figure`.

**Verification:** Zero unexplained row differences; all 52 census classifications
and verdicts equal their source; numerical differences are below `1e-10` relative
for the `R200c` enclosed-mass identity and `1e-6` dex for independently inverted
Moster values; all catalog selections reproduce from normalized snapshots.

## Success Criteria

### Automated Verification

- [ ] Current validation is fail-closed before repair.
- [ ] Pipeline match, physics, census, and figure-input tests pass.
- [ ] Parent validation and figure-workflow tests pass.
- [ ] Offline rebuild produces identical CSV and manifest hashes.
- [ ] The figure catalog reports no missing input for `sightline_halo_grid`.
- [ ] Independent validation exits zero and records both Git commits.
- [ ] All 52 redshift/verdict rows have independent source evidence or an explicit
      blocking disposition; no registry value self-validates.
- [ ] `python3 scripts/figure_review.py verify` passes after owner approval.
- [ ] Manuscript build passes and embeds the promoted hash.

### Manual Verification

- [ ] Inspect all ambiguous matches and every morphology change from the old file.
- [ ] Confirm GSC class is reported as catalog morphology evidence, not a verdict.
- [ ] Confirm Figure 3 shows the intended sightline roster, corrected circle
  scales, one consistent mass definition, readable labels, and no plot title.
- [ ] Manuscript owner approves the staged Figure 3 evidence card.

### Reproducibility and Correctness

- [ ] Snapshot catalog release, retrieval time, query, search radius, row data,
  and SHA-256 are recorded.
- [ ] Linear/logarithmic units, Vega magnitude system, rest-frame requirement,
  cosmology, `h`, mass definition, and radius definition are explicit.
- [ ] Unknown errors remain unknown; no fallback uncertainty or value is invented.
- [ ] Clean-worktree rebuild and independent validation reproduce exact artifacts.

## Testing Strategy

Unit tests cover match ordering, ambiguity, status separation, catalog flags,
formula coefficients, units, applicability, and analytic invariants. Integration
tests cover registry joins, overrides, deduplication, 52-row completeness,
offline hashes, figure-input filtering, staging, approval, and manuscript build.
Fixtures are normalized VizieR responses committed with their query metadata;
live network results are never test expectations.

## Migration Strategy

1. Land pipeline logic, fixtures, corrected CSV, and Figure 3 input on a focused
   pipeline branch and review them there.
2. Deliberately bump the parent submodule pin in a separate focused commit.
3. Regenerate parent documentation and independent validation.
4. Stage Figure 3; preserve installed bytes until approval.
5. Promote exact approved bytes and compile.

**Rollback:** Revert the parent promotion/pin commit and pipeline repair commit.
The failed validation remains in history, and immutable review batches retain
both candidate and receipt evidence.

**Backward compatibility:** Preserve census keys and verdict columns. Consumers
must migrate from ambiguous `derived_rvir_kpc` to explicit `m200c_msun` and
`r200c_kpc`; reject the legacy field rather than aliasing it.

## Risk Assessment

1. **Catalog services drift or fail.** Likelihood medium; impact medium. Normalize
   and hash responses, keep refresh separate, and never overwrite complete
   snapshots with partial results.
2. **WISE blends bias stellar mass.** Likelihood medium; impact high. Retain
   extension/artifact flags and owner overrides; diagnostic Cluver values do not
   supersede adopted masses.
3. **Mass definitions mix.** Likelihood medium; impact high. Encode `M200c`,
   `R200c`, `M500`, and `R500` in names and units; prohibit generic `Rvir`.
4. **Figure promotion outruns validation.** Likelihood low; impact high. Staging,
   approval slot, receipt verification, and installed-byte guard fail closed.

## Edge Cases and Error Handling

- Zero matches: `unmatched`, count zero, no identifier.
- Multiple plausible matches: `ambiguous`; retain ranked evidence; no derived
  photometry from the ambiguous selection.
- Service exception: `query_error`; refresh exits nonzero; old complete snapshot
  remains unchanged.
- Upper limit, contamination, artifact, or extended-source flag: retain value as
  evidence but mark diagnostic derivation inapplicable unless its method allows it.
- Missing rest-frame correction or uncertainty: derived value/error null with
  `missing_k_correction` or `missing_source_uncertainty`.
- Cluster row: preserve `M500/R500`; no galaxy stellar-to-halo mapping.
- Moster inversion outside bracket: null with `outside_model_domain`; never clamp.
- Missing figure input or approval: regeneration or promotion exits nonzero.

## Performance Considerations

The offline build is 52 rows and should finish in seconds. Network refresh makes
208 cone queries; cache per-catalog normalized responses, use bounded retries,
and print progress. Numerical inversion is negligible. Deterministic Monte Carlo
is unnecessary where source uncertainty is absent; preserve null errors instead.

## Documentation Updates

- [ ] Replace the catalog methodology and inventory from the rebuilt CSV.
- [ ] Replace the invalid validation report; retain a clear supersession note.
- [ ] Update Figure 3 validation with versioned input and approval receipt.
- [ ] Update `figures/catalog.yaml`, `figure_review/slots.json`, and reproduction
      documentation with the exact offline and review commands.
- [ ] Record both repository commits and artifact hashes in build manifests.
