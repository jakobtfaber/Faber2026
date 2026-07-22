# Count-audit remediation: evidence review and owner decision packet

**Status:** review packet; human decision pending  
**Scope:** Wayfinder ticket 15 only  
**Repositories checked:** `Faber2026-analysis` `84b84cc638fdad46164b705e7de50e8c609c30e5`; `dsa110-FLITS` `f3c8d22a9088914e0179cfecf1ee4086777dc927`  
**Scientific effect:** none. No component count, fit, table, figure, ticket, or map state changed.

## Recommendation

Adopt the fixed-gain-variance neighboring-count comparison as a **necessary
validation step**, with the guards below. Do not use it as a count setter by
itself. Do not adopt any pending count change from the reviewed artifacts.
Owner morphology remains admissible input, but it must be recorded separately
from the numerical comparison and verified by a mode-matched fit.

Treat this method as a stopgap implementation aid for the profile-component
count statistic in ticket 05, not as that statistic's completed realization.
Ticket 05 still needs a sample-wide, injection-calibrated definition of what
constitutes a resolved component.

## Evidence boundary

The committed evidence packet is
`docs/rse/specs/validation/evidence/jointtf-v2-harvest-2026-07-19/manifest.json`.
Its canonical content, excluding its generation timestamp, has SHA-256
`363c8589868c32cebd260b403aaea3d4b5567bef1007745709079d5106ad6b56`.

A fresh read-only h17 harvest initially failed because the fit products moved
from the active results directory into the 2026-07-22 trust-reset archive.
Re-running the same harvester against the archive recovered:

- 14 of 14 successful job logs;
- all 56 job artifacts, six configurations, six inputs, six executed-code
  files, and two review figures;
- identical SHA-256 and byte size for every recovered item;
- identical numerical comparisons and fit-window checks;
- all component-time medians and central intervals inside the logged windows.

This verifies the preserved bytes and arithmetic. It does not make the fits
science-ready. No sampler seed was recorded; two executed files were modified
and one was untracked; hashes taken later cannot prove the exact runtime code;
and the archived products are explicitly revoked pending the current evidence
contract.

## Comparison rules

The quantity below is the difference in log model evidence between a model
with one extra component and its neighbor. A positive value favors the extra
component. The old `>5` rule is insufficient without these guards:

1. Compare only the same data bytes, frequency and time binning, fit window,
   pulse-broadening family, prior version, gain-prior variance, and sampler
   contract.
2. Prove before fitting that the window contains every candidate component.
   Prove after fitting that every component-time prior and posterior remains
   inside that window.
3. Save a reconstructable model product. A fit whose window cannot be replayed
   cannot support a count verdict.
4. Require the shared screen and nuisance solution to remain in the same mode
   across the count step. Non-overlapping central intervals, a large jump in
   the turbulence index or scattering time, or a different residual family
   makes the evidence difference a mode comparison, not a count comparison.
5. Require the same direction at both predeclared proper gain-prior variances
   (`s2=10` and `s2=100`). Require the evidence difference to exceed `+5`
   after allowing for the reported numerical uncertainty.
6. Require the added component to coincide with a candidate feature, have
   bounded non-null amplitude, and improve the local residual. Reject ghost,
   pedestal, unresolved, duplicated, or label-swapped components.
7. Require at least one independent repeat or seed before promotion. Record the
   owner visual morphology decision separately; it cannot rescue a failed
   numerical guard, and a numerical pass cannot waive visual review.
8. Never compare profiled-gain evidence with fixed-gain-variance evidence,
   different prior versions, or different pulse-broadening families.

## Fresh arithmetic and admissibility

### Prior-version-2 jobs 169--182

