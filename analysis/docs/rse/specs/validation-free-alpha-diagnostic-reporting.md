# Validation complete: free-alpha diagnostic reporting

> Validated against the reporting ticket and owner-approved execution contract
> from analysis base commit `2db10b7bac942730c251f17a226c9167f8cf971b`
> plus this task diff on 2026-07-22.

## Overall Status: Ready

## Implementation Status

- Mechanism blocker checked against live h17 artifacts: complete.
- Six-run evidence packet preserved and hash-bound: complete.
- Landed bounds independently parsed: complete.
- Fail-closed reporting contract recorded in the ticket: complete.
- Map and board state reconciled: complete.

## Automated Verification Results

- `python3 docs/rse/specs/research/evidence/free-alpha-diagnostic-2026-07-22/verify_packet.py`
  passes 23 hashes, six products, six successful logs, empty error logs,
  posterior and bias arithmetic, and both leakage bounds.
- `python3 -m py_compile docs/rse/specs/research/evidence/free-alpha-diagnostic-2026-07-22/verify_packet.py`
  passes.
- Exact search of the live manuscript `main.tex` and `sections/*.tex` finds no
  current free-alpha values or evidence-difference claims that violate the
  contract.
- Focused Wayfinder controller tests: 17 passed.
- Full analysis suite: 224 passed and one expected failure; state, figure-review,
  and journal gates passed.
- Ticket, map, and board status assertions pass.

## Code Review Findings

The reporting contract matches the evidence and standing context. One preserved
metadata field reports nominal rather than actual frequency-grid spacing; the
verifier checks the distinction and confirms the computed effective modulation
used the actual grid. The fit driver and provenance were untracked on h17, and
the currently available campaign-input records postdate the injection. These
limitations prohibit a clean-room fitter-reproduction claim but do not affect
the independently parsed `|bias| < 0.02` result.

## Manual Testing Required

None for this decision. Future manuscript wording must remain within the locked
Methods/appendix-only contract. The separate two-screen forward-model lane has
its own owner review gate.

## Recommendations

No critical or important follow-up within this ticket. Do not promote the
diagnostic through later table or prose regeneration.

## References

- [Ticket](../wayfinder/tickets/14-free-alpha-diagnostic-reporting.md)
- [Research](research-free-alpha-diagnostic-reporting.md)
- [Evidence packet](research/evidence/free-alpha-diagnostic-2026-07-22/)
