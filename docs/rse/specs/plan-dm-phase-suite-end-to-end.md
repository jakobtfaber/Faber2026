# End-to-end implementation loop: controlled DM-phase suite and 24-product campaign

**Date:** 2026-07-12  
**Status:** Ready to launch; implementation not yet started  
**Owner authorization:** Execute end-to-end without per-phase confirmation. Stop only at the
external/data blockers and adoption gates defined below.  
**Code repository:** `pipeline/` (`jakobtfaber/dsa110-FLITS`)  
**Manuscript repository:** this Faber2026 repository  
**Primary scientific output:** per-band structure-optimizing DM (`DM_struct`) for CHIME and
DSA for all 12 events, with calibrated uncertainties, explicit nulls, and visual evidence.  
**Related:** `research-dm-measurement-methods.md`, `plan-dm-measurement-methods.md`,
`dm-provenance-audit-2026-07-07.md`

## 1. Outcome and non-negotiable contract

Build a controlled, documented reimplementation of the literature-standard DM-phase method,
validate it against the frozen published package and known-truth injections, run it on all
24 CHIME/DSA products, and produce an inspectable evidence package for every measurement.

The campaign is complete only when:

1. every one of the 24 products has a terminal status of `PASS`, `MARGINAL`, or
   `UNCONSTRAINED`, never a silent blank;
2. every numerical result is tied to an input checksum, code commit, environment, config,
   random seed, resolution, search grid, and diagnostic page;
3. the selected resolution is the highest time-frequency resolution that satisfies the
   preregistered signal and fit-quality gates;
4. known-truth injection coverage and published-package parity have passed;
5. an agent has visually reviewed every per-product and per-burst diagnostic and recorded the
   verdict in a tracked `figures.review.json`;
6. CHIME and DSA values are reported separately before any event-level combination;
7. no tension, null, edge peak, or morphology-sensitive result is converted into a precise
   event DM merely to fill the manuscript table;
8. adopted event DMs, if any, have been propagated through association timing, the DM budget,
   host-DM posteriors, DM-sensitive scattering fits, figures, tables, and prose;
9. code and validated compact artifacts are committed, reviewed, merged to the FLITS pin
   branch, and the Faber2026 submodule is bumped in a separate focused change.

The campaign measures `DM_struct`: the trial DM that maximizes coherent temporal structure.
It is promoted to manuscript `DM_obs` only through the event-level adoption rule in Section 12.

## 2. Scope and fixed sample

The sample is fixed before development begins:

- 12 bursts: `casey`, `chromatica`, `freya`, `hamilton`, `isha`, `johndoeII`, `mahi`,
  `oran`, `phineas`, `whitney`, `wilhelm`, `zach`;
- two products per burst: CHIME and DSA;
- 24 total products, enumerated by `pipeline/data-manifest.csv`;
- local input root: `~/Data/Faber2026/dsa110/DSA_bursts`;
- CHIME native arrays: 1024 channels x 32000 samples, 2.56 us sampling;
- DSA native arrays: 6144 channels x 2500 samples, 32.768 us sampling.

No product may be dropped because it is hard to fit. The same implementation, resolution
ladder, search policy, quality gates, and diagnostic contract apply to all 24 products.

## 3. Repository and worktree routing

The shared parent checkout is mixed-dirty. Execution therefore uses isolated worktrees.

1. Fetch FLITS and create a clean worktree from the current `pin/faber2026`:

   ```bash
   git -C pipeline fetch --all --prune
   git -C pipeline worktree add \
     ~/Developer/scratch/worktrees/flits-dm-phase-suite \
     -b agent/dm-phase-suite-v1 upstream/pin/faber2026
   ```

2. Develop and run the campaign only in that worktree. Do not edit the active `pipeline/`
   checkout or change the parent gitlink during implementation.
3. Put pipeline code and compact computational artifacts in the FLITS branch.
4. Put the campaign plan, final synthesis memo, and manuscript-facing evidence index in a
   focused Faber2026 branch/commit.
5. Merge the FLITS PR first. Bump the Faber2026 submodule only after the exact merged FLITS
   commit passes the full campaign closeout.

## 4. Runtime and reproducibility

FLITS is Conda-first. All unattended commands use the clean runner:

