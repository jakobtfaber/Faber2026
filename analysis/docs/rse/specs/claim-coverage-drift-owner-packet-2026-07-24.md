# Claim-coverage drift owner packet — 2026-07-24

Status: **decision pending; fail closed**

Compared:

- manuscript parent: `2d3e41b86b2766b84adbba0193ee637b96fb13e0`
- analysis registry: `f7f7fbba50c4bf2e29c0a79b565c84ef2b3c7d6f`
- registry: `docs/rse/control/results-registry.toml`
- generator: `scripts/generate_results_coverage.py`

The compiled artifact assignments are unchanged. Five prose records drift:
two fingerprints need an explicit assignment decision; three records changed
line number only and retain their reviewed exclusions.

Compiled-registry validation has a separate provenance blocker. This is not a
shallow-clone problem and must not be hidden by a workflow-only fetch change.

## Decisions required

| Source | Old record | Current record | Recommended assignment | Owner decision |
|---|---|---|---|---|
| `main.tex` | fingerprint `2971236a2c81cfaf`, line 120, excluded as taxonomy/software/facility/repository text | fingerprint `00e0946017b1a82d`, line 119: `full CHIME/FRB and DSA-110 fit results, per-event diagnostic figures, injection` | Keep excluded for the same reason: the numeric token is the instrument name `DSA-110`, not a project measurement. | pending |
| `sections/observations.tex` | fingerprint `092aad83e03e60bc`, line 179, owner `mw.foreground_characterization` | fingerprint `eb6ae874d58c8cd4`, line 179: `(\texttt{scripts/mw_model_comparison.py}), NE2001 exceeds the NE2025 disk` | Keep owner `mw.foreground_characterization`; only the repository-relative script path changed. | pending |

## Mechanical line-only drift

These fingerprints and reviewed exclusions are unchanged; only their line
numbers moved from manuscript edits:

| Source | Fingerprint | Old line | Current line | Existing disposition |
|---|---:|---:|---:|---|
| `main.tex` | `13ef7d3b3462d91d` | 125 | 123 | facility identifier; excluded |
| `main.tex` | `70bec1b84a25429e` | 131 | 129 | software/model identifiers; excluded |
| `main.tex` | `436ea786eac4a796` | 130 | 128 | software/model identifiers; excluded |

## Pipeline provenance blocker

The registry names five pipeline commits. Four are advertised by a remote ref:

- `17d9...`, `23f...`, and `666...` are reachable from `origin/main`;
- `6c878906...` is reachable from `origin/agent/dm-phase-v2`,
  `origin/pin/faber2026`, and upstream branches.

Commit `9175b92529b33980503490bccf58491baf7d6a1f` exists only in the canonical
local pipeline object database. No remote branch contains it. Fetching that
exact object from a fresh shallow clone fails with `not our ref`; unshallowing
the clone still does not make it available.

That unavailable commit backs these current registry rows:

- `association.sample_roster`;
- `association.sample_table`;
- `association.pcc_sum`;
- the dispersion-measure table;
- the timing-offset decomposition figure.

Owner decision required:

1. preserve the exact commit under a durable authoritative remote ref; or
2. independently revalidate every affected row against a reachable commit and
   record replacement provenance.

Do not replace the hash mechanically. Do not weaken compiled-registry
validation. A workflow fetch adjustment is appropriate only after every
accepted historical commit is remotely advertised.

## Gate

Do not regenerate or commit the registry from this packet alone. After the
owner records both decisions:

1. update only the two changed fingerprints and three line numbers;
2. rerun
   `test_coverage_generator_preserves_reviewed_assignments_byte_for_byte`;
3. rerun compiled-registry validation with every referenced pipeline commit
   available from authoritative provenance;
4. open a focused registry PR.

The current mismatch remains intentionally failing until those decisions and
the separate pipeline-provenance issue are resolved.
