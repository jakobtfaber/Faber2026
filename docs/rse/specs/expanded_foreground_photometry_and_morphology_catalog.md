# Expanded foreground photometry, morphology, and halo catalog

**Status:** versioned audit product; scientific release remains governed by the independent validation and Figure 3 owner-review gates.

**Rows:** 52
**Catalog SHA-256:** `17ef142bc5d57f0f1f42d11a397c084de2b9763fbb7543ce82e90e1a6d6ef727`
**Catalogs:** GSC 2.4.2 (`I/353/gsc242`), ALLWISE (`II/328/allwise`), CatWISE2020 (`II/365/catwise`), and unWISE (`II/363/unwise`).

## Matching and quality contract

Each 3-arcsecond cone response is stored in a normalized committed snapshot. Rows are sorted by exact spherical separation and then catalog identifier. The nearest row is selected only when the second-nearest separation is more than 0.3 arcsecond farther away. States are `matched`, `unmatched`, `ambiguous`, and `query_error`; a query error is never reported as an unmatched source.

- GSC 2.4.2: `matched` 39, `ambiguous` 9, `unmatched` 4.
- ALLWISE: `matched` 47, `unmatched` 5.
- CatWISE2020: `matched` 47, `unmatched` 3, `ambiguous` 2.
- unWISE: `matched` 37, `ambiguous` 11, `unmatched` 4.

The table retains selected separation, candidate count, second-nearest separation, release, retrieval time, response hash, identifiers, photometric errors, and native quality/artifact/extension flags. CatWISE2020 has no `ccf` field in its VizieR table; the catalog records this explicitly as `not_published_in_vizier_table`.

GSC `Class 3` means non-star, not a secure galaxy classification. Crossmatches are audit evidence and never change the adjudicated census verdict.

## Physical quantities

- **Cluver et al. (2014):** diagnostic Equation 2, `log10(M*/Msun) = log10(L_W1/Lsun) - 2.54(W1-W2) - 0.17`, requires rest-frame color, valid W1/W2 photometry, and uncertainties. The current observed-frame catalog therefore leaves this diagnostic null with status `not_rest_frame`; no colorless fallback is used.
- **Moster et al. (2013):** adopted galaxy stellar masses come only from the adjudicated census mass table and override ledger. Linear stellar mass in solar masses is inverted through the redshift-dependent Table 1 relation to obtain `M200c`.
- **Radius:** `R200c = [3 M200c / (4 pi 200 rho_crit(z))]^(1/3)` in proper kpc. Concentration is not used to compute the radius.
- **Dutton and Maccio (2014):** `log10(c200c)=a+b log10(M200c h / 10^12 Msun)`, with the calibration's published `h=0.671`, `b=-0.101+0.026z`, and `a=0.520+(0.905-0.520) exp[-0.617 z^1.21]`. It is used only for the scale radius `R200c/c200c`.
- **Clusters:** retain catalog `M500` and `R500`. No galaxy stellar-mass relation or unvalidated cluster conversion is applied.
- **Uncertainty:** native photometric errors and propagated W1-W2 errors are retained. Unknown adopted-mass, halo-mass, and radius uncertainties remain null with `pass_uncertainty_unavailable`; no numerical uncertainty is invented.

## Stern et al. (2012) active-galaxy check

The W1-W2 >= 0.8 selection is evaluated only for valid color and W2 <= 15.05 Vega. Outcomes are `selected_by_stern12`, `not_selected_within_depth`, `outside_validated_depth`, and `insufficient_color`. A blue color is not interpreted as proof of starlight dominance.

Observed outcomes: `outside_validated_depth` 23, `not_selected_within_depth` 21, `insufficient_color` 8.

## Candidate inventory

