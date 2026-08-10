# Choose the code and manuscript authority policy

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: [Define authority roles and their required proof](authority-01-define-authority-roles-and-proof.md), [Reconcile the code and manuscript truth surfaces](authority-02-reconcile-code-and-manuscript-surfaces.md), [Classify worktrees, scratch clones, and preservation packets](authority-03-classify-worktrees-and-preservation-packets.md)
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-human`

## Question

Given the reconciled inventory, which surface is authoritative for manuscript
prose, figures, fitting code, repository history, submodule pins, and Overleaf
sync? Define the allowed merge/sync order and the treatment of detached or
dirty fitting worktrees, including the JointTF lane. Decide how independent
working copies may diverge and what receipt returns their work to authority.

## Answer

Owner-ratified 2026-07-20. All recommendations were accepted together.

### Authority split

- Faber2026 GitHub `main` is authority for repository history, manuscript
  prose, bibliography, generated tables, the figure catalog, and approved
  tracked figure outputs.
- The canonical Mac checkout and every other checkout are working copies. Dirt,
  local commits, cleanliness, or recency never override GitHub `main`.
- `jakobtfaber/dsa110-FLITS` `main` is authority for fitting-code history. The
  `dsa110/dsa110-FLITS` organization repository is upstream, not this project's
  authority.
- The `pipeline` gitlink on Faber2026 GitHub `main` is authority for the
  manuscript's exact reproducibility pin. A clean detached `pipeline/`
  checkout at that identity is a replica; mutation makes it a working copy.
- Raw inputs, large results, and evidence outside tracked manuscript figures
  remain governed by the separate data-and-results authority decision.

### Overleaf

Overleaf is an independent manuscript working copy and publication-sync
endpoint. Collaborators may originate edits there, but those edits remain
non-authoritative until reconciled into Faber2026 GitHub `main`. Overleaf-only
historical files do not enter authority automatically.

Allowed reconciliation order:

1. Briefly freeze new manuscript edits.
2. Snapshot exact GitHub and Overleaf identities.
3. Pull Overleaf content into a dedicated reconciliation branch.
4. Compare paths and bytes; never merge the orphaned histories directly.
5. Review and merge a focused GitHub pull request.
6. Sync the merged GitHub manuscript back to Overleaf.
7. Compile and compare the resulting PDF.
8. Record the GitHub merge and Overleaf synchronization receipts.

A concurrent Overleaf edit invalidates the comparison and restarts the
sequence. Successful compilation alone is not reconciliation proof.

### Figures

Tracked figure definitions, catalog entries, provenance, and approved rendered
outputs become authoritative only through Faber2026 GitHub `main`. Copies in
Overleaf are working-copy or replica content. A figure receipt must identify
the generating commit, input identities or checksums, catalog entry, rendered
hash, merged pull request, and visual check. Scientific adoption remains a
separate gate.

### Pipeline-pin advancement

Fork advancement never updates the manuscript pin automatically, including an
analysis-only advance. A dedicated Faber2026 pull request must name the
accepted FLITS commit and child pull request, relevant tests, affected products,
and provenance compatibility. The resulting parent merge commit and gitlink
are the pin receipt.

### Detached and dirty fitting lanes

Known-owner lanes remain working copies. Unknown-owner, provenance-ambiguous,
or scientifically ambiguous outputs remain unclassified or quarantined.

JointTF code must first be committed and reviewed into FLITS authority. Its
outputs require separate scientific validation. Only then may a dedicated
Faber2026 pull request update the pin, figures, or manuscript. Nothing may be
adopted directly from a dirty worktree. Current detached fitting evidence and
dirty JointTF state remain preserved and fail-closed.

### Permitted divergence

An active independent working copy may diverge only while it retains a named
base identity, owner, purpose, dirty and unique-content inventory, and handoff
checkpoint. Divergence grants no authority. Before owner release, each unique
change must be merged, explicitly abandoned, or placed in a verified
preservation packet.

### Return-to-authority receipt

Work returns to authority only through a merged, scoped pull request recording:

- source and base identities;
- exact changed paths;
- owner and reviewer decision;
- required tests, manuscript compilation, and visual checks;
- input/output provenance for figures or fits;
- resulting merge commit;
- resulting pipeline pin when applicable; and
- Overleaf synchronization and PDF-comparison receipt when manuscript files
  are affected.

Clean status, newer timestamps, manuscript references, or successful
compilation alone are insufficient.