```bash
env -i \
  HOME="$HOME" \
  PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  OMP_NUM_THREADS=1 \
  OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 \
  /opt/anaconda3/bin/conda run -n flits <command>
```

At campaign initialization, write:

- `run_manifest.json`: code commit, dirty-state hash, platform, Python and package versions;
- `inputs.json`: absolute input paths, sizes, shapes, dtypes, and SHA-256 hashes;
- `config.snapshot.yaml`: the exact resolved configuration;
- `source_hashes.json`: every source file used by the measurement kernel and runner;
- `campaign_events.jsonl`: append-only state transitions, commands, start/stop times, and
  failure classifications.

Writes are atomic (`tmp` then rename). The campaign runner supports `--resume`, `--replot`,
`--only burst/telescope`, and idempotent restart after interruption.

## 5. Package to implement

Create:

```text
dispersion/dm_phase_suite/
  __init__.py
  model.py          # typed inputs/results/config and units
  shifts.py         # cold-plasma delays and padded Fourier/zero-fill shifts
  coherence.py      # phase-only coherent spectrum and integrated DM metric
  cutoff.py         # published, fixed, and stability cutoff policies
  search.py         # coarse/fine search, interpolation, edge expansion
  uncertainty.py    # bootstrap and injection-derived calibration
  quality.py        # product and event gates; structured failure reasons
  resolution.py     # deterministic native-to-coarser resolution ladder
  diagnostics.py    # product, burst, contact-sheet, and HTML evidence renders
  oracle.py         # frozen published DM_phase wrapper
  injection.py      # estimator-independent known-truth injections
  campaign.py       # resumable end-to-end state machine
  cli.py             # command-line entry point
  configs/
    campaign_v1.yaml
```

Public measurement contract:

```python
result = measure_dm_phase(
    waterfall,                 # (frequency, time)
    frequencies_mhz,
    sample_time_s,
    reference_dm,
    channel_mask=None,
    config=DMPhaseConfig(...),
)
```

The result schema contains at least:

```text
burst, telescope, status, failure_reasons
dm_reference, dm_reference_source, dm_residual, dm_absolute
sigma_bootstrap, sigma_injection, sigma_resolution, sigma_method, sigma_total
native_shape, selected_shape, time_factor, frequency_factor
native_dt_s, selected_dt_s, native_df_mhz, selected_df_mhz
profile_snr, valid_channels, emission_bandwidth_mhz
coherence_peak_z, peak_contrast, edge_distance_cells
bootstrap_success_fraction, cutoff_policy, cutoff_hz
coarse_grid, fine_grid, coherent_power, bootstrap_peaks
input_sha256, config_sha256, code_commit, diagnostic_paths
```

No downstream consumer may infer units, residual sign, reference frequency, or quality from a
filename. These are explicit fields.

## 6. Mathematical specification and oracle gate

Before writing the new kernel, produce `docs/dm_phase_algorithm_v1.md` containing equations,
pseudocode, array shapes, units, sign conventions, and boundary behavior for:

1. residual cold-plasma delay relative to the top of the band;
2. trial-DM shifting with padding rather than accidental wrap-around;
3. Fourier transform along time for every frequency channel;
4. phase-only normalization;
5. coherent sum over channels;
6. coherent power versus fluctuation frequency;
7. fluctuation-frequency cutoff selection;
8. integration into the trial-DM metric;
9. coarse search, fine search, and local peak interpolation;
10. uncertainty and quality classification.

The vendored published DM_phase commit `b7cf5fd61436` remains a frozen oracle. It is never
silently edited. Generate and commit compact golden fixtures for:

- one narrow component;
- two components;
- scattered component;
- masked band;
- pure noise;
- CHIME geometry;
- DSA geometry;
- positive and negative residual DM;
- peak near, but not on, a search boundary.

Parity tests compare, where intended:

- shifted waterfalls;
- phase-only spectra;
- coherent-power spectra;
- integrated DM curves;
- peak locations.

Every intentional deviation from the published package gets a named ADR entry in the algorithm
document and a test showing its effect. Unexplained parity failure blocks science runs.

## 7. Test-first implementation sequence

Implement only after the corresponding failing test exists.

### 7.1 Units and sign

- analytic one-channel and two-channel delay tests;
- CHIME 400--800 MHz and DSA 1311--1499 MHz physical-scale tests;
- positive residual means low frequencies arrive later;
- applying `shift(+dm)` followed by `shift(-dm)` recovers the padded interior;
- the former spurious `1e-3` factor fails by construction.

