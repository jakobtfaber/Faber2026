# Rejected CHIME/FRB RFI prototype archive — 2026-07-24

Immutable recovery packet for three retained worktrees. Nothing here is a production cleaner or science-admissible product.

## Conclusion

- The package/row cleaner was rejected after owner review found residual horizontal RFI at 700–750 MHz.
- The Pixel-6 time-frequency candidate recovered 98.69% of injected RFI pixels, but clipped burst signal and failed protected morphology, normalized-residual, and spectral-modulation checks.
- Later automated horizontal-row variants either left visible RFI or erased broad frequency structure; all were rejected.
- The analysis controlled example fails five preservation checks and is explicitly not cleaner validation.
- The only accepted operational boundary is fail-closed manual-map review; no rejected experimental module is promoted to production paths.

## Recovery

`SOURCE_MANIFEST.json` records source checkout, branch, head, status hash, archived path, size, and SHA-256 for every byte. `recovery/*/*.patch` preserves tracked dirty deltas. `payloads/` preserves committed verification products and untracked experiment bytes at archive time. Verify first with `shasum -a 256 -c SHA256SUMS` from this directory.

Source labels:

- `successor`: consolidated committed prototype and real-event verification evidence.
- `dirty-parent`: rejected horizontal-row experiments and dirty source/test deltas.
- `analysis`: controlled preservation-limit review and owner-decision note.
