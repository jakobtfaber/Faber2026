# Handoff: freya CHIME generation-3 product — dedispersion defect closed, full band usable

---
**Date:** 2026-07-04 12:30
**Author:** AI Assistant
**Status:** Handoff
**Branch:** main (Faber2026)
**Commit:** `be6d189` (pushed; tree clean)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Diagnose "strange" freya CHIME dynamic spectrum (owner-spotted) | ✅ Complete | Root cause: h17 script discarded `coherent_dedisp`'s return — product never de-chirped (gen-1 DEFECTIVE) |
| Regenerate with de-chirp fix (gen-2, `time_shift=True`) | ✅ Complete | All 4 causal predictions confirmed; pass-4 Δν_d = 35.43 ± 5.06 kHz |
| Explain low-band anomaly in gen-2 | ✅ Complete | FFT phase-ramp shift is circular per channel buffer → burst wrapped to `386 mod L` below ~505 MHz; verified 3 ways |
| Band-selection check (owner: "fix it if wrap-driven") | ✅ Complete | 600–800 choice predates wrap (floor resolvability + scattering S/N); 505–800 run: same value, worse total error (17.2 vs 14.8 kHz) |
| Make low band usable (gen-3, owner-requested) | ✅ Complete | `--no-time-shift` de-chirp + metadata-aligned builder; low band z 10.6–13/slice; pass-5 canonical |
| Commit v3 config windows to FLITS | 📋 Planned | Uncommitted in `flits-rerun` worktree — owner-gated new lane |
| E3/E4 rerun on fixed product; other 4 targets; real redshift | 📋 Planned | See Action Items |

**Current Workflow Phase:** Validate (measurement lane); the FLITS config commit is a small pending Implement.

## Workflow Artifacts

**Experiment Reports:**
- `experiment-freya-chime-dnu-science-readiness.md` — E1–E4 + defect addendum + gen-2 outcome (4 causal predictions) + low-band wrap mechanism + band-extension check + gen-3 record. THE evidence chain for this lane.

**Implementation Summaries:**
- `implement-freya-chime-dnu-durable-fix.md` — #120/#121 merged pipeline fixes (grid regularization, m_acf, fit-window scan; squash `2931e1bf`).

**Prior Handoffs:**
- `handoff-2026-07-03-18-22-freya-scint-lane-closeout.md` — updated through this session (epistemic-status block + defect/regeneration record are current); superseded by this handoff as the entry point.

## Critical References

- `~/Data/Faber2026/dsa110/upchan_codetections/PROVENANCE.md` — canonical generation history (gen-1 DEFECTIVE → gen-2 SUPERSEDED → gen-3 CURRENT), md5s, verification numbers, builder pointer. Read first for any data question.
- `experiment-freya-chime-dnu-science-readiness.md` (this dir) — full evidence chain.
- `~/Data/Faber2026/dsa110/upchan_codetections/build_npz_aligned_20260704.py` — the aligned builder (canonical copy; also in session scratchpad).

## Recent Changes

- Faber2026 `docs/rse/specs/` — five commits this session (`6ff71b3` → `be6d189`), all pushed: defect addendum, gen-2 outcome, wrap mechanism, band check, gen-3 record.
- h17 `scripts/upchannelize_chime.py` — two patches: (a) feed `coherent_dedisp` return into `_upchannel` (the defect fix); (b) `--no-time-shift` flag. Backups alongside (`.pre-dedisp-fix-20260704`, `.bak-timeshift-20260704`); verbatim snapshots + md5s in `upchan_codetections/` (`…_20260704_dedispfix.py` = `58c3f5b7…`, `…_20260704_noshift.py` = `c7fe98f9…`). h17 tree is NOT a git repo.
- `flits-rerun` worktree `scintillation/configs/bursts/freya_chime{,_hi}.yaml` — v3 windows `[253, 264]`/`[10, 200]` (hi), `[253, 268]`/`[10, 200]` (full) + provenance comments. **Uncommitted.**

## Reproducibility & Data State

- **Environment:** conda `flits`; measurement CLI run from `~/Developer/scratch/worktrees/flits-rerun` (detached at merged main `2931e1bf`) with `FLITS_ROOT=$PWD`.
- **Data (canonical, `~/Data/Faber2026/dsa110/`):**
  - `upchan_codetections/freya_chime_upchan.npy` md5 `8215e051…` (gen-3, = h17), `freya_chime_freq.npy` `ad0ddb20…`, `freya_time0_metadata.json` (fpga_count per coarse channel from `singlebeam_278720455.h5`).
  - `scintillation-data/freya_chime.npz` `0b3b423a…`, `freya_chime_hi.npz` `1f644b07…` (446-bin aligned canvas, burst bin 254).
  - Quarantines: `DEFECTIVE_nodedisp_20260703/` (gen-1), `SUPERSEDED_timeshift_20260704/` (gen-2) — npy + npz, locally and on h17. Never deleted.
- **Partial results:** run outputs in `flits-rerun scintillation/plots/`: `freya_chime_pass4_dedispfix/` (gen-2), `freya_chime_pass5_v3aligned/` (gen-3, canonical); pass-1–3b archives in `~/Data/Faber2026/dsa110/scintillation-data/freya-chime-runs-2026-07/`; 505–800 band-check run in session scratchpad (`pass4b_505/`, numbers preserved in the experiment doc).
- **Regeneration recipe (for the other 4 targets):** h17 docker `chimefrb/baseband-analysis:latest`, `scripts/upchannelize_chime.py <target> --no-time-shift --out …/upchan_codetections`; pull `time0` metadata (one ssh docker python command, see PROVENANCE); build with `build_npz_aligned_20260704.py` (adjust paths/DM per target).

