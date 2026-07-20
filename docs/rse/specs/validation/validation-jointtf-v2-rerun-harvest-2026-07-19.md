# Validation: JointTF v2 re-run harvest, jobs 169–182

> Independently re-harvested against
> `handoff-2026-07-19-16-33-jointtf-audit-twoscreen-stage0.md` at Faber2026
> commit `b5d593cd` on 2026-07-19. Remote evidence: h17 worktree `d292f4b`
> plus dirty/untracked executed code. Prior-spec: v2 window-bounded t₀.

## Overall Status: Candidate verdicts supported; owner adoption pending

- Jobs: 14/14 present; 14/14 logs end `RC=0`.
- Products: 14/14 JSON and sample-archive pairs present and hashed.
- Fit-window check: every t₀ median and central interval is inside its band window.
- Figures: both reviewed full-size; local copies match remote SHA-256 hashes.
- Reproducibility: harvest reproducible; original fits not exactly rerunnable.
- Owner gates: count adoption and rung 2 remain open. No production changes made.

## Implementation Status

| Item | Status | Fresh evidence |
|---|---|---|
| Jobs 169–182 completion | Validated | All 14 endpoint logs end `RC=0`; queue empty at live check. |
| Numerical harvest | Validated | Re-extracted from 14 JSON files; arithmetic below. |
| Structural checks | Validated | All t₀ central intervals inside logged windows; ζ diagnostics extracted. |
| Visual check | Validated, bounded | Both preserved PNGs reviewed; findings below. |
| Count dispositions | Decision pending | Evidence supports candidates; owner has not adopted them. |
| Original-fit reproducibility | Incomplete | No seeds; executed code includes modified and untracked files. |
| Rung-1 two-screen closure | Incomplete | Separate provenance remains local-only on h17. |
| Rung 2 | Not authorized | Explicit owner gate; no launch performed. |

## Automated Verification Results

### Passing checks

- `python3 -m py_compile scripts/revalidate_jointtf_v2_harvest.py` — pass.
- Fresh manifest generation over live SSH — 14 jobs; all return codes zero;
  all JSON/sample pairs present; all t₀ medians and central intervals in-window.
- `python3 -m json.tool .../manifest.json` — pass.
- Six input arrays, six run configurations, 14 logs, 14 JSON files, 14 sample
  archives, executed code, job scripts, and both figures are SHA-256 bound in
  `docs/rse/decks/scintillation/jointtf-v2-harvest-2026-07-19/manifest.json`.

### Fresh fit extraction

| Job | Fit | lnZ ± fit error | β median | Return |
|---:|---|---:|---:|:---:|
| 169 | oran C1D1 s2=10 | 13634.947 ± 0.561 | 3.965 | 0 |
| 170 | oran C2D1 s2=10 | 13625.933 ± 0.576 | 3.806 | 0 |
| 171 | oran C1D1 s2=100 | 13603.009 ± 0.548 | 3.988 | 0 |
| 172 | oran C2D1 s2=100 | 13603.158 ± 0.542 | 3.929 | 0 |
| 173 | johndoeII C1D2 s2=10 | 11725.690 ± 0.612 | 3.799 | 0 |
| 174 | johndoeII C2D2 s2=10 | 11723.327 ± 0.685 | 3.748 | 0 |
| 175 | johndoeII C1D2 s2=100 | 11679.909 ± 0.641 | 3.866 | 0 |
| 176 | johndoeII C2D2 s2=100 | 11678.678 ± 0.648 | 3.519 | 0 |
| 177 | zach C2D3 s2=10 | 25134.978 ± 0.730 | 3.178 | 0 |
| 178 | zach C2D3 s2=100 | 25074.597 ± 0.708 | 3.165 | 0 |
| 179 | zach C2D4 s2=10 | 26560.305 ± 0.774 | 3.979 | 0 |
| 180 | zach C2D4 s2=100 | 25064.495 ± 0.726 | 3.166 | 0 |
| 181 | zach C2D5 s2=10 | 26584.890 ± 0.705 | 3.979 | 0 |
| 182 | zach C2D5 s2=100 | 25081.728 ± 0.869 | 3.161 | 0 |

### Recomputed count steps

Uncertainty is the two reported lnZ errors added in quadrature. “β overlap” asks
whether the two central β intervals overlap; it is a mode-continuity diagnostic,
not a scientific acceptance rule by itself.

