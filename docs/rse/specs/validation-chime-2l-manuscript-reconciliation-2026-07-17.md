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
| `make test-science` | 130 passed, 1 xfailed |
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
