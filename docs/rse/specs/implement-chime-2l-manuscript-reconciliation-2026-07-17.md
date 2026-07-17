# Implementation: CHIME 2L manuscript reconciliation

---
**Date:** 2026-07-17
**Status:** Implemented; joint-figure promotion pending owner review
**Plan:** [plan-chime-2l-manuscript-reconciliation-2026-07-17.md](plan-chime-2l-manuscript-reconciliation-2026-07-17.md)
---

## Delivered

- Advanced the `pipeline` gitlink from `5fb387e` to the merged PR #192 commit
  `17d9d26675702e9f8917da655621bef3231f0ddb`.
- Added `scripts/build_scintillation_campaign_summary.py`, which fails closed
  unless the pinned campaign is closed, contains exactly 24 records, promotes
  only `chromatica_hi`, and retains four resolved qualified sub-bands.
- Generated the twelve-sightline AASTeX campaign table and a JSON provenance
  record with source/output hashes, the exact runtime command, and both repo
  revisions.
- Reconciled `sections/results.tex`, `CONTEXT.md`, the evidence ledger and its
  generated claims audit, the figure wishlist, and reproducibility records.
- Added the finalized campaign to the parent Results Library catalog and opened
  dsa110-FLITS PR #199 for the corresponding upstream pointer; the manuscript
  gitlink remains at the reviewed PR #192 science commit.
- Removed the owner-rejected DSA-only summary from the compiled manuscript and
  reserved its slot with an explicit exact-byte-review placeholder.

## Scientific boundary

The qualified CHIME result is the high-resolution FRB 20240203A record, with
four sub-band widths and a descriptive within-band slope. The qualified DSA-110
result belongs to FRB 20220506D. The manuscript therefore reports both without
connecting them by a cross-burst scaling law or deriving a shared screen.

## Verification summary

- Focused campaign contract: 5 passed.
- Repository science suite: 130 passed, 1 expected failure.
- Consistency audit, state drift/rules, and figure approval gate: passed.
- Clean `latexmk` rebuild: passed; generated table and review placeholder were
  visually inspected in the rendered PDF.

The separately stacked candidate-only figure work is governed by the same plan
and cannot be promoted until the manuscript owner approves its exact bytes.
