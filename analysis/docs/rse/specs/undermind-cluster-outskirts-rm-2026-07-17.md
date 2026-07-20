# Cluster outskirts RM synthesis

##### [**Undermind**](https://undermind.ai)

---


## Table of Contents

- [Cluster outskirts RM excess and scatter](#cluster-outskirts-rm-excess-and-scatter)
  - [Purpose and scope](#purpose-and-scope)
  - [Candidate-set overview](#candidate-set-overview)
  - [Study-by-study extraction](#study-by-study-extraction)
    - [Anderson et al. 2024: galaxy groups and the cosmic web](#anderson-et-al.-2024-galaxy-groups-and-the-cosmic-web)
    - [Anderson et al. 2021: Fornax](#anderson-et-al.-2021-fornax)
    - [Loi et al. 2025: dense Fornax RM grid](#loi-et-al.-2025-dense-fornax-rm-grid)
    - [Khadir et al. 2025: A3581](#khadir-et-al.-2025-a3581)
    - [Böhringer et al. 2016: CLASSIX](#böhringer-et-al.-2016-classix)
    - [Osinga et al. 2025: Planck clusters](#osinga-et-al.-2025-planck-clusters)
    - [Alonso-López et al. 2025: Shapley Supercluster Core](#alonso-lópez-et-al.-2025-shapley-supercluster-core)
    - [Osinga et al. 2022: depolarization study](#osinga-et-al.-2022-depolarization-study)
    - [Kim et al. 1991: historical excess-RM study](#kim-et-al.-1991-historical-excess-rm-study)
  - [Cross-study comparability issues](#cross-study-comparability-issues)
    - [Radius conventions](#radius-conventions)
    - [Scatter definitions](#scatter-definitions)
    - [RM frame and redshift handling](#rm-frame-and-redshift-handling)
    - [Source-class mixing](#source-class-mixing)
    - [Depolarization and missing sources](#depolarization-and-missing-sources)
  - [Convenience bracket for the target mass regime](#convenience-bracket-for-the-target-mass-regime)
  - [Evidence limitations](#evidence-limitations)
  - [References](#references)

# Cluster outskirts RM excess and scatter

## Purpose and scope

This report synthesizes every plausibly relevant paper returned by the search **Cluster outskirts RM excess and scatter**. It is deliberately inclusive. Papers are not silently removed because they are weak matches: direct candidates, boundable cases, methodological complements, and historical borderline studies are all listed with explicit reasons for retaining or downgrading them.

The target comparison is a system with $`M_{500}\le 1.7\times10^{14}\,M_\odot`$, but the report does not adjudicate admission or compute the downstream frozen-rule median. It records the measurements, definitions, and caveats needed for that later step.

Reported radial bins are preserved as published. No value is interpolated to $`0.6-
1.0R_{500}`$. Where a figure is the only source, the value is labeled as a figure estimate. Where the paper uses a radius other than $`R_{500}`$ or $`R_{200}`$, the conversion is described rather than imposed.

## Candidate-set overview

| Study | Sample and mass | Radial coordinate | Main reported quantity | Status for later admission |
|:---|:---|:---|:---|:---|
| \[And24\] | 55 groups; halo masses $`10^{12.5}-
10^{14}\,M_\odot`$ | $`0-
2`$ and $`2-
7`$ splashback radii; approximate $`R_{\rm splash}\approx2R_{200c}`$ conversion | $`\sigma_{\rm RRM}`$ enhancement $`6.9\pm1.8`$ and $`4.2\pm1.2`$ rad m$`^{-2}`$ | Strong low-mass bracket, but radial convention is splashback rather than direct $`R_{500}`$ or $`R_{200}`$ |
| \[And21\] | Fornax; total mass $`6^{+3}_{-1}\times10^{13}\,M_\odot`$ | Physical/angular bins; virial radius quoted but not used as normalized coordinate | Scatter enhancement $`16.8\pm2.4`$ rad m$`^{-2}`$ within 1 degree | Borderline below-target precedent; no formal $`r/R_{500}`$ or $`r/r_{200}`$ profile |
| \[Loi25\] | Fornax; $`M_{\rm vir}=5\times10^{13}\,M_\odot`$ | Physical annuli to $`0.73R_{\rm vir}`$ | Radial $`\sigma_{\rm RM}`$ profile, about 11–13.5 rad m$`^{-2}`$ in outer bins | Borderline; normalized to $`R_{\rm vir}`$, not $`R_{500}`$ or $`R_{200}`$ |
| \[Kha25\] | A3581; $`M_{500}=2.15\times10^{14}\,M_\odot`$ | Moving profile to $`2R_{500}`$ | Corrected scatter declines from about 15–20 to 5–7 rad m$`^{-2}`$, then rises outside | Strong near-above-target profile; figure values near the requested range |
| \[Boe16\] | CLASSIX; 65 clusters with sightlines; quoted $`M_{500}=0.02-
19.1\times10^{14}\,M_\odot`$ | $`<0.5r_{500}`$, $`0.5-
1r_{500}`$, $`<r_{500}`$, and $`1-
10r_{500}`$ | Galactic-corrected scatter $`112\pm43`$ in $`0.5-
1r_{500}`$; $`120\pm21`$ inside $`r_{500}`$ | Strong radial match, but heavily weighted toward massive clusters and mostly embedded/unknown sources |
| \[Osi24\] | 124 Planck clusters; mean mass $`5.7\times10^{14}\,M_\odot`$ | $`<0.5R_{500}`$, $`0.5-
1R_{500}`$, $`<R_{500}`$, and outside control | Rest-frame corrected scatter $`127\pm30`$ for all sources in $`0.5-
1R_{500}`$ | Strong above-target benchmark; source-class and depolarization biases matter |
| \[Alo25\] | A3558, A3562, SC 1327, SC 1329; $`M_{500}=0.5-
9.8\times10^{14}\,M_\odot`$ | Nearest-object $`d_{\rm nrst}=r_{\rm nrst}/r_{500}`$, approximately 0.3–1.8 | Excess scatter $`30.52\pm4.55`$ rad m$`^{-2}`$ for SSC; figure profile flattens beyond about 0.7 $`r_{500}`$ | Strong normalized-radius candidate, but overlapping halos and supercluster geometry complicate interpretation |
| \[Osi22\] | 124 massive clusters; approximately $`2-
12\times10^{14}\,M_\odot`$ | $`r/R_{500}`$ | Depolarization profile and per-source $`\sigma_{\rm RM}`$ catalog, not a cluster-induced RM-scatter profile | Methodological borderline; useful context, not a primary excess measurement |
| \[Kim91\] | 161 core-sample sources; 44 Abell clusters listed; no $`M_{500}`$/$`M_{200}`$ masses | $`R_A/6`$, $`R_A/3`$, and $`R_A`$, with $`R_A=3h_{50}^{-1}`$ Mpc | Excess width $`100\pm36`$ in $`<R_A/6`$ and $`36\pm15`$ in $`R_A/6-
R_A/3`$ | Historical borderline; exact sample and estimator are now documented, but no modern mass convention or direct $`R_{500}`$/$`R_{200}`$ mapping |

## Study-by-study extraction

### Anderson et al. 2024: galaxy groups and the cosmic web

\[And24\] analyzes 22,817 RMs toward background radio sources associated with 55 nearby groups at approximately $`0.005\lesssim z\lesssim0.025`$. The group halo masses span $`10^{12.5}-
10^{14}\,M_\odot`$. The mass is a group-halo estimate derived from integrated $`K`$-band luminosity, rather than a directly quoted $`M_{500}`$ or $`M_{200}`$.

The radial coordinate is $`\xi=\beta_{\rm RM}/\theta_{\rm splash}`$. The published bins are:

- Intragroup medium: $`0\le\xi<2`$ splashback radii.
- WHIM/interface region: $`2\le\xi<7`$ splashback radii.
- Field/control: $`\xi>7`$ splashback radii.

The authors state a conservative conversion of approximately $`R_{\rm splash}\simeq2R_{200c}`$, but do not provide a direct $`R_{500}`$ profile. The conversion therefore supports a boundable comparison rather than a literal $`0.6-
1.0R_{500}`$ measurement.

The principal results are enhancements in residual-RM scatter, not a coherent mean RM offset:

- $`6.9\pm1.8`$ rad m$`^{-2}`$ for $`0-
  2R_{\rm splash}`$.
- $`4.2\pm1.2`$ rad m$`^{-2}`$ for $`2-
  7R_{\rm splash}`$.
- The field region has a measured scatter of about $`7.1`$ rad m$`^{-2}`$, while the expected extragalactic point-source field scatter is about 6 rad m$`^{-2}`$.
- The fitted residual-RM location is $`0.02\pm0.06`$ rad m$`^{-2}`$, consistent with no mean RM excess.

RMs are reported in the observed frame. Galactic foreground subtraction uses the median of the nearest 40 RMs outside a 0.4-degree exclusion zone around each source. Important caveats are uneven group weighting—90% of RMs are associated with half the groups and one group contributes nearly 20%—and uneven radial sampling from group overlap and survey coverage.

**Admission note:** This is the strongest conservative low-mass ensemble bracket, but its radial coordinate is splashback-based. It should remain visible whether the downstream rule treats the $`R_{\rm splash}`$ to $`R_{200}`$ conversion as sufficient.

### Anderson et al. 2021: Fornax

\[And21\] uses 870 polarized sources in the Fornax field. The sources used for the cluster analysis are treated as background sources; the only identified cluster-hosted radio source is associated with NGC 1399. The Fornax total mass is quoted as $`6^{+3}_{-1}\times10^{13}\,M_\odot`$, without an explicit $`M_{500}`$ or $`M_{200}`$ convention. The cluster redshift is $`z=0.0048`$.

The main result is a scatter enhancement of $`16.8\pm2.4`$ rad m$`^{-2}`$ within 1 degree, corresponding to 360 kpc. The within-1-degree and outside-1-degree scatters are 20.5 and 11.8 rad m$`^{-2}`$, respectively. The uncertainty is a bootstrap 95% interval. The values are observed-frame; the redshift correction is negligible at this redshift.

The exact annular edges used in the binning experiment are 0.167, 1.014, 1.737, 2.324, 2.826, 3.313, 3.764, and 4.309 degrees. There are 76 polarized sources within 1 degree. The paper quotes a virial radius of 1.96 degrees, or 705 kpc, so the primary enhancement aperture is approximately 0.51 of the quoted virial radius. However, the paper does not present the result as a formal $`r/R_{\rm vir}`$, $`r/R_{500}`$, or $`r/r_{200}`$ profile, and it does not provide an $`R_{500}`$ or $`R_{200}`$ conversion.

Galactic RM subtraction uses a second-degree polynomial surface fit to the position-dependent Faraday-depth values. The signal is strongly asymmetric, with a southwest bow-shock-like feature and a northeast wake associated with the ongoing merger. The Faraday-active region extends beyond the detectable X-ray ICM, and the authors report no evidence that central depolarization explains the source-count deficit.

**Admission note:** This is a deliberately retained borderline study and the precedent for a below-target Fornax bracket. Under a strict normalized-radius rule it would be excluded; under the broader frozen-set precedent it remains a candidate.

### Loi et al. 2025: dense Fornax RM grid

\[Loi25\] detects 508 polarized sources across approximately 6.35 square degrees. Five are cluster sources and 503 are background sources. The Fornax virial mass is quoted as $`M_{\rm vir}=5\times10^{13}\,M_\odot`$. The analyzed circular region extends to approximately 1.4 degrees, or 510–520 kpc, stated to be about $`0.73R_{\rm vir}`$. The cluster is at approximately 20 Mpc; 71 background sources have identified redshifts with median $`z\approx0.11`$, but this is not the cluster redshift.

The radial profiles use annuli of width 8.5 arcmin, corresponding to 51 kpc. The paper reports the following outer-bin values from its radial-profile figure:

| Approximate radius | Approximate fraction of quoted $`R_{\rm vir}`$ | Mean RM | $`\sigma_{\rm RM}`$ |
|:---|---:|---:|---:|
| 400 kpc | 0.58 | about 5 rad m$`^{-2}`$ | about 13.5 rad m$`^{-2}`$ |
| 460 kpc | 0.67 | about 4.5 rad m$`^{-2}`$ | about 11 rad m$`^{-2}`$ |
| 510 kpc | 0.73 | about 4 rad m$`^{-2}`$ | about 11.5 rad m$`^{-2}`$ |

These are figure estimates, not tabulated values. The authors subtract a Galactic RM model based on the Anderson et al. 2021 two-dimensional polynomial reconstruction. The outer scatter plateaus near 13 rad m$`^{-2}`$; the authors attribute about 6 rad m$`^{-2}`$ to source-to-source variation and suggest that the remainder may arise from Fornax outskirts and cosmic-web structure. Positive polarized-intensity bias is corrected, the catalog is reported as 99.99% reliable, and about 95% of sources are Faraday simple.

The paper does not provide an explicit $`R_{500}`$ or $`R_{200}`$, nor a conversion from $`R_{\rm vir}`$ to either. Sector-dependent profiles, a high-RM stripe, and possible sloshing or filamentary accretion complicate a spherical interpretation.

**Admission note:** Retain as a low-mass, high-density radial-profile complement, but mark as boundable only through an external radius conversion. Do not silently treat $`0.73R_{\rm vir}`$ as a measured $`R_{500}`$ or $`R_{200}`$ coordinate.

### Khadir et al. 2025: A3581

\[Kha25\] analyzes 115 initial RMs within $`2R_{500}`$ of A3581. Four embedded cluster-member sources are excluded, leaving 111 background RMs. The cluster has $`M_{500}=2.15\times10^{14}\,M_\odot`$, $`R_{500}=0.925`$ Mpc, and $`z=0.0221\pm0.0050`$. It is therefore slightly above the target mass cap but close enough to serve as a near-above-target bracket.

The profile uses a moving bin containing 20 points, with a median physical width of 0.27 Mpc, or approximately 0.29 $`R_{500}`$. The study analyzes the profile to $`2R_{500}`$, while the semianalytic model fitting is restricted to the inner 0.75 Mpc.

The corrected scatter profile is approximately:

- About 10–12 rad m$`^{-2}`$ near 0.6 $`R_{500}`$.
- About 5–7 rad m$`^{-2}`$ near 0.8 $`R_{500}`$, the end of the monotonic decline.
- About 8–10 rad m$`^{-2}`$ near 1.0 $`R_{500}`$, followed by a peak near 1.2 $`R_{500}`$.

These are figure-based estimates with typical shaded uncertainties of roughly 2–5 rad m$`^{-2}`$, not tabulated fixed-bin measurements. The extrinsic control scatter is $`7.0\pm1.3`$ rad m$`^{-2}`$, estimated from two control regions and subtracted in quadrature along with measurement-error variance. It is a control scatter, not the cluster excess. The extracted results are in the observed frame; the paper does not apply a separate $`(1+z)^2`$ correction to the profile values, although the difference is only about 4.5% at this redshift.

The profile is non-monotonic beyond 0.75 Mpc, with a secondary enhancement near 1.1 Mpc attributed to a possible merger with group \[DZ2015b\] 276. The RM density is stable with radius, reducing concern that the decline is caused only by source incompleteness. Most sources are Faraday simple, and no significant enhancement is found near individual cluster-member galaxies.

**Admission note:** Strong candidate for a normalized-radius profile. The main cautions are that the requested-range values are figure estimates, the mass is above the target cap, and the outer enhancement may be merger-specific.

### Böhringer et al. 2016: CLASSIX

\[Boe16\] correlates 1,383 extragalactic RM measurements with the CLASSIX X-ray cluster survey. There are 65 clusters with at least one RM sightline within $`r_{500}`$, containing 92 sources. The quoted cluster mass range is $`M_{500}=0.02-
19.1\times10^{14}\,M_\odot`$, derived from an X-ray-luminosity–mass relation calibrated with REXCESS.

The primary radial bins are $`<0.5r_{500}`$, $`0.5-
1r_{500}`$, $`<r_{500}`$, and a 1–10 $`r_{500}`$ control region. The Galactic-corrected row of the main table gives:

| Radial region | $`\sigma_{\rm RM}`$ | Notes |
|:---|---:|:---|
| $`<0.5r_{500}`$ | $`124\pm21`$ rad m$`^{-2}`$ | Galactic-corrected row |
| $`0.5-
1r_{500}`$ | $`112\pm43`$ rad m$`^{-2}`$ | Table value; text reportedly gives 144$`\pm43`$ |
| $`<r_{500}`$ | $`120\pm21`$ rad m$`^{-2}`$ | Galactic-corrected row |
| 1–10 $`r_{500}`$ | $`52\pm6`$ rad m$`^{-2}`$ | Control region |

The text–table discrepancy for the 0.5–1 $`r_{500}`$ bin must remain visible. The analysis combines source classes: approximately 61 sources are cluster members, 10 are confirmed background sources, and 26 have unknown redshift. Most clusters have only one sightline; Coma contributes 12.

The values are observed-frame. Galactic correction uses the mean RM in a 10-degree surrounding region, excluding other known clusters. The signal is strongly weighted toward the most luminous and massive systems: the more luminous half has scatter $`158\pm34`$ rad m$`^{-2}`$, versus $`62\pm11`$ rad m$`^{-2}`$ for the less luminous half.

**Admission note:** Strong radial match and an important historical benchmark, but not a clean low-mass constraint. Source-class mixing, sparse sightlines per cluster, and massive-cluster weighting should be retained as explicit caveats.

### Osinga et al. 2025: Planck clusters

\[Osi24\] studies 124 low-redshift Planck clusters at $`z<0.35`$, with a mean mass of $`5.7\times10^{14}\,M_\odot`$; only 15 of 124 have masses below $`3\times10^{14}\,M_\odot`$. The sample contains 819 polarized sources, of which 610 are used in the analysis: 231 sources inside clusters and 363 behind clusters. The paper uses $`R_{500}`$ as the radial scale.

The corrected, cluster-rest-frame scatter values are:

| Source class      | $`<0.5R_{500}`$ |        $`0.5-
                                        1.0R_{500}`$ | $`<R_{500}`$ | Outside control |
|:------------------|----------------:|-------------:|-------------:|----------------:|
| All sources       |    $`244\pm47`$ | $`127\pm30`$ | $`209\pm37`$ |      $`28\pm5`$ |
| Embedded/inside   |    $`196\pm40`$ | $`219\pm59`$ | $`200\pm33`$ |      $`27\pm8`$ |
| Background/behind |   $`312\pm100`$ |   $`51\pm6`$ | $`219\pm66`$ |      $`29\pm6`$ |

An extrinsic scatter of 9 rad m$`^{-2}`$, estimated at radii beyond 3 $`R_{500}`$, is subtracted in quadrature. The tabulated values are corrected by $`(1+z)^2`$ to the cluster rest frame. Galactic foreground subtraction uses the Hutschenreuter et al. 2022 map.

The profile is flatter than simple $`B\propto n_e^\eta`$ models. Near the center, highly scattered sources are likely depolarized and missing, which can artificially flatten the profile. Background-source scatter increases again beyond approximately 0.7 $`R_{500}`$, potentially because larger radii preferentially sample higher-mass clusters or intervening filaments. Cool-core and non-cool-core systems show different profiles.

**Admission note:** Strong above-target benchmark with an exact 0.5–1 $`R_{500}`$ bin and explicit frame correction. The mass mismatch and source-selection/depolarization biases make it unsuitable as a direct low-mass analogue, but valuable as an upper bracket.

### Alonso-López et al. 2025: Shapley Supercluster Core

\[Alo25\] analyzes the Shapley Supercluster Core, consisting of A3558, A3562, SC 1327, and SC 1329 at $`z\simeq0.048`$. The object properties are:

| Object  | $`M_{500}`$ \[$`10^{14}M_\odot`$\] | $`r_{500}`$ \[Mpc\] |
|:--------|-----------------------------------:|--------------------:|
| A3558   |                                9.8 |                 1.5 |
| A3562   |                                4.4 |                 1.2 |
| SC 1327 |                                2.0 |                 0.9 |
| SC 1329 |                                0.5 |                 0.6 |

The RM catalog contains 149 sources: 46 on-target and 103 off-target controls. The on-target sample contains 34 sources assigned to the clusters and 12 in the bridge; four on-target sources are identified as embedded.

The paper reports excess RM scatter after foreground and measurement-noise correction:

| Region          | Sources |                                 Excess scatter |
|:----------------|--------:|-----------------------------------------------:|
| SSC total       |      46 | $`30.52\pm4.55`$ rad m$`^{-2}`$, 6.7$`\sigma`$ |
| Bridge/groups   |      12 | $`25.32\pm8.48`$ rad m$`^{-2}`$, 3.0$`\sigma`$ |
| Cluster regions |      34 | $`27.20\pm4.97`$ rad m$`^{-2}`$, 5.5$`\sigma`$ |

Individual values are $`30.16\pm6.51`$ rad m$`^{-2}`$ for A3558 and $`27.69\pm8.73`$ rad m$`^{-2}`$ for A3562. The off-target scatter is $`12.32\pm1.54`$ rad m$`^{-2}`$.

The radial coordinate is the distance to the nearest cluster or group center, $`d_{\rm nrst}=r_{\rm nrst}/r_{500}`$, covering approximately 0.3–1.8. A sliding window of 16 points has a median width of roughly 0.3 $`r_{500}`$. Figure estimates for the profile are about 38–40 rad m$`^{-2}`$ at 0.6 $`r_{500}`$, about 30 at 0.7, about 25 at 0.8, about 22–24 at 0.9, and about 22 at 1.0. These values are estimates from the plotted profile, not fixed-bin measurements.

The RMs are observed-frame; the authors neglect redshift dilution because $`z\simeq0.048`$. Galactic subtraction uses the mean of the 50 nearest POSSUM RMs outside a 1.7-Mpc exclusion radius. The off-target region is defined using a tSZ boundary. The nearest-object coordinate is necessary because the supercluster is not spherical and halos overlap, especially beyond about 0.7 $`r_{500}`$. A merger or gas trail involving SC 1327 and A3562, plus possible beam depolarization at small radii, complicates interpretation.

**Admission note:** Strong normalized-radius candidate, including a below-target group (SC 1329) and a near-target group (SC 1327), but the reported profile is not a single isolated-halo profile. It should be retained as a supercluster/overlapping-halo case, not treated as an ordinary cluster benchmark.

### Osinga et al. 2022: depolarization study

\[Osi22\] uses 124 massive clusters at $`z<0.35`$, with approximate masses of $`2-
12\times10^{14}\,M_\odot`$, and 819 polarized radio-source components. Sources are classified as inside, behind, or in front of clusters, and the impact parameter is normalized by $`R_{500}`$.

The paper’s primary statistic is the depolarization ratio, not a cluster-induced RM-excess or RM-scatter profile. It models a per-source Faraday-dispersion parameter $`\sigma_{\rm RM}`$, and the electronic catalog contains fitted source-level RM and $`\sigma_{\rm RM}`$ values. The paper does not provide the requested population radial profile of excess $`\sigma_{\rm RM}`$ in the same sense as \[Osi24\].

The study is still relevant for systematics: depolarization increases toward cluster centers, background and embedded sources show similar depolarization trends at comparable radii, and the inferred central magnetic fields are approximately 5–10 $`\mu`$G under the adopted models.

**Admission note:** Retain as a methodological and selection-bias companion, but mark it as non-admissible if the frozen rule requires a reported cluster-induced RM excess or $`\sigma_{\rm RM}`$ radial measurement rather than per-source depolarization-fit parameters.

### Kim et al. 1991: historical excess-RM study

\[Kim91\] analyzes 161 extragalactic radio sources in the primary cluster sample, with 53 sources in the core sample and 108 in the larger-radius control sample. The paper lists 44 Abell clusters in its X-ray reference table, although not every listed cluster necessarily contributes a sightline. The source classes mix identified cluster members with background or unidentified sources; the authors state that removing cluster members does not materially change the result.

The radial scale is the Abell radius, defined as $`R_A=3h_{50}^{-1}`$ Mpc. The published bins are:

- Core I: $`r<R_A/6`$, approximately $`<0.5`$ Mpc; 30 sources.
- Core II: $`R_A/6<r<R_A/3`$, approximately 0.5–1.0 Mpc; 23 sources.
- Entire core: $`r<R_A/3`$; 53 sources.
- Intermediate region: $`R_A/3<r<R_A`$; 32 sources.
- Control sample: $`R_A/3<r<3R_A`$; 108 sources.

The excess width $`\sigma_c`$ is obtained by subtracting the control width in quadrature. The reported estimates are:

- Core I: $`100\pm36`$ rad m$`^{-2}`$, with a 99% interval of 64–137 rad m$`^{-2}`$.
- Core II: $`36\pm15`$ rad m$`^{-2}`$, with a 99% interval of 22–52 rad m$`^{-2}`$.
- Entire core: 99% interval of 46–83 rad m$`^{-2}`$.
- Intermediate/control widths: approximately 20 rad m$`^{-2}`$, consistent with one another.

Cluster redshifts span approximately $`z=0.01-
0.1`$, while background sources extend beyond $`z=1.4`$. The values are observed-frame RMs; no $`(1+z)^2`$ correction is applied. Galactic RM is estimated from the median of sources within 15 degrees after removing 2-sigma outliers. The control sample is intended to capture intrinsic source RM plus residual Galactic structure.

No modern cluster mass convention is provided. The study gives X-ray central electron densities and core radii for 19 clusters, but not $`M_{500}`$, $`M_{200}`$, or a direct conversion from Abell radius to either. Important caveats include the assumption that intrinsic source RM distributions are the same in cluster and control samples, possible beam/source-resolution suppression of RM variation, and the higher fraction of cluster members at small radii.

**Admission note:** The uploaded PDF resolves the sample-count, radial-bin, frame, and foreground-treatment gaps. Retain as a historical borderline candidate for completeness, but keep it outside a strict modern $`r/R_{500}`$ or $`r/R_{200}`$ calculation unless an external radius conversion is explicitly allowed.

## Cross-study comparability issues

### Radius conventions

The studies do not use one common radial coordinate. \[Boe16\], \[Osi24\], \[Alo25\], and \[Kha25\] use $`r/R_{500}`$ or $`r_{500}`$ directly. \[And24\] uses splashback radii and gives an approximate relation to $`R_{200c}`$. \[And21\] and \[Loi25\] use physical bins and/or $`R_{\rm vir}`$ without a direct $`R_{500}`$ or $`R_{200}`$ conversion. \[Kim91\] uses exact Abell-radius bins, but supplies no modern overdensity-radius mapping.

The Fornax papers therefore cannot be treated as exact measurements in the requested normalized interval without an external conversion. Their value is as a deliberately retained low-mass bracket, not as a clean radial match.

### Scatter definitions

The reported quantities are not identical:

- \[And24\] reports an enhancement in the standard deviation of residual RMs relative to field behavior.
- \[And21\] reports a within-versus-outside scatter enhancement with a bootstrap uncertainty.
- \[Boe16\] reports raw or Galactic-corrected ensemble standard deviations in radial bins.
- \[Osi24\] reports corrected, rest-frame $`\sigma_{\rm RRM}`$, subtracting extrinsic scatter in quadrature.
- \[Kha25\] reports a moving-bin corrected scatter after subtracting measurement-error and control-region variance.
- \[Alo25\] reports an excess scatter after subtracting the off-target variance and measurement noise.
- \[Osi22\] reports per-source depolarization-fit $`\sigma_{\rm RM}`$, not the same population excess statistic.
- \[Kim91\] reports excess broadening of the residual-RM distribution, obtained by quadrature subtraction of the control width, with explicit 99% intervals.

A later frozen rule should preserve these distinctions rather than assume that every quoted $`\sigma_{\rm RM}`$ is the same estimator.

### RM frame and redshift handling

\[Osi24\] explicitly applies a $`(1+z)^2`$ correction to report cluster-rest-frame scatter. \[And21\] and \[Alo25\] use observed-frame values and have low enough redshifts that the correction is small. \[Kha25\] appears to retain observed-frame profile values, with a small correction at $`z=0.0221`$. \[And24\], \[Boe16\], \[Loi25\], and \[Osi22\] require care because the extracted material does not establish a uniform rest-frame convention. \[Kim91\] explicitly uses observed-frame RMs without a $`(1+z)^2`$ correction. These frame labels should remain attached to every value used downstream.

### Source-class mixing

The cleanest background-source samples are \[And24\], \[And21\], \[Loi25\], and \[Kha25\]. \[Osi24\] explicitly separates embedded and background sources. \[Alo25\] includes both on-target background and embedded sources in a complex supercluster geometry. \[Boe16\] is a mixed sample dominated by cluster members and sources with unknown redshift. \[Osi22\] is explicitly source-class aware but is primarily a depolarization study.

### Depolarization and missing sources

Central depolarization can remove the most strongly scattered sources from a polarized-source catalog. This is an explicit concern in \[Osi24\] and a model/systematics issue in \[Osi22\]. \[Kha25\] finds a stable RM density with radius, which weakens—but does not eliminate—this concern. \[Alo25\] estimates beam depolarization to be minor, while \[And21\] finds no central fractional-polarization decrement. These differences matter because a flat or declining radial $`\sigma_{\rm RM}`$ profile may be partly selection-driven.

## Convenience bracket for the target mass regime

This section is descriptive only. It does not compute the downstream frozen-rule median or decide which studies are admitted.

- **Below-target group bracket:** \[And24\] covers 55 groups with halo masses $`10^{12.5}-
  10^{14}\,M_\odot`$, with a 6.9$`\pm1.8`$ rad m$`^{-2}`$ scatter enhancement inside 2 splashback radii.
- **Below-target low-mass cluster bracket:** \[And21\] gives $`16.8\pm2.4`$ rad m$`^{-2}`$ within 1 degree in Fornax, whose quoted total mass is $`6^{+3}_{-1}\times10^{13}\,M_\odot`$. \[Loi25\] gives an outer Fornax scatter of about 11–13.5 rad m$`^{-2}`$, but only in $`R_{\rm vir}`$-normalized/physical coordinates.
- **Near-above-target bracket:** \[Kha25\] has $`M_{500}=2.15\times10^{14}\,M_\odot`$, with figure-estimated corrected scatter of roughly 5–12 rad m$`^{-2}`$ across the outer profile and a secondary enhancement near 1.2 $`R_{500}`$.
- **Mixed-mass group/cluster bracket:** \[Alo25\] includes SC 1329 at $`M_{500}=0.5\times10^{14}\,M_\odot`$ and SC 1327 at $`2.0\times10^{14}\,M_\odot`$, but the measured excess is for overlapping supercluster structures rather than isolated halos.
- **Above-target benchmarks:** \[Boe16\] reports 112$`\pm43`$ rad m$`^{-2}`$ in 0.5–1 $`r_{500}`$, but its broad mass range is dominated by luminous clusters. \[Osi24\] reports 127$`\pm30`$ rad m$`^{-2}`$ in 0.5–1 $`R_{500}`$ for a mean-mass $`5.7\times10^{14}\,M_\odot`$ Planck sample.

The low-mass results are therefore of order several to roughly 17 rad m$`^{-2}`$ in the available broad outskirts-scale measurements, while the massive-cluster benchmarks are an order of magnitude higher in some directly normalized bins. That contrast is descriptive and should not be interpreted as a calibrated mass scaling: the studies differ in source class, radius, estimator, redshift correction, and halo selection.

## Evidence limitations

The search returned a useful but heterogeneous candidate set. The main gap is a large, low-mass, isolated-cluster sample with at least ten polarized sightlines per system, a direct $`0.6-
1.0R_{500}`$ bin, and a consistently defined control-subtracted $`\sigma_{\rm RM}`$. The current set instead combines low-mass group ensembles, Fornax case-study grids, near-target individual clusters, complex supercluster structures, and massive-cluster stacks.

The uploaded \[Kim91\] PDF resolves its sample-count, radial-bin, frame, and foreground-treatment details, but it still lacks a modern $`M_{500}`$/$`M_{200}`$ mass convention and direct $`R_{500}`$/$`R_{200}`$ mapping. The Fornax studies remain important borderline cases because they support the low-mass bracket but do not provide the requested modern overdensity normalization directly.

---

## References

\[And24\] C. Anderson *et al.*, “Probing the magnetised gas distribution in galaxy groups and the cosmic web with POSSUM Faraday Rotation Measures,” *Monthly Notices of the Royal Astronomical Society*, Jul. 2024, doi: [10.1093/mnras/stae1954](https://doi.org/10.1093/mnras/stae1954).

\[And21\] C. Anderson *et al.*, “Early Science from POSSUM: Shocks, turbulence, and a massive new reservoir of ionised gas in the Fornax cluster,” *Publications of the Astronomical Society of Australia*, vol. 38, Feb. 2021, doi: [10.1017/pasa.2021.4](https://doi.org/10.1017/pasa.2021.4).

\[Loi25\] F. Loi *et al.*, “The MeerKAT Fornax Survey. IV. A close look at the cluster physics through the densest rotation measure grid,” *Astronomy &amp; Astrophysics*, Jan. 2025, doi: [10.1051/0004-6361/202451711](https://doi.org/10.1051/0004-6361/202451711).

\[Kha25\] A. Khadir *et al.*, “Revealing the Magnetization of the Intracluster Medium of A3581 Using Background Faraday Rotation Measures from the POSSUM Survey,” *The Astrophysical Journal*, vol. 997, Nov. 2025, doi: [10.3847/1538-4357/ae278f](https://doi.org/10.3847/1538-4357/ae278f).

\[Boe16\] H. Boehringer, G. Chon, and P. Kronberg, “The Cosmic Large-Scale Structure in X-rays (CLASSIX) Cluster Survey - I. Probing galaxy cluster magnetic fields with line of sight rotation measures,” *Astronomy and Astrophysics*, vol. 596, pp. 1–7, Oct. 2016, doi: [10.1051/0004-6361/201628873](https://doi.org/10.1051/0004-6361/201628873).

\[Osi24\] E. Osinga *et al.*, “Probing cluster magnetism with embedded and background radio sources in Planck clusters,” *Astronomy &amp; Astrophysics*, Aug. 2024, doi: [10.1051/0004-6361/202451885](https://doi.org/10.1051/0004-6361/202451885).

\[Alo25\] D. Alonso-López *et al.*, “Magnetic fields in the Shapley Supercluster core with POSSUM: Challenging model predictions,” *Astronomy &amp; Astrophysics*, Nov. 2025, doi: [10.1051/0004-6361/202556287](https://doi.org/10.1051/0004-6361/202556287).

\[Osi22\] E. Osinga *et al.*, “The detection of cluster magnetic fields via radio source depolarisation,” Jul. 20, 2022. doi: [10.1051/0004-6361/202243526](https://doi.org/10.1051/0004-6361/202243526).

\[Kim91\] K.-T. Kim, P. Kronberg, and P. C. Tribble, “Detection of excess rotation measure due to intracluster magnetic fields in clusters of galaxies,” Sep. 01, 1991. doi: [10.1086/170484](https://doi.org/10.1086/170484).
