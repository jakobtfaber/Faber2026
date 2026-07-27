# Handoff: sample-wide P3′ CHIME scintillation pass — the eleven remaining co-detections

---
**Date:** 2026-07-15 08:30 (PDT)
**Author:** AI Assistant (Claude Fable 5, session 01Bm6mdK)
**Status:** Handoff (plan written at owner request; **execution awaits an
explicit owner go** — the board's needs_owner item lists this as a separate
decision)
**Branch:** `main` (Faber2026 at `f161f12`; pipeline pinned at FLITS `479d2c8`)
**Commit:** post-PR-#79 (pin carrying the P4 DOCUMENTED-FAIL record)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Freya qualification chain (C1→P1→P2→P3′→P4) | ✅ Complete | P3′: first passing blinded calibration; unblinding → intrinsic-envelope foreground, declined fail-closed. P4: envelope not separable (predeclared E2 fail branch, FLITS #182, pin `479d2c8`) |
| Owner ratifies manuscript closure wording | 🔶 Open (owner) | With P3′ + P4 in hand; board needs_owner card |
| **Sample-wide P3′ pass (eleven remaining bursts)** | 📋 Planned | **This handoff.** Owner asked for the plan 2026-07-15; execution not yet sanctioned |

**Current Workflow Phase:** Plan (next = owner go → predeclare → stage data → implement)

## Workflow Artifacts

- [experiment-chime-scint-p3-optimal-estimator.md](../experiment/experiment-chime-scint-p3-optimal-estimator.md) — the calibrated estimator this pass replicates per burst (§P3′ amendment = the frozen chain)
- [experiment-chime-scint-p4-envelope-model.md](../experiment/experiment-chime-scint-p4-envelope-model.md) §Outcome — the envelope-separability precedent (freya)
- Pinned pipeline `analysis/chime-scintillation/experiments/p3-optimal-estimator/` — harness to generalize; `p2-routeb-voltage/routeb_calibration.py` — the freya-specific `Products`/window/mask layer to parameterize
- [handoff-2026-07-15-06-50-p4-envelope-model-dev.md](../handoff/handoff-2026-07-15-06-50-p4-envelope-model-dev.md) §Learnings — all seven items still bind

## Critical References (read first, in order)

1. P3′ record §P3′ amendment + §Outcome — the exact frozen chain (S2 split-ratio → global demean → rfft → k≥11 matched scan) and why its G3 needs an amplitude clause.
2. P4 record §Outcome — what an envelope-dominated burst looks like and why it closes without a subtraction attempt.
3. `~/Data/Faber2026/dsa110/upchan_codetections/PROVENANCE.md` — generation recipes, per-burst caveats (mahi LTE outlier, isha upper-bound-only, casey 711–799 MHz band subset), quarantine ledger.

## Why (one paragraph)

Freya's qualification produced a fully calibrated, common-mode-immune Δν_d
estimator and then found freya envelope-confusion-limited — a per-burst
outcome, not a sample statement. The other eleven co-detections have never
been through P3′; their intrinsic envelopes differ, so some may calibrate AND
yield an admissible measurement (or a clean upper limit) where freya could
not. A uniform sample-wide pass converts "demonstrated on the qualification
burst" into a per-burst verdict table for the manuscript, closing the CHIME
question quantitatively for all twelve.

## Data state (verified 2026-07-15)

- **Stokes-I upchan products exist for all 12 bursts** at
  `~/Data/Faber2026/dsa110/upchan_codetections/` (casey, chromatica, freya,
  hamilton, isha, johndoeII, mahi, oran, phineas, whitney, wilhelm, zach) —
  gen-2/3 recipe, defective gen-1 quarantined.
- **Pol-split products exist only for freya**
  (`crossacf-2026-07-14/`, producer
  `/data/jfaber/upchannelize_chime_crossacf_v2_20260714.py` on **h17**, from
  the singlebeam h5s at
  `/data/research/astrophysics/frbs/chime-dsa-codetections/chime_singlebeam/`).
  The P3′ S2 construction takes per-pol dynamic spectra → **S0 must
  regenerate pol-split products for the other eleven** with the same
  producer (in-house; h17; no external CHIME requests).
- Verify the burst list against the co-detection sheet (the sheet is the
  authority — [[codetection-near-misses-are-four]]): 12 staged names should
  equal the paper's 12.
