# Adjudicate the results-library real-byte conflicts

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: [Choose the results-library and CHIME-path repair batch](authority-13-choose-link-and-chime-path-repair.md)
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `resolved`

## Question

For `scintillation.dsa-lorentzian-2026-07-07` and
`dispersion.pipeline-results-root`, both the repository source and the
results-library destination are real directories. What are their exact tree
manifests, byte differences, producing commits, consumers, trust states, and
independent recovery copies? Determine whether either side is an authority,
replica, superseded result, or unresolved conflict. Propose an exact
non-overwriting disposition and rollback packet; do not move, relink, replace,
or delete either tree.

## Answer

Resolved by
[`Research: results-library real-byte conflicts`](../../specs/research-authority-16-results-library-byte-conflicts.md),
under the owner's direct 2026-07-20 invocation of this ticket.

Both library directories are exact byte replicas of the corresponding
pre-relocation pipeline trees at commit `af78543d4747`. The current clean
repository paths contain only post-relocation tracked control files, while the
canonical Mac checkout also contains 13 and 289 later ignored working files.
Those ignored files lack complete independent byte recovery and cannot be
assigned a producing commit.

Classify the library directories as immutable historical snapshot replicas and
the canonical repository directories as mixed working/control surfaces. Keep
all four unchanged. Do not materialize or overlay either pair. A later
repository-only implementation may replace the two broad `materialize`
semantics with a commit-and-tree-hash snapshot representation; any working
result publication requires a new identifier, absent versioned destination,
complete manifest, run receipt, and independent recovery copy.

No bytes moved, linked, replaced, deleted, or promoted. Scientific trust and
manuscript claims are unchanged.
