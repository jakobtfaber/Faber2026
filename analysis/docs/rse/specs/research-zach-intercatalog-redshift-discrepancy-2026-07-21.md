# Zach candidate: inter-catalog redshift investigation

Date: 2026-07-21 PDT / 2026-07-22 UTC  
Position: RA `310.0912903 deg`, Dec `+72.81041703 deg` (ICRS)  
Search radius unless stated otherwise: `5 arcsec`

## Question and boundary

The legacy spreadsheet labels `0.012668989` as a photometric redshift from the
combined WISE--Pan-STARRS--STRM catalog. The frozen optical-only PS1--STRM row for PS1
`objID=195373100910393540` gives `z_phot = 0.4693608582 +/- 0.047097985` and
`extrapolation_Photoz=1`. Can official source-row evidence, public spectra,
independent northern photometry, or classification catalogs distinguish them?

This note does not change the adopted redshift, foreground verdict, or budget
eligibility.

## Result

**Not yet.** The supplied MAST extraction identifies the exact combined
WISE--PS1--STRM row, but does not make either redshift trustworthy. It instead
shows that the same WISE source was associated with two PS1 objects separated
by about 1 arcsec. Both classifications, and the target row's photometric
redshift, are extrapolations far outside their training-map thresholds. Every
public spectroscopic and classification query below was a non-detection.
UNIONS/CFIS remains access-blocked pending a CADC account authorized for the
`CFIS-read` group.

The discrepancy must remain explicit. Do not average the two redshifts or
select one because it is closer to the host redshift.

## 1. Combined WISE--PS1--STRM row

