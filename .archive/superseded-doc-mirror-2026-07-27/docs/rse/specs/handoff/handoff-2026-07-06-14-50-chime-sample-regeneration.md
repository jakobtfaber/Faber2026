# Handoff: CHIME sample regeneration — five targets rebuilt de-chirped + packaged; quoting policy set; six co-detections await U sizing

---
**Date:** 2026-07-06 14:50
**Author:** AI Assistant
**Status:** Handoff
**Branch:** main
**Commit:** 18cb511 (my session's commits are 18fbe98, 0c17455, eaf9381; 7b11424/18cb511 are the parallel lane's beta-campaign pin bump to 7e77437 — see Other Notes)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| γ(ν) summary figure export (prior handoff item 2) | ✅ Complete | `figures/freya_dsa_gamma_summary.{pdf,png}` (`18fbe98`), oracle-matched arm-J values, visual match vs archived module figure |
| Owner decision: CHIME Δν quoting policy | ✅ Complete | **Unmasked 35.19 ± 4.42 kHz stays the quoted reference; masked 42.21 ± 2.76 is the config-default variant.** Documented in the experiment doc (B1 status note + Key Insight 1), commit `0c17455`. No tex quotes either number (verified by grep) |
| Owner decision: regenerate CHIME npz for the sample | ✅ Complete (5 of 5 defect-carrying targets) | casey, whitney, phineas, mahi, isha regenerated on h17 (`--no-time-shift`; isha `--run-unresolvable`) and packaged to aligned npz. Scope call: "every burst in the sample" read as every target with an existing (defective) product — the six never-generated co-detections need science sizing first (see Next Steps) |
| Gen-1 quarantine | ✅ Complete | h17 + local `DEFECTIVE_nodedisp_20260703/` with `gen1_md5_ledger_20260706.txt`; local gen-1 casey npz pair also quarantined. Nothing deleted |
| Fresh casey gen-2 measurements | ✅ Complete | mask-on config path: casey_chime 33.13 ± 39.70 kHz, casey_chime_hi 95.96 ± 41.75 kHz; modulation indices now physical (0.81 / 1.42 vs gen-1's 5.5 / −5.3); still non-detections |
| Burst configs for whitney/phineas/mahi/isha | 📋 Planned | FLITS-lane work; no configs exist yet for the four newly packaged targets |
| U sizing + generation for six remaining co-detections | 📋 Planned | zach, oran, wilhelm, johndoeii, hamilton, chromatica — singlebeam h5s on h17, not in the script's TARGETS table |

**Current Workflow Phase:** Validate (campaign executed and verified; residue is new-scope work)

## Workflow Artifacts

**Validation Reports:**
- [validation-harmonic-mask-chime-sweep.md](../validation/validation-harmonic-mask-chime-sweep.md) — earlier mask A/B sweep (gen-1-era casey caveats now superseded by regeneration)

**Experiment Reports:**
- [experiment-freya-chime-instrumental-origin.md](../experiment/experiment-freya-chime-instrumental-origin.md) — carries the quoting policy (B1 status note + Key Insight 1)

**Previous Handoffs (same lane):**
- [handoff-2026-07-06-00-34-harmonic-mask-sweep-validated.md](../handoff/handoff-2026-07-06-00-34-harmonic-mask-sweep-validated.md) — items 2 and 3 now checked off in place with closure notes

## Critical References

- `~/Data/Faber2026/dsa110/upchan_codetections/PROVENANCE.md` — **read first**: the 2026-07-06 campaign section holds the full md5 table (upchan + npz per target), recipe, quarantine ledger, per-target alignment verdicts, and the residue list
- `~/Data/Faber2026/dsa110/upchan_codetections/build_npz_aligned_generic_20260706.py` — the generalized aligned builder (per-target DM/U/dt/FWHM; byte-oracled against freya gen-3 both-npz md5s)
- h17 `/data/research/astrophysics/frbs/chime-dsa-codetections/` — working tree: `scripts/upchannelize_chime.py` (md5 `c7fe98f9…`, TARGETS table), `scripts/extract_time0_metadata.py` (new, validated vs freya reference), `upchan_codetections/` outputs + `regen_20260706.log`

## Recent Changes

- `figures/freya_dsa_gamma_summary.{pdf,png}` — new manuscript export (`18fbe98`)
- `docs/rse/specs/experiment/experiment-freya-chime-instrumental-origin.md` — quoting-policy bullet after the B1 status note + Key Insight 1 pointer (`0c17455`)
- `docs/rse/specs/handoff/handoff-2026-07-06-00-34-…md` — items 2/3 closed in place (`18fbe98`, `eaf9381`)
- `~/Data/Faber2026/dsa110/`: 5 × new upchan npy pairs + time0 jsons (`upchan_codetections/`), 10 × new npz (`scintillation-data/{nick}_chime{,_hi}.npz`), PROVENANCE.md campaign section, generic builder. Not git-tracked (data tree)
- h17: regenerated products, `extract_time0_metadata.py`, `run_regen_20260706.sh`, per-target logs, quarantines
- No pipeline-submodule changes by this session (parallel lane advanced the pin 25b8cc6 → 7e77437 during/after)

## Reproducibility & Data State

- **Recipe per target:** h17 `bin/baseband_analysis_python.sh scripts/upchannelize_chime.py <nick> --no-time-shift [--run-unresolvable] --out upchan_codetections` (docker `chimefrb/baseband-analysis:latest`); time0 via `scripts/extract_time0_metadata.py`; local packaging `conda run -n flits python build_npz_aligned_generic_20260706.py <nick>`
- **All md5s:** PROVENANCE.md table; local == h17 verified per upchan file
- **Alignment verdicts:** casey 8/8 @ bin 890 (z 15–26, flat 400–800); whitney 4/4 @ 1020; phineas 5/5 @ 1079; mahi 5/6 @ 29 (**700–725 MHz outlier bin 49 z 8.3 — LTE-band RFI suspect, inspect before using that sub-band**); isha 4/4 @ 55 (upper-bound only)
- **casey gen-2 run outputs:** session scratchpad only; numbers recorded here + PROVENANCE.md
- **In-flight jobs:** none (h17 idle; regen_20260706.log shows all EXIT 0 + ISHA-EXIT 0)

## Verification State / Known-Broken

- **Verified this session:** builder byte-oracled on freya (full+hi md5 exact, re-run after every check change); canonical casey/whitney/phineas npzs byte-identical to final-builder outputs; provenance md5 table re-derived from disk (15/15); extractor field-identical to the 07-04 freya reference json. Verify-gate records exist for every touched path.
- **Uncommitted / unpushed:** none in Faber2026 (main == origin/main at `18cb511`). Data-tree changes are unversioned by design.
- **Unverified / caveats:**
  - whitney/phineas/mahi/isha npz have passed alignment checks but **no scintillation measurement has ever run on them** (no burst configs) — loader-level contract (keys/orientation) matches casey/freya convention but is untested end-to-end for the four.
  - mahi 700–725 MHz sub-band suspect (above).
  - isha remains upper-bound-only by design.
  - Low-band (<600 MHz) per-target lags were reported informationally, not asserted — check against each target's scattering before using the low band.
  - Pinned `pipeline/scintillation/DATA_PROVENANCE.md` is now stale (gen-1-era casey md5s, `/data/jfaber` path) — fix belongs in a FLITS PR (separate lane, do not edit the pinned submodule).

## Learnings

- **Canvas-edge partial coverage fakes burst peaks.** Staggered per-channel offsets leave few-channel bins at the canvas edges; their high-variance means beat the real burst (phineas: edge bin 2272 with 3952/14512 channels outscored the true burst at ~1079). Coverage-mask the burst search (≥90% channels valid).
- **Peak-flatness tolerance must scale with burst FWHM.** freya's ±2-bin criterion (1.2-bin burst) false-alarms on phineas (36-bin FWHM: per-slice peak jitters within the envelope). Tolerance = 1 FWHM in bins; the gen-1 defect smears over 10⁴–10⁵ bins, so within-FWHM coherence still discriminates decisively.
- **z needs off-pulse-only std when the burst is broad relative to the record.** mahi's 9-bin FWHM in a 54-bin canvas deflated full-profile z below the z>5 gate (real z 9–23 once the burst window was excluded from the std).
- **One RFI slice must not veto alignment.** Majority-vs-median assert (≥2/3 within tol) with mandatory outlier WARNING — mahi's LTE-band slice is flagged, not silently absorbed, and not allowed to fail the build.
- **isha requires `--run-unresolvable`** — the script hard-refuses otherwise (2-second exit 1).
- **h17 paths:** everything lives under `/data/research/astrophysics/frbs/chime-dsa-codetections/`; the `/data/jfaber/upchan_codetections` path in older docs never existed on the current tree (corrected in the local PROVENANCE.md).
- **Redirect both output paths when scratch-testing a builder** — a partial sed redirect let the freya oracle test rewrite canonical `freya_chime_hi.npz` in place (byte-identical, so benign, but only because the builder was correct; later oracle tests asserted both replacements before running).

## Action Items & Next Steps

1. [ ] **Burst configs for whitney, phineas, mahi, isha** (FLITS lane): mirror `casey_chime.yaml` (windows from the builder's reported burst bins: whitney ~1020, phineas ~1079, mahi ~29, isha ~55; per-target off-pulse windows; harmonic mask block is default). First measurement run doubles as the end-to-end loader test.
2. [ ] **U sizing for the six never-generated co-detections** (zach, oran, wilhelm, johndoeii, hamilton, chromatica): apply the NE2025 MW-floor rule (freya precedent in PROVENANCE.md "Sizing Rationale") per sightline, add TARGETS entries (id/dm/fwhm_ms/upchan/h5_relpath from `configs/bursts.yaml` + `chime_singlebeam/`), then rerun the same campaign recipe.
3. [ ] **FLITS PR: refresh `scintillation/DATA_PROVENANCE.md`** (gen-2 md5s, correct h17 path, new targets packaged) and commit `extract_time0_metadata.py` + `build_npz_aligned_generic_20260706.py` into the FLITS tree so the h17-side tooling stops living only in an untracked tree + `~/Data`.
4. [ ] **mahi 700–725 MHz RFI inspection** before any mahi sub-band measurement in that range.

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` is overkill for item 1 — just author the four configs against the casey pattern and run them. Item 2 warrants a short plan (`ai-research-workflows:planning-implementations`) since U sizing is a science decision per sightline.

## Other Notes

- **Parallel lane (benign, again):** while this session ran, the beta-campaign lane merged PR #15 and bumped the pipeline pin 25b8cc6 → 7e77437 (`7b11424`, merge `18cb511`). No interaction with this session's data-tree work. Reminder from last night applies: verify the branch immediately before committing in this repo.
- Owner decisions recorded via AskUserQuestion this session: quoting policy (unmasked reference) and sample-wide regeneration (executed for the five defect-carrying targets; six new targets deliberately deferred to U sizing).
- ICM memories: `ok:01KWVB4J38SPW9MT571G0G9SWV` (campaign), `ok:01KWV2C0ZF495A66633SGX7MBC` (mask sweep).

---

**Handoff created by AI Assistant on 2026-07-06**
