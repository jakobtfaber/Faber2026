# Decide how the free-α diagnostic is reported in the paper

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: — (mechanism-closure verdict completed and independently checked)
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

The three-way model selection (2026-07-18) left a two-way with a puzzle:
clamped production EMG ≈ physical heavy-tail PL-PBF (collapses, inner scale
upper-railed) ≪ free-α EMG (ΔlnZ +5533/+734 on casey/wilhelm) — with tail
shape ruled out as mechanism (harsh-tail injection ceiling −0.21 vs the −1.6
anomaly) and multi-component leakage the lead hypothesis. Once the leakage
injection returns its verdict: how does the paper report the free-α
diagnostic? If leakage reproduces the anomaly, the story is "unmodeled weak
components bias chromatic fits" and count remediation becomes central to the
methods; if not, the anomaly needs another framing. Owner call on framing,
prominence (methods diagnostic vs results claim), and whether α≈2.5-class
values appear anywhere even as labeled mismatch signatures. (PL-PBF as
campaign default is moot — it collapsed.)

## Resolution

Resolved 2026-07-22 under the
[standing delegated decision authority](../standing-delegation-2026-07-20.md)
and the owner's advance approval for the unblock route.

Decision: retain the free-alpha exponential-tail fit only as an effective
model-mismatch diagnostic. It may appear only in Methods or an appendix. Any
numerical alpha near 2.5 must be labeled as a mismatch signature with no
physical thin-screen or turbulence-index interpretation.

Exclude the diagnostic and its values from:

- physical result tables;
- screen geometry, screen distance, or medium inference;
- the abstract, conclusions, and headline claims;
- evidence that a two-screen model has been established.

The mechanism battery did not reproduce the anomaly with a heavy tail, a
missed close component, their combination, the peak dipole, or
scintillation-gain leakage. Two-screen chromaticity remains a candidate by
elimination, not a result; its forward-model lane decides whether that
interpretation advances. Count remediation remains a separate method decision.

Evidence and independent validation:

- [research and reporting decision](../../specs/research-free-alpha-diagnostic-reporting.md);
- [mechanism-closure report](../../specs/notes/report-jointtf-mechanism-closure-2026-07-18.md);
- [hash-bound h17 evidence packet](../../specs/research/evidence/free-alpha-diagnostic-2026-07-22/);
- `python3 docs/rse/specs/research/evidence/free-alpha-diagnostic-2026-07-22/verify_packet.py`
  passes all hashes, six products, posterior intervals, log/product agreement,
  return codes, empty error logs, and the `|bias| < 0.02` bound.
- `make test MANUSCRIPT_ROOT=/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026`
  passes: 224 tests passed, one expected failure, and the state,
  figure-review, and journal gates passed.

No new Wayfinder ticket is needed. The separately chartered two-screen
forward-model lane already carries the remaining physical question.
