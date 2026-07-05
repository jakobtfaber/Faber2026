# Handoff: freya CHIME E3/E4 gen-3 rerun — ν^4.4 verdict reverses; FLITS config lane closed

---
**Date:** 2026-07-05 14:34
**Author:** AI Assistant
**Status:** Handoff
**Branch:** main (Faber2026)
**Commit:** `fbc9855` (pushed; tree clean)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Commit v3 config windows to FLITS (prior handoff item 1) | ✅ Complete | Direct commit `a0a9c83e` on FLITS main (origin re-checked first: tip unchanged, no open PRs). Two yamls only. |
| Close the `flits-rerun` worktree | ✅ Complete | Removed after proofs: plots archived byte-identical, branch zero-cherry vs origin/main, branch deleted. |
| E3 rerun on gen-3 (split-band ν^4.4 + split-time) | ✅ Complete | **REVERSAL**: ratio 0.85 ± 0.18 vs ν^4.4 prediction 1.88 — see below. Split-time consistent. |
| E3b fit-window robustness of the ratio (added this session) | ✅ Complete | Ratio 0.83–1.09 across 1.0/0.5/0.3/0.2 MHz windows — reversal is NOT the window systematic. |
| E4 rerun on gen-3 (m_burst, two-screen coherence) | ✅ Complete | m_burst = 0.30 = pipeline m_acf 0.304; separation 104×; limit 1.12e3 kpc² (placeholder z). |
| Document + verify | ✅ Complete | Experiment doc gen-3 section + appendix; Faber2026 `fbc9855` pushed; adversarial fact-check subagent: PASS, zero discrepancies. |

**Current Workflow Phase:** Experiment complete → next is either Research (instrumental-origin hypothesis) or Plan (fit-window systematic treatment).

## Workflow Artifacts

**Experiment Reports:**
- `experiment-freya-chime-dnu-science-readiness.md` — THE evidence chain. Now includes the gen-3 E3/E4 rerun section ("ν^4.4 verdict REVERSES") + gen-3 raw-data appendix block.

**Implementation Summaries:**
- `implement-freya-chime-dnu-durable-fix.md` — #120/#121 pipeline fixes (unchanged this session).

**Prior Handoffs:**
- `handoff-2026-07-04-12-30-freya-chime-gen3-low-band.md` — items 1–2 ticked this session; superseded by this handoff as the entry point. Its items 3–6 carry forward below.

## Critical References

- `experiment-freya-chime-dnu-science-readiness.md` § "E3/E4 rerun on generation 3 (2026-07-05)" — read first; the science picture changed here.
- `~/Data/Faber2026/dsa110/scintillation-data/exp-dnu-gen3-2026-07-05/` — the three rerun scripts + captured outputs (`out_e3.txt`, `out_e3b.txt`, `out_e4.txt`). Deterministic: reruns reproduced digit-for-digit.
- `~/Data/Faber2026/dsa110/upchan_codetections/PROVENANCE.md` — canonical generation history (unchanged; gen-3 CURRENT).

## The headline result

On the gen-3 (defect-fixed) product the E3 discriminator **rejects the ν^4.4 diffractive-scintillation scaling** for the measured ~35 kHz decorrelation scale:

- band 600–700: 36.94 ± 4.79 kHz (m 0.271); band 700–800: 31.57 ± 5.07 kHz (m 0.271)
- ratio hi/lo = **0.85 ± 0.18** vs ν^4.4 prediction 1.88 (≈5.7σ apart); achromatic prediction 1.00 (≤1σ)
- window-stable: 0.85/0.83/0.87/1.09 at fit_lag 1.0/0.5/0.3/0.2 MHz
- gen-1's "ratio 1.95 ± 0.48, physics check passed" was a defective-product artifact

**Epistemic status:** the ratio is a measured gen-3 result; the *interpretation* (achromatic, channel-locked instrumental correlation ≈ 5–6 fine channels, e.g. PFB leakage) is a hypothesis under test. The canonical Δν_d = 35.19 ± 4.42 ± 17.0 kHz stands as a decorrelation scale, but "consistent with ν^4.4 MW scintillation" must not be quoted. Corroborating: 505–800 band extension left the value unchanged; measurement sits 1.5×(lo)–3×(hi) below the NE2025 floor with the gap growing where ν^4.4 grows fastest.

## Recent Changes

- FLITS main `a0a9c83e` — `scintillation/configs/bursts/freya_chime{,_hi}.yaml`: v3 windows `[253, 268]`/`[253, 264]` burst, `[10, 200]` noise, + provenance comments.
- Faber2026 `fbc9855` — experiment doc gen-3 section + appendix; prior handoff items 1–2 ticked.
- No pipeline code changes this session.

## Reproducibility & Data State

