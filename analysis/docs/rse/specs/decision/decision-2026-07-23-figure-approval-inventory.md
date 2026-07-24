# Final-draft figure approval inventory

**Owner decision, 2026-07-23:** none of the figures in the current local
Overleaf working copy is approved for the final draft.

This is a fail-closed decision. It does not approve an older receipt, promote
bytes, or reject the scientific content of a future replacement.

## Active Overleaf PDF assets

The local Overleaf copy actively references 27 PDFs:

| Figure group | PDF assets | SVG counterparts | Final-draft approval |
|---|---:|---:|---|
| Milky Way electron model | `figures/ne2025_mw_characterization_nside32.pdf` | none | none |
| Foreground halo sightlines | `figures/sightline_halo_grid.pdf` | `figures/sightline_halo_grid.svg` | none |
| Cluster medium | `figures/clusters_icm.pdf` | `figures/clusters_icm.svg` | none |
| Host dispersion posteriors | `figures/dm_host_posteriors.pdf` | none | none |
| Association cards | 12 PDFs under `figures/association_cards/` | none | none |
| Joint-model morphology pairs | 11 PDFs under `figures/jointmodel_pair/` | 11 matching SVGs | none |

Association-card PDFs: `casey`, `chromatica`, `freya`, `hamilton`, `isha`,
`johndoeii`, `mahi`, `oran`, `phineas`, `whitney`, `wilhelm`, and `zach`.

Joint-model pair PDFs: `casey`, `freya`, `hamilton`, `isha`, `johndoeII`,
`mahi`, `oran`, `phineas`, `whitney`, `wilhelm`, and `zach`.

The exact SHA-256 inventory is
[`overleaf-active-figure-inventory-2026-07-23.json`](../../../../figure_review/overleaf-active-figure-inventory-2026-07-23.json).
The Overleaf copy is an independently diverged working copy; this receipt
describes its live local bytes and does not imply GitHub or release promotion.

## Separate review candidate

The only current repository candidate suitable for a future owner review is
`figure_review/batches/2026-07-22-fig3-source-replay/candidates/fig3-halo-grid.pdf`,
SHA-256
`45017274a7e3d60cf6918d72c3e89558c0e9d50e27427d39a216547c4999fa6c`.
It remains available, unapproved, and unpromoted. The owner's statement
“approve none” is not interpreted as a `needs_revision` verdict because no
specific visual or scientific defect was named.

The other apparent queue entries are not current approval questions:

- Figure 1 already has an owner `needs_revision` decision.
- Joint scintillation is diagnostic-only.
- The Verdi-roster Figure 3 batch is superseded.
- Joint-scattering decisions are morphology-only; fitted values remain
  untrusted.

`figure_review/batch_dispositions.json` records these queue dispositions.
