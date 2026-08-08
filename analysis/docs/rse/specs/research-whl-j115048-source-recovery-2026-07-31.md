# WHL J115048.0+714428 source recovery

Date: 2026-07-31

Scope: source recovery and identity adjudication only. This note does not alter
the foreground registry, manuscript, result trust, provenance state, or the
parent submodule pin, and it performs no compile or integration change.

## Result

Treat WHL J115048.0+714428 as an older, poorer catalog fragment or alternate
center of the system represented by J115120.4+714435 in Wen & Han (2024), not
as a second additive halo. The justified cluster-budget input remains the
single Wen & Han (2024) row, with `M500=1.48e14 Msun` and `r500=0.729 Mpc`.
No second cluster dispersion contribution is justified.

This is a catalog-evidence adjudication, not direct observation of the halo
structure. Wen & Han (2024) publish the prior-catalog family (`Cat=WHL`) but
not the exact old-to-new identifier map or member list.

## Primary-source rows

### WHL12

Source: Wen, Han & Liu (2012), VizieR `J/ApJS/199/34`, DOI
`10.26093/cds/vizier.21990034`.

Query:

```text
https://cdsarc.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/199/34/table1&RAJ2000=177.5..178.0&DEJ2000=71.5..72.0&-out=WHL,RAJ2000,DEJ2000,zph,zsp,r200,RL*,N200,Other
```

Exact relevant row:

```text
J115048.0+714428  177.69998  +71.74124  0.1893  [no zsp]  0.92  12.03  12  [no other-catalog identifier]
```

The published columns are `r200`, richness `RL*`, and `N200`; WHL12 does not
publish `M500` or `r500` for this row. Downloaded CDS artifact
`table1.dat.gz` SHA-256:
`da5dbcc656e86f26cae618e60b8af81b32cd23fe80218b27ef24faccbacf4e54`.

### WH15 update

Source: Wen & Han (2015), VizieR `J/ApJ/807/178/table3`, DOI
`10.1088/0004-637X/807/2/178`.

Query:

```text
https://cdsarc.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJ/807/178/table3&RAJ2000=177.5..178.0&DEJ2000=71.5..72.0&-out=WHL,RAJ2000,DEJ2000,zph,zsp,r200,RL*,N200,r500,RL*500,N500sp,N500
```

Exact relevant row:

```text
J115048.0+714428  177.69998  +71.74124  0.1893  [no zsp]  0.92  12.03  12  0.59  11.30  0  5
```

WH15 therefore supplies a source-defined `r500=0.59 Mpc`, but no per-row
`M500`. Its published mass-proxy relation is

```text
log10(M500/[1e14 Msun]) = 1.08 log10(RL*500) - 1.37,
```

with stated proxy uncertainty 0.14 dex. For `RL*500=11.30`, this gives
`M500=0.5852e14 Msun`. This is a derived optical proxy, not a direct mass
measurement. Downloaded CDS `table3.dat.gz` SHA-256:
`0a4ce08e8b0f2a3d7f861cfdbb70c187595a3bb37e9cc5885147cadd455fd5f9`.
The arXiv v2 source archive for `1506.04503` has SHA-256
`3a73130cc723c8c4a86d0bcbba443b7f7331f255c4a31957a968ee8d6910db22`.

### Wen & Han 2024

Source: Wen & Han (2024), VizieR `J/ApJS/272/39/table2`, DOI
`10.26093/cds/vizier.22720039`.

Query:

```text
https://cdsarc.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/272/39/table2&Name=J115120.4%2B714435&-out=ID,Name,RAJ2000,DEJ2000,zCl,f_zCl,r500,lam500,M500,Ngal,Cat
```

Exact row:

```text
1254337  J115120.4+714435  177.83488  +71.74319  0.1938  0  0.729  32.69  1.48  14  WHL
```

Here `f_zCl=0` means the catalog redshift is photometric, `M500` is in units
of `1e14 Msun`, and `Cat=WHL` identifies a counterpart in the WHL catalog
family. The arXiv source archive for `2404.02002` has SHA-256
`baf4f0f7104215018c38b67093a8d40be7d0d84954f40de2f4dd0ca493f9ac78`.

## Crossmatch calculation

The spherical separation between the WHL12 and Wen & Han (2024) centers is
`2.538489 arcmin`. In the flat cosmology used by Wen & Han (2024),
`H0=70 km/s/Mpc` and `Omega_m=0.3`, the proper scale at `z=0.1938` is
`193.136 kpc/arcmin`; the projected separation is therefore `490.274 kpc`, or
`0.6725 r500` for the Wen & Han (2024) radius. The catalog redshift difference
is `0.0045`.

Within the searched box `177.5 <= RA <= 178.0 deg`,
`71.5 <= Dec <= 72.0 deg`, WHL J115048.0+714428 is the only old WHL row at a
compatible redshift and within `1.5 r500` of J115120.4+714435. The other old
WHL row at nearly the same redshift, J115128.2+713637 (`zph=0.1903`), is
`7.9972 arcmin` from the Wen & Han (2024) center and appears separately in the
2024 catalog.

Wen & Han (2024) state that when prior-catalog candidates lie in a close
cluster-binary configuration with separation below `1.5 r500`, their cleaning
regards the pair as one cluster and removes the poorer entry. The observed
catalog transition has that signature: the older low-richness center is
absent, while the surviving richer row is marked `Cat=WHL`.

## Inference boundary and falsifier

VizieR provides no public Wen & Han (2024) member table or exact cross-ID field
linking the two names. The fragment adjudication is therefore an inference
from the unique positional/redshift match, the published `Cat=WHL` flag, the
relative richnesses, the disappearance of the older center, and the stated
catalog-cleaning rule.

The adjudication is falsified by any immutable producer artifact or source
statement assigning WHL J115048.0+714428 to a different Wen & Han (2024)
system, or by spectroscopy/member velocities demonstrating two distinct halos
at these centers. In that case, a separate mass/radius receipt and a reviewed
second cluster-column calculation would be required before changing the
budget.

## Budget consequence

The evidence justifies one modeled cluster, J115120.4+714435, using the
published Wen & Han (2024) `M500` and `r500`. Adding the WH15 optical proxy as
a second halo would double-count the same catalog system. This finding does
not by itself validate the cluster gas profile, dispersion calculation, or
manuscript admission.
