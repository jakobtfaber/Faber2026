# Plan: one Faber2026 submodule

**Status:** proposed; migration not started
**Decision:** `Faber2026-analysis` becomes the sole submodule of `Faber2026`.
`dsa110-FLITS` remains a separate reusable package, not a submodule.

## Desired repository roles

| Repository | Owns | Does not own |
|---|---|---|
| `Faber2026` | TeX, bibliography, generated tables, approved figure bytes, exact `analysis/` gitlink | research control, project campaigns, fitting implementation |
| `Faber2026-analysis` | project configuration, data catalogs, campaign drivers, compact results, diagnostics, provenance, review state, manuscript transformations | reusable fitting algorithms, bulk data |
| `dsa110-FLITS` | reusable fitting, simulation, catalog-query, and batch modules; generic tests and documentation | Faber2026 burst registries, dated campaigns, manuscript products, project custody records |

This removes the repository-layout dependency. A caller should not need a
`pipeline/` directory or know where FLITS source files live.

## Baseline inventory

Inventory against the repositories' `origin/main` branches on 2026-07-27:

- `Faber2026/.gitmodules` contains two gitlinks: `analysis/` and `pipeline/`.
- FLITS contains 669 tracked paths under `analysis/`. These are dated
  campaigns and compact outputs, not the reusable fitting kernel.
- Other large FLITS trees include `scintillation/` (156 paths),
  `galaxies/` (146), `scattering/` (78), `flits/` (34),
  `simulation/` (29), `dispersion/` (15), and `crossmatching/` (14).
  Each mixed tree needs classification by content, not wholesale movement.
- Project inputs in FLITS include `configs/bursts.yaml`,
  `data-manifest.csv`, project data-location documentation, 24
  instrument-specific scattering burst files, scintillation burst files,
  dated campaign definitions, crossmatch products, exports, and compact
  results.
- `Faber2026-analysis` currently has no independent Python project or lockfile.
  Its `Makefile` runs tests through `uv --project pipeline`.
- 312 tracked analysis files mention `pipeline/` or `dsa110-FLITS`. A
  generated path map and exhaustive rewrite are required; manual spot edits
  are insufficient.

Freeze one FLITS commit as the cleanup base. The migration scope is every
tracked path at that commit. Inventory open pull requests and active branches
separately as `included`, `superseded`, or `excluded with owner`; merge any
included work before freezing the base.

Before moving files, generate
`docs/rse/specs/evidence/single-submodule-migration/path-map.csv` with:

```text
source_commit,source_blob,old_path,file_mode,file_type,new_repository,new_path,class,sha256,consumers,destination_collision,history_reachable,split_manifest,disposition
```

Allowed dispositions: `move`, `keep-reusable`, `split`, `delete-obsolete`.
Every tracked FLITS path at the frozen base must appear exactly once, including
paths classified `keep-reusable`. A machine check compares the path map with
the `(path, mode, type, blob)` tuples from `git ls-tree -r` and requires both
set differences to be empty.

A `split` row points to a separate split manifest with one row per output:

```text
source_commit,source_blob,old_path,output_repository,output_path,output_role,sha256,consumers
```

Each split must have at least one `moved-project` output and one
`retained-reusable` output. Both outputs are hashed and consumer-checked. The
original mixed implementation is replaced; it is not left as a hidden third
copy.

Immediately before the FLITS deletion pull request, freeze its exact parent
commit and compare all `(path, mode, type, blob)` tuples with the frozen base.
Classify every added, removed, blob-changed, or mode-changed tuple. Regenerate
the map if necessary. A filename-only comparison is not sufficient.

## Classification and destination map

### Move to `Faber2026-analysis`

