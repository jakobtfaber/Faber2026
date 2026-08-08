# Handoff: Re-calculate co-detection ToAs from metadata (V6 association re-validation)

---
**Date:** 2026-07-07 09:25 -0700
**Author:** AI Assistant (Claude, Faber2026 session)
**Status:** Handoff
**Branch:** main
**Commit:** 85cbf55 (superproject); pinned pipeline submodule 2d62ac8
---

## Task(s)

Recompute the per-burst, per-telescope CHIME/FRB–DSA-110 times-of-arrival (ToAs)
and their CHIME↔DSA agreement from pinned metadata, with documented provenance,
so the association-diagnostics columns (timing residual, chance-coincidence
probability P_cc, association verdict) and DM_obs can be restored to citable
status. These are **Wave-3 revoked** in `CONTEXT.md` and must be re-derived from
raw inputs before they appear in the manuscript.

| Task | Status | Notes |
|------|--------|-------|
| Table 1 (`tab:sample`) — trust-safe sample roster | ✅ Complete (uncommitted) | TNS, nickname, RA/Dec, single detection epoch MJD/UTC @ 400 MHz. No revoked columns. |
| ToA re-calculation from metadata (this handoff) | 📋 Planned | Recipe below + existing Phase 6 plan; not yet implemented. |
| Per-telescope DM provenance (sibling, V6 P6.2) | 📋 Planned | See `dm-provenance-audit-2026-07-07.md`; blocks the same columns. |

**Current Workflow Phase:** Implement (the plan exists — Phase 6 of
`plan-trust-reset-revalidation.md`; the next session implements P6.2/P6.3).

## Workflow Artifacts

**Plan Documents:**
- [plan-trust-reset-revalidation.md](../plan/plan-trust-reset-revalidation.md) — **Phase 6
  (lines 1368–1458)** is the authoritative V6 recipe: P6.1 anchor inventory,
  P6.2 DM provenance table + agreement figure, P6.3 TOA association
  re-derivation. Do not duplicate it — implement it.
- [plan-circulation-readiness.md](../plan/plan-circulation-readiness.md) — parent plan;
  V6 line item at ~145–151.

**Validation / Audit Reports:**
- [dm-provenance-audit-2026-07-07.md](../dm/dm-provenance-audit-2026-07-07.md) — sibling
  audit (codex, read-only). Confirms no DM_obs is citable: CHIME 8/12 measured
  via arrival-time regression, 4 unconstrained; DSA values are frozen catalog
  refs. The ToA problem is the timing analog of this DM problem.

## Critical References

Read these first, in order:

- `pipeline/crossmatching/toa_crossmatch.py` — the ToA arithmetic. **Key finding:**
  `reproduce_notebook_result()` (line 151) is a *reproduce-the-notebook* shim, not
  a fresh derivation. The CHIME ToA is taken verbatim from stored provenance
  (`ChimeTimingProvenance.toa_time_400`, line 36); only the **DSA** ToA is
  computed (`compute_toa`, line 156), and it dedisperses with the **single
  undifferentiated `dm`** (line 154) — the exact Wave-3 defect.
- `pipeline/crossmatching/chime_side_inputs.json` — per-burst CHIME metadata.
  **Both-telescope DMs already live here** (`dm_dsa`, `dm_chime`, `dm_chime_err`,
  `dm_confidence`, `method`) for 8/12 bursts. This is the join key for V6.
- `pipeline/configs/bursts.yaml` — registry of record: `chime_id`, `dm`
  (undifferentiated DM_obs), `dm_err`, `mjd` (= CHIME 400 MHz ToA, verified to
  match `t_unix`), `utc`, `ra_deg`, `dec_deg`.
- `docs/rse/specs/plan/plan-trust-reset-revalidation.md` Phase 6 — the acceptance
  contract.

## Recipe — recompute ToAs from metadata

**Inputs (all from the pinned submodule `pipeline/`, commit 2d62ac8):**
- `configs/bursts.yaml` — chime_id, DM, dm_err, mjd, utc, ra_deg, dec_deg.
- `crossmatching/chime_side_inputs.json` — per-telescope DMs + CHIME method/provenance.
- `crossmatching/notebook_reproduction_fixture.json` — `CrossmatchInput` fixtures
  (`ChimeTimingProvenance`: baseband_path, peak_index, delta_time_s;
  `DsaTimingProvenance`: dsa_mjd, native_frequency_mhz=1530, filterbank tstart/tsamp/nchans/fch1/foff).
