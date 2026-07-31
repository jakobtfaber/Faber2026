# Adjudicate WHL J115048.0+714428

- Type: `wayfinder:research`
- Status: resolved — source recovery adjudicated catalog fragment 2026-07-31
- Assignee: Researcher 3
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)

## Fact

The frozen WHL12 payload identifies `WHL J115048.0+714428` at
RA `177.69998 deg`, Dec `71.74124 deg`, photometric redshift `0.1893`,
`N200=12`, and catalog `r200=0.92 Mpc`. The census places the sightline
`614.3 kpc` from that center and marks the object confirmed but
budget-ineligible. The budgeted Wen--Han system `J115120.4+714435, 1254337`
is a separate registry row at RA `177.83488 deg`, Dec `71.74319 deg`,
spectroscopic redshift `0.2000`, with adopted `M500=1.48e14 Msun` and
`R500=0.729 Mpc`.

Exact evidence:

- `foregrounds/census/data/candidate_redshift_source_payloads_2026-07-22.json`,
  SHA-256 `814845249e0acae8091f7177a56a08015ace03bfdf5786c75198f3e34f4b6cee`;
- `foregrounds/census/data/candidate_redshift_provenance.csv`, SHA-256
  `0a2ba35f3dd7dfdcc855d4d589e062c08e5788e135970802cb7b7b798c47afe7`;
- `foregrounds/census/data/intervening_census_registry.csv`, SHA-256
  `96bfd32302b00df943ba998ba3bf6557f3d8c06d882079cad1a5c9846d47d06a`;
- `docs/rse/specs/research-v4-census-gap-extension.md`, SHA-256
  `83f2a559af40a30a11f9e9a7e7251271d06fe972cad662f435f23e2973536b55`.

## Non-result

These records do not establish whether the two catalog entries represent
distinct physical halos or one fragmented/duplicated system. WHL12 `r200` is
not the adopted model's required Wen--Han `R500`, and `N200` is not an adopted
`M500`. No dispersion-measure contribution is assigned to the WHL12 entry.

## Scientific falsifier

- The distinct-halo interpretation is falsified by a primary-source
  crossmatch showing that both names identify the same physical cluster.
- The duplicate/fragment interpretation is falsified by primary-source
  membership, centers, and redshifts establishing two distinct bound systems.
- Inclusion in the cluster budget is falsified if a sourced `M500` and `R500`
  place the sightline outside the declared cluster model or yield no positive
  column under that model.

## Admission blocker

Before inclusion, the source expert must provide an immutable source citation
and row identity for `M500` and `R500`, including definitions and units, plus a
documented crossmatch between both catalog names using centers, redshifts,
membership or richness, and catalog identifiers. If distinct, the added halo
requires a separately reviewed cluster-column calculation and increases the
current one-cluster budget by an as-yet unknown amount. If duplicate/fragment,
it adds no second column and the existing cluster must carry the reconciled
identity. If excluded after source adjudication, it adds no column and the
exclusion reason remains explicit. None of these choices admits the existing
one-cluster budget by itself.

## Prerequisite check

The frozen identity and catalog payload exist. The required source-bound
`M500`, model-compatible `R500`, and two-object crossmatch adjudication do not.
Therefore no budget rerun command is prescribed.

## Superseded owner-decision framing

Owner direction, 2026-07-31: this is not an owner decision. Researcher 3 must
recover and adjudicate the primary catalog, crossmatch, mass, and radius
evidence. The former choices below remain only as investigation outcomes and
must not appear in the owner queue.

```json
{
  "id": "whl-j115048-identity",
  "kind": "scientific",
  "title": "WHL J115048.0+714428 identity",
  "decision": "How should WHL J115048.0+714428 be treated while its relationship to J115120.4+714435 and its model-compatible mass and radius remain unresolved?",
  "recommended": {
    "choice": "exclude-pending-source",
    "reason": "Preserve the confirmed catalog entry but exclude it from the quantitative budget until primary-source identity, M500, R500, and crossmatch evidence are adjudicated."
  },
  "choices": [
    {
      "id": "distinct-halo",
      "label": "Treat as a distinct halo after source evidence establishes a separate system and supplies model-compatible M500 and R500."
    },
    {
      "id": "duplicate-fragment",
      "label": "Treat as a catalog duplicate or fragment of J115120.4+714435 after primary-source crossmatch adjudication."
    },
    {
      "id": "exclude-pending-source",
      "label": "Preserve the entry but exclude it pending source adjudication; exclude after adjudication if model eligibility is not established."
    }
  ],
  "context": [
    "WHL12 identifies the entry at photometric redshift 0.1893 with N200=12 and catalog r200=0.92 Mpc; the sightline impact is 614.3 kpc.",
    "The budgeted Wen--Han entry is at spectroscopic redshift 0.2000 with adopted M500=1.48e14 Msun and R500=0.729 Mpc.",
    "No primary-source evidence in the current packet establishes distinctness or duplication, and no model-compatible M500 and R500 are adopted for WHL J115048.0+714428."
  ],
  "evidence": [
    {
      "label": "Frozen WHL12 source payload",
      "path": "foregrounds/census/data/candidate_redshift_source_payloads_2026-07-22.json",
      "sha256": "814845249e0acae8091f7177a56a08015ace03bfdf5786c75198f3e34f4b6cee"
    },
    {
      "label": "Frozen census registry",
      "path": "foregrounds/census/data/intervening_census_registry.csv",
      "sha256": "96bfd32302b00df943ba998ba3bf6557f3d8c06d882079cad1a5c9846d47d06a"
    },
    {
      "label": "Census-gap source assessment",
      "path": "docs/rse/specs/research-v4-census-gap-extension.md",
      "sha256": "83f2a559af40a30a11f9e9a7e7251271d06fe972cad662f435f23e2973536b55"
    }
  ],
  "effect": "Records whether the entry remains excluded, is reconciled as a duplicate, or proceeds as a distinct halo requiring a new reviewed column; it does not admit a cluster budget.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/owner-decision-whl-j115048-identity.md",
    "action": "Record the owner or source-expert choice and cite the adjudicating source receipt; do not change the budget until the stated evidence exists."
  },
  "priority": 20
}
```

## Resolution

Research adjudication, 2026-07-31: treat `WHL J115048.0+714428` as an
older, poorer catalog fragment or alternate center of the system represented
by `J115120.4+714435`, not as a second additive halo.

Primary-source recovery is recorded in
`docs/rse/specs/research-whl-j115048-source-recovery-2026-07-31.md`, SHA-256
`d524ecde6dc0fe81f189e01401b89193727792de61c6d0a81797c22831448b2a`.
The centers are separated by `2.538489 arcmin`, or `0.6725` of the modern
`r500`; the older object is the unique compatible WHL entry inside the
published `1.5 r500` cleaning radius, is poorer, and disappears from the 2024
catalog while the surviving row is flagged `Cat=WHL`.

Budget consequence: retain one modeled cluster using the Wen & Han (2024)
`M500=1.48e14 Msun` and `r500=0.729 Mpc`; do not add the older WH15 proxy as a
second contribution. This identity adjudication does not validate the gas
profile, dispersion calculation, or manuscript admission. Reopen if an
immutable producer cross-ID/member artifact or spectroscopy establishes two
distinct halos.
