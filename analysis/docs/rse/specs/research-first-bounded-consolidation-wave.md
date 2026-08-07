# Research: first bounded consolidation wave

**Date:** 2026-07-20 local / 2026-07-21 UTC
**Scope:** Internal, read-only verification of the smallest reported
consolidation candidate. No directory, reference, service, data, or Git state
was changed.
**Codebase state:** `7519db9f090e`; the checkout was already dirty in unrelated
science, manuscript, evidence, and configuration lanes.
**Related Documents:**
[`Ratify preservation gates and the consolidation sequence`](../wayfinder/tickets/authority-11-ratify-preservation-and-consolidation-gates.md),
[`Authorize the first bounded preservation and consolidation wave`](../wayfinder/tickets/authority-12-authorize-first-bounded-wave.md),
[`worktree classification`](research/research-authority-worktree-classification-2026-07-20.md)

## Question / Scope

Identify the smallest exact target that could execute before the next
authority-map decision. Reverify its identity, contents, ownership, processes,
open files, symbolic links, current references, rollback, and exclusions
against the ratified removal gate.

The search was limited to `faber_build` directories within
`/Users/jakobfaber/Developer/scratch` to depth four. No other worktree, scratch
directory, data tree, service, branch, or remote host was an execution target.

## Codebase Findings

### Candidate identity

The authority map's first-wave ticket names empty `faber_build` directories as
candidates, but requires fresh emptiness, process, reference, and ownership
proof before removal
([authority-12:12-16](../wayfinder/tickets/authority-12-authorize-first-bounded-wave.md#L12)).
The prior estate audit found one such directory and classified it as an empty,
ordinary, non-Git build directory whose remaining gate was checking whether a
process expected the path
([worktree classification:78-84](research/research-authority-worktree-classification-2026-07-20.md#L78)).

The live search at `2026-07-21T04:09:24Z` found exactly one target:

```text
/Users/jakobfaber/Developer/scratch/faber_build
```

Live `stat`, `find`, `du`, and `git -C ... rev-parse` checks showed:

- owner `jakobfaber`, group `staff`, mode `0755`;
- inode `312827192`, modification time `2026-07-08T14:26:05-0700`;
- zero child entries and zero allocated KiB;
- not a Git repository or registered worktree.

### Active use and references

`lsof +D`, process-command, and process-current-directory checks found no live
consumer. No symbolic link under `/Users/jakobfaber/Developer/scratch` to depth
five targets `faber_build`. No launch-agent, crontab, launchctl label, dotfiles
source, or current non-historical repository file references the absolute path.

Dated Claude Science execution logs record the directory only as a temporary
Tectonic `--outdir` created with `mkdir -p`. Those historical commands establish
that the path is rebuildable output, not a required persistent input. They do
not constitute a live reference.

### Removal and rollback shape

The fail-closed command is non-recursive `rmdir` on the one exact path. It will
refuse to act if any content appears after preflight. The rollback is
`mkdir -m 0755 /Users/jakobfaber/Developer/scratch/faber_build`, followed by
owner/mode and emptiness verification. There are no bytes to preserve.

All other paths remain explicitly excluded, including `flits_pr_build`,
`Faber2026-logs`, every worktree and preservation packet, all
`scratch/2026-07` content, data/results stores, services, branches, and remote
hosts.

### Authorization status

The owner authorized consolidation in general after ratifying the gates. The
ratified removal gate, however, requires separate explicit owner approval after
the exact deletion list and evidence packet exist. After this research packet
was presented, the owner explicitly approved removal of the one exact path.
Execution and postflight proof are recorded in
[`implement-first-bounded-consolidation-wave.md`](implement-first-bounded-consolidation-wave.md).

## Synthesis

`/Users/jakobfaber/Developer/scratch/faber_build` is the only first-wave
candidate that currently passes emptiness, ownership, process, open-file,
symbolic-link, and current-reference checks. Non-recursive removal has a trivial
tested design for rollback and cannot silently remove unexpected contents.

No broader consolidation action passes the exact-scope requirement in the
current instruction. The results-library and CHIME-path repair remains a
separate unresolved decision, and at-risk science, JointTF, raw-data, and
worktree preservation remain excluded from this removal.

## References / Sources

- [`docs/rse/wayfinder/tickets/authority-11-ratify-preservation-and-consolidation-gates.md`](../wayfinder/tickets/authority-11-ratify-preservation-and-consolidation-gates.md)
- [`docs/rse/wayfinder/tickets/authority-12-authorize-first-bounded-wave.md`](../wayfinder/tickets/authority-12-authorize-first-bounded-wave.md)
- [`docs/rse/specs/research/research-authority-worktree-classification-2026-07-20.md`](research/research-authority-worktree-classification-2026-07-20.md)
- Live read-only `find`, `stat`, `du`, Git, process, `lsof`, symbolic-link,
  repository-reference, launch-agent, and scheduler checks on jakob-mbp at
  `2026-07-21T04:09:24Z`
