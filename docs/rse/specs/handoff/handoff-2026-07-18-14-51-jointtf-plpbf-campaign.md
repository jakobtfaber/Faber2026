# Handoff: Joint-TF mass-refit + PL-PBF three-way model selection

---
**Date:** 2026-07-18 14:51
**Author:** AI Assistant (team-lead session; compute agent: teammate "joint-tf-fits")
**Status:** Handoff
**Branch:** main
**Commit:** cc6ca296

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| α<4 question (owner) | ✅ Complete | Answered via Cordes et al. 2025 full text + relaxed-α experiment. Sub-4 α is a wrong-model signature, never thin-screen physics. |
| Production mass-refit, 12/12 bursts | ✅ Complete | Full landscape landed (see table below). Deck slide 8. |
| Relaxed-α diagnostic (casey+wilhelm) | ✅ Complete | Free α wins ΔlnZ +5537/+731; resolves tail residuals; α≈2.5 = mismatch signature (model still EMG in shape — diagnostic wedge only). |
| PL-PBF three-way experiment | ✅ Complete (verdict) / 🔄 interpretation | **PL-PBF collapses to production on BOTH bursts** — casey lnZ −33571.3 (vs prod −33574.6, Δ+3.3), wilhelm −16499.5 (vs prod −16496.2, Δ−3.3); s_i at upper rail both (tail below noise). Free-α EMG still wins by +5533/+734. Physical heavy tail is NOT the mechanism. |
| Harsh-tail injection (scale closure) | ✅ Complete | Single-component tail grossness maxes at α bias −0.21 (casey-matched: −0.01); cannot produce the −1.6. Consistent with PL-PBF real-data collapse. |
| Multi-component leakage injection | 🔄 In progress (green-lit) | Lead candidate for the −1.6; harness extension chartered with teammate (casey C1D1 + weak scanned secondary → 1-comp free-α refit). |
| zach D3-vs-D4 (owner ground truth D=4) | 🔄 In progress | C2D4 collapsed at 131 µs (ΔlnZ −2.3, params identical) → binning-drop refit 131→65.5 µs triggered. The +2.06 ms member is left UNFIT by D3 (count shortfall, not resolution loss). |
| Neighbor count-tests (task #11) | 🔄 Verdict pending | s2=100 evidences: phineas C4 +75, johndoeII C3 +47 (τ=2.25 sanity flag), whitney D2 +5372 / C2 +65 (β moves off floor to 3.43 → feeds whitney rail classification, task #12). CAVEAT: zach C2-at-s2=100 fits mode-trap to a wrong steep corner — apply ΔlnZ>5 protocol with that suspicion. |
| Follow-on h17 batches (jobs 120–146) | 🔄 Running | Teammate-launched after the PL-PBF verdict: 5×jtfp, 2×jtfzf, 4×jtfdm (~45 min elapsed at handoff). Identity not yet briefed to team-lead — read the journal + `~/flits-runs/logs/` on h17 to attribute before touching. |
| TOA table + triptychs + flags (task #6) | 📋 Planned | Blocked on count verdicts + binning-drop zach + owner ratifications. |

**Current Workflow Phase:** Experiment → Validate (model-selection verdict in; interpretation + campaign deliverables next)

## Mass-refit landscape (12/12, production EMG, RFI-fixed binning)

interior: freya 4.357/3.697 (Kolmogorov 2.3σ), mahi 4.16/3.849, johndoeII 4.26/3.771, isha 4.47/3.623 · ceiling-adjacent: phineas 4.043/3.958 (FLIPPED from steep corner under RFI fix), oran 4.049/3.952, zach 4.021/3.979 (C2D3 baseline) · ceiling rails: casey, wilhelm, chromatica (β=3.990) · **floor-rail class: hamilton 5.986/3.003 (τ=0.75 µs, scattering unresolved), whitney 5.90/3.025 (candidate)**

## Critical References

- `docs/rse/journal.jsonl` — the running lane log (grep `joint-tf-fits`); most compressed true history of this campaign.
- Live deck: https://jakobtfaber.github.io/Faber2026/decks/jointtf-day2/ (15 slides, self-critique on 14) + validation page decks/plpbf-validation/ — built from scratchpad scripts (see Other Notes).
- h17: `~/flits-runs/data/joint/*.json` (all fit posteriors incl. `plpbf_{casey,wilhelm}_joint_fit.json`, `ab_*_relaxalpha_*.json`, `_prerefit_snapshot_20260717-1715/`) and `~/worktrees/joint-tf-fits/analysis/scattering-refit-2026-06/` (fitters, provenance docs: `PLPBF_FITTER_PROVENANCE.md`, `COMPONENT_COUNT_LADDER_AUDIT.md`, `RFI_FIX_FLIP_RECORD.md`, `FFTFIX_DEPLOY_PROVENANCE.md`).

## Reproducibility & Data State

- **Environment (h17):** conda `flits-a1-312`; `FLITS_REPO=~/worktrees/joint-tf-fits`; PYTHONPATH includes `scattering/` + analysis dir. Slurm accounting is OFF (`JobAcctGather=none`) — job history only via logs, `sacct` is empty.
- **Fitters:** production `run_joint_fit*.py`; relaxed-α driver; PL-PBF `plpbf_loglike.py` + `run_joint_fit_plpbf.py` + `jobs/fit_plpbf.sbatch` (α tied UNCLAMPED 2β/(β−2) via FRBParamsPLPBF override — the production `alpha_from_beta` clamp at β≥3.98 was a caught-and-fixed bug, do not reintroduce).
- **Injection validation:** recovery grid 9/9 PASS (β, s_i in 90% CI); embias grids 96–101 + harsh 114–117 in `~/flits-runs/logs/pli_*`.
- **In-flight:** h17 jobs 120–146 (jtfp/jtfzf/jtfdm, teammate-owned). Check `squeue`, then logs `~/flits-runs/logs/`.
- **FFT fix:** `next_fast_len` deployed mid-campaign (exact, 3.16×) — provenance doc has pre/post.

## Verification State / Known-Broken

- **PL-PBF verdict numbers above are read from the landed JSONs** but not yet postprocessed (no corners/residuals/triptychs for the PL-PBF fits yet); teammate owns that postprocess incl. explicit s_i-posterior reporting (upper rail = "EMG adequate" verdict, not failure).
- **Neighbor-test count changes NOT yet adopted** — evidences are raw; the mode-trap caveat is unresolved; no production count has been changed anywhere.
- **Uncommitted (separate lanes, preserve):** `docs/rse/board/readiness.html`, `docs/rse/journal.jsonl` (both dirty), several untracked `docs/rse/specs/*-2026-07-17.md` drafts + `handoff-2026-07-18-14-44-fig1-observed-peak-decision.md` (another session's lane).
- **whitney β=3 rail classification (task #12)** untouched pending count verdicts.
- **Deck/validation pages** were current through the harsh-tail verdict but do NOT yet show the PL-PBF real-data collapse result — first stale item to fix when publishing next.

## Learnings

- **The three-way is now a two-way with a puzzle:** clamped EMG ≈ PL-PBF ≪ free-α EMG. The free-α advantage (+5533/+734) is NOT tail shape (harsh-tail injection max −0.21; PL-PBF s_i upper-railed). Lead hypothesis: multi-component leakage (wilhelm-C precedent); the leakage injection is the discriminant. Discipline holds: α≈2.5 stays a mismatch signature, not physics.
- **Count-ladder gap:** D4 was never launched campaign-wide; several counts were hand-assigned. Fixed-s2 neighbor protocol (s2=100, ΔlnZ>5) is the remedy but s2=100 can mode-trap low-count fits (zach) — evidence gaps there conflate count with solution mode.
- **Owner morphology knowledge beats ladders:** zach D=4 (1 + cluster of 3) confirmed at native 32.8 µs; fit binning at 131 µs cannot host the 4th component (collapse, not refutation).
- **Standing owner directives:** visually vet every fit figure for left-out components (CnDm annotated) before publishing; uniform methodology across all 12; figures with every substantive step; journal every ≤10 min of active work.
- **Messages with the compute teammate cross frequently** — re-verify claimed state on disk (the "fully de-risked" fitter still had the clamp bug; the "04:36 batch" was phantom monitor replay).

## Action Items & Next Steps

1. [ ] Attribute h17 jobs 120–146 (journal + logs), sync with teammate "joint-tf-fits" (SendMessage; it survives crashes — resend anchors as needed).
2. [ ] Publish the PL-PBF collapse verdict: update deck slide 6/15 + validation page §5 with the three-way numbers (deploy pattern in Other Notes); relay to owner with the disciplined framing.
3. [ ] Drive the leakage injection to a verdict on the −1.6; if leakage reproduces it, the paper story is "unmodeled weak components bias chromatic fits" and count remediation becomes central.
4. [ ] Close zach: binning-drop refit verdict vs owner D=4; then neighbor-test protocol pass (with mode-trap caveat) → adopt counts → task #6 deliverables (TOA table with limit framing; wilhelm error caveat must cite the DSA single-bin dipole ±20σ as a separate non-scattering systematic; isha DSA excluded).
5. [ ] whitney rail classification (task #12) once its counts settle (C2D2 moves β off the floor — the "rail" may be a count artifact).
6. [ ] Owner decisions pending: 2L scint table ratification; count-audit remediation as standing method; PL-PBF as campaign default is now MOOT (it collapsed) — instead decide how the free-α diagnostic is reported in the paper.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` for the PL-PBF verdict + count adoption; `ai-research-workflows:running-experiments` for the leakage-injection lane.

## Other Notes

- Deck/page build scripts live in the session scratchpad `/private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/a573656f-9ea8-4ebd-aab6-58332c63c659/scratchpad/` (`build_day2_deck.py`, `build_plpbf_figs_page.py`, `build_triptych_page.py` — base64-embed images; scratchpad is session-scoped, so copy them into the repo if this session's scratchpad is gone). Deploy: gh-pages worktree (`git worktree add --detach $TMP origin/gh-pages` → cp → commit → push → `until curl` 200).
- Telegram is NOT configured ("ping me" = in-chat). Cost is never a gate (Max subscription).
- claude-science accounts were merged today (gmail org → caltech org) and the Faber2026 OPERON project is archived in-repo at `docs/rse/claude-science/` (PR #133) — transcripts/execution logs/artifacts of 14 conversations, useful as searchable prior context.
- Standing push/PR authorization exists (CLAUDE.md); pipeline submodule pin is deliberate — never bump as a side effect.

---

**Handoff created by AI Assistant on 2026-07-18**
