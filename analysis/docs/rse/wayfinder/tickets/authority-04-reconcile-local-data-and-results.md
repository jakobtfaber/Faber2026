# Reconcile local data and results custody

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-agent`

## Question

What does `~/Data/Faber2026/` currently contain by artifact class, and how do
those bytes relate to repository manifests, `results-registry.toml`, and
`results-library`? Identify and explain all eight broken links without changing
them. Inventory scripts and documents that still reference obsolete CHIME data
paths, separating broken authorities from harmless historical references.
Record hashes, sizes, link targets, generation receipts, and trust status where
available; do not regenerate, relink, or move data.

## Answer

Resolved by
[`Research: local data and results custody`](../../specs/research/research-authority-local-data-results-2026-07-20.md).

The full-resolution local split is real and complete at the count level: 12
CHIME/FRB cubes under `chimefrb/` and 12 DSA-110 cubes under `dsa110/`, while
upchannelized, remediated, packaged, and result products remain distinct
derived lineages. The claim registry and byte-level results library are
complementary but have no shared identifiers and are not reconciled. The
library inventory was generated from a deleted worktree and is stale.

Exactly eight results-library links are broken. All are navigation links to a
deleted worktree; their present repository sources still exist, so this is a
relink/refresh problem, not evidence loss. Current producers, certificates,
and authority documents still contain obsolete co-mingled CHIME paths;
historical receipts can remain historical. Large bytes were not rehashed and
no trust state was promoted.
