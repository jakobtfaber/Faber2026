# Handoff: Joint-TF audit closure — two-screen Stage-0 FAIL, t0-prior bug, production ghosts, v2 re-runs

---
**Date:** 2026-07-19 16:33
**Author:** AI Assistant (team-lead session; compute agent: teammate "joint-tf-fits" on h17)
**Status:** Handoff
**Branch:** main (this session's lane is fully merged; dirty files in the tree belong to a SEPARATE lane — see Verification State)
**Commit:** eb09bb39

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Document/store/commit/merge campaign closure (owner order) | ✅ Complete | Faber2026 PR #142 (closure report + decision brief) and #143 (two-screen charter) merged to main. FLITS PRs #203 (campaign artifacts), #204 (RFI/binning rebase), #205 (t0 clamp), #206 (off-window audit table), #207 (TOA-suspect notes) merged. |
| Two-screen decision → charter (owner chose A) | ✅ Complete | `charter-two-screen-forward-model-2026-07-18.md`; non-gating parallel lane; rung-1 = double-exp PBF, shared β, r=τ₂/τ₁, nested. |
| Two-screen Stage-0 wedge-reproduction falsifier | ✅ Complete (verdict) / 🔄 write-up | **FAIL, wrong sign, 16/16 injection points positive**: r-grid (casey +0.17/+0.42/+0.56; wilhelm +0.90/+1.45/+1.68) + W/τ envelope sweep 0.1–10 (casey +0.25…+2.00 rail; wilhelm +1.42…+2.00 rail). Same-α mixing pushes apparent α ABOVE 4 — opposite the observed sub-4 wedges. No real-data two-screen fits ever run. Teammate owes: envelope numbers into `TWOSCREEN_FITTER_PROVENANCE.md` + two-screen lane PR (kernel currently local-only on h17). |
| Rung-2 decision (independent β₂) | 📋 Owner decision PENDING | Only remaining mechanism that can flip the deformation sign. Charter §2 rung-2 clause; gate condition met. Owner has the framing in-chat; not yet answered. |
| zach D3-vs-D4 (task #10) | ✅ Independently re-harvested / 📋 owner pending | Fine pair (133/134) INVALID (off-window). v2 ladder 177–182 all RC=0: s2=10 D3→D4 MODE-JUMP (+1425, β 3.18→3.98) invalid; s2=100 candidate is **C2D3** after structural rejection of a null-like D5 member. Owner adoption remains pending. |
| t0-prior bug (root cause + fix) | ✅ Fix landed / 🔄 consequences | `build_priors` t0 half-width 2·max(τ,10) → ±20 ms priors campaign-wide. Fix = FLITS PR #205 (`_clamp_t0_priors_to_window`, all 5 spec variants, validated). Prior-spec v1/v2 split versioned in `COMPONENT_COUNT_LADDER_AUDIT.md`. |
| Production off-window audit (12/12) | ✅ Complete | **2 production ghosts CONFIRMED by visual vet**: oran C2D1 (t0_C1=−5.2 ms, fluence ≈ real C2) and johndoeII C2D2 (t0_C1=−6.2 ms, fluence 26.2 vs real 8.4 — severe). 6 clean (casey, wilhelm, chromatica, freya, mahi, whitney_fine); isha edge-watch; phineas npz-unresolved; hamilton/zach TOA rows empty. TOA rows oran+johndoeII CHIME structure SUSPECT pending v2 re-runs. |
| oran/johndoeII v2 audit re-runs | ✅ Independently re-harvested / 📋 owner pending | Jobs 169–176 RC=0. Evidence supports candidate drops: **oran → C1D1** and **johndoeII → C1D2**. Owner adoption and production changes remain pending. Report: `validation-jointtf-v2-rerun-harvest-2026-07-19.md`. |
| hamilton probes (task #12-adjacent) | 🔄 Diagnosed | C5D1 rejected (−41, same floor mode). C4D2 flips hamilton to healthy corner (β=3.978, τ 19×) = whitney-twin pattern, but cross-mode ΔlnZ invalid → profiled-gain fallback needed. |
| phineas C4D4 | 🔄 Diagnosed | Mode-trapped (β=3.018 floor vs production 4.043 healthy) → invalid; whole phineas neighbor story suspect until re-run under v2. |
| TOA table + triptychs (task #6) | 📋 Blocked | On count verdicts + owner ratifications. |

**Current Workflow Phase:** Validate (audit remediation + verdict harvests)

## Workflow Artifacts

- `report-jointtf-mechanism-closure-2026-07-18.md` — three-way model-selection verdict + five-mechanism elimination table (evidence base for everything here).
- `decision-two-screen-charter-2026-07-18.md` — A/B/C brief, marked DECIDED (A).
- `charter-two-screen-forward-model-2026-07-18.md` — the executed charter incl. the Stage-0 falsifier that fired and the rung-2 clause now in play.
- `handoff-2026-07-18-14-51-jointtf-plpbf-campaign.md` — mid-day 07-18 snapshot (superseded by the report but has env/infra detail).

## Critical References

1. `docs/rse/specs/notes/charter-two-screen-forward-model-2026-07-18.md` — the rung-2 decision reads directly off its §2/§3.
2. h17: `~/worktrees/joint-tf-fits/analysis/scattering-refit-2026-06/COMPONENT_COUNT_LADDER_AUDIT.md` — single source of truth for count-audit state, prior-spec v1/v2, off-window table, standing guardrails.
3. Live deck https://jakobtfaber.github.io/Faber2026/decks/jointtf-day2/ — slides 6 (elimination + Stage-0 update), 10 (zach INVALID + vet fig), 11 (production ghosts + vet fig), 15 (decision queue). Build script: session scratchpad `build_day2_deck.py` (scratchpad is session-scoped — copy out if resuming elsewhere).

## Reproducibility & Data State

- **Environment (h17):** conda `flits-a1-312`; `FLITS_REPO=~/worktrees/joint-tf-fits` (worktree at d292f4b + landed v2 `burstfit_joint.py` via `git checkout origin/main --`); `FLITS_RUNS=~/flits-runs`.
- **Prior-spec versioning:** v1 = ±20 ms t0 (ALL evidences landed before 2026-07-19); v2 = windowed (PR #205). NEVER cross-compare v1 and v2 lnZ. Stage-0 grid + envelope ran v1 (verified immaterial: single component injected at 30% of window).
- **Snapshots:** `~/flits-runs/data/joint/_v1_preclamp_20260719/` (23–24 files, pre-overwrite); `_invalid_zachfine_offwindow_20260718/` (the invalid pair).
- **Stage-0 products:** `~/flits-runs/data/twoscreen_stage0/*.json` (6 r-grid) + envelope-sweep logs `jtfts0_159–168`.
- **Historical state at 16:33 handoff; superseded:** jobs 180–182 were then RUNNING and 169–179 were unharvested. Jobs 169–182 later finished `RC=0` and were independently re-harvested in `validation-jointtf-v2-rerun-harvest-2026-07-19.md`. Count adoption remains owner-pending.

## Verification State / Known-Broken

- **Adjudicated this session, verified on disk by team-lead:** Stage-0 16/16 wrong-sign; zach fine pair INVALID; oran/johndoeII ghosts (visual vets rendered by team-lead: zachfine_vet.png, ghost_vet.png — embedded in deck).
- **Historical state at 16:33 handoff; superseded:** jobs 169–179 were then unadjudicated. Jobs 169–182 now have an independent arithmetic, fit-window, artifact-hash, and visual re-harvest. Candidate dispositions exist; owner ratification and production changes do not.
- **Not yet landed anywhere:** two-screen kernel code + `TWOSCREEN_FITTER_PROVENANCE.md` (h17 worktree local-only; teammate owes the lane PR). `build_toa_table.py` + `residual_check.py` deferred (entangled, land with task #6).
- **Suspect until v2 re-adjudication:** oran + johndoeII TOA-row CHIME structure; phineas neighbor evidences (C4 +75/D4 +27); 29 higher-count diagnostics untestable without npz regen (list in audit doc).
- **Separate lane in this working tree (PRESERVE, not this session's):** dirty `docs/rse/protocols/journal.jsonl` (shared append log — fine), `docs/rse/control/results-registry.toml`, `docs/rse/specs/handoff/handoff-2026-07-19-stratified-restart.md`, `docs/rse/wayfinder/*`, untracked `docs/rse/certificates/l0-certificates.json`, `scripts/build_l0_certificates.py`, `scripts/l0_conventions.py`, `tests/test_l0_axis_conventions.py` — the stratified-restructure/L0-certification lane (PR #145, merged eb09bb39, another session). Do not sweep into any commit from this lane.

## Learnings

- **Off-window ghost components** are a distinct count-test failure mode: a component whose t0 prior extends past the fitted window gives the gain marginal per-channel baseline freedom worth thousands of lnZ (+3550 on zach) while fitting nothing real. Structural diagnostic: median outside window + straddling multi-ms CI + real recovered fluence, while genuine components sit tight in-window. Guardrail pair: window-contains-all-candidates AND t0-priors-bounded-to-window.
- **A decisive Bayes factor pointing where you expect is the most dangerous kind** — the zach +3550 "matched owner D=4" and was pure artifact. Visual vet before verdict is not optional (owner standing rule; it caught this).
- **Stage-0-first charters pay off**: rung-1 two-screen was excluded for ~16 cheap injection fits, zero real-data spend. Wrong-SIGN exclusions are stronger than too-weak ones: wilhelm r=1 reaches |1.68| ≈ observed |1.6| but deforms oppositely — only different-scaling-law screens (rung 2) can flip the sign.
- **Physics:** two same-α convolved exponential tails broaden low-ν MORE than one screen → single-screen refit reads SUPER-4 scaling. The observed wedge (low-ν less broadened than ν⁻⁴) cannot be made this way.
- **Teammate messages cross constantly** — three crossings this session (D4 verdict, vet request, Stage-0 hold). Protocol that worked: adjudicate from disk, cite msg IDs, re-point instead of re-arguing.
- **Slurm on h17 lies about memory** (bookkeeping-only) and `sacct` is empty (`JobAcctGather=none`) — job history only via `~/flits-runs/logs/`.

## Action Items & Next Steps

1. [x] Independently re-harvest jobs 169–182 — arithmetic, fit-window checks, hashes, and visual review complete. Candidate dispositions: oran C1D1, johndoeII C1D2, zach C2D3. Owner adoption remains pending; no production rewrite occurred.
2. [ ] Verify teammate's two-screen lane PR when it lands (kernel + TWOSCREEN_FITTER_PROVENANCE.md with envelope table + v1-label clause) and the Stage-0 FAIL write-up; then update deck slide 6/15 with the envelope numbers. (Still local-only on h17 at harvest.)
3. [ ] Put the rung-2 charter decision to the owner if unanswered (charter §2 rung-2 = independent β₂, Stage-0-first, ~6 injection fits; Stage-0 FAIL gate met).
4. [ ] After owner ratifies count drops: hamilton profiled-gain fallback + whitney rail (task #12), phineas re-run under v2, then task #6 TOA table (oran/johndoeII rows per v2).
5. [ ] Owner decision queue standing: ratify EMG-stays; count-audit remediation as method; ratify oran/johndoeII drops + zach D3; 2L table ratification; **rung-2**.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` (harvest/adjudication of the landed re-runs); `ai-research-workflows:running-experiments` if rung-2 is chartered.

## Other Notes

- Deck deploy pattern: gh-pages worktree (fetch → `worktree add --detach` → cp → commit → push → curl-verify). Journal every ≤10 min of active work (`scripts/journal-append.sh`).
- Telegram NOT configured — "ping me" = in-chat. Cost never a gate (Max subscription). Standing push/PR auth on this repo; pipeline/ pin never bumped as a side effect; overleaf-* branches never deleted.
- Teammate session survives crashes/spend-limit drops — resume by SendMessage with a state anchor; its wave monitor survived one drop this session.
- Memory `plpbf-rejected-emg-stands.md` carries the durable arc (PL-PBF → wedges → elimination → charter → Stage-0 FAIL → t0 bug) — keep it updated as verdicts land.

---

**Handoff created by AI Assistant on 2026-07-19**
