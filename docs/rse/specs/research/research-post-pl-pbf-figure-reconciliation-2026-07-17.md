# Research: post-PL-PBF joint-fit figure reconciliation

**Date:** 2026-07-17
**Manuscript base:** `a9b881a35bee0a65f453dff9b5aa1455747fa64a`
**Reviewed pipeline pin:** `17d9d26675702e9f8917da655621bef3231f0ddb`

## Question

Do trustworthy post-PL-PBF production artifacts exist for the compiled Whitney
triptych and the six appendix joint-model grids, or must the pre-PL-PBF figures
be suppressed?

## Evidence

- The reviewed pin contains the beta-native production code and the automatic
  time-frequency preparation merged through FLITS PRs #193 and #197, but not a
  committed full-roster production result set or regenerated panels.
- A live read-only audit of `/central/scratch/jfaber/flits-runs/data/joint` on
  HPCC found eleven expected-tag fit JSONs dated 2026-06-19 through 2026-06-23.
  Every one lacks a `beta` posterior and is therefore alpha-era/pre-PL-PBF; the
  expected Whitney C2D2 JSON is absent.  The matching model dumps are explicitly
  tagged `pbf-exp-exp`.
- No joint/PL-PBF production jobs were running during the audit.  The h17 host
  has no `/central/scratch/jfaber/flits-runs/data/joint` store.
- The local scratch store contains one Whitney
  `pbf-powerlaw-powerlaw` JSON dated 2026-06-26, but it has no commit or creation
  metadata and no matching dump or panel.  It is neither a complete campaign nor
  a promotion candidate.
- The separate `joint/tf-fit-window-resolution` worktree contains additional
  producer development, including a standalone inner-scale PL-PBF injection
  harness.  That harness states that production integration is a later gated
  step; the worktree is unreviewed for this manuscript pin and currently dirty.

## Conclusion

No exact, provenance-backed post-PL-PBF replacement set exists.  The only safe
manuscript action is to disconnect the stale Figure 2 and Figures 11--16 inputs,
retain their historical source and bytes, mark their manifest rows unembedded,
and state the exact production/refit/review blocker.  Old artifacts must not be
relabeled or promoted.