- Per-burst caveats to carry into masks/records: mahi 700–725 MHz alignment
  outlier (LTE-adjacent; widen its exclusion if the predeclared mask rule
  flags it), isha is upper-bound-only (`--run-unresolvable`), casey's hi
  band is historically 711–799 MHz (band rule must adapt).

## The plan

### S0 — data staging (h17, mechanical)

Run `upchannelize_chime_crossacf_v2_20260714.py` per burst on h17 → pol0/pol1
upchan npys + freq npy + crossacf metadata json (with per-product SHA-256s,
as for freya). Pull to
`~/Data/Faber2026/dsa110/upchan_codetections/crossacf-<date>/`; extend the
pipeline `DATA_MANIFEST.yaml`; append to PROVENANCE.md. The metadata records
the applied DM per burst — CHIME-optimized DMs, state the convention
([[chime-products-carry-chime-optimized-dms]]).

### S1 — one sample-wide predeclaration (uniform methods)

Single record `experiment-chime-scint-samplewide-p3.md`, frozen before any
burst's fine-channel statistic is inspected. Uniform methodology across all
eleven (the owner's standing rule: no per-burst method cherry-picking;
morphology differences become per-burst systematics, not method choices):

- **Estimator:** P3′ verbatim (S2 split-ratio, global demean, k ≥ 11 matched
  scan, 25-point 20–400 kHz grid, N_TEMPLATE=200, null-mean-subtracted z).
- **Per-burst geometry by frozen recipe, not judgment:** on-pulse window and
  off-pool from the **band-mean time profile only** (Gaussian-smoothed σ=2;
  window = contiguous S/N>3 region around the peak padded to ≥100 samples;
  off-pool = everything ≥10 samples outside, with the freya-style tail
  guard). Reading the band-mean profile does not open the spectral blind.
  RFI/LTE mask by the P2 rule; band = widest common 600–800 MHz subset the
  products support (casey: 711–799). f_b measured as the window-mean on/off
  contrast (the P2 definition) — profile-level, blind-safe.
- **Injection grid:** m ∈ {0.15, 0.17} uniformly (per-burst DSA m priors are
  revoked pending the trust reset — do NOT import them), Δν_d ∈ {35 control,
  77, 127, 213, 352} kHz, 50 realizations; G1″/G2″ gates verbatim from P3′.
- **Blinding:** the eleven bursts' on-pulse spectra have never been seen —
  full blind discipline per burst (structural guard, calibrated-selection
  gate, explicit unblind flag).
- **G3 admissibility with the amplitude clause from day one** (the P3′
  lesson): z ≥ trials threshold AND width in the Gate-0 window AND implied
  m = √â/f_b ∈ [0.05, 0.30]. Envelope-dominated outcomes (freya-like:
  amplitude above ceiling, width railed) close per the freya P4 precedent —
  **no automatic per-burst P4**; a separability re-run for a specific burst
  is its own owner sanction.
- **Seeds:** per-burst offset spaces, e.g. burst_index·10⁷ + the P3′
  offsets — disjoint from every prior space; enumerate in the record.
- **Verdict taxonomy per burst:** admissible measurement / envelope-dominated
  (fail-closed) / calibration-fail (DOCUMENTED-FAIL) / upper limit.

### S2 — per-burst blinded calibration (mechanical once S1 is frozen)

Generalize the P3′ harness: replace the freya-hardcoded `Products` defaults
(`routeb_calibration.py`) with a per-burst config (paths, band, window
recipe outputs, f_b); then per burst: `freeze → tbattery → g1 → g2 →
select`. Sanity gates: envelope contrast ≈ f_b; Gate-0b-style forecast ≥3σ
at 213 kHz before G1 (skip bursts that fail the forecast — that is a
recorded outcome, not a silent drop). Figures per burst (calibration plots,
E0-style descriptive panel) — visual vetting for all twelve together, the
owner's standing preference.

### S3 — unblinding policy (owner decision at S1 freeze)

Options to put in the record: (a) batch authorization — bursts whose
selection = `calibrated` unblind automatically under the fail-closed G3;
(b) per-burst owner authorization as for freya. Recommend (a): the gates are
frozen and fail-closed, and eleven separate asks adds latency without adding
control. Either way the record freezes it BEFORE any calibration verdict
exists.

### S4 — aggregation and manuscript

Sample-wide verdict table (per burst: calibration status, verdict class,
z/â/width where unblinded, ceiling comparison); RESULT.md + INVENTORY
entries; FLITS PR(s) → pin bump → board. Manuscript integration rides the
closure-wording ratification (still open from P3′/P4).

