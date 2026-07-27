# Superseded root docs/ mirror — archived 2026-07-27

This directory holds the stale root-level `docs/` mirror (plus associated root
`logs/` merge notes and `language_audit.md`), archived by `git mv` with relative
paths preserved. Nothing was deleted.

**Successor / authoritative tree: `analysis/docs/`** (the `analysis` submodule,
repository `Faber2026-analysis`).

## Basis

A verified inventory (2026-07-27) compared the root `docs/` tree against
`analysis/docs/`: 211 files were byte-identical duplicates and roughly 50 were
older revisions of their `analysis/docs/` counterparts. No reference in
`README.md`, `CLAUDE.md`, `AGENTS.md`, or `Makefile` points at the root tree.
Root-only files were moved only when they matched known-stale families
(scint-notebook wayfinder tickets, the interactive-scintillation-notebook map,
the 2026-07-17 outdated-science-quarantine specs, and two superseded implement
specs). The seven root/`logs/` markdown files were each confirmed byte-identical
(`cmp`) to their `analysis/` counterparts before moving.

## Kept in place (root-only, still active — NOT archived)

- `docs/rse/ops/raw-data-provenance.md`
- `docs/rse/research/research-overleaf-native-git-contract-2026-07-21.md`
- `docs/rse/specs/handoff-2026-07-24-12-33-worktree-content-disposition.md`
- `docs/rse/specs/handoff-2026-07-24-12-40-worktree-content-disposition.md`
- `docs/rse/specs/validation-worktree-content-disposition.md`
- `docs/rse/verify/rfi-rejected-prototypes-20260724/` (entire preservation packet)

## Restoring a file

`git mv` back to its original path (the path under this directory mirrors the
original repository-root-relative path), or read it here directly.