| FLITS source | Analysis destination | Rule |
|---|---|---|
| `analysis/<campaign>/` | `campaigns/<campaign>/` | Preserve campaign-relative layout and tracked result bytes. |
| `configs/bursts.yaml` | `config/bursts.yaml` | Project burst registry. |
| Faber2026 files under `scattering/configs/` and `scintillation/configs/` | `config/fits/<method>/` | Move burst and project sampler choices; keep only generic examples in FLITS. |
| `data-manifest.csv` and current data-source records | `data/catalog/` | Keep checksums, object identities, and active locations together. |
| Project-specific crossmatch inputs and accepted outputs | `campaigns/crossmatching/` | Keep generic association code in FLITS. |
| Project foreground census inputs, accepted tables, and exports | `campaigns/foregrounds/` and the results registry | Keep generic catalog-query and budget code in FLITS. |
| Project notebooks, run scripts, and compact results | matching `campaigns/` tree | Register every manuscript-facing output. |

Tracked outputs move byte-for-byte first. Obsolete receipts and superseded
diagnostics may be deleted instead of migrated when Git history is the only
remaining consumer.

### Keep in FLITS

- Reusable Python implementations under `flits/`.
- Generic physics and fitting code under `scattering/` and `scintillation/`.
- Generic foreground, dispersion, association, and simulation code.
- Console commands, generic examples, architecture decisions, and tests of
  reusable behavior.
- Package metadata and the FLITS environment lock.

### Split mixed paths

- Move Faber2026 burst files out of reusable configuration directories. Leave
  a small schema and synthetic example in FLITS.
- Move known Faber2026 simulation scenarios and verdicts; retain simulation
  engines and known-truth test fixtures.
- Move catalog query inputs, sightline lists, cached project responses, and
  accepted tables; retain query adapters and calculations.
- Move run orchestration and result adjudication; retain likelihoods,
  estimators, plotting primitives, and serialization modules.

The deletion test applies: if removing a path would make another project lose
general fitting capability, keep it in FLITS. If its meaning depends on the
Faber2026 sample, manuscript, trust state, or data catalog, move it.

## Interface seam

The seam lives at the installed FLITS package, not at a sibling checkout.

`Faber2026-analysis` will add `pyproject.toml` and `uv.lock`. The lockfile pins
FLITS to an exact Git commit. Analysis callers use only:

1. documented imports from `flits.batch`, `scattering.scat_analysis`,
   `scintillation.scint_analysis`, `galaxies.foreground`, and retained public
   parts of `dispersion`, `crossmatching`, and `simulation`;
2. installed commands selected from `flits-scat`, `flits-scint`,
   `flits-chime-product`, `flits-batch`, `flits-configs`, and `flits-halos`;
   and
3. one machine-readable provenance command or function that reports the FLITS
   version and Git commit.

Phase 1 freezes the exact supported import and command subset in a versioned
interface manifest. It also versions the project-configuration schema, run
manifest schema, and compact-result schema. Compatibility tests install a
built wheel, remove the source checkout and `.git`, then exercise every
declared import, command, and schema.

The build writes the source revision into package data such as
`flits/_build_info.py`; provenance reads that embedded value. Runtime Git
metadata is not part of the interface.

Each run receives explicit paths:

```text
project config + input product + output directory + random seed
    -> compact result files + run manifest + validation result
```

The run manifest records input hashes, configuration hash, FLITS commit,
analysis commit, environment lock hash, seed, command, and output hashes.
FLITS must not discover the manuscript root, import project configuration from
its own repository, or write directly into the manuscript. Analysis must not
import FLITS files by relative path or alter `PYTHONPATH` to reach a checkout.

Tests cross the same interface. Internal FLITS tests may still exercise private
implementation, but analysis integration tests install the pinned package and
use only the public interface.

## Migration phases

### Phase 0 — freeze and classify

1. Tag the final accepted two-submodule parent state.
2. Record parent, analysis, and FLITS commits.
3. Generate the complete path map, tracked-file hashes, producer-consumer
   graph, and the list of all `pipeline/` references.
4. Mark each result as trusted, provisional, diagnostic-only, or obsolete from
   the existing results registry.
5. Create a frozen baseline manifest containing:
   - raw and fit-input object identities and full-file checksums;
   - environment and dependency lock hashes;
   - test names and outcomes;
   - compact result and provenance hashes;
   - accepted scientific values and declared comparison tolerances;
   - table and figure hashes, figure approvals, and trust states; and
   - manuscript page count, build inputs, included asset hashes, and claim
     values.