### 7.2 Boundary behavior

- no power wraps from the last sample to the first;
- padding is at least the maximum trial sweep plus the burst guard interval;
- crop selection cannot remove a valid trial-DM sweep;
- insufficient time support returns `UNCONSTRAINED`, not a biased edge peak.

### 7.3 Coherence metric

- phase-only normalization is finite for zero-amplitude Fourier bins;
- masked/dead channels have zero weight;
- channel ordering does not change the result;
- uniform amplitude rescaling does not move the DM peak;
- a known structured injection produces an interior, significant peak;
- noise produces the calibrated null distribution, not a measurement.

### 7.4 Search

- coarse grid brackets truth;
- fine grid resolves the peak independently of coarse step;
- an edge peak expands once within physical time support;
- a persistent edge peak fails;
- interpolation cannot escape its local bracket;
- zero or non-finite uncertainty fails.

### 7.5 Determinism and resume

- fixed seeds reproduce byte-identical compact JSON results;
- interrupted runs resume without recomputing completed products;
- `--replot` needs only compact results, not raw arrays;
- missing input produces a complete failure record and does not crash the batch;
- provenance hashes include the DM kernel, shared IO/orientation code, config, and diagnostics.

Fast unit tests run on every commit. Slow injection and 24-product tests run at phase gates.

## 8. Native-first time-frequency resolution loop

The campaign begins at native resolution for every product. Coarser resolutions are considered
only when the current level does not meet the signal/metric gates.

### 8.1 Fixed resolution grid

Use power-of-two block averaging, with remainder bins masked rather than silently discarded.

- CHIME frequency factors: `1, 2, 4, 8, 16` (minimum 64 channels).
- CHIME time factors: `1, 2, 4, 8, 16, 32, 64, 128, 256`.
- DSA frequency factors: `1, 2, 4, 8, 16, 32, 64` (minimum 96 channels).
- DSA time factors: `1, 2, 4, 8, 16`.

Reject a resolution if:

- fewer than 64 CHIME or 96 DSA valid channels remain;
- effective time resolution exceeds `min(0.5 ms, fitted_FWHM / 4)`;
- the trial-DM sweep cannot fit inside the padded/cropped time support;
- the emission bandwidth contains too little leverage for an identifiable DM peak.

### 8.2 Eligibility gates

A resolution is eligible only if:

1. robust band-summed profile S/N is at least 8;
2. the coherent-power peak exceeds the trial-corrected noise/null distribution at a
   family-wise false-positive probability of 1% or less;
3. the peak is at least three fine-grid cells from either edge;
4. at least 90% of bootstrap resamples return finite interior peaks;
5. peak contrast exceeds the global threshold calibrated by the injection/null campaign;
6. the fitted peak is stable against one adjacent cutoff choice;
7. no diagnostic hard-failure is present.

The numeric coherence/contrast thresholds are calibrated globally on the preregistered null
and injection set before the science run, then frozen in `campaign_v1.yaml`. They are never
tuned per burst.

### 8.3 Selection rule

Evaluate all valid candidate resolutions. Define information loss as:

```text
loss = log2(time_factor) + log2(frequency_factor)
```

Choose the eligible resolution with minimum loss. Ties prefer:

1. smaller time factor;
2. smaller frequency factor;
3. larger coherence significance;
4. smaller calibrated total uncertainty.

Require resolution stability: the selected DM must agree with at least one distinct eligible
resolution within

```text
max(0.10 pc cm^-3, sqrt(sigma_selected^2 + sigma_neighbor^2)).
```

If native resolution passes, it wins. If no resolution passes, the product is
`UNCONSTRAINED`; the loop does not choose the prettiest failed fit.

Record the entire resolution surface so the final figure shows why the chosen resolution was
the highest usable one.

## 9. Known-truth validation campaign

The science campaign cannot start until the custom estimator passes known-truth tests.

### 9.1 Injection matrix

Run both native instrument geometries across:

