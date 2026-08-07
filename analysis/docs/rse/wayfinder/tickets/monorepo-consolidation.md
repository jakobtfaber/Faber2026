# Consolidate Faber2026-analysis into Faber2026 as a monorepo

- Type: `wayfinder:task` (owner-chartered)
- Status: open
- Assignee: unassigned
- Blocked by: none (sequencing preconditions listed below)
- Map: [ApJ submission](../map-apj-submission.md)

## Charter

Owner decision (2026-08-07, chat): retire the submodule arrangement and fold
the analysis repository into the parent Faber2026 repository as an `analysis/`
directory, preserving history. The submodule pin has been the recurring
operational failure surface (accidental pointer changes, registry-before-pin
ordering, cross-repository checkpoints, the July gitdir destruction); a single
commit covering manuscript and analysis is strictly better provenance.

## Verified facts the plan rests on (2026-08-07)

- Parent `.olignore` already excludes `analysis/`, agent briefs, `.github/`,
  and `scripts/` from Overleaf sync, so the merged tree stays out of Overleaf
  the way the submodule path does today.
- Analysis's tracked working tree is 0.48 GiB. The ~7 GiB pack is dominated by
  nine historical `archive/*.bundle` blobs (~6.3 GiB) from the 2026-07-26/27
  preservation purges, deleted from the tree but retained in history. A
  filtered import that drops those blobs lands the full history well under
  1 GiB. The bundles remain preserved in the archived Faber2026-analysis
  repository and under `~/Data`.
- One oversized live file:
  `docs/rse/specs/evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/evidence-bundle.tar.gz`
  (133.6 MB, above GitHub's 100 MiB push limit). It must move to `~/Data`
  with a checksum pointer before or during the import.

## Sequencing preconditions

1. Land Faber2026-analysis PR #260 (blocked only on the GitHub-outage CI
   rerun, run 31113118784).
2. Disposition Faber2026-analysis PR #259 and Faber2026 PR #339.

## Phases

1. **Freeze.** No writes to Faber2026-analysis main during the import.
2. **Import.** `git filter-repo` the analysis history into the `analysis/`
   path, excluding the nine purge bundles and the oversized evidence bundle;
   verify the imported tip tree matches the current submodule pin's content.
3. **Rewire.** Remove `.gitmodules` and the gitlink; merge the two CI
   workflow sets with path filters; audit everything that assumes
   `analysis/.git` exists (the knowledge-base indexer indexes parent and
   submodule Git history separately; any script running Git inside
   `analysis/` will see the parent repository after the merge).
4. **Governance.** Owner relaxes the Faber2026 main ruleset to the standard
   the analysis repository uses today (admin action, owner-only). Archive
   Faber2026-analysis read-only on GitHub — never delete it; it is the
   provenance authority for the unfiltered history.
5. **Verify.** One Overleaf pull on the merged repository confirming the
   file-count cap is applied after `.olignore` filtering; CI green on the
   merged workflows; knowledge-base reindex; receipt written under
   `docs/rse/specs/`.

## Guardrails

- Preservation-first: the original repository and its purge bundles are never
  deleted; the filtered import is a copy, not a migration of authority until
  the verification phase passes.
- The final cutover (archiving the analysis repository, retargeting open
  work) is a one-way action and takes explicit owner confirmation at that
  step, with the receipt in hand.

## Done when

The parent repository contains the analysis history at `analysis/` with CI,
Overleaf sync, and the knowledge base working against the merged layout;
Faber2026-analysis is archived read-only; a receipt records the import
command, the exclusions, and the tree-equivalence check against the last
submodule pin.
