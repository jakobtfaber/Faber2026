# DM provenance audit — CHIME vs DSA (12 co-detections)

---
**Date:** 2026-07-07  
**Author:** codex-gpt-5.5 (read-only audit, dispatched from Faber2026)  
**Full transcript:** `logs/codex-dm-provenance-audit.json`  
**Trust boundary:** `CONTEXT.md` — DM_obs not citable until V6 ladder passes  
---

## Bottom line

**No DM_obs value is currently citable.** Manuscript tables/prose collapse CHIME and DSA into one column; the pipeline does not document per-telescope measurement methods in a pinned, reproducible artifact set.

## Per-burst summary

| Burst | CHIME DM (pc cm⁻³) | CHIME status | DSA/ref DM (pc cm⁻³) | DSA status |
|-------|-------------------|--------------|----------------------|------------|
| zach | 261.524 ± 0.020 | measured (8/12 set) | 262.368 ± 0.1 | catalog in `bursts.yaml` |
| whitney | — | unconstrained | 462.174 ± 0.1 | catalog |
| oran | — | unconstrained | 396.882 ± 0.1 | catalog |
| isha | 411.215 ± 0.111 | measured | 411.568 ± 0.1 | catalog |
| wilhelm | 601.902 ± 0.013 | measured | 602.346 ± 0.1 | catalog |
| phineas | 609.821 ± 0.031 | measured | 610.274 ± 0.1 | catalog |
| freya | 912.277 ± 0.006 | measured | 912.4 ± 0.1 | catalog |
| johndoeII | — | unconstrained | 696.506 ± 0.1 | catalog |
| hamilton | 518.834 ± 0.006 | measured | 518.799 ± 0.1 | catalog |
| mahi | — | unconstrained | 960.128 ± 0.1 | catalog |
| chromatica | 272.384 ± 0.020 | measured | 272.664 ± 0.1 | catalog |
| casey | 491.168 ± 0.0005 | measured | 491.207 ± 0.1 | catalog |

**Sources:** `pipeline/crossmatching/chime_side_inputs.json`, `pipeline/configs/bursts.yaml`, `pipeline/crossmatching/notebook_reproduction_fixture.json`.

## Method chains

### CHIME

1. Coherent dedispersion at DSA reference DM → sub-band EMG arrival fits → weighted `t₀` vs `ν⁻²` regression (`dispersion/chime_dm.py`).
2. Recorded in `chime_side_inputs.json` as “arrival-time regression” (8 constrain, 4 do not).
3. Legacy DMPhase/structure-max route **retracted** (`.agents/audit-chime-side-dm.md`).
4. **Gap:** producing artifacts (`chime_dm_final.json`, grid NPZ) live off-repo on h17 `/data/...`; repo has summary JSON + plot script only.

### DSA

1. Values in `configs/bursts.yaml` are **catalog/frozen references** (±0.1 pc cm⁻³ placeholder uncertainty in fixture), not remeasured by this pipeline.
2. Scattering fits use them as `dm_init`; CHIME configs use `dm_init: 0` (pre-dedispersed products).
3. `burstfit.py` `delta_dm` is a **residual** around `dm_init` (±50 pc cm⁻³ cap), not full DM_obs.

## Gaps / conflicts (V6 blockers)

1. `association.py` still marks CHIME DM “SUSPENDED” while `chime_side_inputs.json` holds 8 active measurements.
2. CHIME extraction artifacts not pinned in git; figure manifest points to off-repo docker run.
3. `budget_table.tex` single `DM_obs` column — no CHIME/DSA split; `sightline_budget.py` parses filename DMs, not measured per-telescope values.
4. Manuscript abstract/sample still cite undifferentiated DM_obs range (trust-reset violation).

## Next lane

Plan target: **V6** per-burst, per-telescope DM_obs provenance table (`plan-trust-reset-revalidation.md` P6).