- `crossmatching/association_report.json` — committed reference output to diff against.
- `scattering/scat_analysis/burst_metadata.py::_FALLBACK_TNS` — nickname → TNS.

**Computation (functions already in `toa_crossmatch.py`):**
1. Dedisperse each telescope's arrival to a common 400 MHz reference —
   `compute_toa(t0, offset, f_center, DM, f_ref=400 MHz)` (line 99):
   `shift = K_DM · DM · (1/f_ref² − 1/f_center²)`. Matches the manuscript
   `eq:dmdelay` in `sections/toa.tex`.
2. Geometric light-travel delay — `compute_geometric_delay(t, src, DRAO, OVRO)`
   (line 128): GCRS baseline projection onto the source unit vector / c. Matches
   `eq:geodelay`. **Verify site coords**: the function uses
   `EarthLocation.of_site("DRAO"/"OVRO")` (lines 169–170), whereas `main()` uses
   explicit lat/lon/height (lines 270–271) that differ slightly — pick one and
   document it.
3. Residual = `measured_offset_ms` (chime_toa − dsa_toa, line 163) − `geometric_delay_ms`.
4. DM-uncertainty timing error per telescope via
   `calculate_dm_timing_error(dm_err, f_center, f_ref)`, combined in quadrature
   (`main()` lines 254–258).

**The four corrections that make the output citable (the V6 delta):**
1. **Per-telescope DM.** Dedisperse the DSA ToA with `dm_dsa` and the CHIME ToA
   with `dm_chime` (from `chime_side_inputs.json`) — not one shared `dm`. This is
   the core Wave-3 fix.
2. **Re-derive (or pin) the CHIME ToA.** `reproduce_notebook_result` returns the
   stored `toa_utc_400`; the `baseband_path`/`peak_index`/`delta_time_s`
   provenance fields exist but are not recomputed. V6 must either re-derive from
   raw baseband or cite the producing artifact with a checksum.
3. **Handle the 4 CHIME-unconstrained bursts** — whitney, oran, johndoeII, mahi
   (per the DM audit). Their offset currently uses the DSA DM on both sides, so
   CHIME↔DSA agreement is undefined; flag rather than quote.