- S/N: `6, 8, 12, 25, 50, 100`;
- intrinsic Gaussian width: `0.05, 0.1, 0.3, 1, 3 ms` where supported;
- scattering at 1 GHz: `0, 0.1, 1, 5, 20 ms`;
- components: one, two, and three;
- component separation and amplitude ratio;
- spectral index and patchy/narrow-band emission;
- intrinsic downward and upward drift;
- residual DM spanning the physically supported search interval;
- channel masks, band gaps, RFI-like contamination, and crop offsets;
- at least five independent noise realizations per cell.

Use real off-pulse noise from all 24 products as the primary noise source. A separate analytic
Gaussian-noise set isolates implementation errors.

The injected pulse generator must not share the custom estimator's shifting implementation.
Use an analytically independent delay/shift path and cross-check it against direct time-domain
interpolation.

### 9.2 Injection gates

For S/N >= 12 cells within the supported morphology domain:

- absolute median bias <= 0.05 pc cm^-3 for CHIME and <= 0.20 pc cm^-3 for DSA;
- 68% interval coverage between 0.60 and 0.76;
- 95% interval coverage between 0.90 and 0.98;
- catastrophic error rate (`|error| > max(0.5, 3 sigma_total)`) below 1%;
- no sign, scale, orientation, or edge-dependent bias;
- unresolved cells count as failures when the injection is inside the declared supported
  domain; they are not omitted from denominators.

For drift/morphology cells, measure the difference between injected propagation DM and
recovered structure DM. This becomes a morphology-dependent systematic or a declared domain
exclusion; it is not hidden inside statistical uncertainty.

Run a small local matrix on every kernel change. Run the full matrix detached on h17 if the
predicted local runtime exceeds 30 minutes. Before a remote run, verify the live SSH handshake,
remote checkout commit, environment, input hashes, available space, and process launch. Poll
the job and retain stdout, stderr, exit status, runtime, and output hashes.

## 10. Autonomous development and repair loop

The orchestrator runs this state machine:

```text
PREFLIGHT
  -> SPEC_ORACLE
  -> UNIT_IMPLEMENTATION
  -> QUICK_INJECTIONS
  -> FULL_INJECTIONS
  -> PILOT_PRODUCTS
  -> ALL_24_PRODUCTS
  -> RENDER_EVIDENCE
  -> VISUAL_REVIEW
  -> EVENT_SYNTHESIS
  -> ADOPTION_DRY_RUN
  -> DOWNSTREAM_REVALIDATION
  -> PUBLISH_CLOSEOUT
```

At every state:

```text
implement smallest scoped change
  -> run focused tests
  -> run affected injection cells
  -> run affected real products
  -> regenerate compact results and figures
  -> inspect figures
  -> classify outcome
```

Outcome classes and responses:

| Class | Evidence | Response |
|---|---|---|
| implementation defect | parity/unit/sign/orientation failure | fix globally; rerun all lower gates |
| uncertainty defect | unbiased recovery but bad coverage | calibrate globally; rerun full injections |
| resolution/S/N failure | stable peak appears only after binning | retain deterministic selected resolution |
| morphology sensitivity | DM moves with drift/components/cutoff | add systematic or return marginal/null |
| data/provenance defect | missing hash, wrong stem DM, bad axis, crop/timing ambiguity | stop affected product; repair provenance |
| estimator-domain failure | no significant stable peak at any resolution | record `UNCONSTRAINED`; do not substitute |
| visual defect | numeric pass but waterfall/curve/bootstrap is visibly pathological | fail or marginalize; add regression test |

Repairs must be sample-wide rules. A repair triggered by one burst is tested on all injections
and all 24 products before acceptance. No burst-specific search range, mask, cutoff, resolution,
or quality threshold may enter the production config.

Pilot products before the full run:

- `casey`: bright/nominal behavior;
- `mahi`: weak/problematic behavior;
- `chromatica`: known reference-DM discrepancy;
- both telescopes for all three.

Passing the pilot triggers the full 24-product run automatically.

## 11. Visual evidence contract

Every product gets a publication-quality diagnostic page with:

1. native-resolution waterfall at the product/reference DM;
2. selected-resolution waterfall at the product/reference DM;
3. selected-resolution waterfall at the candidate `DM_struct`;
4. difference/alignment view between reference and candidate;
5. band-summed profiles at both DMs;
6. phase-coherent power versus fluctuation frequency;
7. integrated coherent power versus trial DM, including bootstrap band;
8. bootstrap peak distribution and calibrated uncertainty components;
9. full resolution surface with eligible/failed levels and selected level;
10. cutoff, mask, crop, and neighboring-resolution stability;
11. published DM_phase oracle comparison;
12. DM-power, S/N-max, and arrival-regression cross-checks;
13. explicit status, failure reasons, units, reference DM, input hash prefix, and code commit.

