# Validation — Phase 6 (V6 association + DM_obs re-validation)

> Validated against `plan-trust-reset-revalidation.md` **Phase 6 only** (P6.1–P6.3)
> at Faber2026 commit `04232b7` on 2026-07-07. FLITS work validated in the
> isolated worktree `~/Developer/scratch/worktrees/flits-v6-phase6`
> (branch `agent/v6-dm-provenance-toa`, cut from pin `2d62ac8`). All evidence
> below is fresh output re-run for this validation — no checkmark or prior report
> was trusted.

**Scope:** this validates Phase 6 of a multi-phase plan. Phases 0–5 are out of
scope and unaffected.

**Verdict: PASS (automated). Owner follow-up on 2026-07-07 restored the
residual / P_cc / association-verdict columns under the shared-DSA-DM
convention.**

## 1. Implementation status

| Item | Status | Evidence |
|------|--------|----------|
| P6.1 anchor inventory | ✅ Complete | DSA DM origin (`bursts.yaml`, catalog, 0.1 placeholder err); CHIME origin (`chime_side_inputs.json`, arrival-time regression, 8/12 constrained); report reproduces at pin. In [v6-association-dm-report-2026-07-07.md](../notes/v6-association-dm-report-2026-07-07.md). |
| P6.2 DM provenance table | ✅ Complete | `crossmatching/dm_provenance.csv` — 12 rows, all method/source cells populated, **no UNDOCUMENTED**. `delta_dm_sigma` reconciled to `association.py` σ_eff floor (matches report `n_sigma`). |
| P6.2 agreement figure | ✅ Complete | `crossmatching/dm_agreement.png` → copied to `docs/rse/decks/dm/dm-campaign-2026-07/v6-dm-agreement.png`. |
| P6.2 failing test → green | ✅ Complete | `tests/test_dm_provenance.py` (plan spec verbatim); red without CSV, green with it. |
| P6.3 baseline oracles | ✅ Complete | 20 passed at the pin. |
| P6.3 re-derivation parity | ✅ Complete | Report re-derives value-identical; only `separation_deg` differed cross-machine at ≤4.65×10⁻¹⁶ (finding). |
| P6.3 re-derived association table | ✅ Complete | In the V6 report; all 12 pass position, 8 pass DM. |
| Finding-#2 fix (stale banner) | ✅ Complete | `association.py` `chime_dm_method` rewritten from "SUSPENDED" to the actual arrival-time-regression description; report regenerated; oracles green. |
| TOA residual column re-certified | ✅ Complete | Owner chose the shared-DSA-DM convention; `sample_table.tex` restores the residual / P_cc / verdict columns. |

## 2. Automated verification results (fresh)

- ✅ **P6.2 CSV regenerates + test green** — deleted the CSV, re-ran
  `build_dm_provenance.py` (12 rows; 8 agreement, 4 unconstrained), then
  `pytest tests/test_dm_provenance.py -q` → **1 passed**.
- ✅ **P6.3 baseline oracles** — `pytest tests/test_association.py
  tests/test_chime_singlebeam_toa.py tests/test_crossmatching_notebook_reproduction.py -q`
  → **20 passed**.
- ✅ **P6.3 re-derivation parity** — regenerated report vs committed: **0 differing
  fields** after this-machine regeneration (cross-machine: only `separation_deg`,
  max rel 4.65×10⁻¹⁶). Banner now reads the corrected method.
- ✅ **Full FLITS suite** — `pytest tests/ -q` → **129 passed, 2 skipped**
  (data-gated `test_flux_cal`, unrelated), 5 pre-existing warnings. No regression
  from the new test/scripts/banner change.
- ✅ **Faber2026 build** — `make` exits 0 (docs-only additions are not tex inputs).

Plan Phase 6 automated success criteria met: `test_dm_provenance.py` green,
existing suite green, `make` exits 0.

## 3. Code review findings (vs plan)

**Matches the plan:**
- CSV carries exactly the required columns plus `dm_confidence`/`note`; test
  contract (`REQUIRED ⊆ header`, 12 rows, non-empty method/source) satisfied.
- `build_dm_provenance.py` joins `chime_side_inputs.json` × `bursts.yaml`,
  documents method/source per side, computes ΔDM and σ — the P6.2 spec.
- Re-derivation follows P6.3: baseline oracles, then diff regenerated report
  against committed.

