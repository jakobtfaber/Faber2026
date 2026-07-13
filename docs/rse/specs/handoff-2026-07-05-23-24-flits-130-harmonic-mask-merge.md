# Handoff: FLITS #130 merged — CHIME harmonic-comb mask enabled + config-path wiring; pin bumped; ICM write path repaired

---
**Date:** 2026-07-05 23:24
**Author:** AI Assistant
**Status:** Handoff
**Branch:** main
**Commit:** 61b8710 (my pin-bump commit is 28b3a44, superseded same evening by the parallel lane's 61b8710 — see Other Notes)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Merge dsa110-FLITS PR #130 (harmonic mask + `plot_subband_gamma_summary`) | ✅ Complete | Merge commit `b4be9085`, 2026-07-06T06:00Z; remote branch deleted |
| Enable mask in the four CHIME configs | ✅ Complete | casey_chime, casey_chime_hi, freya_chime, freya_chime_hi — `analysis.fitting.harmonic_mask {enable: true, spacing_mhz: 0.390625, halfwidth_mhz: 0.05}` |
| Wire yaml mask block through the config-driven CLI path | ✅ Complete | Gap found mid-task: only `_fit_acf_models` read the block; `freya_scintillation` CLI ignored it. Wired in FLITS commit `634920b` |
| A/B validation through the config path | ✅ Complete | freya_chime_hi, mask as the only toggle: off 35.19±4.42 kHz (exact canonical pass-5), on 42.21±2.76 kHz (exact arm-B1 oracle) |
| Grit lane cleanup (agent/claude-faber2026) | ✅ Complete | Worktree removed, branch deleted after ancestor-of-main proof, zero locks |
| Faber2026 `pipeline/` pin bump + build | ✅ Complete | 13e1d00a → b4be9085 (`28b3a44`); clean rebuild exit 0, no undefined refs. Parallel lane then advanced pin to 028fa7c (`61b8710`, FLITS #131) — b4be9085 is its ancestor |
| ICM memory-store failure: permanent fix + live test | ✅ Complete | See Learnings. Store/recall round-trip PASS against fresh `mskill mcp icm` spawn |

**Current Workflow Phase:** Validate (implementation and merge done; canonical-number adoption is the open question)

## Workflow Artifacts

**Experiment Reports:**
- [experiment-freya-chime-instrumental-origin.md](experiment-freya-chime-instrumental-origin.md) — arms A–I incl. B1 masking oracle (35.19 → 42.21 kHz @ ±0.05 MHz) that this session's config enablement operationalizes
- [experiment-freya-chime-dnu-science-readiness.md](experiment-freya-chime-dnu-science-readiness.md) — the retraction context: freya CHIME 35 kHz is instrumental, not scintillation

**Previous Handoffs (same lane):**
- [handoff-2026-07-05-14-34-freya-chime-e3-reversal.md](handoff-2026-07-05-14-34-freya-chime-e3-reversal.md) — E3 ν^4.4 reversal closeout that preceded this work

## Critical References

- `pipeline/scintillation/configs/bursts/freya_chime_hi.yaml` — the pattern config: `harmonic_mask` block under `analysis.fitting`, with provenance comment (PR #130, arm B1)
- `pipeline/scintillation/scint_analysis/freya_scintillation.py` — config wiring: `run_config_path` reads the block, threads `harmonic_mask_spacing_mhz`/`halfwidth_mhz` through `run_notebook_style_analysis` and `_scan_fit_windows` into `measure_scintillation_bandwidth`
- `pipeline/scintillation/scint_analysis/analysis.py` — `harmonic_lag_mask()` + the `_fit_acf_models` consumption of the same yaml block (notebook/pipeline path)

## Recent Changes

All in dsa110-FLITS (merged via #130, now inside the pinned submodule):

- `scintillation/scint_analysis/analysis.py` — `harmonic_lag_mask(lags, spacing_mhz, halfwidth_mhz)` before `_fit_acf_models`; mask applied inside `_fit_acf_models` when `analysis.fitting.harmonic_mask.enable`
- `scintillation/scint_analysis/freya_scintillation.py` — kwargs threaded through `_scan_fit_windows`, `run_notebook_style_analysis`, and `run_config_path` (commit `634920b`)
- `scintillation/scint_analysis/plotting.py` — `plot_subband_gamma_summary()` (reconstruction of the lost notebook figure design)
- `scintillation/configs/bursts/{casey_chime,casey_chime_hi,freya_chime,freya_chime_hi}.yaml` — mask enabled
- Faber2026: `pipeline` pin `13e1d00a → b4be9085` (`28b3a44`), then `→ 028fa7c` by parallel lane (`61b8710`)

## Reproducibility & Data State

- **Environment:** conda `flits` (editable-installs the canonical clone at `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS/` — run from inside `pipeline/` to get pinned code)
- **Data:** `~/Data/Faber2026/dsa110/scintillation-data/freya_chime_hi.npz` (configs reference `${FLITS_ROOT}/scintillation/data/`, satisfied by symlink)
- **A/B outputs:** scratchpad `hm_config_run/` (masked) and `hm_config_run_off2/` (control) — session-temporary; the numbers are recorded here and in FLITS commit `634920b` message
- **Repro command:** from a FLITS checkout root: `cd scintillation && FLITS_ROOT=<checkout> conda run -n flits python -m scint_analysis.freya_scintillation configs/bursts/freya_chime_hi.yaml --out <dir> --no-figures` (module must be imported as `scint_analysis.*`, not `scintillation.scint_analysis.*` — numba disk cache is keyed to the former)

## Verification State / Known-Broken

- **Tests:** PR #130 CI green (Python 3.12, review, Socket ×2) on final commit `634920b`. A/B oracle pass. Faber2026 `make` clean rebuild exit 0, zero undefined references, 6 overfull boxes pre-existing.
- **Uncommitted / unpushed:** none in Faber2026 (main == origin/main at `61b8710`). Canonical FLITS clone is checked out on the (now-merged) `chore/deferred-followups-2026-07` branch with dirty `docs/entire-tracing-checkpoints.md` — that is the parallel lane's file; left untouched.
- **Unverified:** casey_chime/casey_chime_hi and freya_chime (lo-band) masked numbers have **not** been rerun — only freya_chime_hi was A/B'd. Enabling the mask changes their fitted Δν the next time anything reruns those configs.
- **Session-local:** this Claude session's `icm` MCP connection is down (stale server killed; needs `/mcp` reconnect). New sessions unaffected.

## Learnings

- **The yaml `harmonic_mask` block originally reached only one of two fit paths.** `_fit_acf_models` (notebook/pipeline) read it; the `freya_scintillation` config-driven CLI silently ignored it. Enabling a config flag is not done until every consumer path is traced — the A/B control (35.19 exact) was the proof the wiring, not something else, moved the number.
- **A/B controls must toggle exactly one key.** First control attempt used `sed 's/enable: true/enable: false/'` which also flipped `grid_regularization` and `bandpass_normalization`, giving a wrong baseline (36.79 kHz). Targeted flip restored the exact canonical 35.19.
- **Numba disk cache pins the import name.** Running `python -m scintillation.scint_analysis.freya_scintillation` from repo root crashes (`ModuleNotFoundError: scint_analysis`) because cached overloads were compiled under `scint_analysis.*`. Run from inside `scintillation/`.
- **Telescope-config resolution is relative to the burst-config path** — control configs must live in `configs/bursts/`, not a scratch dir.
- **ICM readonly failure root cause:** not the DB (perms fine) — the *session-lifetime MCP server process* predated the 2026-07-05 registry fix (`meta/mcps.json` → `icm-0.10.57-consolidate-gate`, `--read-only` dropped). Long-lived MCP servers don't pick up registry changes; after a registry edit, running sessions must reconnect. Fixed by killing the stale `ro-fix --read-only` process (PID 66137); live MCP handshake against a fresh `mskill mcp icm` spawn passed store+recall. Zero read-only ICM servers remain.
- **`gh pr merge --delete-branch` + grit:** when `grit done` refuses (dirty shared tree from another lane), pushing the agent branch as a PR branch works; post-merge cleanup needs `git merge-base --is-ancestor <branch> main` as the deletion proof because `git branch -d` checks against HEAD's branch, not main.

## Action Items & Next Steps

1. [ ] **Decide canonical adoption of masked CHIME numbers.** freya CHIME hi masked fit is 42.21±2.76 kHz (vs 35.19±4.42 unmasked). The scale is retracted as instrumental either way, so this is documentation — but the experiment doc's comparison matrix and any tex touching CHIME Δν should state which number is quoted and why. Update `docs/rse/specs/experiment-freya-chime-instrumental-origin.md` (arm B1 section) to note the mask is now config-default in the pinned pipeline.
2. [ ] **Rerun casey_chime / casey_chime_hi / freya_chime with the mask on** (now default in their configs) and record deltas before any manuscript number relies on them.
3. [ ] Optionally regenerate the DSA γ(ν) summary figure via `plot_subband_gamma_summary` from the pinned pipeline for `figures/` (currently only in the experiment archive, not a manuscript export).

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` (item 2 is a validation sweep of the enabled-by-default mask across the remaining CHIME configs)

## Other Notes

- **Parallel-lane pin advance:** minutes after `28b3a44` (pin → b4be9085), the other active lane merged FLITS PR #131 (`chore/deferred-followups-2026-07`) and bumped the pin to `028fa7c` (`61b8710`). `b4be9085` is an ancestor of `028fa7c`, so this session's work is fully contained in the current pin — no conflict, nothing to reconcile.
- Verify-gate records exist for: the freya_scintillation wiring (oracle), the four configs (oracle), the pin bump (test), and the ICM MCP fix (reproduce).
- ICM memory `context-Faber2026` entry `ok:01KWV0JV1YMMHRNRPRK34AN3Q9` stores this session's PR #130 summary.

---

**Handoff created by AI Assistant on 2026-07-05**