Every burst also gets a two-band page containing:

- CHIME and DSA product pages side by side;
- per-band `DM_struct` and uncertainty decomposition;
- CHIME-minus-DSA difference with combined statistical and systematic uncertainty;
- catalog DM and file-stem DM markers;
- event-level support class and combination/adoption verdict.

Generate:

```text
results/dm_phase_campaign/v1/
  run_manifest.json
  inputs.json
  config.snapshot.yaml
  source_hashes.json
  campaign_events.jsonl
  injections/
  products/<burst>/<telescope>/result.json
  products/<burst>/<telescope>/diagnostic.png
  bursts/<burst>/two_band_diagnostic.png
  contact_sheets/
  measurements.csv
  event_summary.csv
  figures.manifest.json
  figures.review.json
  report.md
  index.html
```

The HTML index links every table cell to its diagnostic, provides filters by status/telescope,
and shows native versus selected resolution. Compact JSON/CSV/PNG/PDF/HTML evidence is tracked
when size permits; large regenerable intermediates are archived with checksums and documented
locations.

Visual review is an actual gate. The reviewing agent opens every product page, both contact
sheets, every burst page, and the injection recovery grids. `figures.review.json` records one
of `match`, `marginal`, or `fail` plus specific notes for every figure. A generic statement
that figures were generated is not review evidence.

## 12. Per-band and event-level decision rules

### 12.1 Per-product status

`PASS` requires all numeric, injection-domain, resolution-stability, provenance, and visual
gates. `MARGINAL` retains a candidate for audit but not precision science. `UNCONSTRAINED`
contains no adopted DM and a structured reason.

### 12.2 Event support

- `two-band-consistent`: both products PASS and
  `|DM_C - DM_D| <= 2 sqrt(sigma_C^2 + sigma_D^2)`;
- `two-band-tension`: both products PASS but fail that consistency test;
- `single-band`: exactly one product PASS;
- `none`: neither product PASS.

### 12.3 Event DM adoption

- Two-band consistent: combine using a hierarchical/common-DM model with per-instrument
  calibrated systematics; do not use a naive inverse-variance mean that lets one tiny formal
  error dominate.
- Two-band tension: do not combine. Report both values and investigate morphology,
  frequency-dependent DM, reference/crop errors, and instrument systematics.
- Single-band: retain the passing `DM_struct` as single-band evidence; adoption as event
  `DM_obs` requires its calibrated uncertainty to cover the missing-band limitation.
- None: retain the DSA catalog value only as an explicitly labeled upstream reference; no new
  measured DM is claimed.

The event table preserves all per-band values regardless of whether a combined DM is adopted.

## 13. Downstream adoption and scientific revalidation

Before modifying manuscript inputs, run an adoption dry-run that diffs old and proposed DMs
and predicts every downstream change.

For each adoptable event:

1. update the machine-readable DM source of truth with method and provenance;
2. regenerate dedispersed display products at the adopted per-band values;
3. regenerate the codetection gallery and verify morphology visually;
4. rerun CHIME/DSA association timing under the declared shared-reference convention;
5. rerun DM agreement and chance-coincidence inputs;
6. rerun the DM budget and host-DM posterior;
7. rerun any scattering fit whose residual-DM nuisance or intra-channel smearing changes;
8. regenerate affected tables and figures;
9. rebuild the manuscript from scratch;
10. repeat the V6 association/DM and V5 budget validation ladders.

Adoption is atomic at the campaign level: all changed consumers are regenerated from the same
versioned DM table. Do not hand-edit `budget_table.tex`, figure labels, or prose numbers.

If any previously load-bearing conclusion changes, stop manuscript adoption at
`decision pending`, preserve the validated measurements, and present the scientific delta for
owner adjudication. This is not a failed measurement campaign.

## 14. Orchestration commands

Add the project script `flits-dm-phase = "dispersion.dm_phase_suite.cli:main"` and support:

