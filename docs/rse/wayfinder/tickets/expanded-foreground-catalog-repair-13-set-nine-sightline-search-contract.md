# Set the nine-sightline search-region and candidate-selection contract

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `resolved`

## Question

What exact sky region and deterministic candidate-admission rule should govern
the expanded nine-sightline replay?

The frozen census records recovered candidates but not the original galaxy
discovery-cone aperture. Decide the center and angular or proper-radius rule for
each sightline; whether galaxy and cluster searches use different regions; the
catalog fields and quality cuts that create a candidate; and the identity,
ambiguity, and duplicate rules applied before classification enrichments.

This decision defines a new reproducible audit search. It does not retroactively
claim completeness for the frozen census or authorize changing any adopted
redshift, verdict, budget flag, trust state, or Figure 3 status.

## Decision log

- Owner approved a two-stage, mass-independent discovery structure on
  2026-07-21. Each search is centered on the burst position. Catalog quality
  and foreground-redshift rules create the candidate pool; derived halo
  intersection is classified afterward using `b <= R200c` for galaxies and
  `b <= R500` for clusters. A halo mass is not required for discovery.
- Owner approved separate circular search regions on 2026-07-21: `5 arcmin`
  for galaxy catalogs and `20 arcmin` for cluster catalogs, both centered on
  the burst coordinates. Admission uses exact spherical separation at or
  inside the boundary. Query cones are `5.1 arcmin` and `20.1 arcmin`;
  guard-ring rows are retained but not admitted. These limits enclose all
  frozen rows: the largest stored separations are `4.72 arcmin` and
  `19.999 arcmin`.
- Owner approved the foreground-redshift rule on 2026-07-21. A secure
  spectroscopic redshift is admitted only for `0 < z < z_host`; a source
  within 500 km/s of the host is `host_local_ambiguous`. A photometric
  redshift is admitted when its published 95% interval overlaps
  `0 < z < z_host`; if only a one-sigma error is published, the interval is
  `z +/- 1.96 sigma`. If the central estimate lies outside the foreground
  range while its interval overlaps, the row is `redshift_ambiguous`. Rows
  without usable redshift evidence remain frozen as `no_usable_redshift` and
  enter only if another catalog identifies the same source and supplies
  admissible evidence.
- By the owner's instruction to accept the remaining recommendations, discovery
  uses only predeclared catalog-native fatal-quality exclusions: invalid
  coordinates, missing stable release/source identity, failed redshift fit, or
  a documented non-astrophysical artifact. Every excluded row remains in the
  corpus with its native flags and exclusion reason. Missing optional quality
  fields yield `quality_unknown`, not rejection. Morphology, color, halo mass,
  richness, and later classification enrichments are not discovery cuts.
- A source identity is its `catalog + release + source_id`. Published
  cross-identifiers may link catalogs. Otherwise, galaxy detections link only
  when separation is at most 1 arcsec and their redshift evidence is compatible.
  Separations from 1 to 3 arcsec, one-to-many links, and any WISE identifier
  shared by multiple optical sources are `ambiguous`, never automatic merges.
  Cluster detections link only through a published cross-identifier or through
  centers within 1 arcmin with compatible redshifts and overlapping published
  extents. Position alone never merges clusters.
- Duplicate groups preserve every member and provenance row. A representative
  is only a deterministic view: secure spectrum, then smallest redshift
  uncertainty, then smallest burst separation, then lexical
  `catalog/release/source_id`. Every group must satisfy the identity rule
  pairwise; chained proximity does not create an identity. Conflicting secure
  spectra, non-overlapping photometric 95% intervals, or mixed source classes
  make the group `ambiguous` and require separate owner adjudication.
- Classification follows discovery. Secure stellar evidence marks a
  `star_contaminant`; uncertain or conflicting class evidence remains
  `classification_ambiguous`. Only a galaxy or cluster with resolved geometry
  can be tested against `R200c` or `R500`. Missing mass or radius produces
  `geometry_unresolved`, never a fallback aperture.
- All calculations use the frozen International Celestial Reference System
  coordinates and exact spherical separation. Output order is separation,
  catalog, release, then source identifier. The corpus retains query text,
  release, retrieval time, coverage, native rows and uncertainties, normalized
  state, and SHA-256 hash. `outside_footprint`, `access_denied`, and
  `query_error` are distinct from `unmatched`; any unresolved service state
  keeps the completed-corpus and independent-replay gates closed.

## Resolution

Resolved 2026-07-21 through the owner exchange recorded above. The approved
contract defines a new audit search, not a reconstruction of the unknown
historical aperture. It preserves all raw evidence and all existing scientific
authority fields while making search region, candidate admission, identity,
ambiguity, duplicate grouping, and post-discovery halo intersection
deterministic.

No adopted redshift, verdict, duplicate disposition, budget flag, trust state,
or Figure 3 artifact changed.
