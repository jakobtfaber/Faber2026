# Restore the repository knowledge-base launcher

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Triage: `ready-for-agent`

## Question

Can the documented `python3 scripts/kb search "<topic>"` and `make kb-index`
interfaces be restored with regression coverage, without changing the knowledge
base's indexed sources or search semantics?

## Resolution

Resolved 2026-07-20. Overleaf sync commit `48c98023` deleted the tracked
`scripts/kb` package, `scripts/kb_refs_sync.py`, and `tests/test_kb.py` while
leaving the Makefile and operator documentation in place. Restored the last
repository-native implementation from `9a9f1de2`; no adapter, source allowlist,
database schema, or ranking behavior changed.

Verification:

- `python3 scripts/kb --help` exposes `index`, `search`, and `stats`.
- `python3 -m pytest tests/test_kb.py -q` passes all eight tests.
- `make kb-index` completes: 322 documentation files, 40 tickets, 1,597 Git
  records, 671 code files, 90 configuration files, and 63 references indexed.
- A live ticket search returns the current foreground redshift-verdict tickets.
- JSON search output parses successfully.

The active Python lacks optional `fastembed`, so new or changed chunks currently
use the documented full-text fallback. This does not block the restored command;
semantic embedding remains an optional environment enhancement.