4. **Reconcile `association.py`** — it still marks CHIME DM "SUSPENDED" while
   `chime_side_inputs.json` holds 8 live measurements (DM audit gap #1).

## Reproducibility & Data State

- **Environment:** conda env `flits` (Python 3.12). Run pipeline code as
  `conda run -n flits python …`. When validating *pinned* behavior, run from
  inside `pipeline/` so the cwd shadows the editable-installed canonical clone
  (see repo `CLAUDE.md`).
- **Pin:** pipeline submodule at `2d62ac8`, branch
  `agent/codetection-dm-power-20260707` (see Known-Broken — not detached, one
  dirty file). All metadata above is read from this checkout.
- **Data:** ToA/DM inputs are small JSON/YAML committed in the submodule. The
  **CHIME extraction artifacts** (`chime_dm_final.json`, grid NPZ) that produced
  `chime_side_inputs.json` live **off-repo on h17 `/data/...`** — not pinned; the
  repo has only the summary JSON + plot script (DM audit gap, method chain step 4).
  Provenance is therefore incomplete until those are pinned or checksummed.
- **Seeds:** none — the ToA/geometric math is deterministic.

## Verification State / Known-Broken

- **Tests (not run this session — run as the P6.3 baseline first):**
  `tests/test_association.py`, `tests/test_chime_singlebeam_toa.py`,
  `tests/test_crossmatching_notebook_reproduction.py`, `tests/test_chime_dm.py`.
  Record pass/fail at the pin before changing anything.
- **Uncommitted (this session, Faber2026 working tree):**
  `sections/observations.tex` (Table 1 wired in + §2 prose unbundled),
  `sample_table.tex` (new), `scripts/make_sample_table.py` (new). `make` exits 0,
  table renders p3, no new warnings. **Not committed, not pushed** — Table 1 is
  not yet in Overleaf (Overleaf pulls GitHub `main`).
- **Separate active lane (do not touch):** pipeline submodule has an in-flight
  dirty file `flits/batch/codetection_plots.py` on branch
  `agent/codetection-dm-power-20260707` — another task's work. This session only
  *read* pinned data; it did not modify the submodule.
- **Unverified:** every current ToA residual / P_cc / DM_obs in
  `toa_crossmatch_results.json` and `association_report.json` is **revoked** and
  must not be quoted until V6 re-derivation passes.

## Learnings

- The both-telescope DMs the DM audit "needs" already exist in
  `chime_side_inputs.json` (`dm_chime`/`dm_dsa`) for 8/12 bursts — V6 is largely a
  *join + provenance-documentation + re-derivation* task, not a new measurement
  campaign (except the 4 CHIME-unconstrained bursts).
- `toa_crossmatch.py` conflates two things: it *reproduces* the CHIME ToA (stored)
  but *computes* the DSA ToA. A faithful V6 re-derivation must treat both
  symmetrically, each with its own documented DM and method.
- The single detection epoch already in `tab:sample` (MJD/UTC) is the CHIME
  arrival referenced to 400 MHz — safe to show as identification; showing CHIME
  and DSA ToAs side-by-side is the revoked comparison and must wait for V6.
- Trust-boundary rule (CONTEXT.md:28–40): positions, nicknames, designations, and
  raw epochs are *inputs* (quotable); residuals, P_cc, verdicts, and DM_obs are
  *revoked products*. Keep that split when deciding what a table may show.

## Action Items & Next Steps

1. [ ] Run the P6.3 baseline oracles at the pin and record pass/fail
   (`tests/test_association.py`, `tests/test_chime_singlebeam_toa.py`,
   `tests/test_crossmatching_notebook_reproduction.py`).
2. [ ] Do the P6.1 anchor inventory: confirm each burst's DSA-side DM origin and
   where the `chime_side_inputs.json` values were produced (file:line), and
   whether `association.py`/`toa_crossmatch.py` reproduce `association_report.json`
   at the pin.
3. [ ] Implement P6.2: `scripts/build_dm_provenance.py` → `crossmatching/dm_provenance.csv`
   (12 rows; per-telescope DM, method, source, ΔDM, ΔDM σ); make
   `tests/test_dm_provenance.py` green; produce the per-burst ΔDM agreement figure.
4. [ ] Implement P6.3: re-derive ToAs symmetrically (per-telescope DM), regenerate
   `association_report.json`, diff against committed — parity ⇒ reproducible; any
   mismatch is a finding to resolve.
5. [ ] Resolve the 4 CHIME-unconstrained bursts (whitney/oran/johndoeII/mahi) and
   the `association.py` "SUSPENDED" inconsistency.
6. [ ] Only after V6 passes: extend `tab:sample` (or add a companion association
   table) with the re-derived residual / P_cc / verdict columns, and reconcile the
   `sections/toa.tex` §3.1.2 "withheld" prose. Regenerate with
   `scripts/make_sample_table.py` and rebuild (`make` exits 0).
7. [ ] Pin or checksum the off-repo h17 CHIME extraction artifacts so the CHIME
   ToA/DM provenance is complete.

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` (Phase 6 of
`plan-trust-reset-revalidation.md` is written and ready to execute). Use
`ai-research-workflows:validating-implementations` once P6.2/P6.3 land.

## Other Notes

- **Outward-facing boundary:** getting Table 1 (and later the association columns)
  into Overleaf requires committing to `main` and pushing — Overleaf pulls GitHub
  `main`. That push is the one-way door; leave it to the owner.
- Do not bump the `pipeline/` pin casually; a pin bump is a deliberate `build:`
  commit after the corresponding pipeline work merges upstream (repo `CLAUDE.md`).
- Journal cadence: append `docs/rse/protocols/journal.jsonl` via `scripts/journal-append.sh`
  every ≤10 min of active V6 work.

---

**Handoff created by AI Assistant on 2026-07-07**
