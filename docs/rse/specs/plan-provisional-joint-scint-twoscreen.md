# Implementation Plan: provisional joint fits, DSA bandwidths, and two-screen analysis

---
**Date:** 2026-07-15
**Author:** AI Assistant
**Status:** Validated; pending PR merge
**Related Documents:**
- [Research](research-provisional-joint-scint-twoscreen.md)
- [Foreground alignment research](research-foreground-propagation-alignment.md)
---

## Overview

Generate manuscript tables directly from the frozen July joint-fit and DSA
catalogs, promote their existing figures, and report the policy-compliant
readiness state of the component-level two-screen calculation.

**Goal:** The compiled manuscript contains the best current figures and values,
without weakening the existing robust-verification caveat.

## Current State Analysis

- `sections/results.tex:158` reports DSA methodology but reserves the summary
  figure and defers the screen calculation.
- `sections/jointmodel_pairs.tex:1` and `sections/dsa_scint_acf.tex:1` are empty.
- `sections/twoscreen_formalism.tex:80` defines the common-screen relation.

## Desired End State

Generated tables provide traceable joint-fit and DSA values plus explicit
screen-consistency readiness; the main text and appendix compile the matching diagnostic figures;
captions and prose distinguish best-so-far values from certified results.

## What We're NOT Doing

- Re-running the nested sampling fits or DSA ACF fits.
- Calling current joint-fit posteriors V1-certified.
- Certifying the 40 DSA components outside the frozen Oran qualification.
- Inferring screen distances or assigning the two screens to specific media.

## Implementation Approach

One standard-library generator reads the frozen CSV/JSON inputs, validates
their schema and roster, hashes every input, and emits four TeX tables plus a
JSON provenance/result record. It enforces the dual-$\tau$ policy: products are
computed only from $\alpha=4$ consistency refits and otherwise remain pending.
No DSA frequency-law fit is introduced.

## Implementation Phases

### Phase 1: tested numerical core

- Add `tests/test_provisional_propagation.py` with analytic unit-conversion,
  frequency-scaling, uncertainty, and verdict tests; run it first and observe
  import failure.
- Add `scripts/build_provisional_propagation_tables.py`; rerun the focused test.

### Phase 2: generated products

- Run `python3 scripts/build_provisional_propagation_tables.py`.
- Verify 12 DSA rows, 12 joint-fit rows, seven screen-analysis rows, and source
  hashes in `analysis/provisional_propagation/results.json`.

### Phase 3: manuscript integration

- Replace reserved figure slots and empty appendix include files with the
  frozen PDFs; input the generated tables from `sections/results.tex`.
- Rewrite the screen-attribution discussion to report the missing
  consistency-refit gate and withhold screen verdicts.

### Phase 4: foreground-census alignment

- Join the twelve-row V4 budget and foreground sources to the July fit
  adjudication by TNS name and validate roster parity.
- Emit a complete alignment ledger with coverage, deduplicated eligible-system
  count, nearest inconclusive impact parameter, foreground and fitted
  scattering, their diagnostic ratio, and a non-causal interpretation.
- Restrict “plausible partial foreground contribution” to accepted fits with a
  nonzero eligible census and a fiducial foreground fraction of at least 0.1.
- Integrate the ledger and bounded interpretation into the discussion and
  conclusions.

### Phase 5: verification

- Run focused tests, the full science suite, a forced LaTeX rebuild, and visual
  inspection of all affected PDF pages.

## Success Criteria

### Automated Verification

- `python3 -m pytest -q tests/test_provisional_propagation.py` passes.
- Generator exits zero and emits all four tables plus the machine-readable
  result ledger.
- `make test-science` passes.
- `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex` passes.

### Manual Verification

- Tables fit and remain legible.
- Every promoted caption says provisional/not robustly verified.
- The representative joint residual and DSA summary are visually readable.

### Reproducibility & Correctness

- Analytic same-screen unit tests anchor `P=1/(2*pi)`.
- Input SHA-256 hashes and exact build command are recorded.
- A clean temporary virtual environment reproduces the standard-library
  generator and focused tests.

## Testing Strategy

Unit tests cover the closed-form conversion and classification invariant.
Integration tests check frozen roster counts, foreground classification,
diagnostic ratios, and generated TeX. The compiled PDF supplies the final
visual integration check.

## Risk Assessment

The principal risk is readers mistaking provisional numbers for certified
measurements. Repeated status columns, captions, and section-level caveats
mitigate that risk. Missing posterior covariance can understate propagated
uncertainties, so the calculation reports component ranges and avoids distance
inference.

Independent review found that the first implementation incorrectly paired the
free-$\alpha$ morphology track with DSA bandwidths. The corrected generator
loads only the policy-required $\alpha=4$ consistency track and fail-closes all
seven rows as pending because those refits are absent.

The foreground extension adds two risks: treating a coverage-limited zero as a
clean control, and treating projected alignment as causation. Explicit coverage
and fit-adjudication columns, deterministic cautious categories, and the ban on
sample-wide correlation claims mitigate both.

## Reproducibility

- Delivery basis: parent `4eea03b1`, pipeline
  `93157723fed19dc66cc54c8eb804c3c498ac10c9`; the working branch contains the
  generator, foreground alignment, and manuscript integration described here.
  The exact-byte figure receipts retain their original pipeline provenance at
  `a70b9c54817a94d2739eaa95860333e6e3f03c0a`. The intervening pin update touches
  none of the joint-fit, DSA-scintillation, or foreground inputs used here.
- Environment: macOS, Python 3.13; generator is standard-library-only. Tests
  use pytest. Input CSV/JSON SHA-256 values are written to
  `analysis/provisional_propagation/results.json`.
- Exact command: `python3 scripts/build_provisional_propagation_tables.py`.
- Clean-environment reproduction passed in a new virtual environment at
  `/tmp/faber2026-provisional-venv`; the generator reran and the focused tests
  passed.
- Correctness anchor: the analytic thin-screen identity
  `tau=1 ms`, `Delta-nu=1/(2*pi*1000) MHz` gives
  `tau[s]*Delta-nu[Hz]=1/(2*pi)` to relative tolerance `1e-12`. The test was
  observed to fail under an intentionally wrong zero expectation, then pass.
- Integration validation: 83 tests passed with one pre-existing xfail; the
  exact-byte figure-approval gate and consistency audit were clean. A forced
  LaTeX rebuild produced a visually inspected 53-page PDF, including the
  foreground ledger on page 26.
- The manuscript owner approved all 26 protected figure bytes included by this
  change. The remaining delivery gate is focused PR review and merge.
