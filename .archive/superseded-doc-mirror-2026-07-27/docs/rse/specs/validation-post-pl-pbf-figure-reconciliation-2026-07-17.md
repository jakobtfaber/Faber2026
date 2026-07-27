# Validation: post-PL-PBF joint-fit figure reconciliation

Validated against
`plan-post-pl-pbf-figure-reconciliation-2026-07-17.md` and
`implement-post-pl-pbf-figure-reconciliation-2026-07-17.md` at commit
`9942727` on 2026-07-17.

## Implementation Status

1. **Pinned provenance audit — complete.** The manuscript base is `a9b881a3`
   and the submodule remains at reviewed pin `17d9d266`. Live local/HPCC/h17
   inspection found no complete post-PL-PBF production result set.
2. **Replacement gate — complete, failed closed.** The HPCC expected-tag files
   are June alpha-era fits without beta posteriors, Whitney C2D2 is missing,
   and the only local power-law JSON lacks a commit pin, dump, and panel.
3. **Compiled suppression — complete.** The representative triptych and six
   appendix grids are unreachable from the compiled TeX graph. Historical
   source and artifact bytes remain present.
4. **Provenance/docs — complete.** Both manifest families are unembedded and
   marked `superseded_pre_pl_pbf`; manuscript prose, the sweep checklist, and
   `REPRODUCE.md` name the complete refit/dump/review blocker.
5. **Regression coverage — complete.** A focused test guards TeX reachability,
   source retention, manifest state, reviewed-pin notes, and the full gate
   wording in Observations.

## Automated Verification Results

- PASS — `uv run --project pipeline --frozen python -m pytest -q -ra
  --strict-config --strict-markers tests/test_pl_pbf_figure_suppression.py
  tests/test_consistency_audit.py`: 17 passed.
- PASS — `uv run --project pipeline --frozen python -m pytest -q -ra
  --strict-config --strict-markers tests`: 143 passed, 1 expected xfail.
- PASS — `uv run --project pipeline --frozen python
  scripts/consistency_audit.py`: `F3 consistency audit: clean`.
- PASS — `python3 scripts/sync_state.py --check --offline`: 3/3 views match;
  rules pass; offline check passes.
- PASS — `python3 scripts/figure_review.py verify`: figure approval gate OK.
- PASS — `bash tests/test_journal_append.sh`.
- PASS — `latexmk -C`, followed by `latexmk -g -pdf
  -interaction=nonstopmode -halt-on-error main.tex`: clean 40-page PDF,
  8,859,307 bytes.
- PASS — the rebuilt `main.fls`, `main.aux`, `main.log`, and `main.out` contain
  no reference to `codetection_triptychs.tex`, `jointmodel_pairs.tex`, or the
  suppressed joint-fit figure directories. The compiled figure sequence now
  contains nine figures, numbered 1 through 9.
- PASS — extracted PDF text contains the post-PL-PBF production-refit blocker
  in Observations, Results, and Appendix F.

## Code Review Findings

- The implementation matches all five plan steps.
- No old artifact was copied, renamed, relabeled, or promoted.
- The source inventory discrepancy is explicit: the owner checklist described
  twelve panels, while the historical compiled source contains eleven retained
  per-burst panels because Chromatica has no retained joint fit.
- The submodule gitlink is unchanged and its detached reviewed checkout is
  clean.
- No critical or important implementation issue was found.

## Manual Testing Required

None for this suppression change. Exact-byte manuscript-owner review remains a
future promotion gate for newly generated replacement panels; no replacement
candidate exists in this change.

## Recommendations

- **Critical:** none.
- **Important follow-up:** run the complete twelve-burst post-PL-PBF production
  campaign at a reviewed FLITS commit, emit matching model dumps, and bind a
  candidate packet to exact output hashes before restoring any panel.
- **Nice to have:** include fit commit, configuration, seed/sampler settings,
  input hashes, dump hashes, and panel hashes in the future campaign manifest.

## References

- [Plan](plan-post-pl-pbf-figure-reconciliation-2026-07-17.md)
- [Implementation](implement-post-pl-pbf-figure-reconciliation-2026-07-17.md)
- [Research](research-post-pl-pbf-figure-reconciliation-2026-07-17.md)
