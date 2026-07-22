# Plan: controlled joint-scattering reruns

**Status:** accepted for implementation by the manuscript owner, 2026-07-22  
**Scope:** Oran C1D1, JohnDoeII C2D2, and Zach C2D4 joint CHIME/FRB–DSA-110 fits  
**Owner morphology authority:** `figure_review/owner-morphology.yaml`  
**Fit re-trust contract:** [Wayfinder ticket 03](../wayfinder/tickets/03-ratify-fit-retrust-contract.md)  
**Temporary component-count guards:** [Wayfinder ticket 15](../wayfinder/tickets/15-count-audit-remediation-standing-method.md)

## Objective

Replace the three diagnostic-only joint-scattering candidates with clean,
seeded fits whose complete generation and rendering chains can be reproduced.
Only panels made from those new fits may return to owner visual review.

The immediate purpose is rapid visual judgment of model and residual
morphology. Passing the panel-reproduction gate does not approve a fitted
value, component-count evidence comparison, manuscript claim, or promotion.

## Fixed scientific scope

| Burst | Required morphology | Seed policy |
|---|---:|---|
| Oran | C1D1 | explicit and recorded |
| JohnDoeII | C2D2 | explicit and recorded |
| Zach | C2D4 | explicit and recorded |

The counts come from the owner's hash-bound data-only morphology review. The
old JohnDoeII C1D2 and Zach C2D3 candidates cannot substitute for these fits.
The deprecated Zach C2D4 job 180 cannot be promoted or copied into the new
run. It is evidence used to design the new run's failure guards.

## Required sequence

1. Reconstruct and quantify the deprecated Zach C2D4 failure from its producing
   artifacts. Freeze the resulting guards before any new fit starts.
2. Make the joint-fit entry point accept and record an explicit sampler seed.
   Add a controlled-run receipt that fails closed on dirty source, unhashed
   inputs, missing configuration, or missing environment identity. Prove the
   mechanism with a cheap deterministic test.
3. Run the three sightlines independently from the frozen code and run
   contract. Each produces a fit summary, weighted samples, model grid,
   residual diagnostics, panel, and reproduction receipt.
4. Admit only new candidates whose reproduction receipts pass. Keep prior
   batches immutable and keep all fitted values trust-pending.

## Deprecated-Zach guards

The audit must verify values against the original fit and model artifacts, not
against prose. At minimum the controlled path must expose:

- every component arrival time relative to the fitted window;
- component temporal width and band-integrated fluence fraction;
- a flag for a very broad, low-fluence component that behaves as a pedestal;
- component-count identity in the fit summary, sample file, model grid, and
  review manifest;
- residual morphology in both bands; and
- whether an evidence comparison uses the same likelihood, gain-prior arm,
  fitted support, and posterior mode.

The audit may refine numerical thresholds. It may not hide the old failure by
rerendering it with a more favorable crop.

## Controlled-fit receipt

Before sampling, record and verify:

1. exact CHIME/FRB and DSA-110 input paths and SHA-256 values;
2. exact per-band run configurations and SHA-256 values;
3. component counts, gain-prior configuration, priors, fitted time support,
   live-point count, stopping rule, worker count, and explicit seed;
4. source revision and a clean-worktree assertion;
5. argument-vector command and working directory; and
6. Python, dependency-lock, operating-system, and machine identity.

After sampling, append hashes for the fit summary, weighted samples, model
grid, diagnostics, and rendered panel. A second clean execution using the same
receipt inputs must reproduce the fit content and candidate panel. Any
nondeterministic container bytes must be normalized before hashing; scientific
arrays and metadata must agree exactly.

## Per-sightline diagnostic packet

Each run records:

- prior-edge status; a prior rail rejects that model family and is never quoted
  as a limit;
- posterior-predictive residual maps and band-summed residual profiles;
- component arrival, width, and fluence diagnostics;
- window and crop support; and
- an agent recommendation: visually plausible, suspicious, or failed.

A suspicious but exactly reproduced panel may enter visual review so the owner
can flag it immediately. A provenance or reproduction failure may not.

## Review admission

The final admission step must:

- create a new immutable review batch; never revise the completed
  `2026-07-22-joint-scattering-current` batch;
- bind every displayed panel to the new fit and model-grid hashes;
- reject any old fit, sample, model-grid, or panel hash;
- make `make figure-review-next` return at most one eligible new panel;
- leave owner decisions unset; and
- keep the results registry trust state pending and manuscript promotion
  disabled.

## Ticket graph

```text
deprecated Zach audit
        |
seeded reproducible runner
     /     |      \
  Oran  JohnDoeII  Zach
     \     |      /
 new-panel review admission
```

Tickets 3–5 may execute concurrently only in separate worktrees and output
roots. Ticket 6 is the sole writer to the shared review-admission surfaces.

## Completion

This plan is complete when all six tickets resolve, the newly generated panels
are either admitted or explicitly withheld by the reproduction gate, and an
independent code-and-spec review passes. Completion does not imply that any fit
value is citable.
