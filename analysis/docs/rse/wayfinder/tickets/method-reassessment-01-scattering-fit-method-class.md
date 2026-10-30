# Reassess the two-band scattering fit method class

- Type: `wayfinder:task` (AFK; owner-chartered autonomous execution)
- Status: open
- Assignee: Claude (Fable 5.1) lead; Codex independent review
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Evidence root: [`specs/research/method-reassessment-2026-09-11/`](../../specs/research/method-reassessment-2026-09-11/)
- Authorization: manuscript owner, 2026-09-11

## Owner decision

- Decision: charter a wholesale reassessment of the scattering re-fit
  methods before any further re-fit campaign; execute autonomously through
  repository publication if the results are ready.
- Recorded: manuscript owner, 2026-09-11, in session. Owner's words: "I'm
  dubious of the refitting methods that might be employed, they have
  remained problematic for quite some time. I wonder if a wholesale
  reassessment of the methods is warranted." Then: "Yes, charter the
  reassessment, but proceed through to execution and even publication, if
  ready, autonomously."
- Scope of "publication": the repository publication phase (receipts,
  independent review, landed pull requests under the standing branch and
  pull-request authorization). External submission, DOI minting, and any
  one-way action remain owner gates.
- Effect: the controlled Zach reruns
  ([ticket 07](joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md))
  are parked until this ticket's method decision is recorded; they inherit
  whichever method family survives.

## Boundary

- Objective: decide, on evidence, whether the beta-coupled thin-screen joint
  model is a defensible headline measurement for this sample, and if not,
  which method family replaces it and what the paper can then claim.
- Scientific phase: scientific validation (assumption, sensitivity, and
  model-adequacy tests). No fitted value is promoted to the manuscript by
  this ticket.
- Operational phase: discovery → verification → landing, one at a time.
- May change: files under the evidence root; this ticket; ticket 07's
  status line; `CONTEXT.md` trust-state notes that this work confirms
  stale; the manuscript methods text only in a separately scoped change
  after the method decision.
- Must not change: any archived fit product, `_cntr_bpc` inputs, the
  scintillation campaign, the foreground census or budget products.
- Done when: the four deliverables below exist, an independent
  cross-provider review has returned approve/revise on the decision memo,
  and the method decision card is recorded here with its evidence.

## What to build

1. **Code audit** of the production fitter as implemented (model class,
   priors, gain marginalization, likelihood, sampler, identifiability).
2. **History ledger** of every campaign failure since 2026-07-01 with the
   diagnosed cause class and whether the fix was validated.
3. **Injection-recovery study** that assigns each railed sightline a cause:
   simulate two-band bursts with known turbulence index, geometry, and
   component count; fit with the production model; test (a) whether an
   interior true beta is recovered interior on clean simulated data
   (inference defect if not), (b) whether extended-medium or two-screen
   truths reproduce the observed rails under the thin-screen model
   (model-class defect if so), (c) sensitivity to signal-to-noise and the
   gain-prior variance.
4. **Decision memo** ranking candidate method families (beta-coupled with
   extended kernel; per-band tau with fixed-family pulse-broadening
   function and empirical two-band alpha with mismatch flags; hybrid with
   beta-coupled as sensitivity test only) by referee acceptability,
   honesty, and effort, with what the manuscript can claim under each.

## Acceptance criteria

- [ ] Code audit memo with file:line evidence for each stated defect.
- [ ] History ledger with per-entry cause class and validation status.
- [ ] Injection-recovery results with a re-runnable script, fixed seeds,
      and per-case recovery tables and figures.
- [ ] Decision memo with a recommended family and the manuscript claims
      it supports.
- [x] Independent cross-provider review of the decision memo recorded in
      the evidence root.
- [x] Method decision card appended to this ticket (provisional; charter incomplete).

## Decision card

- Recommendation: family 3, **provisional**. Intended headline is per-band
  exponential scales plus a descriptive index; beta is conditional on a
  separately validated thin-screen comparison.
- Evidence: [decision memo](../../specs/research/method-reassessment-2026-09-11/decision-memo.md),
  29 harness cases and five production controls. Selected synthetic mismatches
  yield rails or misleading interior fits; complete production kernel/alpha
  discontinuity is reproduced.
- Review: initial independent Codex verdict **BLOCK**. Corrections remove invalid
  mean-delay targets, unsupported sampler/bias causation and current-capability
  overclaims. Final independent Claude review approves provisional draft publication; no scientific validation approval.
- Unfinished charter requirement: assign actual sightline causes. This synthetic
  assessment does not fulfill that requirement, and it is not waived.
- Follow-ups: complete-model continuity; implement specified headline path;
  repeated calibration, prior and geometry checks; actual-sightline diagnosis;
  repair current simulation-gate import. Production changes remain separate.
- Disposition: ticket stays open; ticket 07 parked. A reviewed draft pull request
  may publish the provisional evidence. No scientific merge or manuscript promotion.