## Infrastructure / execution details

- **Repo:** FLITS branch `scint/samplewide-p3` off `479d2c8`; fresh worktree
  (`git -C <any FLITS worktree> worktree add
  ~/Developer/scratch/worktrees/flits-samplewide-p3 -b scint/samplewide-p3
  origin/main`). Never touch the in-repo `pipeline/` checkout (separate
  lane, `scint/c1-allpairs-crossgp`, dirty).
- **Lane:** one lane `chime-samplewide-p3` (GitHub issue required by
  `--check`), per-burst progress in the journal, board via
  `program-state.toml` + `sync_state.py` only.
- **Compute:** staging on h17 (~hours, 11 producer runs); calibration on the
  laptop ≈ 45–90 min/burst serial (freeze ~2 min, tbattery ~10, G1 ~30, G2
  ~10) — parallelize 2–3 bursts if wall-clock matters; conda `py312`.
- **Journal every ≤10 min of active work**
  (`bash scripts/journal-append.sh claude chime-samplewide-p3 …`).

## Reproducibility & Data State

- Freya artifacts untouched by this pass; its verdicts stand.
- All inputs pinned by SHA-256 at S0; per-burst frozen configs hashed.
- Exactly one burst in the sample has a certified DSA-band anchor
  (FRB 20220506D, γ = 0.446 MHz at 1328.24 MHz — map its codename from the
  sheet at S1): only there can a CHIME result be cross-band-checked; note
  availability per burst in the record (the freya E3c lesson).
- In-flight: none. Faber2026 main `f161f12` clean & deployed; FLITS main
  `479d2c8` green.

## Verification State / Known-Broken

- P3′ chain: 18/18 tests at pin; P4 additions: 11/11. tbattery re-runs per
  burst (geometry-dependent).
- Known quirks that will recur: +12 % matched-estimator amplitude bias
  (measured, re-measure per burst); ~1σ positive null mean (always
  null-mean-subtract); freya's off-pool tail rise (~samples 430–437, likely
  dedispersion wrap) — the window recipe's tail guard must check for the
  analogous feature per burst.

## Learnings (beyond the P4 handoff's seven, which all still bind)

1. **`conda run` buffers stdout until exit** — write scripts to files and
   log to files; never watch a heredoc.
2. **Freeze every implementation choice the record leaves open** (surrogate
   source scale, template carrier, injection weight) in the frozen config
   BEFORE running; post-hoc adjustment is forbidden even when a choice looks
   harsh in hindsight.
3. **Check discriminant-input availability at predeclare time** (trusted
   anchors, component counts) — freya's E3b/E3c were both unavailable and
   that shaped what any candidate could ever become.
4. **Background merge chains:** `gh pr merge` can silently no-op — always
   re-verify `state == MERGED`; poll `gh pr checks` with a bounded loop.
5. **A 40σ z_max can be a foreground, not a detection** — the amplitude
   ceiling is the discriminating gate; carry it in G3 from the start.

## Action Items & Next Steps (priority order)

1. [ ] **Owner go/no-go** for the sample-wide pass (this handoff is the
   plan; nothing runs without it).
2. [ ] S1 predeclaration record + lane + issue; owner picks the S3
   unblinding policy at freeze.
3. [ ] S0 staging on h17 (11 pol-split regenerations, SHA-256 manifest,
   PROVENANCE append).
4. [ ] Harness generalization + per-burst configs; window-recipe unit tests.
5. [ ] S2 calibrations (forecast-gated), figures, journal.
6. [ ] S3 unblindings per the frozen policy; G3 fail-closed.
7. [ ] S4 verdict table, RESULT, INVENTORY, FLITS PR, pin bump, board,
   owner review together with the closure wording.

**Recommended Next Skill:** `ai-research-workflows:experiment-records` for
S1, then `implementing-plans` against this handoff.

## Other Notes

- Expectation-setting: plausible outcomes range from a first admissible
  CHIME Δν_d (if any burst has a weak envelope + strong scintle) to eleven
  more fail-closed records; every outcome is manuscript-usable because the
  gates are uniform and predeclared.
- The four excluded co-detections (data-availability exclusions, sheet
  authority) stay out of scope.
- freya = FRB 20230325A; wilhelm = FRB 20221203A; map remaining codenames
  from the sheet when building configs.

---

**Handoff created by AI Assistant on 2026-07-15**