| FRB | Object | Type | Verdict | GSC state/class | ALLWISE state | Adopted log M* | M200c (Msun) | R200c (kpc) |
|---|---|---|---|---|---|---:|---:|---:|
| FRB 20220207C | 195373100910393540 | halo | inconclusive | matched/4 | matched | -- | -- | -- |
| FRB 20220310F | 1472 | halo | refuted | matched/3 | matched | -- | -- | -- |
| FRB 20220310F | 1473 | halo | confirmed | unmatched/-- | unmatched | 9.605 | 2.761424e+11 | 120.874 |
| FRB 20220310F | 1582 | halo | inconclusive | unmatched/-- | matched | -- | -- | -- |
| FRB 20220310F | 196191347354360083 | halo | refuted | matched/3 | matched | -- | -- | -- |
| FRB 20220310F | J085546.0+732230, 1160094 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20220310F | J085531.9+732432, 1159975 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20220310F | J085808.2+731234, 1161367 | cluster | confirmed | ambiguous/3 | matched | -- | -- | -- |
| FRB 20220506D | 195393180643665627 | halo | inconclusive | matched/4 | matched | -- | -- | -- |
| FRB 20221203A | 194453151328186646 | halo | inconclusive | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | 832 | halo | confirmed | matched/3 | matched | 10.211 | 5.422734e+11 | 161.187 |
| FRB 20230307A | 953 | halo | confirmed | matched/3 | matched | 10.086 | 4.494001e+11 | 151.040 |
| FRB 20230307A | 983 | halo | confirmed | ambiguous/3 | matched | 8.944 | 1.127872e+11 | 96.457 |
| FRB 20230307A | 986 | halo | inconclusive | matched/3 | matched | 9.577 | 2.357774e+11 | 121.414 |
| FRB 20230307A | 1072 | halo | inconclusive | ambiguous/3 | unmatched | 9.539 | 2.442360e+11 | 118.704 |
| FRB 20230307A | 1153 | halo | confirmed | matched/3 | matched | 10.672 | 1.707590e+12 | 234.354 |
| FRB 20230307A | 1190 | halo | confirmed | matched/0 | matched | 9.989 | 3.560817e+11 | 144.276 |
| FRB 20230307A | 194021777634832653 | halo | confirmed | matched/3 | matched | 10.211 | 5.422734e+11 | 161.187 |
| FRB 20230307A | 194031778315722893 | halo | refuted | matched/3 | unmatched | 10.223 | 8.360261e+11 | 141.533 |
| FRB 20230307A | 194041777780157594 | halo | confirmed | matched/3 | matched | 10.672 | 1.707590e+12 | 234.354 |
| FRB 20230307A | 194051777813062524 | halo | confirmed | matched/0 | matched | 9.989 | 3.560817e+11 | 144.276 |
| FRB 20230307A | J115120.4+714435, 1254337 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | J115128.2+713637, 1254415 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | J114944.0+714348, 1253496 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | J115140.5+712732, 1254506 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | J115400.9+713320, 1255773 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | J115031.4+715735, 1253898 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | J115436.9+713930, 1256077 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | J114928.5+712526, 1253366 | cluster | confirmed | ambiguous/0 | matched | -- | -- | -- |
| FRB 20230325A | 197030881733398302 | halo | inconclusive | ambiguous/3 | matched | 11.028 | 1.301898e+13 | 445.866 |
| FRB 20230325A | 197040882212782495 | halo | inconclusive | matched/3 | matched | 10.758 | 2.492956e+12 | 226.868 |
| FRB 20230913A | 192943050854547067 | halo | inconclusive | matched/3 | matched | -- | -- | -- |
| FRB 20230913A | 192963050359413614 | halo | inconclusive | matched/3 | matched | 10.676 | 1.753565e+12 | 228.272 |
| FRB 20240203A | 196673126794497004 | halo | inconclusive | matched/4 | matched | -- | -- | -- |
| FRB 20240203A | 196723126173351736 | halo | inconclusive | matched/0 | matched | 11.462 | 4.040517e+14 | 1310.232 |
| FRB 20240203A | 196733128040225775 | halo | confirmed | ambiguous/3 | matched | 10.827 | 3.871502e+12 | 325.623 |
| FRB 20240229A | 192821699728654764 | halo | refuted | matched/3 | matched | 11.039 | 1.392329e+13 | 443.724 |
| FRB 20240229A | 192821700026167542 | halo | confirmed | ambiguous/0 | matched | 10.935 | 7.077422e+12 | 378.081 |
| FRB 20240229A | 192831699797402822 | halo | confirmed | matched/0 | matched | 10.899 | 5.544095e+12 | 343.793 |
| FRB 20240229A | 660 | halo | refuted | matched/3 | matched | -- | -- | -- |
| FRB 20240229A | 795 | halo | refuted | matched/3 | matched | 11.039 | 1.392329e+13 | 443.724 |
| FRB 20240229A | 796 | halo | refuted | unmatched/-- | unmatched | 10.864 | 4.184766e+12 | 291.758 |
| FRB 20240229A | 827 | halo | confirmed | matched/0 | matched | 10.899 | 5.544095e+12 | 343.793 |
| FRB 20240229A | 824 | halo | confirmed | ambiguous/0 | matched | 10.935 | 7.077422e+12 | 378.081 |
| FRB 20240229A | 825 | halo | inconclusive | unmatched/-- | unmatched | 9.501 | 2.424909e+11 | 116.212 |
| FRB 20240229A | J111929.5+705441, 1237905 | cluster | confirmed | matched/0 | matched | -- | -- | -- |
| FRB 20240229A | J112235.5+705438, 1239515 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20240229A | J112350.9+704142, 1240175 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20240229A | J111930.9+702041, 1237924 | cluster | confirmed | matched/3 | matched | -- | -- | -- |
| FRB 20221113A | WISEA J044538.83+701843.3 | halo | inconclusive | matched/0 | matched | -- | -- | -- |
| FRB 20220506D | WISEA J211150.32+724807.8 | halo | inconclusive | matched/3 | matched | -- | -- | -- |
| FRB 20230307A | WHL J115048.0+714428 | cluster | confirmed | ambiguous/0 | matched | -- | -- | -- |

## Reproduction

```bash
uv run --project pipeline --frozen python -m galaxies.foreground.build_expanded_catalog --offline
uv run --project pipeline --frozen python -m galaxies.foreground.build_sightline_halo_grid_input
python3 scripts/build_expanded_foreground_provenance.py
```

The census verdict, duplicate, and budget fields are copied unchanged from the frozen registry. Redshift or budget re-adjudication requires a separate evidence record.
