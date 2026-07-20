# Implementation Summary: freya production β co-model joint fit (dsa110-FLITS #104)

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Complete (merged 2026-07-03, squash `e09ac78b`, owner-authorized)
**Plan Reference:** dsa110-FLITS issue #104 Agent Brief + PRD ([prd-freya-beta-comodel-real-data-fit.md](../notes/prd-freya-beta-comodel-real-data-fit.md)); #103 gate green (merged `41bfe977`)

---

## Overview

The production joint fit: freya's real CHIME+DSA bands through the shared-ζ(ν)
driver path (`fit_joint_scattering --shared-zeta`, Route B) with the β co-model
(ADR-0006) — single sampled turbulence index β driving both the power-law PBF
shape and the α = 2β/(β−2) thin-screen closure. dynesty nested sampling,
nlive 600, dlogz 0.5, rwalk, fork pool, on jakob-mbp in the `flits` env.

**Headline result (fit claim status: current-model result):**

| Quantity | Value |
|---|---|
| β (sampled) | **3.684 +0.013/−0.014** — un-railed (52σ / 24σ from the [3, 4) prior edges), ~1σ above Kolmogorov 11/3 |
| α (derived, thin-screen closure) | **4.376 +0.019/−0.018** |
| τ₁GHz | **0.1144 ± 0.0011 ms** |
| ζ₁GHz, x_ζ | 0.0855 ± 0.0006, −0.752 ± 0.019 (x_ζ–β corr r = +0.011, benign) |
| ln Z | −24144.12 ± 0.55 (ncall 1,050,284, ~6.6 min wall) |
| t0_C | 17.258 ms (raw-init 17.557; the #98 drag worry was moot — ±20 ms prior floor covers it) |
| PPC χ²/dof | CHIME **1.18**, DSA **1.03** — both PASS Level-2 (0.3–1.5); figure visually reviewed, verdict "match" |

Against the exp-era deprecated-fit *suggestion* (α = 4.355, τ = 0.119 ms): the
co-model shifts α by ≈ +0.02 — well within the PRD's "≤ 0.1 → wording-only"
manuscript claim band — and τ by −0.005 ms.

**Binding caveat (owner-adopted window decision):** the #101 tail-coverage
preflight at the *fitted* candidate (τ=0.1144, β=3.684) gives 2.07 e-folds /
87.4% captured — **FAIL** against the 3.0 threshold. This is the documented
sensitivity-regime caveat: the raw 81.9 ms captures cannot reach 3 e-folds for
β ≲ 3.7 at this τ (widening the window to all available headroom only reaches
2.82), so the β measurement rests on the fitted-tail region available, and the
**#106 verdict artifact must carry this caveat verbatim.**

## What changed (PR #114, branch `feat/104-freya-joint-production-fit`)

**`analysis/scattering-refit-2026-06/local_runs/run_joint_fit.py`** — the
gain-recovery block crashed post-ADR-0006: `FRBParams(alpha=…)` TypeErrors
(FRBParams is beta-native; alpha is a derived property). Found by pre-run
inspection, fixed *before* the production run (would have crashed after the
sampler finished): both constructions now pass `beta=p["beta"]`; β→α is
monotone so the β median is the α median's preimage. Codex-verified: no other
`alpha=` FRBParams construction reachable on the driver path; every joint-mode
name set that reaches the block carries `beta`.

**`analysis/scattering-refit-2026-06/joint_ppc.py`** — four changes:
1. beta-native FRBParams at all 4 construction sites (same TypeError class).
2. Derived α read from the top-level `d["alpha"]["median"]` summary
   (beta-native `percentiles` carry only the 8 sampled params).
3. Optional variant-tag argv (`joint_ppc.py freya _sharedzeta`) matching the
   driver's output naming — and, per Codex round-1 P1, the tag flows into the
   **output** names too (`{b}_joint_ppc{tag}.{png,json}`), so a tagged PPC can
   no longer clobber/impersonate the untagged baseline pair that
   `gate_joint_committed.py` / `report_prepost.py` read (fix `8e620309`).
4. Per Codex round-1 P1: legacy alpha-only JSONs with α < 4 now **raise**
   instead of silently exp-clipping (`beta_from_alpha_thin_screen` is only
   faithful for α ≥ 4; α < 4 maps to β > 4 which the model clips to the
   exponential branch — the PPC would have validated at effectively α = 4).

**Committed artifacts** (`local_runs/`): `freya_joint_fit_sharedzeta.json`,
`freya_joint_samples_sharedzeta.npz` (the fit is not seed-pinned — the
posterior npz is the only provenance record), `freya_joint_ppc_sharedzeta.json`
+ `.png` (force-added), `figures.manifest.json` + `figures.review.json`
(figure-review gate, verdict "match" from a visual read of the rendered PNG).

**Known-stale JSON metadata (do not read as results):** `pbf_C: powerlaw` /
`pbf_D: exp` and `beta_C = beta_D = 3.667` in the fit JSON are dead per-band
attrs from the pre-co-model CLI defaults; the fit result is `percentiles.beta`
and the top-level derived `alpha`.

**Physics kernel untouched** (`burstfit.py` not in the diff — Codex-verified).

## Verification Results

- ✅ Production run end-to-end through the previously-crashing gain-recovery
  block (`gain_recovered: true` in the JSON).
- ✅ PPC: CHIME 1.18 / DSA 1.03; post-fix tagged rerun byte-identical χ² values.
- ✅ Figure gate: rendered PPC visually Read — model overlays data through the
  CHIME tail's full decay (~17–25 ms) and the DSA spike; no unmodeled
  sub-structure at band-summed scale.
- ✅ ruff: no new findings (pre-existing E402×8 + B007 in joint_ppc.py verified
  pre-existing by stash A/B; left per the #113 precedent on out-of-lane lint).
- ✅ CI green on the PR (3/3 checks).
- ✅ **Adversarial review** (Codex, gpt-5.5 high, read-only): round 1
  REQUEST_CHANGES — two P1s on joint_ppc.py (silent α<4 exp-clip in the legacy
  fallback; tag not flowing into output names), both fixed in `8e620309`;
  driver fix and kernel-untouched checks passed round 1. Round 2 **APPROVE,
  zero findings** — Codex independently traced the α=4.0 boundary
  (`beta_from_alpha_thin_screen(4.0) → 4.0`, not caught by the guard), the
  unchanged untagged path, tag propagation at all three read/write sites, and
  artifact consistency (PPC JSON values exactly match the fit JSON; no
  leftover untagged pair in the git tree).

## Known Caveats

- **Tail-coverage FAIL at the fitted candidate** (2.07 e-folds / 87.4%): the
  binding sensitivity-regime caveat for #106 (above).
- The fit is not seed-pinned (`fit_joint_scattering` passes no `rstate`);
  reproduction is statistical, not bitwise — the committed npz is provenance.
- χ²_red is mildly diluted by the ~50%-off-pulse window (by design: noise
  estimated from window outer quarters); PPC/visual review sees structure.

## Next Steps

1. ~~Merge PR #114~~ — **merged** 2026-07-03 (squash `e09ac78b`,
   owner-authorized); worktree/branch cleaned up, canonical clone synced.
2. **#105** Route A cross-check fit (`run_beta_poc.py --real`) — agreement
   band per the PRD.
3. **#106** verdict artifact — must carry the truncation caveat verbatim.
4. **Pin bump** in Faber2026 (deliberate `build:` commit, target ≥ #114's
   squash SHA) once the DAG's code has merged; manuscript motion only after
   #106.

## References

**Issue/PR:** https://github.com/jakobtfaber/dsa110-FLITS/issues/104 · https://github.com/jakobtfaber/dsa110-FLITS/pull/114
**Sibling docs:** [implement-likelihood-equivalence.md](../implement/implement-likelihood-equivalence.md) (#103) · [implement-freya-tail-coverage-preflight.md](../implement/implement-freya-tail-coverage-preflight.md) (#101) · [implement-poc-beta-native.md](../implement/implement-poc-beta-native.md) (#102)

---

**Implementation completed by AI Assistant on 2026-07-03**
