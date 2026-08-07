# Law 2024 host-redshift evidence for Zach and Whitney

Law et al. (2024), *Deep Synoptic Array Science: First FRB and Host Galaxy
Catalog*, supplies the missing public source chain. The version of record is
The Astrophysical Journal **967**, 29, DOI
[`10.3847/1538-4357/ad3736`](https://doi.org/10.3847/1538-4357/ad3736), dated
2024-05-20.

Table 2 identifies the hosts. Table 3 gives the redshifts. Joining those tables
on the formal FRB identifier gives:

| Nickname | FRB | Table 2 host | Table 3 redshift |
| --- | --- | --- | ---: |
| Zach | FRB 20220207C | PSO J310.1977+72.8826 | 0.043040 |
| Whitney | FRB 20220310F | PSO J134.7211+73.4910 | 0.477958 |

The spectroscopy method says that host redshifts were measured with pPXF by
jointly fitting the stellar continuum and nebular emission, with at least three
emission lines for all hosts except FRB 20220509G. That exception is neither
row here. Therefore both values are spectroscopic. Neither Table 3 nor the
method reports a row-level redshift uncertainty; the uncertainty is explicitly
recorded as unavailable, not zero.

The final publisher PDF was independently retrieved and checked. Its SHA-256
is `f484b7dd23acd2f36cb3de65865d2d4f01c1d29e11978dcdaf3467f928d01478`.
The official arXiv v2 source archive was also retrieved from
[`2307.03344v2`](https://arxiv.org/abs/2307.03344v2); its SHA-256 is
`03d941deaa0bc98326a4c3c11466d18efb5a648d9c04acad2ed81743e5b3ee99`.
The checked-in TeX files are byte-exact contiguous slices of that archive's
`main.tex`, including the complete Table 2 and Table 3 environments and the
measurement method. [`source_manifest.json`](source_manifest.json) records
every source and artifact hash.

This evidence supports the exact published values only. It does not change the
local census, identifiers, verdicts, budgets, or Figure 3.
