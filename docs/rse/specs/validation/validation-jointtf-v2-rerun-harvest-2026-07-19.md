# Validation: joint-TF v2 re-run harvest (jobs 169–182)

Validated against handoff
`docs/rse/specs/handoff/handoff-2026-07-19-16-33-jointtf-audit-twoscreen-stage0.md`
and h17 audit
`~/worktrees/joint-tf-fits/analysis/scattering-refit-2026-06/COMPONENT_COUNT_LADDER_AUDIT.md`
at Faber2026 commit `8fc1179e` on 2026-07-19.

**Prior-spec:** v2 windowed t₀ (FLITS PR #205). Never cross-compare lnZ with
pre-2026-07-19 v1 evidence.

## Implementation Status

| Item | Claimed | Verified |
|------|---------|----------|
| Jobs 169–176 oran/johndoeII DONE RC=0 | handoff: landed unharvested | ✅ all 8 stdout `RC=0`; JSON+npz on disk |
| Jobs 177–182 zach fine ladder DONE | handoff: 177–179 done, 180–182 running | ✅ all 6 DONE RC=0 (last 182 @ 17:53 PDT) |
| Mode-check + in-window + ΔlnZ harvest | pending | ✅ this session (tables below) |
| Visual structural vet | pending | ✅ `/tmp/v2_harvest_vet.png` → `~/flits-runs/data/joint/_v2_harvest_20260719/` |
| Residual ladder vet (zach DSA) | pending | ✅ `zach_v2_ladder_vet.png` rendered; durable under `_v2_harvest_20260719/` |
| Two-screen lane PR + envelope write-up | teammate owes | ❌ still local-only on h17 worktree; provenance §5 still says PENDING |
| Rung-2 owner decision | pending | 📋 surfaced below |

## Automated Verification Results

### Job inventory (fresh disk read, 2026-07-19)

All outputs under `~/flits-runs/data/joint/`. Queue empty (`squeue` no jobs).

| Job | Burst | Config | lnZ | β | RC |
|----:|-------|--------|----:|--:|:--:|
| 169 | oran | C1D1 s2=10 | 13634.95 | 3.965 | 0 |
| 170 | oran | C2D1 s2=10 | 13625.93 | 3.806 | 0 |
| 171 | oran | C1D1 s2=100 | 13603.01 | 3.988 | 0 |
| 172 | oran | C2D1 s2=100 | 13603.16 | 3.929 | 0 |
| 173 | johndoeII | C1D2 s2=10 | 11725.69 | 3.799 | 0 |
| 174 | johndoeII | C2D2 s2=10 | 11723.33 | 3.748 | 0 |
| 175 | johndoeII | C1D2 s2=100 | 11679.91 | 3.866 | 0 |
| 176 | johndoeII | C2D2 s2=100 | 11678.68 | 3.519 | 0 |
| 177 | zach | C2D3 s2=10 fine | 25134.98 | 3.178 | 0 |
| 178 | zach | C2D3 s2=100 fine | 25074.60 | 3.165 | 0 |
| 179 | zach | C2D4 s2=10 fine | 26560.30 | 3.979 | 0 |
| 180 | zach | C2D4 s2=100 fine | 25064.50 | 3.166 | 0 |
| 181 | zach | C2D5 s2=10 fine | 26584.89 | 3.979 | 0 |
| 182 | zach | C2D5 s2=100 fine | 25081.73 | 3.161 | 0 |

### Count-step ΔlnZ (same prior-spec, same s2 only)

| Step | ΔlnZ | Δβ | Mode-check | Adjudication |
|------|-----:|----:|------------|--------------|
| oran C2−C1 s2=10 | **−9.0** | 0.16 | mild β drift | **C1 wins** |
| oran C2−C1 s2=100 | +0.1 | 0.06 | ok | null; C2 is ζ-runaway |
| johndoeII C2−C1 s2=10 | **−2.4** | 0.05 | ok | **C1 wins** |
| johndoeII C2−C1 s2=100 | **−1.2** | 0.35 | mode drift | **C1 wins**; C2 ζ=757 |
| zach D4−D3 s2=10 | +1425.3 | **0.80** | **MODE JUMP** | **INVALID** count BF |
| zach D5−D4 s2=10 | +24.6 | 0.00 | within ceiling family | not a D3 baseline |
| zach D4−D3 s2=100 | **−10.1** | 0.00 | continuous β≈3.16 | **D3 preferred** |
| zach D5−D3 s2=100 | +7.1 | 0.00 | continuous | weak; null high-ζ members remain |

### In-window / ghost structural check

| Burst | v1 ghost | v2 extra component | Verdict |
|-------|----------|--------------------|---------|
| oran C2 | t0_C1≈−5.2 ms off-window, fluence≈real | C2 t0 in-window; ζ=0.02 (s2=10) or **737** (s2=100) | ghost remediated → **C1D1** |
| johndoeII C2 | t0_C1≈−6.2 ms, fluence 26 vs 8 | C2 ζ=**90** / **757** | ghost remediated → **C1D2** |
| zach fine v1 | D1 at −8…−9 ms | all D t0 ∈ [0, 5.9] ms under v2 | off-window class fixed; count still not D4 |

Every v2 fit still has at least one high-ζ DSA “null-like” member on zach (ζ∼170–450).
That is residual model slack, not a clean extra physical pulse.

## Code Review Findings

- v2 clamp (PR #205) did what it was meant to: no off-window t₀ medians in this wave.
- Mode-trap class still active on zach s2=10 (ceiling β≈3.98 family with inflated lnZ).
  Guardrail “screen params continuous across count step” kills the +1425 D4 claim.
- Two-screen kernel + `TWOSCREEN_FITTER_PROVENANCE.md` still uncommitted on h17
  detached worktree (`d292f4b` + local dirty); Stage-0 envelope table not yet in §5
  (still “PENDING” despite 16/16 FAIL sealed in handoff).

## Manual Testing Required

1. **Owner: rung-2 charter decision** (charter §2–§3). Stage-0 FAIL wrong-sign on
   rung-1 met the pre-registered gate. Options:
   - **Charter rung-2** (independent β₂, Stage-0-first, ~6 injection fits, no real data
     until Stage-0 PASS) — only remaining mechanism that can flip deformation sign.
   - **Close two-screen lane** — accept elimination table as final for multi-screen
     exponential tails at this campaign scope.
2. Spot-check residual figure `zach_v2_ladder_vet.png` (cluster residuals remain;
   not resolved by D4/D5). Structural harvest figure sufficient for count verdicts.
3. Ratify production count drops (oran C1D1, johndoeII C1D2) before TOA table rewrite.

## Recommendations

### Critical
- Treat oran / johndoeII production C2 as **superseded ghosts**; rewrite TOA rows only
  after owner ratifies count drops.
- Do **not** publish zach s2=10 D4/D5 ΔlnZ; quote only mode-continuous s2=100 ladder.

### Important
- Land teammate two-screen PR: kernel + provenance with Stage-0 FAIL table (r-grid +
  W/τ envelope, all positive bias) + v1-label clause.
- Update jointtf-day2 deck slides 6 / 11 / 15 with harvest + Stage-0 envelope numbers.
- Close task #10 as **D3 stands under v2 fine binning**.

### Follow-up
- hamilton profiled-gain fallback + whitney rail (task #12).
- phineas re-run under v2 (neighbor story still suspect).
- Task #6 TOA table once count verdicts ratified.

## Verdicts (this harvest)

1. **oran → C1D1** (drop C2).
2. **johndoeII → C1D2** (drop C2).
3. **zach fine ladder → C2D3** on s2=100; owner D=4 not supported under v2.
4. **Stage-0 rung-1 FAIL** remains sealed; **rung-2 is the open owner decision**.

## References

- `docs/rse/specs/handoff/handoff-2026-07-19-16-33-jointtf-audit-twoscreen-stage0.md`
- `docs/rse/specs/notes/charter-two-screen-forward-model-2026-07-18.md`
- `docs/rse/specs/notes/report-jointtf-mechanism-closure-2026-07-18.md`
- h17: `COMPONENT_COUNT_LADDER_AUDIT.md` (append harvest section 2026-07-19)
- h17 products: `~/flits-runs/data/joint/_v2_harvest_20260719/`
