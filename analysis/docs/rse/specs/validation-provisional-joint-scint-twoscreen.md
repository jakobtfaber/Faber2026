# Validation: provisional joint fits, DSA bandwidths, and two-screen analysis

Validated against `plan-provisional-joint-scint-twoscreen.md` at implementation
commit `02f43b29` on 2026-07-15. This report also covers the validation-time
generator whitespace correction committed with the report.

## Implementation Status

- **Phase 1 — tested numerical core: PASS.** The standard-library generator and
  focused analytic, scaling, verdict, foreground-classification, and frozen-roster
  tests are present and pass.
- **Phase 2 — generated products: PASS.** The generator reproduces the four TeX
  tables and the machine-readable result ledger byte-for-byte. The ledger contains
  12 DSA rows through the table product, 12 joint-fit rows, seven screen-analysis
  rows, 12 foreground-alignment rows, the exact build command, and SHA-256 hashes
  for every frozen input.
- **Phase 3 — manuscript integration: PASS.** The representative and appendix
  figures and all generated tables compile from the intended manuscript include
  chain. Captions and prose preserve the provisional/not-certified boundary.
- **Phase 4 — foreground-census alignment: PASS.** The complete twelve-sightline
  ledger retains coverage, deduplicated foreground count, nearest inconclusive
  impact parameter, fitted and foreground scattering, diagnostic ratio, and the
  bounded non-causal interpretation.
- **Phase 5 — verification: PASS.** All automated and manual checks below pass.

## Automated Verification Results

- **PASS** — `python3 -m pytest -q tests/test_provisional_propagation.py`:
  5 passed.
- **PASS** — `python3 scripts/build_provisional_propagation_tables.py`: exited
  zero; a subsequent path-scoped `git diff --exit-code` found no generated drift
  before the validation-only whitespace correction.
- **PASS** — `make test-science`: 83 passed, 1 expected xfail.
- **PASS** — `python3 scripts/consistency_audit.py`: clean.
- **PASS** — `python3 scripts/figure_review.py verify`: all protected figure
  bytes match their approval receipts.
- **PASS** — clean temporary virtual environment: the generator reran and the
  five focused tests passed using a newly created Python 3.13 venv with only
  pytest installed.
- **PASS** — `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex`:
  forced rebuild produced a 53-page PDF.
- **PASS after correction** — `git diff --check origin/main...HEAD` initially
  found trailing spaces emitted after TeX row terminators and an extra blank EOF
  line. The emitter was corrected, all generated tables were regenerated, and
  the commit-range check was rerun before publication.

## Code Review Findings

- The screen product uses the dimensionally correct
  `tau[ms] * Delta-nu[MHz] * 1000 = tau[s] * Delta-nu[Hz]` conversion and evaluates
  scattering at each actual component frequency.
- The two-screen-favored verdict is conservative: every retained component must
  remain above the single-screen upper bound at one propagated standard deviation.
- Foreground interpretation is fit-adjudication- and coverage-aware; coverage-limited
  zero-foreground rows are not treated as clean controls, and the emitted language
  does not claim causation.
- Full posterior covariance is unavailable. The generator, tables, ledger, and
  prose consistently label the first-order independent propagation approximate
  and the science products provisional.
- No unrelated, sensitive, submodule-pointer, cache, or credential-bearing path
  is part of the implementation commit.

## Manual Testing Required

Completed in this validation session by inspecting the rendered PDF:

- Tables 6–9 fit on their pages and remain legible.
- The representative joint residual, twelve-panel DSA summary, certified Oran
  qualification plot, twelve DSA ACF diagnostics, and eleven retained joint-fit
  diagnostics are readable and not clipped.
- Every promoted figure family carries a provisional/not-certified caveat in its
  first caption, with subsequent paired pages explicitly captioned “As above.”

No additional manual publication gate remains for this provisional lane.

## Recommendations

- **Critical:** none.
- **Important:** none before merge.
- **Follow-up:** preserve the provisional status until the V1 re-trust ladder and
  component-level certification work are completed; do not use this change to
  infer screen distances or a sample-wide foreground correlation.

## References

- [Implementation plan](plan-provisional-joint-scint-twoscreen.md)
- [Propagation research](research-provisional-joint-scint-twoscreen.md)
- [Foreground-alignment research](research-foreground-propagation-alignment.md)
