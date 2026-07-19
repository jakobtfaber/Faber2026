# Handoff: Scint input remediation — casey DM/RFI calibration mid-flight; owner needs a figure-capable session

---
**Date:** 2026-07-19 14:56
**Author:** AI Assistant (Cowork session, with owner in the loop)
**Status:** Handoff
**Branch:** `ms/handoff-sync-20260718` (primary checkout; note a concurrent lane added `3ef33c80` "charter two-screen forward model — owner Option A" on this branch)
**Commit:** `3ef33c80`

---

## Why this handoff exists

The owner is reviewing dedispersion/RFI quality of the CHIME upchannelized
scintillation inputs **figure-by-figure** and the current session's inline
figure display was too confusing to continue. The next session MUST be able
to show the owner figures directly (open PNGs/HTML at full size, render new
DM strips on request). Everything is on local disk; nothing needs h17.

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Owner data review of all 36 input dynamic spectra | ✅ Complete | Verdict: RFI unexcised (CHIME upchan nearly all; DSA central channel in isha/phineas/zach); over-dedispersion in ≥9 upchan products; upchan-vs-full-res DM inconsistency. Recorded in `owner-data-review-findings-2026-07-18.md` |
| Remediation attempt 1 (peer agent) | ✅ Complete — **REJECTED by owner** | Aligned to catalog DM + weak 5σ masks. Owner: "RFI still there; DMs still wrong." Products in `~/Data/Faber2026/dsa110/upchan_codetections_remediated_20260718/` (do not reuse; provenance scaffolding OK) |
| Remediation attempt 2 (12-burst redo) | 📋 Aborted | Owner narrowed to **casey only** to calibrate the method first |
| casey DM calibration | 🔄 **In progress — the live task** | Sign bug found+fixed; corrected strip rendered; owner has NOT yet picked casey's DM (candidates 491.148 / 491.178 vs chime_dm 491.208) |
| Aggressive RFI pass (casey) | 📋 Planned | After DM pick; owner chose aggressive hand-rolled masking (NOT the pipeline masker, NOT the weak 5σ variant) |
| Scale to remaining 11 bursts | 📋 Planned | Only after owner blesses the casey recipe |

**Current Workflow Phase:** Experiment (interactive calibration with owner) → then Implement

## Critical References (read these first)

1. `docs/rse/specs/owner-data-review-findings-2026-07-18.md` — the defect adjudication, per-burst ΔDM table, remediation charter. Everything flows from this.
2. **The four casey figures** (open them for the owner immediately on request):
   - DURABLE copies: docs/rse/decks/casey-dm-calibration-2026-07-19/ — `casey_dm_strip_CORRECTED.png` (the current decision figure), `casey_dm_strip_annotated.png` + `casey_dm_strip.png` + `casey_compare.png` (SIGN-BUGGED labels — superseded, keep only to explain history)
   - Durable copies of galleries: `docs/rse/decks/waterfall-review-2026-07-18/index.html` (36 input panels), `docs/rse/decks/acf-review-2026-07-18/index.html` (both-band ACFs), `docs/rse/decks/remediation-preview-2026-07-18/index.html` (attempt-1 before/after, rejected)
3. `~/Data/Faber2026/results-library/dispersion/dm-joint-phase-v2/diagnostics/summary.csv` — the measured DM catalog (per-burst chime_dm/dsa_dm/joint_dm + σ + quality). Owner decision: **chime_dm was the chosen authority, but see Learnings — it over-dedisperses scattered bursts; structure-optimal DMs (below chime_dm) are where this is heading.**

## The state of the casey calibration (resume exactly here)

- Raw upchan product: `~/Data/Faber2026/dsa110/upchan_codetections/casey_chime_upchan.npy` (12336×1748, freq axis file alongside, ASCENDING 400.59→799.02 MHz), built at DM 491.207 (= builder TARGETS; ≈ chime_dm 491.2078 — casey is a DM no-op between build and catalog).
- **Corrected shift transform** (THE key formula, sign verified by single-channel test):
  `binshift(f) = −K_DM·(dm_new − dm_build)·(1/f² − 1/400²)/DT`, K_DM = 1/2.41e-4, DT = 2.56e-6·2·U (casey U=16 → 81.92 µs); apply with fractional-bin `np.interp`, NaN edge fill. Positive ΔDM must move HIGH frequencies LATER (verified: +1 pc/cm³ moves a 780-MHz pulse 1000→1233 bins).
- Corrected-sign DM strip (`casey_dm_strip_CORRECTED.png`, cols at −0.30/−0.15/−0.06/−0.03/0/+0.06/+0.15 around chime_dm): lower DM leans right-down (under-dedispersed), higher leans left-down (over). At chime_dm casey still bends slightly LEFT = slightly over-dedispersed, matching the owner's eye. Straightest columns: **491.148 (−0.06) and 491.178 (−0.03)**.
- **OPEN QUESTION TO THE OWNER (first thing next session):** pick casey's DM from the corrected strip — 491.148, 491.178, or request a finer strip between them. Then codify the metric that reproduces the pick (structure/onset alignment, NOT peak S/N — see Learnings) and roll to the other 11 with a per-burst strip for owner spot-check.

## Verification State / Known-Broken

