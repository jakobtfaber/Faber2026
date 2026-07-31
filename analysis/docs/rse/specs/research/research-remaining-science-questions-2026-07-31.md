# Remaining science questions — independent reasoning audit, 2026-07-31

**Status:** PRELIMINARY — research questions only; nothing here closes a gate,
promotes trust or provenance, or changes any registry, manuscript, or receipt
state.

**Snapshot:** analysis worktree `codex/claude-fable-science-questions` at
commit `b51d0d1abe455c788401a740fb37b21ac22a03c2`, clean baseline. All evidence
below was read at this commit; any later mutation of the cited files makes
this note STALE.

**Tooling blocker (recorded, not worked around by mutation):** the required
knowledge-base searches (`python3 scripts/kb search "<topic>"`) were denied by
the session permission policy on every attempt. Orientation therefore used
ignore-aware `rg`/`fd` sweeps plus direct reads, per the AGENTS.md fallback
("grep for exhaustive sweeps"). No index refresh was run.

---

## Question 1 — Can a source-bound census plus an independently reproduced
## cluster model establish a substantial intracluster dispersion contribution
## toward FRB 20230307A?

### Source paths (exact, this commit)

- Census roster (authoritative): `foregrounds/census/data/intervening_census_registry.csv`
  — FRB 20230307A rows 12–30 and 53; the single budget-eligible cluster is
  row 23, `J115120.4+714435, 1254337` (Wen & Han 2024 catalog; `z=0.200`,
  `b=603.6` kpc, `b/R500=0.83`, `M500=1.48e14`, DESI spectroscopic redshift).
- Frozen census inputs: `foregrounds/census/data/frozen_census/`
  (`bursts.csv`, `foreground.csv`, host-redshift extracts),
  `foregrounds/census/data/candidate_redshift_provenance.csv`,
  `candidate_redshift_replay_2026-07-22.json`,
  `candidate_redshift_source_payloads_2026-07-22.json`.
- Cluster/halo geometry: `foregrounds/census/data/sightline_halo_grid.csv`
  (+ `.receipt.json`), `foregrounds/census/data/census_masses/halo_rvir_ADJUDICATED.csv`.
- Cluster column model: `scripts/dm_budget_uncertainty.py` (mNFW vs
  X-ray/SZ-motivated β-model bracket; Monte-Carlo over M500, f_gas, shape),
  `scripts/phineas_halo_crossing_probability.py` / `.json`.
- Independent mass bound: `docs/rse/specs/experiment/experiment-cluster-xray-sz-mass-bound-2026-07-17.md`
  (adjudicated; RASS X-ray cap `M500 ≤ 1.7e14 M_sun`, worst-case ECF; SZ null).