6. Run the baseline from a clean two-submodule clone and record the commands
   and results in one gate summary.
7. Make no scientific-value, model, fit, seed, or plotting changes in migration
   commits.

Gate: the complete tracked-path complement is classified; the frozen baseline
passes from a clean clone; no ambiguous path is deleted.

### Phase 1 — establish the package seam

1. Make the reusable FLITS modules install cleanly without the dated
   `analysis/` tree or project configuration.
2. Stabilize the Python imports, console commands, and provenance report.
3. Add the analysis Python project and lock FLITS to the accepted commit.
4. Change analysis mount checks and tests so they require the parent manuscript
   when appropriate, but never require `Faber2026/pipeline`.

Gate: a clean analysis clone installs from its lockfile and passes a synthetic
end-to-end FLITS run with no FLITS checkout beside it.

### Phase 2 — move one complete fit slice

Choose one already-reviewed, deterministic scattering campaign. Move its burst
registry entry, fit configuration, driver, compact outputs, provenance, tests,
and results-registry links together. Rewrite all consumers in the same pull
request.

Gate: moved tracked bytes and provenance are complete and hash-identical; an
independent fresh rerun produces the same deterministic outputs, or agrees
within predeclared numeric tolerances for stochastic output using the same
seed; registry trust and any affected visual approval are preserved.

### Phase 3 — move remaining vertical slices

Move and validate one complete science family at a time:

1. remaining scattering campaigns;
2. scintillation campaigns;
3. dispersion-measure and timing association work;
4. foreground census and budget products;
5. simulations and calibration campaigns;
6. remaining notebooks, exports, and compact results.

For each slice: copy, rewrite consumers, run its tests, reproduce every current
accepted product, update the results registry, then mark the source eligible
for later deletion. Do not mix families into a single unreviewable move.

Gate for every slice:

- moved tracked bytes and provenance are complete and hash-identical;
- deterministic outputs match the frozen baseline by hash;
- stochastic results use the frozen seed and satisfy predeclared tolerances;
- an independent comparison records the result;
- trust states and registry consumers are preserved;
- affected plots pass visual review; and
- the path map has no unresolved consumer.

### Phase 4 — rewrite workspace references

Use the path map to update:

- analysis scripts, tests, documentation, catalogs, and schemas;
- figure catalog producers and review records;
- results registry and reproduction manifest;
- knowledge-base adapters and indexed source labels;
- parent `Makefile`, workflows, agent briefs, and documentation.

Add fail-closed checks:

- no tracked analysis or parent file refers to a `pipeline/` checkout;
- no analysis test constructs a sibling FLITS source path;
- every manuscript product resolves to an analysis producer and locked FLITS
  commit;
- every moved path has one current destination.

Gate: exhaustive search is clean and the knowledge base indexes manuscript,
analysis, and installed-package provenance without a pipeline source tree.

### Phase 5 — science and reproduction closeout

1. Run the complete analysis test suite from a clean environment.
2. Reproduce every manuscript table and figure affected by a moved producer.
3. Compare deterministic artifacts by hash and scientific values by declared
   tolerances.
4. Recheck figure approvals and results-registry trust.
5. Build the manuscript and compare page count, included figure hashes, tables,
   and claim values to the frozen baseline.
6. Require the owner raw-data spot-check before calling the raw layer trusted.

Green software tests do not clear scientific gates. Any changed scientific
value, fit, or visual returns to its normal independent review.

### Phase 6 — parent cutover

1. Merge all required analysis changes and record the exact analysis commit.
2. Remove the `pipeline` gitlink and its `.gitmodules` entry in a focused parent
   pull request.
3. Pin the merged analysis commit.
4. Update parent workflows and commands to install from the analysis lockfile.
5. Validate a fresh recursive clone.

Gate: `git submodule status` reports exactly one submodule, `analysis/`; the
full test and manuscript build work without a `pipeline/` directory.

### Phase 7 — delete migrated FLITS material

Only after Phase 6 is merged:

1. Delete paths marked `move` or `delete-obsolete` from FLITS.
2. For every `split`, remove the project fragment and retain only the
   reusable output recorded in its split manifest.
