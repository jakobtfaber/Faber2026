# Handoff: V6 Phase 6 complete & validated — follow-up commit/pin/surface authorized

---
**Date:** 2026-07-07 10:11 -0700
**Author:** AI Assistant (Claude, Faber2026 session)
**Status:** Handoff
**Branch:** main (Faber2026); FLITS work on worktree branch `agent/v6-dm-provenance-toa`
**Commit:** Faber2026 `04232b7`; FLITS worktree cut from pin `2d62ac8`
---

## Task(s)

Phase 6 (V6 association + DM_obs re-validation) of
`plan-trust-reset-revalidation.md` — implemented and validated this session.
Owner follow-up authorized the remaining local git plumbing and manuscript
surface restoration.

| Task | Status | Notes |
|------|--------|-------|
| P6.1 anchor inventory | ✅ Complete | DSA DM = catalog (0.1 placeholder err); CHIME = arrival-time regression 8/12 constrained. |
| P6.2 DM provenance table + figure + test | ✅ Complete | `dm_provenance.csv` (12 rows, no UNDOCUMENTED), `dm_agreement.png`, `test_dm_provenance.py` green. |
| P6.3 baseline oracles + re-derivation | ✅ Complete | 20 oracles green; report reproduces to machine precision. |
| Finding-#2 fix (stale "SUSPENDED" banner) | ✅ Complete | `association.py` banner rewritten; report regenerated; oracles green. |
| Validation | ✅ PASS (automated) | Full FLITS suite 129 passed / 2 skipped; `make` exit 0. |
| Dispersion-reference decision | ✅ Decided | Owner: keep **shared DSA DM**; joint (DM,dt) fit deferred. |
| **Commit FLITS branch (w/ gitignore fix)** | ✅ Done | `dm_provenance.csv`/`.png` force-added in FLITS commit `9175b92`. |
| Merge FLITS upstream → bump Faber2026 pin | ⏳ Local pin only | Faber2026 gitlink bumped locally to `9175b92`; upstream FLITS push/merge remains external. |
| Restore withheld TOA-residual/P_cc columns | ✅ Done | `sample_table.tex` restores residual / P_cc / verdict under shared-DM. |

**Current Workflow Phase:** local commit/pin/surface follow-up; upstream push/merge still pending.

## Workflow Artifacts

- [plan-trust-reset-revalidation.md](plan-trust-reset-revalidation.md) — Phase 6 (P6.1–P6.3) spec.
- [v6-association-dm-report-2026-07-07.md](v6-association-dm-report-2026-07-07.md) — **the V6 deliverable** (provenance table, agreement figure, re-derived association table, findings, dispersion-reference decision).
- [validation-trust-reset-revalidation-phase6.md](validation-trust-reset-revalidation-phase6.md) — validation report (PASS, fresh evidence).
- [dm-provenance-audit-2026-07-07.md](dm-provenance-audit-2026-07-07.md) — sibling DM audit (codex).
- [handoff-2026-07-07-09-25-toa-recalc-from-metadata.md](handoff-2026-07-07-09-25-toa-recalc-from-metadata.md) — the prior handoff that scoped this work.

## Critical References (read first)

- `docs/rse/specs/v6-association-dm-report-2026-07-07.md` — everything V6, incl.
  the dispersion-reference decision (§4) and the named findings.
- `~/Developer/scratch/worktrees/flits-v6-phase6/` — the **isolated FLITS worktree**
  where all pipeline changes live (branch `agent/v6-dm-provenance-toa`, from pin
  `2d62ac8`). Not the pinned submodule checkout.
- `docs/rse/specs/validation-trust-reset-revalidation-phase6.md` — the PASS
  evidence and the Critical/Important/Nice-to-have recommendation split.

## Recent Changes

