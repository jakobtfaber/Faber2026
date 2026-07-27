# Classify worktrees, scratch clones, and preservation packets

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-agent`

## Question

Which listed local directories are registered Git worktrees, independent
clones, preservation packets, generated builds, logs, or ordinary working
directories? Cover `~/Developer/scratch/worktrees/`,
`~/Developer/scratch/2026-07/`, `~/Developer/scratch/Faber2026-*`,
`~/scratch/kulkarni-profile/Faber2026`, `~/handoffs`, and relevant backups.
For each, record parent/remote, commit/branch, dirt, unique and ignored files,
active processes or agent ownership, preservation evidence, and the exact gate
that prevents or permits later consolidation. Nothing is deletion-approved by
this research.

## Answer

Resolved by
[`Research: Local worktrees and preservation packets`](../../specs/research/research-authority-worktree-classification-2026-07-20.md).

The estate contains registered parent and pipeline worktrees, an independent
FLITS worktree, four non-Git preservation packets, two independent bare
history-rewrite repositories, and ordinary analysis/log/build/handoff
directories. Names alone do not identify the class.

Most paths remain **hold**: `review-prose-89` has 99 modified tracked files;
science-gates and JointTF worktrees are dirty; several clean worktrees carry
unique commits or large unverified ignored trees; preservation packets retain
binding domain gates; both rewrite repositories differ; Kulkarni notes and
`~/handoffs` contain untracked evidence/source. The Overleaf and FLITS
quarantine worktrees are candidates only, not approved. The empty
`faber_build` directory is only a candidate pending reference, process, and
ownership checks. No directory was deletion-approved.