| Step | ΔlnZ ± error | Δβ | β overlap | Evidence reading |
|---|---:|---:|:---:|---|
| oran C2−C1 s2=10 | −9.014 ± 0.804 | −0.160 | no | C2 disfavored; mode differs. |
| oran C2−C1 s2=100 | +0.149 ± 0.771 | −0.059 | no | Null evidence; added C2 has ζ≈737. |
| johndoeII C2−C1 s2=10 | −2.364 ± 0.919 | −0.051 | yes | C2 disfavored. |
| johndoeII C2−C1 s2=100 | −1.231 ± 0.912 | −0.347 | no | C2 disfavored; mode differs; ζ≈757. |
| zach D4−D3 s2=10 | +1425.327 ± 1.064 | +0.801 | no | Mode jump; invalid count comparison. |
| zach D5−D4 s2=10 | +24.586 ± 1.047 | −0.000 | yes | Same ceiling-β family; not a D3 comparison. |
| zach D4−D3 s2=100 | −10.102 ± 1.015 | +0.001 | yes | D4 disfavored. |
| zach D5−D3 s2=100 | +7.130 ± 1.121 | −0.004 | yes | Numerical gain, but D5 contains a ζ≈337 null-like member. |

## Code Review Findings

### What the evidence supports

- v2 removed the off-window class: all component central t₀ intervals lie
  inside the logged CHIME/FRB or DSA-110 fit windows.
- oran: C2 loses strongly on s2=10 and is null on s2=100 with a high-ζ extra
  component. Candidate disposition: C1D1.
- johndoeII: C2 loses on both arms; its extra component has ζ≈90 or ζ≈757.
  Candidate disposition: C1D2.
- zach: s2=10 crosses β modes and cannot supply a count Bayes factor. On s2=100,
  D4 loses to D3. D5 gains lnZ but includes a null-like member, failing the
  resolved positive-power structural condition. Candidate disposition: C2D3.

### Visual review

- `v2_harvest_vet.png`: no plotted central interval crosses a window boundary.
  High-ζ extra components are visible for oran, johndoeII, and every zach count.
- `zach_v2_ladder_vet.png`: residual structure near the main pulse and the
  3.5–4.5 ms cluster persists across D3/D4/D5. Added components do not produce
  a clean, stable resolution; null-like components move between rungs.
- The figures validate structural diagnostics only. They do not establish a
  unique physical component count.

### Reproducibility gaps

- Dynesty was called without `rstate`; no seed appears in logs or JSON.
- Executed paths are not commit-bound: `joint_tf_prep.py` and
  `burstfit_joint.py` are modified; `run_joint_fit_zachfine.py` is untracked.
- Current hashes and mtimes are captured, but cannot prove byte identity at job
  start for those uncommitted paths.
- The exact conda package list and input hashes are captured. No clean rerun was
  attempted because missing seeds and non-versioned executed code prevent exact
  reproduction; rerunning now would be a new stochastic experiment.
- Therefore: existing-result harvest is reproducible; fit generation is not.

## Manual Testing Required

1. Owner spot-check and ratify, reject, or defer the three candidate counts:
   oran C1D1; johndoeII C1D2; zach C2D3.
2. Reconstruct and commit the executed v2 code before any new fit wave. Add an
   explicit sampler seed and persist it in each result.
3. Independently close the rung-1 two-screen code/provenance lane. Its Stage-0
   claim was not revalidated in this harvest.
4. Separately decide whether to charter independent β₂. This validation does
   not authorize rung 2.

## Recommendations

### Critical

- Do not rewrite production or time-of-arrival tables before owner ratification.
- Do not publish the zach s2=10 D4/D5 evidence steps.
- Do not call jobs 169–182 exactly reproducible.

### Important

- Use the manifest and preserved figures as the evidence packet for owner review.
- Land clean, versioned fitting code with seed capture before further production fits.

### Follow-up

- After owner count decisions: handle production-table changes in a separate lane.
- Rung 2 remains a separate owner decision; no launch occurred here.

## References

- Recovery handoff: `../handoff/handoff-2026-07-19-23-24-jointtf-grok-harvest-revalidation.md`
- Handoff: `../handoff/handoff-2026-07-19-16-33-jointtf-audit-twoscreen-stage0.md`
- Decision: `../decision/decision-two-screen-charter-2026-07-18.md`
- Evidence: `../../decks/scintillation/jointtf-v2-harvest-2026-07-19/README.md`
- Manifest: `../../decks/scintillation/jointtf-v2-harvest-2026-07-19/manifest.json`
- Remote audit: h17 `COMPONENT_COUNT_LADDER_AUDIT.md`, lines 132–180
