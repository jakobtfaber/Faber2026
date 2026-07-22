# Implementation Summary: POC validation semantics + diagnostic figures (dsa110-FLITS #111)

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Complete (merged 2026-07-03, squash `d0d3592a`)
**Plan Reference:** dsa110-FLITS issue #111 (filed from Codex's adversarial review of PR #110; both findings pre-existing from PR #96). Ordered as its own slice by the owner rather than folded into the #102 migration PR, to keep the migration's behavior-preservation evidence clean.

---

## Overview

Follow-up slice to #102: the beta POC's private `_validate()` no longer contradicts the kernel's `classify_fit_quality`, and the runner now emits the full diagnostic-figure set the fit-quality contract requires. Route A's real fit is now quality-bearing for #105.

**Final Status:** ✅ Complete — PR https://github.com/jakobtfaber/dsa110-FLITS/pull/112 (`Closes #111`), branch `fix/111-validate-classify-fit-quality` off `37d76a49`, **merged** 2026-07-03 (squash `d0d3592a`, owner-authorized).

## What changed

**`analysis/beta_poc/run_beta_poc.py`:**

- `_validate()` Level-2 now **delegates** to the kernel's `classify_fit_quality(red_chi2, r2)` (burstfit.py:1464) instead of re-implementing gates: χ²_red is the only verdict-driving Level-2 statistic (PASS 0.3–1.5, MARGINAL 1.5–10 or suspicious <0.3, FAIL >10); R² and Durbin–Watson demote to informational `notes`. Level-1 τ/α physical-plausibility gates unchanged. Return shape gains `notes` alongside `verdict`/`fails`/`marginals`.
- New `_matched(m, tau, z1, x, t0, ddm, beta)` helper returns (data, gain-matched model, valid-mask); `_goodness()` consumes it — χ², dof, R², DW expressions verbatim from before (math unchanged, confirmed by source comparison in review).
- New `_diagnostic_figure(...)`: per-band 3-panel figure — band-summed data-vs-model, residual profile, and normal Q-Q of the standardized 2-D residuals (`sqrt(2)*erfinv(2q-1)` theoretical quantiles). Satisfies the fit-validation contract checklist (data-vs-model + residual + Q-Q + DW; `.cursor/rules/AGENT_CONFIGURATION_FLITS.md:403-406`).
- `_write_manifest(outdir, figures, data_source)` writes/merges `figures.manifest.json` entries; summary JSON gains a `diagnostics` field pointing at the figures.

**Committed artifacts (`analysis/beta_poc/freya/`):** refreshed `freya_beta_poc_fit.json` (verdict now PASS, with the R²/DW observations as notes); `freya_beta_poc_diag_{chime,dsa}.png` (force-added past `.gitignore` `*.png` per the tracked `dsa_figs` precedent); `figures.manifest.json` + `figures.review.json` (both figures visually reviewed, verdict "match", per the figure-review Stop gate).

**`CLAUDE.md` (dsa110-FLITS):** Level-2 validation prose rewritten to `classify_fit_quality` semantics; the "single source of truth" thresholds line tightened — the Level-2 χ²_red bands (0.3/1.5/10.0) live beside `classify_fit_quality` in `burstfit.py`; `VALIDATION_THRESHOLDS.py` remains canonical for other constants but its `CHI_SQ_RED_MARGINAL_MAX = 3.0` is superseded for Level 2.

**Physics kernel untouched** (`burstfit.py` not in the diff — verified in review with `git diff --quiet origin/main...HEAD`).

## Verification Results

All in the `flits` conda env on jakob-mbp:

- ✅ **Behavior-preserving posterior:** same-seed re-run reproduces β = 3.7136028229935194 and ncall = 181,743 *exactly*; structured JSON comparison shows only `validation` and the new `diagnostics` changed. The MARGINAL→PASS verdict flip is therefore attributable solely to validation-label semantics (the old code let informational R² drive the verdict), not to any change in the fit.
- ✅ **`_validate()` oracle** (standalone script, importlib): PASS at χ²_red ≈ 1 regardless of R²/DW; χ²-driven MARGINAL (2.5), FAIL (12.0), and suspicious-low MARGINAL (0.1) all gate; Level-1 α gate still FAILs; R²/DW observations land in `notes`.
- ✅ **Q-Q construction** verified against an independent known-normal sample before adoption.
- ✅ Figures visually reviewed (both bands: model tracks data, residuals structureless at this scale, Q-Q hugs y=x); review JSON committed.
- ✅ `ruff check` + `ruff format --check` clean.
- ✅ **Adversarial review** (Codex, gpt-5.5 high, read-only): initial REQUEST_CHANGES — MAJOR: diagnostic set incomplete (no Q-Q panel; the contract checklist requires it — Codex also asked for a residual histogram, which is only example code in the contract, not a checklist item); MINOR: CLAUDE.md still called `VALIDATION_THRESHOLDS.py` the single source of truth. Both fixed in-lane (third panel added, prose tightened), re-reviewed, merged.

## Known Caveats

- The committed diagnostic figures are for the **synthetic** POC fit; the `--real` Route A fit at #105 must regenerate its own set (the runner now does this automatically).
- Verdict semantics now match the kernel; any future change to `classify_fit_quality` bands propagates to the POC automatically (that is the point of delegating).

## Next Steps

1. **#103** (likelihood equivalence, Route A `BetaCoupledLogL` vs Route B `_JointLogLikelihoodGainSharedZeta`) — re-triaged `ready-for-agent` with an Agent Brief 2026-07-03; the brief also assigns the stale "alpha" θ-label docstring at `burstfit_joint.py:672` to that lane.
2. #104 (production joint fit) — gated on the #101 preflight at adopted candidates + #103 PASS; CHIME window decision (`FLITS_ONPULSE_PAD`) first.
3. #105 (Route A cross-check fit) — now unblocked on the quality side by this slice.

## References

**Issue/PR:** https://github.com/jakobtfaber/dsa110-FLITS/issues/111 · https://github.com/jakobtfaber/dsa110-FLITS/pull/112
**Sibling docs:** [implement-poc-beta-native.md](../implement/implement-poc-beta-native.md) (#102) · [implement-freya-tail-coverage-preflight.md](../implement/implement-freya-tail-coverage-preflight.md) (#101)

---

**Implementation completed by AI Assistant on 2026-07-03**
