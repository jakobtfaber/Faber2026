# Zach candidate: inter-catalog redshift investigation

Date: 2026-07-21 PDT / 2026-07-22 UTC  
Position: RA `310.0912903 deg`, Dec `+72.81041703 deg` (ICRS)  
Search radius unless stated otherwise: `5 arcsec`

## Question and boundary

The legacy spreadsheet attributes `z_phot = 0.012668989` to the combined
WISE--Pan-STARRS--STRM catalog. The frozen optical-only PS1--STRM row for PS1
`objID=195373100910393540` gives `z_phot = 0.4693608582 +/- 0.047097985` and
`extrapolation_Photoz=1`. Can official source-row evidence, public spectra,
independent northern photometry, or classification catalogs distinguish them?

This note does not change the adopted redshift, foreground verdict, or budget
eligibility.

## Result

**Not yet.** Every public spectroscopic and classification query below was a
non-detection. The two decisive source-level checks are access-blocked:

1. MAST CasJobs authentication is required to extract the exact combined
   WISE--PS1--STRM row.
2. The UNIONS/CFIS catalog requires a CADC account authorized for the
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

The full compressed strip was deliberately not downloaded. Anonymous MAST
CasJobs does not permit row extraction and no CasJobs credentials were present
in the execution environment.

### Owner acquisition step

Create or sign into a free [MAST CasJobs](http://mastweb.stsci.edu/mcasjobs/)
account, select context `HLSP_WISE_PS1_STRM`, and run:

```sql
SELECT TOP 20 *
FROM catalogRecordRowStore
WHERE objID = 195373100910393540
  AND ABS(raMean - 310.0912903) < 0.001
  AND ABS(decMean - 72.81041703) < 0.001
```

Export the result as CSV without opening it in spreadsheet software. Freeze
the original bytes, retrieval UTC time, query text, and SHA-256. At minimum,
retain `objID`, `raMean`, `decMean`, `distance_Deg`, `sqrErr_Arcsec`,
`BayesFactor`, WISE `cntr`, WISE coordinates and photometric flags, `class`,
the three class probabilities, both classification coverage fields,
`z_phot`, `z_photErr`, `z_phot0`, `extrapolation_Photoz`,
`cellDistance_Photoz`, and `cellID_Photoz`.

This needs a MAST account, not Caltech journal access.

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

## Disposition

- Same-object association remains strongly supported by the sub-milliarcsecond
  agreement of the recorded PS1 coordinates, but the combined official row is
  not yet frozen.
- Public DESI, SDSS, LAMOST, Gaia, and Legacy Surveys searches add only
  documented non-detections.
- The first required owner action is a MAST CasJobs export. CADC/CFIS access is
  useful second, if `CFIS-read` can be obtained.
- Until those artifacts are checked, retain both redshifts as attributable but
  mutually inconsistent. No scientific re-adjudication is authorized here.
