# Casey joint-fit performance recovery

Status: exploration. No Casey sampler is running.

## Scientific objective

The Casey test case fits one shared absolute dispersion measure and one
unscattered geocentric arrival time at 400 MHz to the separate native
CHIME/FRB and DSA-110 grids. The required comparison contains a Gaussian and a
scattering model for the primary DSA-110 anchor at sample 15259 and the
predeclared timing sensitivity at sample 15256.

The first primary run was stopped after 6 hours 43 minutes. The Gaussian model
barely reached the evidence stopping rule; the scattering model remained
unconverged after more than four hours. This is an execution failure, not a
scientific result. Its checkpoints remain preserved and must not be resumed or
overwritten.

## Measured performance

| State | Gaussian likelihood | Scattering likelihood | Sampler evidence | Full primary plus sensitivity projection | Decision |
|---|---:|---:|---|---:|---|
| Reference implementation | 105.7 ms | 213.1 ms | Gaussian: 849,724 calls, barely converged. Scattering: 742,901 calls, unconverged. | Observed run exceeded 6 h 43 min before primary completion. | Reject |
| Exact one-component gain reduction | 34.1 ms | 150.2 ms | Same mathematical likelihood; no new sampling. | Already-observed primary calls alone require at least 146 min, or 183 min with a 25% margin. This excludes the remaining scattering calls and the complete sample-15256 comparison. | Reject for sampling |
| Exact flattened response evaluation | 37.5 ms | 100.0 ms | Maximum absolute likelihood difference from the independent reference check: 1.21e-8, about 2.1e-15 relative. 107 tests pass locally and on h17. | About 221 min for all four fits using the observed morphology-specific call counts. | Reject for sampling |
| Static 125-sample DSA-110 window | 14.5 ms | 50.7 ms | Posterior difference below 1e-9, but absolute likelihood differences reach 837–1,165 at allowed prior edges. The full-prior scattering bound requires the entire delivered window. | 104.1 min for all four fits using observed call counts and 16 workers. | Reject: changes the likelihood |
| Band-specific broadened-width windows | 2.0 ms | 8.0 ms | Posterior-median absolute difference about 5e-9, but nearby posterior points reach 4.6e-8 and broad-prior differences reach about 8,275. | Hypothetical fixed crop: 30.8 min. Full-prior-safe conservative projection: 419.4 min. Both include a 25% margin and 10.256 historically effective workers. | Reject: changes the likelihood and misses target |

The current reduction evaluates the one-component gain integral in closed form,
caches parameter-independent mask and noise terms, and flattens response-node
evaluation. The exact candidate is based on source state
`47db30323a97c0a8213e1565cb7fd1562f9edd9d`; its patch digest is
`4a94af9c5f185a397596f09caefcb7a43281c7c125495ac9e700ea6792a8ee83`.
These checks establish numerical consistency, not a restart decision.

## One-hypothesis rule

Only one measured bottleneck is changed at a time. Every experiment must state
one falsifiable prediction and return:

1. before/after timings on the real Casey likelihood for both models;
2. agreement with the reference likelihood at deterministic real, synthetic,
   posterior, prior, and prior-edge points;
3. focused test results;
4. an observed or justified sampler-call count;
5. a conservative end-to-end duration for all four fits.

An experiment is rejected if it lacks numerical-equivalence evidence or does
not materially reduce the conservative full-fit duration. The original
products remain unchanged; window design is read-only, not a fit-definition
change.

The band-specific broadened-width windows use the left half-maximum through
right 1/e profile width plus two such widths of margin on each side. They give
approximately 20% occupancy and large per-call speedups, but fail the nearby
posterior likelihood tolerance and still project to 30.8 minutes under a fixed
crop. The current hypothesis is parameter-adaptive, two-sided support with a
full-grid fallback and a direct likelihood-error bound through both gain Gram
and data-projection terms. Its duration must include the measured slow-path
fraction and historical pool efficiency.

## Separation of responsibilities

- One writer owns likelihood profiling and performance changes.
- Numerical verification begins only after an exact candidate is frozen.
- Input identity, candidate identity, and checkpoint preservation are checked
  once for that frozen candidate.
- The scientific go/no-go decision uses the measured full-fit projection and
  the independent checks; implementation success alone cannot authorize a run.

Changing priors, the likelihood, morphology comparison, native grids, live
points, evidence stopping rule, or sampling method is outside this recovery
test.

## Freeze, review, and restart conditions

A candidate may be frozen for independent review only when its conservative
primary-plus-sensitivity projection is a few minutes. The frozen record must
bind the exact source state, Casey inputs, timing variant, measured likelihood
times, sampler-call basis, numerical-equivalence evidence, and tests.

A controlled restart requires all of the following:

1. a measured few-minutes end-to-end projection with margin;
2. numerical equivalence to the reference model over the predeclared test set;
3. an independent frozen-candidate pass;
4. unchanged, hash-verified reference checkpoints and a distinct output root;
5. exact source-bound approval of the scientific inputs;
6. explicit authorization to sample the exact reviewed event binding.

Until every condition passes, no sampler restart occurs. A completed fit still
fails scientific interpretation if it is prior-railed, non-converged,
boundary-limited, or model-inadequate.

## Independent pre-freeze checks

The 2026-08-04 independent review confirms the closed-form gain reduction and
flattened response calculation, but requires four additional checks for any
support-limited candidate: bound the likelihood change through both the gain
Gram term and the data projection; include two-sided support, the worst
frequency node, residual-dispersion sweep, and full-grid fallback; time the
parameter-dependent slow-path fraction; and correct the wall-time projection
for measured pool efficiency rather than assuming perfect 16-worker scaling.
Cached observation arrays must also remain immutable. The independent review is
repeated at the frozen candidate hash.

## Companion diagnostic notebook

The exploratory notebook `casey-fit-input-diagnostic.ipynb` is not tracked:
repository policy (config/grandfathered-notebooks.txt) freezes the set of
tracked notebooks. It is preserved at Git tag
`rescue/casey-fit-performance-recovery` (path
`docs/analysis/casey-fit-input-diagnostic.ipynb`) and, for live work, belongs
under `~/Data/Faber2026/workbench/` per docs/rse/ops/live-analysis.md.
