# Implementation Summary: RFI preservation dynamic-spectrum prototype

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** Automated work complete; manual owner review pending
**Plan Reference:** [plan](plan-rfi-preservation-dynamic-spectrum-prototype.md)
---

## Overview

Implemented a deterministic, development-only known-truth RFI preservation
review. The script uses Zach's verified CHIME frequency/support geometry, never
opens observed burst intensity or sealed data, runs the exact rejected package
cleaner on h17, and creates an SVG plus complete JSON provenance.

## Plan Adherence

The plan was followed with two corrections:

- Float32 bandpass round-trip tolerance changed from `1e-10` to `5e-6` to match
  the real product storage precision.
- Cleaner-induced missing values in the development bandpass arrays are
  interpolated only as synthetic response shape; they do not redefine source
  support. Run 1 exposed and preserved this error before correction.

## Phases Completed

- Phase 1: deterministic truth and four known RFI classes — complete.
- Phase 2: exact rejected cleaner and finite-support measurements — complete.
- Phase 3 automated: deterministic SVG, JSON, checksums, and repeated clean run
  — complete.
- Phase 3 manual: owner visual review — pending.

## Files

- `scripts/prototype_rfi_preservation_review.py` — generator, cleaner runner,
  measurements, plot, and provenance.
- `tests/test_prototype_rfi_preservation_review.py` — five deterministic and
  missing-data tests.
- `docs/rse/verify/rfi-preservation-prototype-20260721/` — canonical review
  packet from h17 run 8.
- [experiment report](experiment-rfi-preservation-dynamic-spectrum-prototype.md)
  — result interpretation and failure history.

## Verification

```text
python -m pytest -q tests/test_prototype_rfi_preservation_review.py
..... 5 passed

sha256sum -c SHA256SUMS
rfi_preservation_review.svg: OK
rfi_preservation_review.json: OK
prototype_rfi_preservation_review.py: OK

run-8 versus run-9: SVG, JSON, and script byte-identical
```

`git diff --check` passed. Peak observed container memory was about 1.1 GiB.

## Remaining Work

- Owner accepts or revises the tentative preservation limits after viewing the
  figure.
- Fold that decision into the Wayfinder acceptance-contract ticket.
- Do not validate any cleaner until the frozen distribution benchmark and blind
  test pass.

## References

- [Research](research-rfi-preservation-dynamic-spectrum-prototype.md)
- [Plan](plan-rfi-preservation-dynamic-spectrum-prototype.md)
- [Experiment](experiment-rfi-preservation-dynamic-spectrum-prototype.md)
- [Review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)
