# Source authoritative host redshifts for Zach and Whitney

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: Codex (host-redshift source agent)
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `resolved`

## Question

Which source-owner or published rows establish the adopted host redshifts for
Zach (`FRB 20220207C`, local `0.043`) and Whitney (`FRB 20220310F`, local
`0.479`), which are absent from the owner-approved Verdi table?

Freeze the exact source rows or approved minimal extracts with FRB and host
identifiers, redshift, available uncertainty, measurement kind, bibliographic
source, stable upstream row identifier, release or retrieval date, and SHA-256.
Do not treat the local census value as its own verification evidence.

## Resolution

Resolved 2026-07-22 from Law et al. (2024), *Deep Synoptic Array Science:
First FRB and Host Galaxy Catalog*, The Astrophysical Journal **967**, 29,
DOI `10.3847/1538-4357/ad3736`.

The version-of-record Table 2 identifies Zach's host as
`PSO J310.1977+72.8826` and Whitney's as `PSO J134.7211+73.4910`. Joining
Table 2 to Table 3 on the formal FRB identifier gives:

- `FRB 20220207C` / Zach: `0.043040`;
- `FRB 20220310F` / Whitney: `0.477958`.

The paper's method classifies both as spectroscopic redshifts: pPXF jointly
fits the stellar continuum and nebular emission, and these rows fall under the
at-least-three-emission-line rule. Neither Table 3 nor the method gives a
row-level redshift uncertainty, so uncertainty is recorded as unavailable, not
zero.

The exact Table 2, Table 3, identifier-macro, and method source bytes; normalized
rows; and source manifest are frozen under
[`law2024-zach-whitney-host-redshifts-2026-07-22/`](../../specs/evidence/law2024-zach-whitney-host-redshifts-2026-07-22/).
The final publisher PDF SHA-256 is
`f484b7dd23acd2f36cb3de65865d2d4f01c1d29e11978dcdaf3467f928d01478`;
the official arXiv v2 source archive SHA-256 is
`03d941deaa0bc98326a4c3c11466d18efb5a648d9c04acad2ed81743e5b3ee99`.
The published PDF and author source agree on both Table 2/Table 3 links.

This resolution freezes source evidence only. It does not change the census,
identifiers, verdicts, budgets, or Figure 3. Any adoption or difference remains
with
[Adjudicate census host redshifts against the approved Verdi table](expanded-foreground-catalog-repair-19-adjudicate-host-redshift-differences.md).
