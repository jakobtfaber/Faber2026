# Implementation Plan: repository content audit

**Date:** 2026-07-22
**Status:** Complete.
**Research:** [repository content audit](research-repository-content-audit-2026-07-22.md)

## Overview

Move proven obsolete material into `.archive/`, update active references, and
keep provenance snapshots whose duplication is intentional.

## Desired End State

- One populated knowledge database at `analysis/.kb/kb.sqlite3`.
- Obsolete science trees under `.archive/outdated-science/2026-07-17`.
- Sign-bug Casey figures outside the live deck.
- No active code or documentation points at the former quarantine paths.
- Current tests and knowledge-base search pass.

## What We're NOT Doing

- No removal of review snapshots, reference-arc evidence, compatibility
  symlinks, active wayfinder tickets, scientific results, or manuscript files.
- No parent submodule-pin changes.
- No modification of pre-existing untracked parent lanes.

## Phases

1. Preserve the empty analysis DB; move the populated legacy DB to the
   configured path; verify document and chunk counts.
2. Move obsolete science trees and sign-bug figures; update active references.
3. Archive the two unreferenced completed implementation records.
4. Refresh the knowledge base; run targeted tests, link checks, status checks,
   and repository closeout checks.

## Automated Verification

- `sqlite3 analysis/.kb/kb.sqlite3 'select count(*) from documents; select count(*) from chunks;'`
  returns non-zero counts.
- `rg 'quarantine/2026-07-17-outdated-science|SUPERSEDED-signbug' analysis pipeline`
  finds only preserved historical receipts or archived material.
- `python3 analysis/scripts/kb search 'repository content archive'` succeeds.
- Targeted archive/quarantine and results-library tests pass.
- `git diff --check` passes in all three repositories.

## Manual Verification

- Owner may review the archived Casey figures; no scientific judgment is needed
  to identify their known sign-label defect.

## Rollback

All moves remain in Git history or `.archive/`; reverse the renames and restore
the previous catalog paths.
