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

- Owner revised the search contract on 2026-07-22. This decision supersedes the
  earlier 5-arcminute galaxy cone, 20-arcminute cluster cone, and redshift-first
  candidate admission recorded on 2026-07-21.
- Center every query on the frozen FRB International Celestial Reference System
  coordinates in `pipeline/galaxies/foreground/data/frozen_census/bursts.csv`.
  Do not center on the host or a foreground candidate.
- Galaxy search: a fully paginated, inclusive 15-arcminute cone per sightline.
  Record exact spherical separation. A service row limit must not truncate the
  result set.
- Cluster search: a separate, inclusive projected-separation limit of 5 proper
  Mpc at each candidate cluster redshift. Compute the unrounded transverse
  separation as `b = theta * Planck18.angular_diameter_distance(z_cluster)`,
  where `theta` is the exact spherical separation in radians. If a service
  requires an angular prefilter before returning redshifts, the query must
  either evaluate the projected limit server-side or use a documented cone
  proven to contain every catalog row satisfying the 5 proper Mpc rule. If
  completeness cannot be proved, the query remains incomplete rather than
  silently truncating candidates.
- A returned cluster row without a finite positive catalog redshift cannot be
  tested against the projected search region. Preserve it in the raw response
  as `cluster_search_geometry_unresolved`, do not admit it to the candidate
  corpus, and keep the completed-corpus gate closed until the catalog supplies
  usable geometry or the row receives a separately sourced redshift. This is a
  search-geometry failure, not a scientific redshift or class rejection. There
  is no finite angular fallback because the 5 proper Mpc angle is unbounded as
  redshift approaches zero.
- Initial candidate admission is geometry-first. A returned row needs a stable
  catalog release/source identifier, finite coordinates, and inclusion in the
  approved region. Redshift, color, morphology, catalog class, photometry,
  richness, halo mass, and quality warnings are not initial admission cuts.
  Invalid coordinates or missing stable identity prevent candidate formation
  but remain frozen as source-response defects.
- Preserve every returned row with its native values and flags. Missing
  optional quality fields yield `quality_unknown`, not rejection. A documented
  non-astrophysical artifact or failed redshift fit is classified later; it is
  not removed from the raw corpus.
- Redshift classification follows admission. For galaxies, and for clusters
  whose catalog redshift already established search geometry, a secure
  spectroscopic redshift
  is foreground only for `0 < z < z_host`; a source within 500 km/s of the host
  is `host_local_ambiguous`. A photometric estimate is potentially foreground
  when its published 95% interval overlaps `0 < z < z_host`; if only a
  one-sigma error is published, use `z +/- 1.96 sigma`. A central estimate
  outside the foreground range with an overlapping interval is
  `redshift_ambiguous`. Missing usable scientific redshift evidence is
  `no_usable_redshift`, not an admission failure; the cluster geometry exception
  above applies before this classification.
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
- Classification follows admission. Secure stellar evidence marks a
  `star_contaminant`; uncertain or conflicting class evidence remains
  `classification_ambiguous`. Only a galaxy or cluster with resolved geometry
  can be tested against a catalog or model radius. Galaxy halo intersection
  uses `b <= R200c`. Every cluster admitted by the 5 proper Mpc search remains
  in the audit corpus; no second `R200` retention cut applies. Cluster rows
  retain catalog `M500` and `R500`, and dispersion-budget admission alone uses
  the inclusive rule `b <= R500`. Do not derive cluster `M200c` or `R200c` from
  the pipeline's approximate `M200/M500 = 1.3` factor. Any future `R200c` rule
  must name and validate a separate cluster conversion model first. Missing
  catalog `R500` produces `geometry_unresolved`, never a fallback aperture.
- All calculations use the frozen International Celestial Reference System
  coordinates and exact spherical separation. Output order is separation,
  catalog, release, then source identifier. The corpus retains query text,
  release, retrieval time, coverage, native rows and uncertainties, normalized
  state, and SHA-256 hash. `outside_footprint`, `access_denied`, and
  `query_error` are distinct from `unmatched`; any unresolved service state
  keeps the completed-corpus and independent-replay gates closed.

## Executable acceptance gates

- Boundary tests use unrounded values: galaxy rows at exactly 15 arcminutes and
  cluster rows at exactly 5 proper Mpc are admitted; rows beyond either limit
  are not.
- A reference test computes cluster impact independently with Astropy
  `Planck18.angular_diameter_distance` and exact spherical separation. Producer
  and replay must agree to `1e-10` relative tolerance away from zero.
- A cluster row with missing, non-finite, zero, or negative redshift is frozen
  as `cluster_search_geometry_unresolved`, is absent from the admitted corpus,
  and makes the completed-corpus check fail. The corresponding galaxy fixture
  remains admitted and receives `no_usable_redshift` after admission.
- A cluster with finite search geometry but missing `R500` remains in the audit
  corpus as `geometry_unresolved` and is not budget eligible. A row at exactly
  `b = R500` is budget eligible; a row beyond it is not.
- Tests reject any cluster admission or retention path that uses `R200`, the
  approximate `M200/M500 = 1.3` conversion, a rounded separation, an undocumented
  cosmology, an incomplete page set, or a service-truncated result.
- Corpus validation fails unless all nine frozen sightlines have query text,
  catalog release, retrieval time, coverage state, native rows, normalized
  states, pagination evidence, and SHA-256 hashes. Independent replay must use
  the same frozen inputs but a separate calculation path.

## Resolution

Resolved 2026-07-21 and revised by the owner on 2026-07-22 through the exchange
recorded above. The approved contract defines a new audit search, not a
reconstruction of the unknown historical aperture. It preserves all raw
evidence and all existing scientific authority fields while making search
region, candidate admission, identity, ambiguity, duplicate grouping, and
post-admission classification deterministic.

No adopted redshift, verdict, duplicate disposition, budget flag, trust state,
or Figure 3 artifact changed.
