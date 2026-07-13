# Plan — CHIME scintillation γ + modulation-index campaign (lane B)

**Owner loop:** claude-fable-5 (orchestrator), 2026-07-12 →. Auto-proceeding;
2026-07-13 owner grant: fully autonomous through manuscript integration —
PR merges and science sign-offs included, no per-step approval. Figure
review stays agent-executed (visual vetting is methodology, not approval);
never force-push/rewrite shared history; pipeline pin bump lands as its own
focused PR with a merge-base ancestor check.
**Standing dispatch:** claude-fable-5 xhigh (design/verification), Codex
gpt-5.6-sol medium (implementation/validation). Heavy compute → h17 (and hpcc
if needed); keep jakob-mbp CPU load bounded (fit fan-out ≤ ~4 local workers).

## Goal (loop termination condition)

For every CHIME co-detection with a viable up-channelized product (12 npz, per
`pipeline/scintillation/DATA_PROVENANCE.md`; isha/hamilton/johndoeII carry
lower-confidence upper-bound status and must not be silently promoted):

1. **γ** — scintillation-bandwidth frequency-scaling index from sub-band
   Δν_d(ν) power-law fit, with uncertainty and a PASS/MARGINAL/FAIL verdict
   under the FLITS fit-validation contract (Levels 1–3).
2. **m(t)** — modulation index vs time across the burst profile.
3. **m(ν)** — modulation index vs frequency (sub-bands).
4. Per-burst diagnostic figures generated AND reviewed (figure-review gate
   cleared; visual vetting per owner's uniform-methods rule — one methodology
   for all bursts, morphology handled as per-burst systematic, never method
   cherry-picking).