**Deviations (deliberate, each an improvement over a literal reading):**
1. **σ convention reconciled.** The plan says `delta_dm_sigma` "quantifies
   agreement"; a raw statistical σ would report zach at −8.3σ (artifact of the
   0.1 placeholder). Aligned to the pipeline's own `σ_eff = max(quadrature, 1.0
   floor)`, so the CSV matches `association_report.json` `n_sigma`. **Coherent
   with existing pipeline, not a new convention.**
2. **TOA residual column restored after owner decision.** The validation pass
   initially withheld it pending the dispersion-reference decision (§4). Owner
   follow-up chose the shared-DSA-DM convention and authorized surfacing the
   residual / P_cc / verdict columns.

**New findings surfaced (in the V6 report):**
- DSA DM error is a 0.1 placeholder (governs every σ).
- CHIME reads systematically ~0.36 pc cm⁻³ below DSA (coherent, sub-floor).
- `separation_deg` serialized at full float repr → cross-machine ULP churn.
- Off-repo h17 CHIME extraction artifacts unpinned.
- **Gitignore gap (new, this validation):** `crossmatching/dm_provenance.csv`
  (`*.csv`) and `dm_agreement.png` (`*.png`) are globally gitignored in FLITS.
  The test reads the CSV as a committed artifact, so a fresh clone / CI would
  fail unless the CSV is `git add -f`'d or a regeneration step runs before the
  test. **Must be resolved when the FLITS branch is committed.**

## 4. Design decision — dispersion reference (owner-confirmed) + joint DM fit

**Owner decision (this session):** keep the **DSA DM as the shared reference**;
report CHIME–DSA agreement separately (as P6.2 does). This is implemented.

**Joint DM-fit feasibility** (owner asked; Codex consulted as reference —
`logs/codex-jointdm.json`). Fitting DM from a stitched CHIME+DSA time–frequency
spectrum is scientifically attractive but is **new methods work**, gated by:
- **DM↔dt rank degeneracy** — with one effective TOA per telescope,
  `delay = K_DM·DM·Δ(ν⁻²) + dt` is rank-degenerate. Well-posed only with multiple
  frequency-resolved sub-band TOAs (which the 4 CHIME-unconstrained bursts lack).
- **Clock calibration** — an unknown ~1 ms inter-telescope offset maps to
  ~0.04 pc cm⁻³ in DM, the same scale as the sought improvement; geometry is
  computable but the residual clock/instrument delay needs a strong prior.
- **Profile evolution/scattering** across the ~700 MHz gap can make a naive fit
  measure morphology, not DM.
- **Building blocks exist** (`analysis/scattering-refit-2026-06/fullband_aligned.py`
  aligns the two bands via fitted t0 + geometric delay + clock term;
  `scattering/scat_analysis/burstfit_joint.py` shares sightline params;
  `dispersion/chime_dm.py` does sub-band arrival regression) — but there is **no
  joint (DM, dt) fitter**, and `JOINT_FIT_STATE.md:21-29` deliberately leaves t0
  free per telescope ("Don't model delay"), so it is not DM/dt-identifying today.

**Recommendation:** defer the joint fit; it would add clock-calibration and
profile-evolution systematics harder to defend than the current "reference DM +
independent agreement check" story. Revisit as a dedicated methods effort if a
future paper can absorb the validation ladder. This **keeps the TOA residual on
the shared-DSA-DM convention**; the owner authorized surfacing those numbers in
the manuscript after this validation.

## 5. Manual testing required (human)

- [ ] Spot-check the `dm_provenance.csv` CHIME values against h17 (or via the
      h17-ssh-troubleshooter lane) — the extraction artifacts are off-repo.
- [ ] Review the systematic CHIME-low offset (~0.36 pc cm⁻³) — is it worth a
      manuscript sentence?

## 6. Recommendations

**Resolved in FLITS commit `9175b92`:**
- The gitignore gap for `dm_provenance.csv` and `dm_agreement.png` was fixed by
  force-adding both artifacts with the V6 branch commit.

**Important:**
- Push/merge the FLITS branch `agent/v6-dm-provenance-toa` upstream after review.
- Pin/checksum the off-repo h17 CHIME extraction artifacts (completes CHIME
  provenance).

**Nice to have:**
- Round `separation_deg` on write in `build_association_report` to kill the
  cross-machine ULP churn (finding #6).

**Follow-up (future paper):**
- Joint (DM, dt) cross-telescope fitter — see §4; new methods work.

## References

- [plan-trust-reset-revalidation.md](../plan/plan-trust-reset-revalidation.md) — Phase 6 spec (P6.1–P6.3).
- [v6-association-dm-report-2026-07-07.md](../notes/v6-association-dm-report-2026-07-07.md) — the V6 deliverable report.
- [dm-provenance-audit-2026-07-07.md](../dm/dm-provenance-audit-2026-07-07.md) — sibling DM audit (codex).
- `logs/codex-jointdm.json` — joint DM-fit feasibility reference (Codex, read-only).
