# Handoff: Harmonic-mask default-on sweep validated across remaining CHIME configs — deltas recorded, no conclusion changes

---
**Date:** 2026-07-06 00:34
**Author:** AI Assistant
**Status:** Handoff
**Branch:** main
**Commit:** d50a3e3 (my validation commit is d3f27d3; d50a3e3 is the parallel lane's pin bump on top — see Other Notes)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Masked A/B rerun of casey_chime, casey_chime_hi, freya_chime (handoff item 2 from `handoff-2026-07-05-23-24`) | ✅ Complete | 6 runs at pin `028fa7c`, all exit 0, `success=true`; single-key `enable: false` controls, diff-verified one-line deltas |
| freya_chime_hi regression at new pin | ✅ Complete | 42.21 ± 2.76 kHz — exact match to the recorded arm-B1/config-A/B oracle |
| Validation report | ✅ Complete | `validation-harmonic-mask-chime-sweep.md`, committed `d3f27d3`, on `origin/main` |
| Experiment-doc B1 status note (mask now config-default) | ✅ Complete | Factual sub-part of handoff item 1; the adoption *decision* itself remains open |
| Verify-gate | ✅ Complete | cross-check (13/13 numbers + 3/3 deltas vs preserved JSONs) + oracle (fresh 42.21 reproduction) recorded |
| Canonical adoption decision (item 1) | 📋 Planned | Owner decision — which CHIME Δν (masked vs unmasked) docs/tex quote |
| γ(ν) summary figure export (item 3) | 📋 Planned | `plot_subband_gamma_summary` → `figures/`; untouched |

**Current Workflow Phase:** Validate (complete for item 2; remaining items are a decision and an optional export)

## Workflow Artifacts

**Validation Reports:**
- [validation-harmonic-mask-chime-sweep.md](validation-harmonic-mask-chime-sweep.md) — the full A/B table, verification detail, caveats, recommendations

**Experiment Reports:**
- [experiment-freya-chime-instrumental-origin.md](experiment-freya-chime-instrumental-origin.md) — arm-B1 section now carries the config-default status note (this session)

**Previous Handoffs (same lane):**
- [handoff-2026-07-05-23-24-flits-130-harmonic-mask-merge.md](handoff-2026-07-05-23-24-flits-130-harmonic-mask-merge.md) — the specification this session executed (its item 2)

## Critical References

- `docs/rse/specs/validation-harmonic-mask-chime-sweep.md` — all numbers, repro commands, and caveats; read this first
- `docs/rse/specs/handoff-2026-07-05-23-24-flits-130-harmonic-mask-merge.md` — remaining open items 1 and 3 defined there
- `~/Data/Faber2026/dsa110/scintillation-data/exp-hm-config-sweep-2026-07-05/` — preserved result JSONs for all 7 runs (the verify-gate cross-check source)

## Recent Changes

- `docs/rse/specs/validation-harmonic-mask-chime-sweep.md` — new (commit `d3f27d3`)
- `docs/rse/specs/experiment-freya-chime-instrumental-origin.md:147-156` — B1 status-update bullet: mask config-default since FLITS #130, oracle reproduced at pin `028fa7c` (same commit)
- No code changes anywhere; `pipeline/` submodule untouched by this session (pin advanced `028fa7c → 25b8cc6` by the parallel lane, FLITS #132 = ADR-0007 docs, no fit-code impact)

## Reproducibility & Data State

- **Environment:** conda `flits`; run from inside `pipeline/scintillation` so cwd shadows the canonical-clone editable install (verified via `scint_analysis.__file__`)
- **Command:** `cd pipeline/scintillation && FLITS_ROOT=<Faber2026>/pipeline conda run -n flits python -m scint_analysis.freya_scintillation configs/bursts/<cfg>.yaml --out <dir> --no-figures`
- **Data:** `~/Data/Faber2026/dsa110/scintillation-data/{casey_chime,casey_chime_hi,freya_chime,freya_chime_hi}.npz` via the gitignored symlink `pipeline/scintillation/data` (created this session, persists)
- **Results:** off → on (kHz): casey_chime 28.05±32.47 → 23.32±36.54 (−4.73); casey_chime_hi 60.07±38.94 → 64.81±38.50 (+4.74); freya_chime 54.13±10.32 → 59.07±8.29 (+4.95). All deltas ≲0.5σ of fit errors.
- **Preserved outputs:** result JSONs at `exp-hm-config-sweep-2026-07-05/` (above); control configs (`*_hmoff.yaml`) were temporary and deleted; run logs were session-scratchpad only (gone after session cleanup — numbers live in the JSONs and report)
- **In-flight jobs:** none

## Verification State / Known-Broken

- **Tests:** no code changed, none run. All 7 pipeline runs exit 0. Verify-gate records: cross-check `e5eb4fafeaf8` (report numbers vs JSONs, 16/16 OK), oracle `f10f9ef5d108` (B1 note vs fresh reproduction).
- **Uncommitted / unpushed:** none — main == origin/main at `d50a3e3`.
- **Unverified / caveats (recorded in the report):** casey npz pair still carries the h17 de-dispersion defect (regeneration never requested — both casey fits are non-detections regardless: errors exceed values, casey_chime_hi fitted m negative); freya CHIME tens-of-kHz scale remains retracted as instrumental. None of the sweep numbers is manuscript-citable; they are config-default tracking numbers.

## Learnings

- **The mask engages silently.** No log line exists in `analysis.py`/`freya_scintillation.py` when the harmonic mask applies; engagement had to be proven via A/B deltas + the exact oracle reproduction. Report recommends a one-line INFO log (nice-to-have).
- **A live parallel lane can switch HEAD under you between `git status` and `git commit`.** My commit targeted main but landed on `build/pin-bump-25b8cc6` because the pin-bump lane checked that branch out in the same checkout 16 s earlier. Reflog forensics (`git reflog --date=iso`) decoded it; the lane ff-merged to main and pushed, absorbing my commit cleanly — no action needed, but check `git log -1` output's branch name immediately after committing in this repo.
- **`/scintillation/data` is gitignored in FLITS** — the data symlink can be created inside the pinned submodule without dirtying it (matches the canonical-clone convention).
- **These three configs have no `fit_lag_scan_mhz`** — their numbers are single-window; only freya_chime_hi carries the scan. If a future comparison needs the fit-window systematic, add the scan key first.
- Whole 6-run sweep is cheap: ~3.5 min wall for all three config pairs run as 3 concurrent pairs.

## Action Items & Next Steps

1. [ ] **Owner decision (item 1, unchanged):** which CHIME Δν number (masked vs unmasked) the experiment doc's comparison matrix and any tex quote, and why. The mask-is-default fact is now documented; only the quoting policy is open. Both freya_chime_hi numbers (35.19 unmasked / 42.21 masked) are in the validation report.
2. [ ] **Optional (item 3, unchanged):** regenerate the DSA γ(ν) summary figure via `plot_subband_gamma_summary` from the pinned pipeline into `figures/` as a manuscript export.
3. [ ] **Before any casey CHIME number is used anywhere:** regenerate the casey npz pair from a de-dispersion-fixed h17 product (defect lane; regeneration not yet requested — same for isha/mahi/phineas).

**Recommended Next Skill:** none required for the open items — 1 is a human decision, 2–3 are small self-contained tasks. If item 3 is picked up, `ai-research-workflows:implementing-plans` is overkill; just do it and review the figure.

## Other Notes

- **Parallel-lane interleave (again, benign):** the pin-bump lane created `build/pin-bump-25b8cc6` at 23:36:00, my commit `d3f27d3` landed on it at 23:36:16, their pin bump `d50a3e3` at 23:36:21, ff-merge to main at 23:36:32, then pushed. `lane-liveness` said live throughout; their local branch left untouched. Same pattern as the previous evening's `028fa7c` advance.
- ICM memory `context-Faber2026` entry `ok:01KWV2C0ZF495A66633SGX7MBC` stores this session's sweep summary.

---

**Handoff created by AI Assistant on 2026-07-06**
