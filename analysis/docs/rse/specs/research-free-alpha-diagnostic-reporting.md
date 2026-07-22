# Research: free-alpha diagnostic reporting

**Date:** 2026-07-22
**Scope:** Internal codebase, pipeline provenance, and live h17 evidence
**Codebase state:** `2db10b7bac942730c251f17a226c9167f8cf971b`
**Related documents:** [reporting ticket](../wayfinder/tickets/14-free-alpha-diagnostic-reporting.md),
[mechanism-closure report](notes/report-jointtf-mechanism-closure-2026-07-18.md),
[evidence packet](research/evidence/free-alpha-diagnostic-2026-07-22/)

## Question / Scope

Decide whether and where the free-alpha exponential-tail fit may appear after
the mechanism tests, without promoting an internally inconsistent diagnostic
to a physical turbulence or screen measurement.

## Codebase Findings

- The free-alpha fit changes only the frequency scaling of an exponential-tail
  model. Pipeline provenance explicitly calls alpha near 2.5 a model-mismatch
  signature, not a physical screen index
  ([preserved provenance, lines 8--16](research/evidence/free-alpha-diagnostic-2026-07-22/source/PLPBF_FITTER_PROVENANCE.md)).
- The physical heavy-tail model collapsed to the production model, while the
  free-alpha diagnostic retained large evidence differences for casey and
  wilhelm ([mechanism report, lines 13--28](notes/report-jointtf-mechanism-closure-2026-07-18.md)).
- The completed mechanism battery excludes the tested heavy-tail, missed-close-
  component, combined-tail-and-component, peak-dipole, and scintillation-gain
  explanations. Two-screen chromaticity remains only a hypothesis by
  elimination; no forward two-screen model has established it
  ([mechanism report, lines 30--47](notes/report-jointtf-mechanism-closure-2026-07-18.md)).
- Standing manuscript context already retires old free-alpha values and permits
  them only as exponential-parametrization cross-checks, never turbulence
  indices (`CONTEXT.md:469-472`).
- The board still incorrectly listed the leakage verdict and this reporting
  decision as open (`docs/rse/control/BOARD.md:76-85` before this resolution).

## Live h17 Findings

The h17 handshake succeeded on `lxd110h17` at `2026-07-22T11:42:08Z`.
The six products, jobs 147--152 output and empty error logs, driver, Slurm job
script, fitter provenance, and current campaign-input records are preserved in
the [hash-bound packet](research/evidence/free-alpha-diagnostic-2026-07-22/).

The fit worktree was at dsa110-FLITS commit
`d292f4b91ef02dfd120a816c015fbb67cb15261f`; the copied driver and provenance
were untracked there. The currently available campaign-input records are clean
at commit `99dcef138a843d5f6255969d67e13b4aa7c6fcbc`, but postdate the injections
by one day. Exact run parameters are embedded in each product and log. These
limits prevent treating the packet as a fully reproducible rerun of the fit;
they do not prevent independent verification of the landed bounds.

Independent standard-library verification passes:

- all 23 copied artifacts match their SHA-256 hashes;
- all six 90% posterior intervals contain alpha=4;
- all six jobs returned zero and all error logs are empty;
- maximum absolute bias is `0.016916268328` across all runs;
- maximum absolute bias is `0.014075588522` across the four decorrelating runs.

The `0.02` reported bound is therefore supported. The exact decorrelating
maximum rounds to `0.014` at three decimals but is `0.0141`, not mathematically
less than or equal to `0.014` without rounding.

One metadata-only defect was found. The driver records nominal channel width as
bandwidth divided by channel count, while its inclusive frequency grid uses
bandwidth divided by one fewer interval. The effective modulation saved in the
products matches the actual grid spacing, so the injections and bound are not
changed. The verifier checks both meanings explicitly.

## Synthesis

The free-alpha fit is useful only as a stress test showing that the production
model leaves chromatic structure. It cannot identify a turbulence index,
screen geometry, or physical mechanism. Report it only in Methods or an
appendix, explicitly labeled an effective model-mismatch diagnostic. Exclude
it from physical result tables, screen inference, the abstract, conclusions,
and headline claims. Numerical alpha values may appear only beside that label
and the statement that no physical thin-screen interpretation is permitted.

The two-screen explanation remains a candidate for its separately chartered
forward-model lane. This diagnostic alone must not promote it. Count remediation
also remains governed by its own ticket, not by the now-excluded close-component
leakage hypothesis.

## References / Sources

- [`report-jointtf-mechanism-closure-2026-07-18.md`](notes/report-jointtf-mechanism-closure-2026-07-18.md)
- [`PLPBF_FITTER_PROVENANCE.md`](research/evidence/free-alpha-diagnostic-2026-07-22/source/PLPBF_FITTER_PROVENANCE.md)
- [`scint_leakage_inject.py`](research/evidence/free-alpha-diagnostic-2026-07-22/source/scint_leakage_inject.py)
- [`README.md`](research/evidence/free-alpha-diagnostic-2026-07-22/README.md)
- [`verify_packet.py`](research/evidence/free-alpha-diagnostic-2026-07-22/verify_packet.py)