"Confident" = gates pass, γ fit spans ≥3 valid sub-bands, and for the four
legacy bursts (chromatica, freya, hamilton, wilhelm) the result is
cross-checked against the rescued reference_arc recipe's numbers. A burst may
terminate as DOCUMENTED-FAIL (data physically can't support the measurement)
— that is a valid exit, silently dropping a burst is not.

## Evidence base

- `scintillation/scint_analysis/reference_arc/` — verbatim Nimmo-lineage
  originals (PR dsa110-FLITS#162, branch `scint/reference-arc-rescue`,
  worktree `~/Developer/scratch/worktrees/flits-scint-rescue`).
- Current pipeline: `scintillation/scint_analysis/` (12 CHIME npz consumable).
- Related in flight: PR #160 (CHIME instrumental-ACF common-mode correction)
  — coordinate, don't collide: this campaign builds on corrected products
  when that lands.

## Phases

- **P4a recon (RUNNING 2026-07-12):** two parallel agents —
  (i) `recipe-reconstructor` (fable) → `reference_arc/RECIPE.md`: exact
  original sequence (upchan params, cleaning order, ACF windowing/zero-lag
  handling, Lorentzian form, γ sub-band scheme, m formulas, per-burst
  deviations table, explicit ambiguities);
  (ii) Codex gap analysis → `logs/codex-gap-analysis.md`: originals vs
  current pipeline, ranked implementation deltas.
- **P4b synthesis:** orchestrator merges (i)+(ii) into an implementation plan
  appended to this doc; commit RECIPE.md to the rescue branch (PR #162 or
  follow-up).
- **P4c implement:** Codex + fable agents add to `scint_analysis/`:
  sub-band γ scaling fit, m(t), m(ν), recipe-faithful cleaning/ACF options;
  tests (incl. regression vs reference_arc worked-notebook values for the
  legacy four). Worktree-isolated; PR to `pin/faber2026`.
- **P4d campaign run:** all 12 bursts through the new path. Light ACF fits
  local (bounded workers); anything heavy (re-upchannelization, wide MCMC)
  → h17.
- **P4e verify loop:** fit-verify workflow (separate judge agents) + figure
  review on every product; failures → diagnose → re-run; iterate until every
  burst has PASS/MARGINAL/DOCUMENTED-FAIL. This is the loop body; exit only
  on the Goal condition.
- **P4f deliver:** per-burst results table + manuscript-ready γ and m
  figures; journal + board update; merge PR #162 lane.
- **P4g manuscript integration (added 2026-07-13):** bump the Faber2026
  `pipeline` gitlink to the landed branch tip (own PR, ancestor-checked);
  update the scintillation section: γ + m(t) + m(ν) results table, method
  paragraph reflecting the recipe provenance (reference_arc lineage), new
  figures wired into the build; compile clean; agent review pass over the
  section (prose + numbers vs results JSONs); land via PR. Terminal state:
  scintillation results in the manuscript, submission-ready.

## Loop mechanics

Orchestrator wakes on background-agent completion (harness notification) with
a ScheduleWakeup heartbeat fallback (~30 min) so the campaign survives hangs.
Each wake: check agent/task state → advance phase → journal (≤10 min cadence
during active work) → re-arm. State lives in this doc + journal + the rescue
worktree; any future session can resume from here.

## Status log

- 2026-07-12: P1–P3 rescue complete (PR #162). P4a agents dispatched.
- 2026-07-13: CAMPAIGN COMPLETE (terminal state reached). P4c six phases + P4d/P4e loop landed via dsa110/dsa110-FLITS#50 (fork PR #168); Faber2026 pin bump PR #21 (ancestor-checked 3435ba0 -> fba48c6); manuscript PR #22 (results §scintillation CHIME paragraph + Table tab:chime_scint_gates + discussion boundary condition), verifier MERGE-CLEAR, merged 23918bd. Science outcome: 0/12 CHIME bursts certify Δν_d — DOCUMENTED-FAIL sample-wide with named physical causes (fail-closed gates: off-pulse null, two-sided low-lag stability, modulation physicality m≤1.5, sub-band support ≥3, provenance incl. instrumental background correction); freya sweep pins 36–45 kHz to the 35 kHz instrumental scale under all 6 preprocessing×lag variants; γ anchor unavailable, attribution rests on DSA band. m(t) direct + m(ν) products retained as gated diagnostics. Follow-ups (not blocking): cosmetic plot bugs (ΔBIC panel empty, johndoeII glyph dropout, two y-tick overprints); rerun campaign if/when validated instrumental-background-corrected products land sample-wide (would clear the uniform provenance failure and could revive casey_hi/whitney-class candidates).
- 2026-07-13 (post-terminal figure-review note): hamilton and chromatica are the best-morphology CHIME products in the set (resolved cusped ACF peaks, monotonic bw(ν), primary estimators agreeing at α≈5.3–6.6), clean low-lag stability, failing ONLY the off-pulse null and marginally so against the hard cut (off/on width ratio 1.72 and 1.94 vs the 2.0 pass boundary). johndoeII third but weaker (null inconclusive at 2 off fits; fails modulation physicality independently).
- 2026-07-13 (uncertainty-aware null probe — CORRECTS the note above): the earlier "threshold-sensitive" framing and the suggestion that a spread-aware null boundary could flip these two verdicts were FALSIFIED by direct test. Reran hamilton + chromatica with the off-pulse fit population serialized (`off_dnu_mhz`) and computed a log-space MAD-scaled z of the on-pulse width against the off-pulse population: hamilton on = 51.1 kHz sits inside off fits spanning 0.6–246 kHz (z = 0.41, a third of the off fits are *narrower* than on); chromatica on = 92.6 kHz inside off fits 73–357 kHz (z = 0.90). A spread-aware boundary therefore fails both MORE decisively than the hard 2.0 ratio — the verdicts are robust, not threshold-sensitive. The z-statistic is now recorded (non-gating) in `off_pulse_null_verdict` as `off_log_z`/`off_log_mad_sigma` with a regression test pinned to the hamilton numbers (commit 9237e4c, dsa110/dsa110-FLITS#51). Only remaining revival path for any CHIME burst: the corrected-products sample-wide rerun.