**FLITS worktree** `~/Developer/scratch/worktrees/flits-v6-phase6` (branch `agent/v6-dm-provenance-toa`, committed as `9175b92`):
- `scripts/build_dm_provenance.py` (new) — joins `chime_side_inputs.json` × `bursts.yaml` → `crossmatching/dm_provenance.csv`.
- `scripts/plot_dm_agreement.py` (new) — → `crossmatching/dm_agreement.png`.
- `tests/test_dm_provenance.py` (new) — plan-spec test, green.
- `crossmatching/association.py:223` — banner rewritten (finding #2).
- `crossmatching/association_report.json` — regenerated (banner + this-machine `separation_deg`).
- `crossmatching/dm_provenance.csv`, `crossmatching/dm_agreement.png` — **gitignored** (`*.csv`/`*.png`).

**Faber2026** `main` (local V6 follow-up commit pending at handoff-update time):
- `docs/rse/specs/v6-association-dm-report-2026-07-07.md` (new)
- `docs/rse/specs/validation-trust-reset-revalidation-phase6.md` (new)
- `docs/rse/specs/v6-dm-agreement.png` (new, trackable)
- `sample_table.tex`, `scripts/make_sample_table.py`, `sections/toa.tex`, and
  `CONTEXT.md` restore the V6 association diagnostics under shared DSA DM.
- `pipeline` gitlink is bumped locally to FLITS `9175b92`.
- `docs/rse/journal.jsonl` (appended)

## Reproducibility & Data State

- **Environment:** conda env `flits` (Python 3.12); run pipeline code from inside
  the worktree so cwd shadows the editable-installed canonical clone (verified:
  `flits.__file__` resolves into the worktree).
- **Pin:** worktree cut from FLITS `2d62ac8` (the Faber2026 `pipeline/` pin).
- **Regenerate everything:** from the worktree —
  `conda run -n flits python scripts/build_dm_provenance.py` →
  `… scripts/plot_dm_agreement.py` →
  `… python crossmatching/association.py` (regenerates the report).
- **Seeds:** none — DM/ToA/geometric math is deterministic.
- **Off-repo:** CHIME extraction artifacts (`chime_dm_final.json`, grid NPZ) live
  on h17 `/data/…`, unpinned — CHIME provenance incomplete until checksummed.

## Verification State / Known-Broken

- **Green (fresh this session):** `test_dm_provenance.py`; the three P6.3 oracles
  (20); the full FLITS `tests/` suite (**129 passed, 2 skipped** data-gated);
  Faber2026 `make` exit 0; re-derivation parity exact this-machine.
- **Uncommitted:** everything above (FLITS worktree + Faber2026 docs). Nothing
  pushed. No pin bump.
- **Gitignore gap resolved locally:** `crossmatching/dm_provenance.csv` (`*.csv`)
  and `dm_agreement.png` (`*.png`) were force-added in FLITS commit `9175b92`.
- **Separate lanes (do not touch):** the pinned `pipeline/` submodule checkout
  has an active dm_power dirty lane (`dispersion/dm_power_analysis.py`,
  `flits/batch/codetection_plots.py`, `tests/test_dm_power.py`) and a
  `provenance/data-manifest` worktree — both other tasks'. My work is in a
  *separate* worktree and never touched these.
- **Surfaced:** TOA residuals / P_cc / association verdicts are restored in the
  manuscript under the shared-DM convention.

## Learnings

- **σ convention is the crux of P6.2.** `association.py::dm_agreement` floors σ at
  `max(quadrature, 1.0 pc cm⁻³)` precisely so a sub-pc offset doesn't read as
  many-σ (docstring cites casey ±0.0009). The provenance CSV must use the *same*
  floor or it contradicts the report (raw stat σ would show zach at −8.3σ vs the
  report's 0.844). Aligned — CSV `delta_dm_sigma` == report `n_sigma`.
- **The Wave-3 "defect" is a convention, not a bug.** Both telescopes' 400 MHz
  ToAs are referenced at the DSA DM (fixture `dm` == `dm_dsa`; CHIME method =
  "coherent_dedisp at DSA DM"). The handoff's "correction #1" (per-telescope DM)
  would *introduce* a ~12 ms spurious offset (= the DM disagreement), not remove
  one. Owner chose to keep the shared reference — the right call given the DSA err
  is a placeholder.
- **Joint (DM, dt) fit is rank-degenerate with one TOA/telescope** (Codex,
  `logs/codex-jointdm.json`): `delay = K_DM·DM·Δ(ν⁻²) + dt`; separable only with
  multiple sub-band TOAs. ~1 ms clock unknown ≈ 0.04 pc cm⁻³. Building blocks
  exist (`analysis/scattering-refit-2026-06/fullband_aligned.py`,
  `scattering/scat_analysis/burstfit_joint.py`, `dispersion/chime_dm.py`) but no
  joint fitter; `JOINT_FIT_STATE.md:21-29` deliberately leaves t0 free. Future-paper work.
- **CHIME reads systematically ~0.36 pc cm⁻³ below DSA** across the 8 constrained
  bursts — coherent, sub-floor; possibly worth a manuscript sentence.

## Action Items & Next Steps

1. [x] **Fix the gitignore gap, then commit the FLITS branch.** Done in `9175b92`.
2. [ ] Push/merge `agent/v6-dm-provenance-toa` upstream via FLITS PR review.
3. [x] Restore the TOA-residual / P_cc / association-verdict columns to the
   manuscript under the shared-DSA-DM convention.
4. [ ] Spot-check `dm_provenance.csv` CHIME values against h17 (or via the
   h17-ssh-troubleshooter lane); pin/checksum the off-repo extraction artifacts.
5. [ ] (Nice-to-have) Round `separation_deg` on write in
   `build_association_report` to kill cross-machine ULP churn.
6. [ ] (Future paper) Joint (DM, dt) cross-telescope fitter — see report §4.

**Recommended Next Skill:** none automated — the remaining work is upstream
FLITS push/merge and any broader owner-directed publication plumbing.

## Other Notes

- **Outward-facing boundary:** committing/pushing the FLITS branch and pushing
  Faber2026 `main` (Overleaf pulls it) are one-way doors — left to the owner.
- Do not bump the `pipeline/` pin casually; only after the FLITS work merges upstream.
- Journal (`docs/rse/journal.jsonl`) carries both the implement and validate entries.

---

**Handoff created by AI Assistant on 2026-07-07**
