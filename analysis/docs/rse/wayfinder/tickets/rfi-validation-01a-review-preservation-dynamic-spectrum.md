# Review the RFI preservation limits on a controlled dynamic spectrum

- Type: `wayfinder:prototype` (HITL)
- Status: closed
- Assignee: Codex
- Blocked by: [Build the verified Zach CHIME preprocessing baseline](16-build-verified-zach-chime-preprocessing-baseline.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Reconciled question

Which frequency rows may downstream Zach CHIME/FRB analyses exclude without
silently replacing source validity or promoting an unvalidated automated
cleaner?

The original synthetic-only preservation review was diagnostic. Subsequent
real-event reviews showed both missed contamination and excessive signal loss.
The owner therefore selected event-specific manual bad-channel maps as the
channel-row authority. Automated diagnostics may inform review but cannot add
science-mask rows.

## Resolution — owner-approved manual authority, 2026-07-22

The owner approved the regenerated before/after artifact and five exact Zach
CHIME/FRB ranges: 490 manual rows. The immutable downstream mask is the exact
Boolean union of:

- 9,792 rows already unavailable in the source-valid mask; and
- 490 owner-selected manual rows.

The sets have zero overlap: 10,282 bad rows and 55,254 retained rows. Retained
values are unchanged. Any frequency-axis, source-product, source-valid-mask,
map, or approval mismatch fails closed.

- [Approved map](../../../../rfi/manual-bad-channels/chime-frb/zach.json)
- [Policy and queue](../../../../rfi/manual-bad-channels/README.md)
- [Final 700–750 MHz review](../../verify/manual-bad-channel-review-20260721/zach-chime/zach_chime_manual_zap_review_700_750.svg)
- [Full-band review atlas and provenance](../../verify/manual-bad-channel-review-20260721/zach-chime/)
- [Map validator and effective-mask writer](../../../../scripts/manual_bad_channels.py)
- Authoritative h17 directory:
  `/data/Faber2026/evidence/manual-bad-channel-review-20260721/zach-chime/approved/`

Bound artifact hashes:

- approved map: `d3acc570ac8342982579facadc5d9f90e00a2b9a0a7cd88fd2878662d5a9d62e`;
- review SVG: `d769c3a7191e8fb7fa3a50a59e1eb0294325ed769db7fd6fac58336dc3ff53e5`;
- effective mask: `5de1bd08ff2ea0a3aa8b3ea37f609e6c7530ae14869d4d5e5361609c9adb8038`;
- effective-mask provenance:
  `6501fe1bb15a96629e80e6f60d8e206bc955adad144c0128f91b2237033087ee`.

## Boundary

This closes the row-authority choice. It does **not** validate an automated
cleaner, an autocorrelation measurement, scattering, scintillation, or a
manuscript claim. Diagonal or time-local interference remains separate. The
standardized post-dispersion-measure, post-burst-model product must be available
before the approved map is tested in autocorrelation preprocessing.
