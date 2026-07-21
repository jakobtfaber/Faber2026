# Implementation: Results-library and CHIME-path repair

**Date:** 2026-07-20
**Plan:** [plan-results-library-chime-path-repair.md](plan-results-library-chime-path-repair.md)
**Parent base:** `74b7dd6d`
**Landed pipeline pin:** `ded8d195701c4abf5df31e6ad94f1750172d718e`
**Pipeline review:** [dsa110-FLITS #212](https://github.com/jakobtfaber/dsa110-FLITS/pull/212)

## Implemented

- Added exact catalog selection, nested destinations, deterministic manifests,
  and JSON receipts to the results-library tools.
- Split every approved current CHIME/FRB and DSA-110 caller onto distinct
  roots. Preserved the historical joint-DM source snapshot unchanged and added
  a current split-root runner.
- Landed the pipeline change independently through PR #212. The parent pin also
  imports the three pre-existing Chromatica `main` commits between `c6111390`
  and `ded8d195`; the full pin delta was inspected before checkout.
- Added explicit result-to-library fields. Only `sample.gallery_fig1` ↔
  `manuscript.figures` is asserted; other relationships remain explicit empty
  lists.
- Recorded 12 remediation packets and three Freya package manifests as
  incomplete-lineage exceptions. No `input.*` identity was fabricated.
- Replaced eight broken library symlinks, created two missing library symlinks,
  and restored three repository symlinks. No real bytes moved or deleted.
- Regenerated the external inventory with all 18 catalog entries from the
  canonical checkout.

## Receipts and rollback

- Frozen preimage/action packet:
  `docs/rse/certificates/results-library-repair-2026-07-20/action-packet.json`
- Library-link receipt: `library-links-receipt.json`
- Repository-link receipt: `repository-links-receipt.json`
- Complete inventory receipt: `final-inventory-receipt.json`
- External `INDEX.md` and `inventory.yaml` preimages remain encoded beside the
  action packet. Their decoded SHA-256 hashes still match the packet.

## Implementation corrections found during execution

- Tree manifests now sort by relative path strings. Sorting absolute `Path`
  components produced different hashes when a file and directory shared a
  prefix.
- L0 registry regeneration now replaces the existing derived-product section
  instead of appending a duplicate. Its header continues to state that these
  products are derived, not raw CHIME data.

## Deliberate exclusions

- `scintillation.dsa-lorentzian-2026-07-07` and
  `dispersion.pipeline-results-root` remain both-real conflicts.
- JointTF, historical diagnostic, Drive, CANFAR, h17, and scientific trust
  surfaces were not changed.
- Jupyter, MkDocs, and other services remain stopped/unmodified.

## Verification summary

- Parent focused suite: 67 passed.
- Pipeline focused suite at landed pin: 34 passed.
- Live post-repair check: 13 links resolved, 18 inventory entries, six excluded
  manifests unchanged, zero errors.
- L0 certificate file remains byte-identical at SHA-256
  `e3608a6458e8fe7075ca41395cce7a84a22cac968dbba31fd817dd212e8f184b`.
- Historical joint-DM source and provenance show no Git diff.

Full results: [validation-results-library-chime-path-repair.md](validation-results-library-chime-path-repair.md).