- **Sign bug (FIXED, but history poisoned):** this session's earlier casey diagnostics (`casey_dm_strip.png`, `casey_dm_strip_annotated.png`, `casey_compare.png`) have MIRRORED DM labels (transform lacked the leading minus). The "structure-opt 491.2378" claim from the first scan is actually 491.1778. Only `casey_dm_strip_CORRECTED.png` is truthful. The owner caught this ("left is a lower DM but clearly more dedispersed — should be the other way around").
- **Attempt-1 products are rejected** but still on disk (`upchan_codetections_remediated_20260718/`); its `verification.md`/`prov/*.json` diagnostic scans used the CORRECT sign (its formula had the minus) — its "structure optima at/below catalog" finding is trustworthy and matches the owner's eye (casey δ*≈−0.025).
- **Peak-S/N is a broken DM metric on scattered bursts** — biases high (scattering tail piles onto peak). Do not reuse.
- **Uncommitted:** `docs/rse/decks/remediation-preview-2026-07-18/` (untracked), journal dirty, `.DS_Store` noise. Nothing science-critical uncommitted beyond the decks.
- **PR #140 (pin bump + scint figures): DO-NOT-MERGE** stands (input defects). PR #142 (handoff-sync docs) state unknown at write time — check `gh pr view 142`.

## Learnings (hard-won this session — do not rediscover)

1. **Fit DMs (chime_dm, dm_phase candidate) are scattering-biased HIGH.** The fitter over-dedisperses to verticalize the scattered tail. Structure-alignment optima sit BELOW the catalog by a per-burst amount; the owner's nine "clearly over-dedispersed" bursts are the scattered ones. For ACF-window purposes the structure-aligned DM is the relevant one; the catalog DM remains the *measurement* for the DM tables (do NOT rewrite the manuscript DM catalog from this lane).
2. **Sign convention trap:** the 400-MHz-anchored correction needs the leading minus (formula above). Verify with the single-channel test before ANY batch application. The dm_phase JSON convention: `dmphase_raw_trial_dm` is NEGATED into `physical_residual_dm` — signs in stored products are inconsistent across generations; always re-derive.
3. **casey upchan freq axis is ASCENDING; CHIME full-res (1024×32000) channel order was ASSUMED descending in the 36-panel gallery — unverified.** Verify per-product from the freq files before rendering; a flipped axis flips the apparent lean.
4. **RFI masking:** owner wants aggressive hand-rolled (spectral kurtosis + MAD z + time-domain spikiness + iterate), visual bar = no visible streaks in the AFTER panel; the renderer must view its own output. The 5σ off-burst-only mask (attempt 1, 3–6% flagged) is insufficient. DSA band-center DC block (chs 3072–3079) live in isha/phineas/zach.
5. **Upchan channel counts vary per burst** (casey 12336, chromatica 49088) — per-burst U sizing; DT differs per burst (DT = 2.56e-6·2·U; U in builder TARGETS dict in `~/Data/Faber2026/dsa110/upchan_codetections/build_npz_aligned_generic_20260706.py`).
6. Sandbox constraints (if next session is Cowork): 45 s bash timeout, background jobs die at call end, `pip --break-system-packages`, scipy/numpy/matplotlib now installed.

## Reproducibility & Data State

- **Data (all local, read-only originals):** raw upchan + freq + builder script in `~/Data/Faber2026/dsa110/upchan_codetections/`; full-res + DSA in `~/Data/Faber2026/dsa110/DSA_bursts/`; DM catalog in `results-library/dispersion/dm-joint-phase-v2/`.
- **Outputs so far:** rejected attempt-1 set in `~/Data/Faber2026/dsa110/upchan_codetections_remediated_20260718/` (md5-chained provenance inside); v2 dir created but empty except `casey_dm_scan.json` (SIGN-BUGGED scan — discard); casey scratch in session /tmp (gone).
- **No in-flight jobs.** Everything recomputable in seconds-to-minutes from the raw npy files.

## Action Items & Next Steps

1. [ ] **Show the owner `casey_dm_strip_CORRECTED.png` full-size** and get the casey DM pick (491.148 vs 491.178 vs finer strip). This is the calibration anchor.
2. [ ] Codify the DM metric that reproduces the pick (onset/structure alignment via corrected-sign shifts, sub-bin interp; validate it recovers the owner's casey choice blind).
3. [ ] casey aggressive RFI pass (Learnings #4); show before/after; owner approves.
4. [ ] Roll the blessed recipe to the remaining 11 bursts; one corrected strip + before/after per burst for owner spot-check; deliver to `~/Data/Faber2026/dsa110/upchan_codetections_remediated_v2_20260718/` with md5-chained provenance; never touch originals.
5. [ ] Then: re-run the windowed-refit scint campaign on remediated inputs (same predeclared gates), rerun closure, and return to the wf-02 ratification (`docs/rse/wayfinder/tickets/02-ratify-chime-scintillation-method.md`, currently BLOCKED) with fresh galleries.
6. [ ] Wider queue unchanged: fig1 `decide` pair, priors sign-off (wf-07), phineas prescription (wf-06), trust overhaul (wf-13) — see `docs/rse/BOARD.md`.

**Recommended Next Skill:** `ai-research-workflows:running-experiments` for the casey calibration loop (it is an owner-in-the-loop experiment); `ai-research-workflows:implementing-plans` once the recipe is blessed and the 11-burst rollout begins.

## Other Notes

- The owner communicates DM quality visually; every claim must come with a rendered figure, axes explicitly labeled, and the DM-lean convention stated on the figure (lower DM → burst drags right/late going down in frequency; higher → left/early). Never assert a lean direction without the numeric single-channel sign test behind it.
- Wayfinder map: `docs/rse/wayfinder/map-apj-submission.md` (decisions) + `docs/rse/BOARD.md` (execution) are canonical; `results-registry.toml` is the claim-level trust inventory (scint rows currently pending/blocked).
- Standing push/PR authorization exists (CLAUDE.md); pipeline pin bumps are their own reviewed step; PR #140 stays unmerged until remediation completes.

---

**Handoff created by AI Assistant on 2026-07-19**