- Registry state: `docs/rse/control/results-registry.toml` —
  `budget.cluster_column` (trusted, provenance **complete**, cleared
  2026-07-28 by independent reproduction; value `DM_int=281 (+73/-64)`,
  host `38 (+89/-104)` pc cm⁻³), vs `budget.dm_int_nonzero` and
  `budget.budget_table` (trusted, provenance **pending**: "producing pin
  inferred; exact artifact receipt absent"), and `census.clusters_icm_figure`
  (trusted, provenance pending: exact producing commit absent).
- Current diagnostic authority: `foregrounds/results/propagation/intervening_systems.json`
  + `intervening_receipt.json` (hash-bound inputs/outputs; but the result is
  explicitly `diagnostic_not_science_admitted` per the 2026-07-30 audit,
  `docs/rse/specs/research/research-manuscript-claim-evidence-audit-2026-07-30.md`).

### Receipt identity

- `foregrounds/results/propagation/intervening_receipt.json`: producer
  `dddd9dde…`, registry input `96bfd323…` (matches the release-gate-pinned
  census registry hash in `ADVERSARIAL_REVIEW_BLOCKERS.md`), outputs
  `intervening_systems.json` `c5ec471a…`.
- `budget.cluster_column` provenance_refs: producers and inputs all pinned at
  analysis commit `9890aa8cc299fc2696348327a1c2efe14c80fdbe`, artifact
  `budget_table.tex` at manuscript commit `b1d4e8c4…`.
- The 2026-07-17 experiment record carries its own replication anchor: mNFW
  with registry inputs reproduces ≈183–185 pc cm⁻³ (appendix ≈184); β-model
  95% interval [84, 328] pc cm⁻³ under the truncated mass prior (seed 20260707).

### Current evidence

Three independent strands agree that the sightline crosses one cluster inside
R500 and that the modeled column is large (~1–3×10² pc cm⁻³): (a) the frozen,
source-bound census (DESI spectroscopic cluster redshift, adjudicated masses);
(b) the mNFW/β-model bracket with an owner-adjudicated X-ray mass cap that
truncates the high-mass tail (≈80–330 pc cm⁻³, factor ~4); (c) the 2026-07-28
independent reproduction that cleared `budget.cluster_column`.

Open contradictions the strands do not yet resolve:

1. Compiled manuscript value vs current diagnostic: compiled `DM_int=281`
   vs current diagnostic median `242.2` pc cm⁻³ (2026-07-30 audit table); the
   diagnostic is explicitly not science-admitted, and the 2026-07-31 commit
   `b51d0d1` withdrew the per-sightline budget prose claims.
2. A recorded prescription conflict (Phineas DM_int 241/243 vs ≈218) is
   marked resolved on the board (wf-06, `docs/rse/wayfinder/tickets/06-adjudicate-phineas-halo-mass-prescriptions.md`)
   but the registry `notes` for `budget.dm_int_nonzero` and
   `budget.budget_table` still say it "awaits wf-06 adjudication" — a
   registry-note/board disagreement that must be reconciled before quoting.
3. A second candidate cluster, WHL J115048.0+714428 (`z=0.1893`,
   `b≈614` kpc, registry row 53), lacks adopted M500/R500 in the Wen–Han
   model; whether it is a distinct lower-richness system or a duplicate of
   the adopted system is unadjudicated (needs the WHL12 richness-to-M500
   calibration; flagged in the compiled appendix prose,
   `census.clusters_icm_figure` claims).
4. Surrounding provenance is incomplete: census query timestamps
   (`census.foreground_table`), the exact producing commit of the cluster
   figure, and exact budget artifact receipts are all absent.

### Evidence boundary

- **Observed/cited fact:** the census records one budget-eligible cluster
  crossing, and `budget.cluster_column` records a completed reproduction for
  one historical integrated-budget value.
- **What it does not establish:** a current manuscript-admitted cluster column
  or reconciliation between the ticket-06 percentiles and the registry value.
- **Admission/provenance blocker:** the live prescription transformation,
  second-cluster identity, current artifact receipt, and surrounding census and
  figure provenance remain unresolved.

### Explicit falsifier

"Substantial" is not operationally defined in the current authority, so the
quantitative claim is not yet cleanly falsifiable. Its physical premise would
fail if source adjudication removed the only budget-eligible cluster crossing,
or if an independently justified cluster-gas model over the admissible mass and
geometry range were consistent with a negligible column. Failure to reproduce
`281 (+73/-64)` pc cm⁻³ would instead falsify that exact integrated-budget
result, not the broader cluster-contribution premise. The ≈218 prescription
and a reopened high-column tail are adjudication or interval-shape issues, not
falsifiers of substantiality.

### Executable next check

```bash
# Prerequisites present locally: ticket, registry, pinned producer artifacts.
rg -n '203|255|281|322|DM_int' \
  scripts/phineas_halo_crossing_probability.json \
  scripts/dm_budget_uncertainty.csv \
  docs/rse/wayfinder/tickets/06-adjudicate-phineas-halo-mass-prescriptions.md \
  docs/rse/control/results-registry.toml
# Do not claim reproduction until this identifies the transformation or
# additional foreground terms connecting ticket-06's 203/255/322 percentiles
# to the registry's 281 (+73/-64).
```

No producer rerun command is prescribed here: the exact invocation and
environment that generated the admitted artifact have not been established.

Verdict for Q1: the census is genuinely source-bound and the cluster model has
one independently reproduced, provenance-complete row (`budget.cluster_column`).
It can support a *bounded* statement ("the sightline pierces one cluster inside
R500; the modeled column spans ≈80–330 pc cm⁻³") but not yet a specific
admitted value: the per-sightline budget surface is withdrawn, the diagnostic
authority is not science-admitted, and items 2–4 above are open. Research
question, not closed.

---

## Question 2 — Can host dispersion be rerun from a frozen
## intergalactic-medium calibration source?

### Source paths

- Producer: `scripts/dm_budget_uncertainty.py` — the IGM term is
  `DM_IGM ~ LogNormal(mu(z), sigma(z))` with the redshift grid **transcribed
  in-code** at lines ~203–245 (`TNG_ZGRID`, `TNG_MU_IGM`, `TNG_SIG_IGM`),
  attributed in the producer docstring to Walker et al. (2024) [unverified]
  via the reproduction package of Connor et al. (2025, arXiv:2409.16952),
  file `tng_params_new.npy`;
  `TNG_SOURCE_STATUS = "provisional_transcribed_grid_source_artifact_missing"`
  (line 95). Low-z continuation below z=0.1 follows the Macquart integral
  (`igm_lognormal_shape`).
- Fail-closed receipt: `foregrounds/results/propagation/host_dm_receipt.json`
  — `status: fail_closed`,
  `tng_calibration: provisional_transcribed_grid_source_artifact_missing`;
  inputs hash-pinned (`manuscript_dm_catalog.csv` `3730d486…`,
  `intervening_receipt.json` `33d7a5c6…`, `dm_budget_intervening_systems.csv`
  `0dd74d3c…`); outputs `host_dm_results.json` `bb63a369…`,
  `host_dm_diagnostic.csv` `3439692e…`.
- Diagnostic-only wrapper: `foregrounds/propagation/dm_host_posterior.py`
  (states nothing produced is manuscript-quotable).
- Registry: `budget.host_dm_posteriors` — trust **pending**, provenance
  **pending** ("producing pin inferred; exact artifact receipt absent");
  58 manuscript records ride on it (abstract, conclusions, results,
  Appendix C) — all `provisional` admission class.
- Prior owner sign-off (priors, not the source artifact):
  `docs/rse/wayfinder/tickets/07-sign-off-budget-priors-and-host-dm-headline.md`
  (resolved 2026-07-22; includes the low-z sensitivity benchmark,
  `scripts/dm_budget_low_z_sensitivity.py` / `.json`).

### Receipt identity

The blocking receipt is exactly `host_dm_receipt.json` (`fail_closed`). Its
producer hash `43823c73…` binds the run; the missing item is a **source
artifact for the transcribed calibration grid** — the `tng_params_new.npy`
bytes (or an equivalent published table) with a recorded origin, checksum,
and a byte-or-value comparison against the in-code arrays.

### Current evidence

The current diagnostic inputs and outputs are hash-bound, but its environment
and producing commit are not identified. The declared calibration gap is the
transcription without a frozen source. The
2026-07-30 audit's provenance-closure attempt confirmed 0 promotions and
encountered the missing TNG artifact; the registry separately records an
inferred producer pin and missing exact artifact receipt. The priors
themselves have an owner sign-off (ticket 07 resolved 2026-07-22), and the
low-z continuation was stress-tested against `pyhesdm` and the Konietzka
continuous-TNG catalog (headline classification insensitive; max
P(host DM<0) 0.059 for the two low-redshift sightlines). Separately, the
FRB 20230307A host row inherits Question 1's intervening value, so Q2 cannot
fully close ahead of Q1 for that sightline; the compiled host medians are
additionally stale against the current diagnostic (e.g. Phineas 38 vs
74.4 pc cm⁻³, audit table).

### Evidence boundary

- **Observed/cited fact:** the diagnostic receipt binds current inputs and
  outputs and explicitly records the missing transcribed-grid source.
- **What it does not establish:** agreement with the external calibration,
  environment reproduction, or a manuscript-admitted host posterior.
- **Admission/provenance blocker:** canonical calibration URL and immutable
  revision, source bytes, producing commit, environment identity, and exact
  artifact receipt are absent.

### Explicit falsifier

The scientific proposition that the frozen source reproduces the embedded
calibration fails if: (i) the fetched
`tng_params_new.npy` (Connor et al. 2025 reproduction package) disagrees with
the transcribed `TNG_MU_IGM`/`TNG_SIG_IGM` beyond rounding at any grid
redshift — that converts the gap from "provenance" to "wrong calibration" and
invalidates all nine host posteriors; (ii) the package pins a different
`f_IGM,TNG` baseline than the in-code `FIGM_TNG = 0.797`, shifting the
`ln(f_IGM/f_IGM,TNG)` marginalization; (iii) no distributable artifact exists
(licensing or availability), in which case the prescription must be replaced
with a fully sourced model per the audit's decision list, and the current
numbers cannot be admitted at all.

### Executable next check

```bash
# Prerequisite present locally: repository attribution inventory.
rg -n 'tng_params_new|2409\.16952|Walker|TNG_SOURCE_STATUS' \
  scripts foregrounds docs
```

No fetch, checksum, comparison, or rerun command is prescribed until a
canonical repository URL, immutable revision, and artifact path exist. Once
they do, the receipt must include those identities plus a value comparison,
analysis commit, and environment.

Verdict for Q2: plausible in principle, not demonstrated. The frozen external
calibration artifact, canonical source revision, producing commit, environment,
and exact artifact receipt remain missing. A source mismatch would invalidate,
not merely delay, the current host posteriors. Fail closed.

---

## Question 3 — What exact event-specific SEFD (system-equivalent flux
## density), beam, and calibration receipts are required for band energies?

### Source paths

- Measurement chain: `energetics/studies/burst-energies/measure_data_fluences.py`
  → `data_fluences.candidate.csv` (24 event-band rows; every row currently
  `calibration_status=pending_review`, `noise_status=pending_validation`,
  `review_status=pending`; `calibration_systematic_dex` deliberately blank);
  builder `build_data_driven_energies.py` requires a nonexistent
  `data_fluences.accepted.csv`; verifier `verify_data_driven_energies.py`.
- Calibration inputs now used:
  - CHIME SEFD: `energetics/studies/burst-energies/chime_sefd.csv` —
    single zenith value 34.5 Jy from Tsys=50 K, A_phys=8000 m², assumed
    η=0.5 (Amiri et al. 2018 Table 1), blanket 0.25 dex systematic.
    Not event-specific.
  - DSA SEFD: `energetics/studies/burst-energies/dsa_sefd.csv` +
    `fetch_dsa_sefd.py` — one epoch-representative robust median 8016.2 Jy
    (frac scatter 0.267) from the dsa110-rt dashboard 2026-02/03 campaign
    (h23:`/media/ubuntu/ssd/vikram/sefd/sefd_dashboard/state.json`);
    header states **no contemporaneous SEFD exists for the 2022–2024
    bursts**. Not event-specific in time.
  - DSA beam: `/Users/jakobfaber/Documents/DSA110_beam_1.h5` (outside the
    repository; hashed per-row into `calibration_sha256`) +
    `dsa_pointing.csv`, `dsa_primary_beam_pointings.csv`,
    `energetics/methods/dsa_beam.py`.
  - CHIME beam: `energetics/methods/chime_beam.py` (declination/frequency
    dependence folded into the 0.25 dex band).
  - Radiometer conversion: `energetics/methods/flux_cal.py`
    (σ_S = SEFD/(√(n_pol·Δν·Δt)·G) per band per channel).
- Governing reviews: `energetics/studies/burst-energies/CALIBRATION_REVIEW.md`
  (2026-06-22: per-telescope S/N units incommensurable; two unknown scales
  corrupt even relative ordering of the CHIME+DSA sum; DSA γ≈−5 rail likely
  bandpass rolloff), `README.md` (fail-closed admission ladder), and the
  2026-07-30 audit's energetics section and reference audit (Law et al. 2024
  / CHIME/FRB 2018 / Michilli et al. 2021 do **not** supply an
  event-specific absolute calibration receipt; manuscript now says one is
  required; Andersen et al. 2023 is the relevant CHIME flux-calibration
  reference but cannot transfer a scale without that receipt).
- Registry: `energies.burst_energies_table` — trust **revoked**, gaps:
  7/24 failed band receipts (Isha, Oran, Phineas CHIME fail; Hamilton DSA +
  JohnDoeII, Mahi, Whitney CHIME windows unstable); no accepted CSV; no
  admitted artifact. Retained manuscript text is method-class only.

### Receipt identity — the exact receipts band energies require

Per accepted row (event × band), admission needs a receipt binding:

1. **Input identity:** dynamic-spectrum path + SHA-256 (already recorded per
   row in `data_fluences.candidate.csv`).
2. **Event-specific SEFD:** either a contemporaneous measurement at the burst
   epoch, or an explicit epoch-transfer argument from the 2026-02/03 DSA
   campaign (and from the CHIME zenith model) to the burst MJD with a stated,
   reviewed systematic — filled into the currently blank
   `calibration_systematic_dex`. For CHIME this must add the per-event formed
   beam response at the burst position/declination and frequency, not the
   single zenith SEFD.
3. **Event-specific beam gain:** DSA primary-beam attenuation at each burst's
   elevation from the tracked pointing CSVs plus the beam cube — with the
   beam cube itself brought under a tracked path or a pinned external
   checksum + origin (currently a loose file under `~/Documents/`).
4. **Window stability:** the row's window gate passing across the recorded
   threshold (`2.5,3.0,3.5σ`) and pad (`0.25,0.5,1.0`) grid
   (`window_sensitivity_frac`), currently failing/unstable for 7 rows.
5. **Correlated-noise validation:** `noise_status=accepted` after an explicit
   correlated-noise uncertainty calculation.
6. **Owner review:** `review_status=accepted`, then the reviewed
   `data_fluences.accepted.csv` consumed by the builder — never a rename.

### Current evidence

The scaffolding (fail-closed producer, verifier, hard gates, per-row hashing)
exists and 43 focused tests pass; the recorded Zach band fluences reproduce
exactly in a clean rerun (semantic, not byte, PDF reproduction). What does
not exist anywhere in the tree: a burst-epoch or justified transferred
system-equivalent-flux-density receipt for either instrument, a per-event CHIME
response, an independently reviewed DSA per-row beam-gain receipt, a reviewed
calibration systematic, or any accepted row. The audit's
open energetics question 2 ("do defensible calibrations support absolute
fluences with stated systematics?") is exactly this gap.

### Evidence boundary

- **Observed/cited fact:** the candidate contains 24 hash-bound event-band
  rows; seven fail the window gate; all remain pending calibration, noise, and
  review. DSA event-dependent beam response is calculated from the recorded
  pointing inputs and beam cube.
- **What it does not establish:** an absolute event-specific flux scale,
  independently reviewed beam-gain receipt, accepted row, energy value, or
  population comparison.
- **Admission/provenance blocker:** contemporaneous or justified transferred
  system-equivalent flux density, reviewed calibration uncertainty, per-row
  beam-gain review, stable windows, correlated-noise validation, accepted
  receipt, and a defined comparison/roster are absent.

### Explicit falsifier

Any future scientific claim that the band energies are absolutely calibrated
is falsified if an independent calibration shows that the event-specific flux
scale or beam response lies outside its stated systematic uncertainty. No
population-level energy claim or minimum acceptable roster is presently
defined; window loss and broad correlated-noise uncertainty are therefore
admission blockers, not falsifiers of a defined population result.

### Executable next check

```bash
# Enumerate the exact current gate states (no mutation):
python - <<'EOF'
import csv
rows = list(csv.DictReader(open(
  'energetics/studies/burst-energies/data_fluences.candidate.csv')))
for r in rows:
    print(r['nickname'], r['band'], r['window_status'],
          r['calibration_status'], r['noise_status'], r['review_status'],
          r['window_sensitivity_frac'])
EOF
```

The epoch-transfer test is not prescribed as a command until read-only h23
access, the dashboard source path, burst-epoch metadata, and the intended
transfer model are verified as prerequisites.

Verdict for Q3: the required receipts are enumerable and the ladder to admit
them already exists in-tree. Missing items are burst-epoch or justified
transferred system-equivalent flux density, per-event CHIME response,
independently reviewed DSA per-row beam gain, reviewed systematic uncertainty,
and accepted rows. The DSA event-dependent response calculation exists; its
independent review does not. Energies stay method-only. Research question, not
closed.

---

## Cross-cutting note

All three questions share one structural dependency: Question 1's intervening
column feeds Question 2's host residual for FRB 20230307A, and both feed the
manuscript's headline host-DM interpretation, which the 2026-07-30 audit
keeps fail-closed. Question 3 is independent of 1–2 but shares the same
admission discipline. No ordering shortcut exists: the TNG source artifact
(Q2) and the wf-06 registry-note reconciliation (Q1) are the two cheapest
unblocking moves; the SEFD epoch-transfer study (Q3) is the longest pole.

One confirmed stale-documentation item found but **not** fixed (this task
forbids modifying existing files): registry `notes` for
`budget.dm_int_nonzero` and `budget.budget_table` still say the Phineas
prescription conflict "awaits wf-06 adjudication" while
`docs/rse/control/BOARD.md:242-244` marks wf-06 resolved. Reconcile in a
separate, normally-scoped registry edit.