3. Fail if any split output, consumer, or disposition remains unresolved.
4. Remove project-specific tests and documentation now covered through the
   installed-package interface.
5. Confirm FLITS package tests pass with no Faber2026 data or campaign tree.
6. Merge the FLITS cleanup, update the analysis lock to that cleaned commit,
   and rerun the clean-install and affected reproduction gates.
7. Merge the analysis lock update, then update the parent analysis gitlink in a
   final focused pull request.

Gate: FLITS is independently usable as a reusable package; the analysis
lockfile selects the cleaned FLITS commit; analysis retains all current project
material and provenance.

## Data policy

Bulk data never move into Git.

- h17 holds the project's raw and retained data.
- The CANFAR VOSpace `arc` area holds checksum-identified fit-input products.
- Local cubes under `~/Data/Faber2026/chimefrb/CHIME_bursts/` and
  `~/Data/Faber2026/dsa110/DSA_bursts/` are working replicas.
- Repository catalogs record object identities, checksums, roles, and active
  paths. They must not advertise retired archive or staging systems as
  fallbacks.
- Each catalog row names one authoritative object: h17 for raw and retained
  inputs; CANFAR VOSpace `arc` for accepted fit-input products.
- Validate full files with trusted server-side checksums when available.
  Otherwise stream every byte through a local checksum. Header-only checks do
  not establish identity.
- Local working replicas must match their authoritative object's full-file
  checksum before they enter a reproduction run.
- Validation does not recopy or delete bulk data.

## Git and pull-request order

1. FLITS pull request: establish or tighten the reusable package interface.
2. Analysis pull request: add its Python project, lock the merged FLITS commit,
   and prove the synthetic install gate.
3. One analysis pull request per vertical science slice. Keep FLITS source
   copies until all slice gates pass.
4. Analysis pull request: complete path rewrites and reproduction closeout.
5. Parent pull request: pin merged analysis and remove the FLITS submodule.
6. FLITS pull request: delete migrated and obsolete project material.
7. Analysis pull request: lock the cleaned FLITS commit and rerun gates.
8. Parent pull request: pin the final merged analysis commit.

Each pull request is independently revertible and contains no unrelated
science change. Publish dependency commits before pinning them. Do not combine
parent gitlink changes with manuscript prose or figure edits.

## Rollback

- Before parent cutover, rollback is a normal revert of the affected analysis
  slice; FLITS still contains the source.
- If the parent cutover fails, revert its focused pull request and restore the
  frozen two-submodule pair.
- From the final eight-pull-request state, revert in this order:
  1. final parent analysis-pin update;
  2. analysis lock update to the cleaned FLITS commit;
  3. FLITS cleanup deletion;
  4. initial parent one-submodule cutover;
  5. analysis path-rewrite closeout;
  6. analysis vertical-slice moves in reverse merge order;
  7. analysis package/lock bootstrap; and
  8. FLITS interface change, only if no other consumer now depends on it.
- Rehearse rollback in a temporary clone before final closeout. The restored
  checkout must resolve the frozen two-submodule commits and pass the frozen
  baseline.
- Never rewrite shared history. The frozen tag and pull-request commits retain
  the exact pre-migration state.
- Bulk data are outside this migration and are neither moved nor deleted.

## Completion criteria

- `Faber2026` has exactly one submodule: `analysis/`.
- Analysis installs an exact FLITS commit from its lockfile.
- All Faber2026-specific tracked material is in analysis or explicitly deleted
  as obsolete.
- Every split has resolved, hashed moved and retained outputs; no mixed source
  remains unclassified.
- FLITS contains no Faber2026 campaigns, burst registry, project manifests, or
  manuscript products.
- No live parent or analysis path assumes a sibling FLITS checkout.
- Clean-clone tests, manuscript build, figure review, result trust checks, and
  affected reproductions pass.
- The current-tree receipt is limited to the path map, final gate summary, and
  commit identities. Session transcripts and superseded migration notes are
  unnecessary only after their old path and source commit are recorded in the
  path map and the source commit is proven reachable from a permanent merged
  branch or tag. Unmerged or unreachable receipts must be preserved or merged
  before deletion.