- **Environment:** conda `flits`. The `flits-rerun` worktree is GONE — for future measurement runs make a fresh worktree at FLITS main `a0a9c83e` (or run from the canonical clone *checked out* at it; clone currently sits on `feat/vo-halos-integration` @ `2931e1bf` with local main behind origin — pull deferred by convention). Rerun scripts hardcode `WT = ~/Developer/scratch/worktrees/flits-rerun` — edit `WT` to the new location.
- **Data (canonical, unchanged):** `~/Data/Faber2026/dsa110/scintillation-data/freya_chime.npz` `0b3b423a…`, `freya_chime_hi.npz` `1f644b07…` (gen-3); quarantines intact.
- **Archives this session:** `exp-dnu-gen3-2026-07-05/` (3 .py + 3 .txt) and `freya-chime-runs-2026-07/freya_chime_pass{4_dedispfix,5_v3aligned}/` (moved out of the worktree before removal, diff-verified identical).
- **Determinism:** E3/E4/E3b have no seeds; repeat runs byte-identical on the printed numbers.

## Verification State / Known-Broken

- **Verified:** all new doc numbers adversarially fact-checked by an independent subagent against raw outputs, git state, archives, and re-derived arithmetic — PASS, zero discrepancies. verify-gate recorded (`adversarial-review`, sha `ddc4e165424c`).
- **Uncommitted / unpushed:** none in Faber2026 or FLITS for this lane. FLITS canonical clone: local main still behind origin (now by 2: `9ebe02cf` vs `a0a9c83e`) + `docs/entire-tracing-checkpoints.md` rides-dirty (convention — do not clean).
- **Known-open (not broken):**
  - Fit-window systematic (±17 kHz) untreated and dominant; both half-band widths inflate at narrow windows too.
  - E4 two-screen numbers doubly conditional: placeholder z = 1.0000 AND the E3 interpretation question.
  - NOTHING citable yet; Faber2026 `pipeline/` pin still `bffd875` (intentional).
- **Separate-active lanes (preserved, untouched):** FLITS worktree `flits-acf-lag-selector` (`feat/acf-lag-selector` @ `6d833410`); unregistered dirs `~/Developer/scratch/worktrees/flits-{gate,iso}-preserve/`; canonical clone's branch checkout.

## Learnings

- **The gen-1 E3 "pass" was manufactured by the defect**: the un-de-chirped burst smeared ~8 ms across the window, and the band-dependent smear produced a fake chromatic ratio. Any internal-consistency check run on a product with a known defect is void, even when it "passes".
- **Ratio-based checks cancel the fit-window systematic to first order** — the half-band ratio moved only 0.83→1.09 across windows while absolute widths swung 30→54 kHz. Use ratios for hypothesis tests where possible.
- **#121 closed the m dilution issue in-pipeline**: m_acf (0.304) now equals the hand-derived ACF zero-lag m_burst (0.303) — the old E4 off-subtraction machinery is only needed for cross-checks.
- Path gotchas for rerun scripts: `foreground` imports need `WT/galaxies` on `sys.path`; `build_scintillation_source_block("freya")` on merged main returns no distance key — supply d_L manually (placeholder 6791.3 Mpc).
- `git cherry origin/main <branch>` returning empty is the clean proof for deleting a directly-pushed branch (`branch -d` fails against a stale local main).

## Action Items & Next Steps

1. [ ] **Instrumental-origin experiment (NEW, elevated by the reversal):** test the achromatic hypothesis directly — e.g. ACF of off-pulse spectra / a noise-window "measurement" (does ~35 kHz structure appear without the burst?), lag-domain masking at coarse-block harmonics, and/or the same measurement on a DSA-side product where the CHIME upchannelization chain is absent. `ai-research-workflows:running-experiments`.
2. [ ] **Fit-window systematic** (carried): ripple-period-aware fitting or window marginalization — options recorded in the experiment doc. Interacts with item 1 (if the scale is instrumental, the "systematic" is part of the artifact).
3. [ ] **Other 4 targets** (casey, isha, mahi, phineas): regenerate `--no-time-shift` + aligned builder (recipe in prior handoff §Reproducibility). **Add: run E3 split-band on each** — the same achromatic ~35 kHz scale appearing in independent bursts would clinch the instrumental interpretation; ν^4.4-consistent ratios would rescue the scintillation reading.
4. [ ] Real freya redshift (z = 1.0000 placeholder) before quoting any coherence/quenching number.
5. [ ] Faber2026 pin bump only when the manuscript cites scintillation numbers — and only after items 1–2 settle what those numbers mean.

**Recommended Next Skill:** `ai-research-workflows:running-experiments` for item 1 (it has crisp falsifiable predictions); `ai-research-workflows:researching` first if prior art on CHIME upchannelization spectral-leakage scales is wanted.

## Other Notes

- Pushes to Faber2026 main are outward-facing (Overleaf pulls via manual GitHub Sync); oneway-guard sticky window was open this session — may have expired for the next.
- Two pushes this session: FLITS main `2931e1bf` → `a0a9c83e`; Faber2026 main `5b0b125` → `fbc9855`.
- A parallel Codex session historically works these repos — re-check `git status`/PR state immediately before any FLITS push/merge.
- ICM memory store failed this session (readonly database) — durable record is in the repo docs; worth a look if ICM persistence matters.

---

**Handoff created by AI Assistant on 2026-07-05**
