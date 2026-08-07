# Fail-close the invalid expanded-catalog validation

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `resolved`

## Question

What exact status and machine-readable gate prevent the current validation from
being cited as accepted while preserving its findings as superseded evidence?

## Acceptance decision

Replace `Ready / Verified` with `FAILED — superseded; do not use`. Record the
wrong Moster input units, incorrect Cluver equation label and missing rest-frame
condition, incomplete and non-deterministic matches, invalid Stern interpretation,
wrong morphology summary, absent pinned CSV, and unversioned Figure 3 input.
Any validator must exit nonzero until the rebuilt catalog and independent report
both pass.

## Resolution

Resolved 2026-07-20 under the standing delegated decision authority in
[PR #166](https://github.com/jakobtfaber/Faber2026/pull/166), with provenance
follow-up [PR #167](https://github.com/jakobtfaber/Faber2026/pull/167). The
invalid report now says `FAILED — superseded; do not use`, the accepted-status
string is absent from the Markdown validation, and
`docs/rse/specs/validation-expanded-foreground-catalog.json` records the
machine-readable failed gate.

Acceptance evidence:

- Required defects recorded:
  `moster-input-units`, `cluver-equation-and-rest-frame`,
  `incomplete-crossmatches`, `non-deterministic-match-selection`,
  `stern-selection-interpretation`, `morphology-summary`,
  `missing-pinned-expanded-csv`, and `unversioned-figure-3-input`.
- `scripts/validate_expanded_foreground_catalog_gate.py` exits nonzero while
  `status != passed` or any defect has non-pass status.
- `uv run rtk pytest tests/test_expanded_catalog_validation.py -q` passed.
- `! rtk rg -n "Ready / Verified|52 / 52.*matched"
  docs/rse/specs/validation-expanded-foreground-photometry-and-morphology-catalog.md`
  passed.
- `rtk make test-science` passed.
- `agent-closeout-check` passed with a dirty-state packet classifying all
  changed paths as task-scoped.