```bash
# Validate environment, data, hashes, and campaign config
flits-dm-phase preflight --config dispersion/dm_phase_suite/configs/campaign_v1.yaml

# Build/verify frozen published-package golden fixtures
flits-dm-phase oracle --config ...

# Fast development gate
flits-dm-phase test --tier fast --config ...

# Quick and full known-truth campaigns
flits-dm-phase inject --tier quick --config ...
flits-dm-phase inject --tier full --config ... --resume

# Pilot and full real-data campaigns
flits-dm-phase measure --pilot --config ... --resume
flits-dm-phase measure --all --config ... --resume

# Render without recomputing measurements
flits-dm-phase render --config ... --replot

# Validate artifact completeness and numeric gates
flits-dm-phase audit --config ...

# Build proposed event table and downstream dry-run diff
flits-dm-phase synthesize --config ...
flits-dm-phase adoption-dry-run --config ...

# Resume the complete state machine from the last successful state
flits-dm-phase campaign --config ... --resume
```

The unattended launch is:

```bash
mkdir -p logs/dm-phase-campaign
env -i \
  HOME="$HOME" \
  PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /opt/anaconda3/bin/conda run -n flits \
  flits-dm-phase campaign \
    --config dispersion/dm_phase_suite/configs/campaign_v1.yaml \
    --resume \
  > logs/dm-phase-campaign/stdout.log \
  2> logs/dm-phase-campaign/stderr.log \
  < /dev/null
```

Long-running phases use a detached process with PID, start time, commit, command, stdout,
stderr, and heartbeat recorded in the campaign state. The agent polls progress, diagnoses
failures, repairs in scope, and resumes. A running process is not a completed phase.

## 15. Continuous verification and commit cadence

Commit only validated phase boundaries:

1. algorithm specification + oracle fixtures;
2. unit-tested core kernel;
3. resolution selector + uncertainty + diagnostics;
4. quick injection results;
5. full injection results;
6. pilot and all-24 measurement results;
7. visual review + synthesis;
8. downstream adoption, if cleared.

Before each commit:

- run focused tests and the relevant regression tier;
- inspect every changed/generated figure in that phase;
- record dirty-state classification;
- run `agent-closeout-check` with touched paths and the dirty-state packet;
- stage only task-scoped paths.

After validated FLITS completion, push the branch and open/update a focused PR under the
standing repository authorization. Do not merge while CI, review findings, or the scientific
adoption gate remains unresolved.

## 16. Stop conditions and autonomy boundary

The agent proceeds without asking for routine implementation choices, test repairs, local and
h17 runs, figure regeneration, branch pushes, or PR updates that remain within this plan.

Stop and request owner input only when:

1. adopting the new measurements would materially reverse a manuscript conclusion;
2. the only way forward requires changing the fixed sample or using different production
   methods/configs for individual bursts;
3. required raw data or timing provenance is externally unavailable after all documented
   locations are checked;
4. published DM_phase behavior and the literature specification conflict in a way that changes
   the scientific definition of `DM_struct`;
5. licensing requires a distribution decision for copied/derived upstream code;
6. an external credential, account permission, or remote-state change is required;
7. a destructive or history-rewriting action would be necessary.

An individual `UNCONSTRAINED` burst is not a campaign blocker. It is a scientifically valid
terminal measurement result when all resolution levels and quality gates were exhausted.

## 17. Definition of done

The implementation and measurement loop is complete when all of the following are true:

- custom suite tests pass at the merged FLITS commit;
- frozen-oracle parity is documented and green for intended parity surfaces;
- the full injection matrix passes or declares a precise supported domain;
- all 24 products have terminal, visually reviewed results;
- selected resolutions are native-first and justified in the evidence pages;
- `measurements.csv`, `event_summary.csv`, diagnostic pages, contact sheets, HTML index,
  manifests, hashes, and review records are complete;
- no zero uncertainty, unexplained edge peak, silent missing value, or per-burst configuration
  exists;
- CHIME/DSA tensions remain visible and unaveraged;
- any adopted DM has been propagated through all downstream consumers and revalidated;
- the manuscript builds from scratch if adoption occurred;
- task-scoped commits are pushed, reviewed, merged, and the exact FLITS pin is recorded;
- remaining dirty paths are classified and excluded from the task commit;
- the final report states separately: implementation status, measurement status, adoption
  status, downstream revalidation status, and any external blocker.