## Verification State / Known-Broken

- **Canonical measurement (CHIME): Δν_d = 35.19 ± 4.42 (stat) ± 17.0 (fit-window) kHz @700 MHz, m_acf = 0.304** (pass-5, gen-3, windows `[253, 264]`/`[10, 200]`). Gen-2 pass-4 consistent at 0.05σ. NOT citable yet: fit-window systematic dominates and is untreated; E3/E4 not rerun; z=1.0000 placeholder; configs uncommitted; pin not bumped.
- **Verification battery (all passed on gen-3):** sawtooth null (−0.71/−0.20 ms vs |7.0|/|10.7| predictions, R² ≤ 0.22); alignment flat at bin 254–255 across 600–800 (z ≤ 142); low-band peak lag matches ~0.3–0.4 τ(ν) + 0.07 pc/cm³ DM offset; low band z 10.6–13 per 25-MHz slice.
- **Uncommitted / unpushed:**
  - `flits-rerun` worktree: the two config yamls (modified) + `scintillation/plots/` (untracked run outputs) — the yaml delta is the pending FLITS lane; plots are archivable artifacts.
  - Canonical FLITS clone: main behind origin by 1 (`9ebe02cf` vs `2931e1bf`, pull deferred by convention) + `docs/entire-tracing-checkpoints.md` dirty (rides-dirty ledger convention — do not clean).
- **Known data features (documented, not bugs):** narrowband RFI 482–487 MHz near bin 391 (pipeline freq-domain masking handles it); trailing partial-coverage bins ~423–436; leading offsets 0–9 (noise window starts at 10).

## Learnings

- `coherent_dedisp(..., time_shift=True)` applies the inter-channel shift as an FFT phase ramp — **circular within each channel's valid buffer** (trimmed at first NaN). Buffers shorten toward 400 MHz (348 bins at 412 MHz vs 436 at 787), so any product where the aligned burst index exceeds L wraps. The function's own docstring warns "not recommended". Use `--no-time-shift` + explicit builder alignment for anything needing the low band.
- `K_DM` in baseband_analysis = `1/2.41e-4` = 4149.377593360996 exactly (verified by docker import) — matches the naive constant; a suspected K-mismatch was NOT the cause of the low-band peak-lag gradient.
- The low-band peak lag (~7 bins at 412 MHz) decomposes as scattering peak-shift (~0.3–0.4 τ(ν)) + the 0.07 pc/cm³ offset between the DM used (912.4) and CHIME's structure DM (912.4699). Both ≤ 1 bin above 600 MHz. Regenerating at 912.4699 would change nothing measurable in-band (intra-channel residual smear ~1 µs).
- The gen-2 wrap didn't just displace the low-band burst — it sat inside the flat-field off-window, suppressing apparent z (3–4 vs the true 10–13). Fixing alignment recovered real sensitivity.
- Capture (`fpga_count`) tracks the full 17.697 s dispersion sweep; per-channel offsets on the de-dispersed grid span only 9 bins (132–141) — alignment is nearly free once metadata is in hand.
- Slice-peak assertions on scattered bursts need τ-scaled tolerances; a fixed ±4-bin threshold false-alarms below 500 MHz.

## Action Items & Next Steps

1. [x] **Commit the v3 config windows to FLITS** — done 2026-07-05: direct commit `a0a9c83e` on FLITS main; pass-4/5 plots archived to `~/Data/.../freya-chime-runs-2026-07/`; worktree removed.
2. [x] **E3/E4 rerun on gen-3** — done 2026-07-05: **ν^4.4 verdict reverses** (band ratio 0.85 ± 0.18 vs 1.88 predicted, window-stable → achromatic/instrumental origin favored); split-time consistent; m_burst = 0.30 = m_acf. See the experiment doc's gen-3 rerun section.
3. [ ] **Fit-window systematic**: it now dominates (17.0 vs 4.42 stat). Options recorded in the experiment doc (ripple-period-aware fitting, window marginalization).
4. [ ] **Other 4 co-detection targets** (casey, isha, mahi, phineas): regenerate straight to `--no-time-shift` + aligned builder (recipe above). Their existing products carry the gen-1 defect.
5. [ ] Real freya redshift to replace z=1.0000 placeholder (E4 coherence limit + any budget use).
6. [ ] Faber2026 pin bump only when the manuscript starts citing scintillation numbers (deliberate `build:` commit per PIPELINE.md).

**Recommended Next Skill:** `ai-research-workflows:running-experiments` for item 2 (E3/E4 rerun is an experiment with acceptance criteria); `ai-research-workflows:implementing-plans` for item 1 if the owner opens the FLITS lane.

## Other Notes

- Pushes to Faber2026 main are outward-facing (Overleaf pulls via manual GitHub Sync); oneway-guard gates pushes — sticky window may have expired for the next session.
- `pipeline/` in Faber2026 remains pinned at `bffd875`; FLITS main is `2931e1bf` — intentional, do not bump casually.
- A parallel Codex session has historically worked these repos under the same identity — re-check `git status`/PR state immediately before any push/merge in FLITS.
- Display scripts from this session (session scratchpad, ephemeral): `fullband_view.py`, `fullband_unwrap.py`, `sawtooth_image.py`, `sawtooth_test.py`, `build_npz_aligned.py` (canonical copy of the last one preserved in `upchan_codetections/`).

---

**Handoff created by AI Assistant on 2026-07-04**
