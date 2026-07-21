# Independent validation: expanded foreground catalog

## Overall status: FAILED — host-redshift provenance incomplete

The rebuilt catalog, physics, catalog matching, and Figure 3 input pass an
independent calculation path. Scientific promotion remains fail-closed because
the frozen 12-host roster does not carry source-bearing redshift evidence.
Figure 3 also still requires manuscript-owner visual approval.

| Boundary | Revision or hash |
|---|---|
| Parent input | `49a4658a302776c31ba92b49ecbd65ccf37780fa` |
| Pipeline merge | `3e466c1a180fb169ad09845312348cf539b82632` |
| Independently checked feature revision | `db73ac7045f4d9341778eb7e826ffc81d089169d` (identical tree `0683c2ce79ca0ae0cfb5dfd730cc8ca333556b75`) |
| Expanded catalog | `17ef142bc5d57f0f1f42d11a397c084de2b9763fbb7543ce82e90e1a6d6ef727` |
| Figure 3 input | `63e2c980399810a027d6877cf5de118350e8d82a995cb03621d5daa3315259f8` |
| Staged Figure 3 PDF | `0940b333993e540c2caf622a46ebef7a47ef0c1a68b6d3204d988aca651f486f` |

## Passing independent checks

The validator did not import the catalog builder or its physics helpers.

| Check | Result |
|---|---|
| Catalog identity | 52 rows; 52 unique keys; zero verdict or budget differences |
| Catalog queries | 208 responses; zero identifier, nearest-neighbor, ambiguity, count, or second-separation differences |
| Spherical separation | maximum difference `4.34e-11` arcsec; tolerance `2e-8` arcsec |
| Moster et al. (2013) | 25 finite halos; maximum inversion difference `1.75e-11` dex; tolerance `1e-6` dex |
| `R200c` | maximum enclosed-mass relative error `1.26e-15`; tolerance `1e-10` |
| Dutton–Macciò (2014) | published Planck calibration `h=0.671`; maximum concentration relative difference `0` |
| Cluver et al. (2014) | Equation 2 label on 52/52; all values correctly null as `not_rest_frame` |
| Stern et al. (2012) | zero color, propagated-error, or category differences |
| Figure 3 input | 37 rows: 12 hosts plus 25 deduplicated confirmed systems; zero field or geometry differences |
| Manifests | catalog and snapshot hashes reproduce |

Moster's halo mass is validly mapped to `M200c`: the paper defines its main-halo
mass using 200 times critical density. `R200c` uses Planck18 critical density;
the separately calibrated Dutton–Macciò concentration uses its published
`h=0.671`.

## Blocking source-evidence gate

The frozen host table supplies redshift values, not provenance. It lacks host
identifier, uncertainty, measurement kind, citation, upstream row identifier,
release or retrieval date, and source-content hash. Consequently none of the 12
host entries has a complete independent evidence chain. `freya`, `johndoeII`,
and `mahi` also have no host redshift. The candidate ledger is complete: 46
adopted redshifts and six explicit no-redshift dispositions.

Required next artifact: the authoritative Verdi host-redshift table, or a
minimal source-bearing extract satisfying
`expanded-foreground-catalog-repair-07-freeze-host-redshift-provenance.md`.
After it is frozen, repeat source-level validation. Only a zero-difference pass
may change the machine gate to `passed`. Owner visual approval is separately
required before Figure 3 promotion.

## Verdict

Calculation and artifact validation: **passed**.

Scientific release validation: **failed closed**.

Installed manuscript Figure 3: **unchanged**.
