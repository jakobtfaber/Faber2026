# Validation Failed: Expanded Foreground Photometry and Morphology Catalog

> Supersedes the 2026-07-20 report that marked
> `docs/rse/specs/expanded_foreground_photometry_and_morphology_catalog.md`,
> `pipeline/galaxies/foreground/data/expanded_catalog_cross_references.csv`, and
> `scripts/build_expanded_foreground_provenance.py` as accepted at parent commit
> `93b75419`.

## Overall Status: FAILED — superseded; do not use

Machine-readable status: **FAILED - superseded; do not use**.

The previous validation is invalid as acceptance evidence. It may be cited only
as superseded evidence explaining why the expanded catalog repair is required.
The present gate must remain failed until the rebuilt catalog and independent
validation report both pass.

Gate file:
`docs/rse/specs/validation-expanded-foreground-catalog.json`.

## Failed Gate

| Field | Value |
|---|---|
| Status | `failed` |
| Disposition | `superseded_do_not_use` |
| Parent commit checked | `9090d74c9cae0510d5b64c2fb1424dd658c08c9e` |
| Pipeline commit checked | `ded8d195701c4abf5df31e6ad94f1750172d718e` |
| Required next state | Rebuilt catalog passes and independent report passes |
| Validator behavior | Nonzero exit while any defect below has non-pass status |

## Defects Preserved As Superseded Evidence

| Defect identifier | Affected formula or artifact | Rows or count | Scientific effect | Required repair |
|---|---|---:|---|---|
| `moster-input-units` | Moster et al. (2013) stellar-mass-to-halo-mass interface | expanded CSV halo rows using derived stellar mass | Stored radii are roughly 2.5-3.0 Mpc because linear stellar mass was passed through a logarithmic helper path. | Use the redshift-dependent Moster interface with explicit linear stellar-mass units; recompute `M200c` and `R200c`. |
| `cluver-equation-and-rest-frame` | Cluver et al. (2014) stellar-mass relation | all rows with WISE-derived stellar masses | Report labels the relation incorrectly and omits the rest-frame color condition; a colorless fallback was treated as valid. | Implement the correct equation label and rest-frame applicability gate; null invalid or inapplicable derived values. |
| `incomplete-crossmatches` | Expanded crossmatch coverage summary | GSC 48/52, ALLWISE 47/52, CatWISE 49/52, unWISE 48/52; all four present for 46/52 | The old report claimed complete cross-catalog coverage and hid missing matches. | Record per-catalog match status, query status, and missing data explicitly. |
| `non-deterministic-match-selection` | Catalog row selection | nearest-match audit disagreed for 10 GSC, 4 CatWISE, and 10 unWISE rows | Row-zero selection can pick a different source than the nearest source; four GSC differences change morphology code. | Sort candidates deterministically by separation and identifier; preserve candidate count and second separation. |
| `stern-selection-interpretation` | Stern et al. (2012) mid-infrared color selection | only 21/47 ALLWISE matches satisfy `W2 <= 15.05` depth condition | Blue color was described as starlight proof, and sources outside the validated depth were treated as passed. | Emit Stern selection status only within the published depth and color-validity conditions. |
| `morphology-summary` | GSC morphology summary and contaminant wording | summary counts and named starlike/unclassified contaminants | Morphology evidence was overstated as verdict support and did not reflect nearest-match changes. | Report GSC class as catalog evidence only; do not alter census verdicts without adjudication. |
| `missing-pinned-expanded-csv` | Expanded catalog CSV provenance | catalog artifact absent or not pinned at validation boundary | The validation could not be replayed from a checked-in, versioned expanded CSV. | Check in the rebuilt CSV with manifest hashes and deterministic offline rebuild command. |
| `unversioned-figure-3-input` | Figure 3 foreground-halo-grid input | figure input referenced an external unversioned CSV | Figure 3 could be regenerated from a drifting input and must not be promoted from this validation. | Generate and check in the versioned Figure 3 input; block promotion until independent validation and owner visual approval. |

## Supersession Rule

Do not cite the superseded accepted-result label as accepted validation.
The findings above are retained only as repair evidence. The expanded catalog,
derived halo quantities, morphology summary, Stern status, and Figure 3 input
remain not accepted until a later validation changes the JSON gate to `passed`
with zero non-pass defects.
