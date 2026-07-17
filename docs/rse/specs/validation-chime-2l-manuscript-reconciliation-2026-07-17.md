# Validation: CHIME 2L manuscript reconciliation

---
**Date:** 2026-07-17
**Result:** Parent manuscript change validated
**Plan:** [plan-chime-2l-manuscript-reconciliation-2026-07-17.md](plan-chime-2l-manuscript-reconciliation-2026-07-17.md)
**Implementation:** [implement-chime-2l-manuscript-reconciliation-2026-07-17.md](implement-chime-2l-manuscript-reconciliation-2026-07-17.md)
---

## Automated evidence

| Check | Result |
|---|---|
| Clean-Conda generated-output rebuild and `--check` | pass |
| `pytest -q tests/test_scintillation_campaign_manuscript.py` | 5 passed |
| `make test-science` | 137 passed, 1 xfailed |
| `python scripts/consistency_audit.py` | clean |
| `python scripts/sync_state.py --check --offline` | pass |
| `python scripts/figure_review.py verify` | pass |
| `latexmk -C` then strict `latexmk -pdf` | pass, 53 pages |

The expected failure is the pre-existing association-diagnostics test for the
class-aware lane absent from the rewritten FLITS history. It is unrelated to
the scintillation pin and is explicitly marked `xfail` by the repository.

## Manual evidence

Rendered pages 22--24 were inspected after the clean rebuild. The placeholder
is legible, names both telescopes and bursts, and contains no stale DSA-only
plot. The four CHIME measurements fit without overflow, and the campaign table
uses the repository's AASTeX `deluxetable*` pattern with compact gate codes.

## Remaining gate

The joint DSA+CHIME summary is a candidate-only artifact. Its exact PDF bytes
must be reviewed and approved by the manuscript owner in a later promotion PR;
the current manuscript intentionally compiles the placeholder instead.
The upstream Results Library documentation follow-up is ready for review as
dsa110-FLITS PR #199, merged as `8f5f06a4`, and is deliberately not part of the
parent science pin.

## Candidate-only figure validation

The immutable batch
`figure_review/batches/2026-07-17-joint-scintillation-qualified-and-chime-acf`
contains 25 pending candidates: one two-panel qualified-measurement summary and
24 standard/high-resolution CHIME ACF diagnostics. All 24 diagnostic hashes
match the PR #192 `figures.review.json`; the packet freezes the campaign
validation, JSONL records, Chromatica measurement, figure-review verdicts, Oran
qualification, and generator provenance. After rebasing onto `origin/main` at
`341e2200`, the shared review registry and CLI preserve both the Figure 1 and
joint-scintillation candidate families and their separate evidence rules.
Focused loader/approval tests pass (12 tests), the full science suite passes
(139 passed, 1 expected xfail), packet validation, consistency, offline state
sync, and the figure gate pass, and a clean strict LaTeX rebuild produces 47
pages. The summary, representative ACF panels, and contact sheet were inspected
visually.

No post-finalization DSA ACF campaign exists at pipeline pin `17d9d266`.
Consequently the packet does not claim that its CHIME-only diagnostic panels
replace the owner-removed joint appendix gallery. That replacement remains
blocked on new DSA products and exact-byte owner review.
