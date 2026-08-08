# Receipt: family 5 — scintillation branch verdict (2026-07-26)

**Objective/phase:** second family of the branch-landing roster
(`roster-branch-landing-2026-07-26.md`), owner-chartered ("Proceed with
family 5"). Single branch: dsa110-FLITS
`codex/chromatica-cross-band-scintillation` (4 unabsorbed commits, head
`3feb82ec`).

## Verdict: SUPERSEDED — nothing to land

Evidence, all read from producing artifacts this session:

1. **PR #200 was closed unmerged with a full preservation audit** (final
   PR comment, audit against `origin/main` = `b69dea16`, head =
   `3feb82ec`). The audit's conclusions, per component: the result JSON,
   plots, runners, reports, and cross-band fitter are diagnostic;
   `rigorous_campaign.py` encodes campaign-specific scientific choices,
   not reusable infrastructure; the `acf_covariance.py` wrapper and the
   `window_refit.py` payload plumbing have no consumer outside the
   draft's own runner; the tests exercise those same assumptions. Its
   explicit finding: "No scientifically neutral subset can be isolated
   without retaining campaign-specific assumptions. Therefore no
   replacement PR is opened."
2. **The scientific result is superseded.** The branch's campaign
   admitted 0/4 CHIME and 0/4 DSA scintillation measurements for
   Chromatica. The later, independently merged window-tuning campaign
   (PR #192, injection-validated) and its two-component successor
   (`window_campaign_2L`, false-positive rate 0/150) produce the
   authoritative table, with Chromatica measured 4/4 in both products.
3. **The code path is superseded.** Main already carries the merged
   window-campaign implementation; the branch's parallel interface would
   add a second unsupported path (audit point, re-confirmed: the branch's
   `window_refit.py` changes conflict with the merged design).

## Disposition

No landing PR. The branch remains preserved on origin at its recorded
head `3feb82ec`. Retirement of the branch is a separate
Tier-2-gated step, not performed here. Family 5 is closed.