| Sightline and step | `s2=10` | `s2=100` | Mode continuity | Admissible count result |
|---|---:|---:|---|---|
| oran, C2 minus C1 | -9.01 +/- 0.80 | +0.15 +/- 0.77 | fails in both arms | none |
| johndoeII, C2 minus C1 | -2.36 +/- 0.92 | -1.23 +/- 0.91 | passes at 10; fails at 100 | none |
| zach, D4 minus D3 | +1425.33 +/- 1.06 | -10.10 +/- 1.01 | fails at 10; passes at 100 | none |
| zach, D5 minus D4 | +24.59 +/- 1.05 | +17.23 +/- 1.13 | nominally continuous | none; lower rung changes mode and D5 contains weak or unresolved members |
| zach, D5 minus D3 | +1449.91 +/- 1.02 | +7.13 +/- 1.12 | fails at 10; passes at 100 | none |

Interpretation:

- **oran:** the two gain-prior arms disagree and both count steps move the
  turbulence-index solution. The extra CHIME component is not established;
  neither is the proposed drop to C1 without the owner morphology review.
- **johndoeII:** neither arm reaches the evidence threshold. The `s2=100`
  comparison changes mode. The current evidence supports no count change.
- **zach:** the spectacular `s2=10` D4 result is a steep-mode jump, not evidence
  for a fourth component. The mode-continuous `s2=100` D4 step favors D3, but
  the D5 ladder is non-monotonic and includes broad or near-null members.
  These fits do not adjudicate the owner's four-feature morphology.

### Earlier prior-version-1 neighbors

The archived earlier grid reproduces the recorded numbers but is not eligible
for count adoption:

- **phineas:** at `s2=100`, C4D3 minus C3D3 is `+75.44` and C3D4 minus
  C3D3 is `+26.47`. Both steps move the turbulence index from about `3.15` to
  about `3.02`, only one gain-prior arm exists, and the old window evidence is
  incomplete. C4D4 is lower than C4D3 by `15.54`. Reject the proposed C4 and
  D4 adoption from this grid.
- **johndoeII:** the older reported C3 `+47` step was already rejected because
  scattering time ran from about `0.114` to `2.25` ms. That is a mode change.
- **whitney:** the `s2=10` C2D2 fit has off-window ghost components. Across the
  remaining grid, count steps change sign or move between turbulence-index
  modes. The apparent C2 and D2 evidence therefore cannot establish C2D2.
  Keep the owner's two-feature morphology as a provisional target for a clean,
  mode-matched validation; do not present the old evidence as its proof.

## Invalid comparisons to prohibit

- profiled or flat-gain evidence versus any fixed-`s2` evidence;
- `s2=10` versus `s2=100` as though their evidence difference selected a count;
- prior-version 1 versus prior-version 2;
- mixed versus all-exponential pulse-broadening families;
- coarse versus fine binning without a separately calibrated resolution model;
- any rung with an off-window component or without a saved replayable window;
- any neighboring-count step that jumps between screen modes;
- any high-count result whose added component is null, unresolved, or not the
  candidate morphology the test was intended to assess.

## Minimal owner decision

**Recommended decision:** accept the guarded neighboring-count procedure as a
temporary validation method; accept none of the proposed count changes; retain
all affected counts as pending until clean, mode-matched, two-arm comparisons
and owner morphology review agree. Direct ticket 05 to turn these guards into
an injection-calibrated sample-wide statistic rather than treating the current
protocol as the finished statistic.

Owner choices:

- **Accept recommendation:** method adopted as temporary validation; no count
  changes; ticket 05 remains the permanent-statistic lane.
- **Amend:** name the specific count to adopt and the owner morphology evidence
  that overrides the incomplete numerical packet. The manuscript and production
  tables remain unchanged until a clean validation fit confirms that choice.

Ticket 15 remains open until this human-in-the-loop decision is recorded.

## Verification performed

- Recomputed every jobs 169--182 evidence difference and uncertainty from the
  freshly read archived JSON files.
- Rechecked central turbulence-index interval overlap for every comparison.
- Recomputed the earlier phineas and whitney fixed-variance grids from archived
  JSON files.
- Confirmed current archive byte parity with the committed manifest by basename,
  SHA-256, and size.
- Ran the pulse-broadening-family separation self-check and fixed-gain commensurability tests.
