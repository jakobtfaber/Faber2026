# Validation: repository content audit

**Date:** 2026-07-22
**Plan:** [repository content audit](plan-repository-content-audit-2026-07-22.md)
**Implementation:** [implementation record](implement-repository-content-audit-2026-07-22.md)

## Verdict

Automated criteria pass. Manual owner review of archived sign-bug figures is
optional; the source handoff already records the defect.

## Fresh Evidence

- `pytest` analysis archive, knowledge-base, results-library, and registry-link
  tests: 23 passed.
- `pytest` pipeline archive, joint-summary reproducibility, and attribution
  tests: 15 passed; 20 pre-existing Astropy deprecation warnings.
- Ruff on every changed Python/test file: passed.
- Knowledge-base rebuild and search: passed.
- Populated database after rebuild: 3,398 documents; 14,278 chunks.
- External archive link resolves to
  `analysis/.archive/outdated-science/2026-07-17`.
- Active-path scan finds no former dated-quarantine path or sign-bug filename,
  excluding immutable historical receipts and `.archive/` itself.

## Scope Boundary

No scientific result was promoted, recalculated, or newly trusted. No
manuscript text or submodule pin changed. Intentional provenance duplication
remains.