The [official MAST release](https://archive.stsci.edu/hlsp/wise-ps1-strm)
identifies release date `2022-09-14`, DOI `10.17909/wf64-kq10`, and CasJobs
context `HLSP_WISE_PS1_STRM`. Row extraction must use
`catalogRecordRowStore`. The relevant declination file is:

- `hlsp_wise-ps1-strm_ps1-wise_multi_p70-p75_multi_v1_cat.csv.gz`
- HTTP `Content-Length`: `3968290147` bytes
- published SHA-256:
  `0a65f94dd79d0427332c3dbc0950d040f11910ed5eb40c1e8d0e03acef4ec3ca`

The full compressed strip was deliberately not downloaded. The owner-supplied
CasJobs [export](research/evidence/zach-intercatalog-redshift-2026-07-21/zach_foreground_jfaber.csv)
contains two rows and 5,230 bytes;
its SHA-256 is
`d2fcc7fb2db3f1a627b1716ec7cf70d87456eacc57d1ef27d22c7f9bee6105f1`.
The local filesystem records creation and modification at
`2026-07-21T18:24:26-0700`; that timestamp is not a substitute for a recorded
CasJobs retrieval time. The query text and CasJobs job identifier were not
embedded in the file and should still be frozen with it for complete
provenance.

### Supplied-row audit

The [official MAST field definitions](https://archive.stsci.edu/hlsp/wise-ps1-strm)
define `distance_Deg` as the PS1--WISE angular separation, `BayesFactor` as the
cross-match likelihood ratio, and `cntr` as the unique WISE catalog-source
identifier. They also warn that PS1 `objID` is not unique, so coordinates must
remain part of the identity check.

| field | target PS1 row | second PS1 row |
|---|---:|---:|
| `objID` | `195373100910393540` | `195373100922233363` |
| PS1 position | `310.09129027`, `+72.81041703` deg | `310.09219124`, `+72.81049238` deg |
| WISE `cntr` | `3113172601241027886` | `3113172601241027886` |
| PS1--WISE separation | `0.856754` arcsec | `0.186042` arcsec |
| `BayesFactor` | `1.93041481238421e10` | `6.41894631707602e11` |
| class | `GALAXY` | `QSO` |
| galaxy / star / quasar output | `0.774156 / 0.214111 / 0.011734` | `0.154233 / 0.107350 / 0.738417` |
| class extrapolation; distance; cell | `1`; `14.0726`; `750` | `1`; `16.3601`; `460` |
| `z_phot` | `0.01229792` | missing (`-999`) |
| `z_photErr` | `0.06530163` | missing (`-999`) |
| `z_phot0` | `0.012668989` | missing (`-999`) |
| photo-z extrapolation; distance; cell | `1`; `12.2521`; `146` | missing (`-999`) |

The first row is the requested PS1 object: its identifier matches exactly and
its position agrees with the recorded candidate to about `0.00003` arcsec.
The second row is a distinct PS1 object `0.9962` arcsec away. It is not another
row for `objID=195373100910393540`. Both rows nevertheless contain the same
WISE identifier, coordinates, and photometry. The WISE association is therefore
not unique at PS1 resolution. The second row is closer to the WISE position and
has a `33.2516` times larger match likelihood ratio, but the published field
definition does not make that ratio a rule for assigning the WISE flux uniquely
between nearby PS1 objects. Shared or blended infrared information remains a
material concern.

The [official catalog definitions](https://archive.stsci.edu/hlsp/wise-ps1-strm)
set the classification extrapolation boundary at `cellDistance_Class > 4.233`.
Both values are more than three times that boundary, so neither class label is
an in-domain classification. They set the photometric-redshift extrapolation
boundary at `cellDistance_Photoz > 3.702`; the target's value `12.2521` is also
far outside the modeled region. Its calibrated error `0.06530` exceeds either
low-redshift point estimate. The legacy spreadsheet value `0.012668989` is an
exact match to the base estimate `z_phot0`, not the catalog's Monte Carlo
estimate `z_phot=0.01229792`. MAST describes `z_phot0` as slightly more accurate,
but that does not override the row's explicit extrapolation flag.

The second row has no redshift estimate because it is classified as a quasar;
the catalog estimates photometric redshifts for galaxy-classified sources.
Its `-999` entries therefore do not provide a third redshift. The supplied rows
prove the low value's exact catalog provenance while weakening its scientific
weight: it is an extrapolated estimate using WISE measurements also assigned
to a separate, closer PS1 source.

## 2. Spectroscopic searches

### DESI Data Release 1

The [DESI DR1 database documentation](https://data.desi.lbl.gov/doc/access/database/)
states that the public `iron.zpix` catalog is mirrored as
`desi_dr1.zpix` at NOIRLab Astro Data Lab and permits anonymous synchronous
queries. At `2026-07-21T21:30Z`, this query returned the header and zero rows:

```sql
SELECT z.targetid,z.survey,z.program,z.healpix,z.z,z.zerr,z.zwarn,
       z.spectype,z.subtype,z.deltachi2,z.zcat_primary,p.ra,p.dec
FROM desi_dr1.zpix AS z
JOIN desi_dr1.photometry AS p ON z.targetid=p.targetid
WHERE q3c_radial_query(p.ra,p.dec,310.0912903,72.81041703,0.0013888889)
```

An independent cone query of `desi_dr1.photometry` also returned zero rows.
Thus there is neither a DESI DR1 spectrum nor a DESI-target photometry row at
this position in the public native database.

### Sloan Digital Sky Survey Data Release 19

The [DR19 access page](https://www.sdss.org/dr19/data_access/) identifies
SkyServer as the catalog authority. At `2026-07-21T21:29Z`, a join between
`SpecObjAll` and `dbo.fGetNearbySpecObjEq(310.0912903,72.81041703,0.0833333333)`
returned zero rows. A separate bounding-box query of DR19 `allspec`, which
includes the cumulative SDSS and SDSS-V spectrum inventory, also returned zero
rows. No public DR19 spectrum is present within 5 arcsec.

### LAMOST Data Release 11 v2.0

The official [LAMOST DR11 VO page](https://www.lamost.org/dr11/v2.0/vo)
publishes a Simple Cone Search endpoint. This request:

```text
https://www.lamost.org/dr11/v2.0/voservice/conesearch
  ?RA=310.0912903&DEC=72.81041703&SR=0.0013888889&VERB=3
```

returned `QUERY_STATUS=OK` and empty `TABLEDATA` at
`2026-07-22T05:38:04.427675Z`. No LAMOST DR11 low-resolution spectrum is
present within 5 arcsec.

## 3. UNIONS/CFIS photometry

The [CFIS DR3 description](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/community/unions/MegaPipe_CFIS_DR3.html)
offers calibrated `u` and `r` measurements and errors, which would be useful
inputs to a new, separately validated optical--infrared redshift fit. It does
not itself supply an authoritative catalog redshift for this candidate.

The anonymous CADC TAP query against `cfht.cfiscat` failed closed with:

```text
Table [ cfht.cfiscat ] is not found in TapSchema. Possible reasons:
table does not exist or permission is denied.
```

This matches the [official query documentation](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/community/unions/querydoc.html):
users must log into CADC and belong to `CFIS-read`. Caltech institutional
authentication alone is not evidence of that authorization.

An authenticated follow-up at `2026-07-22T02:10:13Z` separated general CADC
access from CFIS authorization. The local CADC proxy certificate for
`/CN=jfaber_1ff/OU=cadc/O=hia/C=ca` is valid through
`2026-08-20T02:45:02Z`, and a live read-only VOSpace listing succeeded. A live
CADC Group Management Service check nevertheless returned false for membership
in `CFIS-read`; the authenticated `youcat` query continued to return the same
hidden-table response. The machine can access CADC, but this identity cannot
read `cfht.cfiscat` until a group administrator grants `CFIS-read`.

### Owner acquisition step

1. Log into CADC/CANFAR and confirm membership in `CFIS-read`; if absent,
   request it from a CFIS principal investigator or `support@canfar.net`.
2. Run the [UNIONS catalog query](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/community/unions/query.html)
   at the position above with a 5-arcsec cone.
3. Export the merged row with identifiers, coordinates, angular separation,
   `U_MAG_AUTO`, `U_MAGERR_AUTO`, `R_MAG_AUTO`, `R_MAGERR_AUTO`, curve-of-growth
   and aperture-corrected magnitudes and errors, image-quality fields,
   morphology, and flags. Freeze query, bytes, retrieval time, and SHA-256.
4. Treat any resulting redshift as a new fit requiring its own validation;
   the photometry must not directly overwrite either STRM value.

## 4. Classification-only and equivalent checks

At `2026-07-21T21:31Z`, anonymous queries of the official
[Gaia DR3 TAP service](https://gea.esac.esa.int/archive/documentation/GDR3/)
returned zero rows within 5 arcsec from each of:

- `gaiadr3.gaia_source`;
- `gaiadr3.galaxy_candidates` joined to `gaia_source`;
- `gaiadr3.qso_candidates` joined to `gaia_source`.

Therefore Gaia supplies neither a stellar astrometric rejection nor an
extragalactic classification/redshift here.

The official BASS DR3 XGBoost catalog is public only as a roughly 46.7 GB bulk
file at the National Astronomical Data Center. The VizieR mirror
`J/MNRAS/506/1651` contains only a 1,000-row sample, not the full
110,896,598-row classified product. A sample non-match cannot adjudicate this
candidate; the bulk file was not downloaded. The public BASS coadd web service
did not yield a defensible source row in this run.

As a higher-value equivalent, anonymous NOIRLab queries of Legacy Surveys DR10
`ls_dr10.tractor` returned zero rows within 5 arcsec. There is no independent
DR10 morphology or photometric-redshift row to use at this position.

### Additional northern-survey sweep

An additional source-level sweep on `2026-07-22 UTC` checked surveys that could
either supply an independent photometric redshift or test the quasar/blend
interpretation:

| survey or service | radius | result | scientific use |
|---|---:|---|---|
| [J-PLUS DR4](https://www.j-plus.es/datareleases/data_release_dr4) dual-object and tile services | 5 arcsec | zero object rows and zero tile rows | The position is not covered; its 12-band photometric redshifts cannot be used. |
| J-PAS EDR dual-object and tile services | 5 arcsec | zero object rows and zero tile rows | The position is not covered. |
| [LoTSS DR3](https://lofar-surveys.org/dr3.html) source catalog | 10 arcsec | zero rows | No cataloged 120--168 MHz counterpart. |
| [VLASS quick-look catalog](https://cirada.ca/vlasscatalogueql0) | 10 arcsec | zero rows | No cataloged 3 GHz counterpart. |
| NVSS, WENSS, and TGSS ADR1 | 30, 60, and 30 arcsec | zero rows | No brighter low-resolution radio counterpart. |
| [eROSITA eRASS1](https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/) | 30 arcsec | zero rows | No cataloged all-sky X-ray counterpart. |
| 5XMM-DR15, Chandra Source Catalog 2.1.1, and Swift 2SXPS | 30 arcsec | zero rows | No cataloged pointed X-ray counterpart. |
| NED | 10 arcsec | one WISE infrared-source entry, no redshift and no redshift measurement | Repeats the known WISE source; adds no distance constraint. |
| SIMBAD | 10 arcsec | zero rows | Adds no independent classification or redshift. |

The radio and X-ray non-detections do not distinguish a normal galaxy at low
redshift from one near `z=0.47`; they only fail to provide positive evidence for
a radio- or X-ray-bright active nucleus. J-PLUS and J-PAS would have been the
most useful independent multi-band photometric-redshift catalogs, but neither
covers this position. UNIONS/CFIS therefore remains the only identified public
northern imaging program likely to add a decisive optical band and sharper
morphology here, subject to `CFIS-read` access and a separately validated fit.

## Disposition

- The combined row is now identified exactly as PS1
  `objID=195373100910393540`; the legacy `0.012668989` value is its `z_phot0`.
- The shared WISE `cntr` across two PS1 objects, separated by `0.9962` arcsec,
  prevents treating the infrared association as uniquely resolved.
- Both supplied classifications and the target row's redshift are explicit
  extrapolations. The low-redshift value is attributable and source-row
  verified, but not scientifically validated.
- Public DESI, SDSS, LAMOST, Gaia, and Legacy Surveys searches add only
  documented non-detections.
- J-PLUS and J-PAS do not cover the position. Additional radio and X-ray
  catalogs contain no counterpart and therefore add no redshift constraint.
- Freeze the CasJobs query, job identifier, and retrieval time beside the
  supplied bytes. CADC/CFIS access remains useful if `CFIS-read` can be
  obtained.
- Until independent data adjudicate them, retain both redshifts as attributable
  but mutually inconsistent. No scientific re-adjudication is authorized here.
