# Decision: P1 is the final CHIME recovery attempt; paper scope forks on its outcome

---
**Date:** 2026-07-15
**Recorded by:** Claude (Fable 5), under the owner's 2026-07-15 session directive
to proceed autonomously on the declared critical path. This record is agent-recorded
and owner-governed: the owner ratifies, amends, or revokes it by editing this file.
**Status:** Amended by owner 2026-07-15 (in-session direction) — the fail-branch
narrowing is NOT ratified; see §Owner amendment below. **Amendment wording
ratified by the owner 2026-07-15 (in-session, second confirmation).**
**Related documents:**
- [Decision: Figure 1 + CHIME C1 route (owner, 2026-07-14)](decision-2026-07-14-figure1-and-chime-c1.md) — the stop rule this record extends
- [Plan: corrected CHIME products revival](plan-chime-scint-corrected-products-revival.md) — P1 design (a v1.2 revision is in flight in a separate worktree; this record governs scope regardless of that revision's final form)
- [Experiment: C1 blinded calibration](experiment-chime-scint-c1-calibration.md) — the DOCUMENTED-FAIL record
---

## Context

C1 closed as DOCUMENTED-FAIL on 2026-07-15 (FLITS #176): 0/8 required
low-modulation calibration cells passed, nulls failed the family-wise gate, and
the burst was never unblinded. The 2026-07-14 decision's stop rule forbids
further estimator tuning on the retained product and requires any successor to
change the information content of the input product. P1 (`p1-window-upchan`)
is that successor: it regenerates the freya product from the coherently
dedispersed baseband with predeclared windowed fine-channelization variants.

The stop rule bounds each *experiment*. It does not by itself bound the
*campaign*: after a P1 failure, another product-changing route (external
calibrators, voltage-domain reprocessing, finer time resolution) would again be
formally sanctioned, and so on indefinitely. This record closes that loop for
the current paper.

## Decision

1. **P1 is the final CHIME scintillation recovery attempt within the scope of
   this paper.** Its go/no-go gates are those predeclared in its own experiment
   record before unblinding. No threshold may change after inspection; per the
   2026-07-14 decision, a changed threshold creates a new experiment — and a
   new experiment is outside this paper's scope.
2. **If P1 qualifies on freya:** freeze the configuration, run the twelve-burst
   campaign, rebuild the two-screen/scattering attribution chain on the
   corrected products, and only then write the synthesis.
3. **If P1 fails:** the paper narrows to DSA scintillation plus CHIME upper
   limits and diagnostics. The dependency spine is revised accordingly and the
   manuscript is finished on that basis. A P1 failure is a valid, publishable
   conclusion that the retained CHIME products are information-limited for
   Δν_d at the relevant modulation depths.
4. **Deferred routes** (external-calibrator campaigns, voltage-level
   reprocessing beyond P1's scope) become candidate future-paper lanes. They
   are not blockers, dependencies, or reasons to postpone the scope decision.
5. **Execution discipline:** no sample-wide P1 execution before the
   single-target qualification gate passes, and broad Discussion/synthesis
   prose stays frozen until the fork resolves.

## Why predeclare this now

Declared before P1 produces any result, while no one knows which branch will
be taken — the same fail-closed posture as the C1 calibration itself. Without
it, each documented failure sanctions the next recovery attempt and the paper
has no finish line; with it, P1's outcome — either outcome — resolves the
paper's scope.

## Outcome (same day, 2026-07-15)

P1 closed as a mechanism-level `DOCUMENTED-FAIL` nine minutes after this
record merged: none of the five predeclared window variants passed the frozen
10× common-mode suppression screen, so P1 ended without on-pulse fitting or a
C1-style calibration (PR #47; revival plan Phase 3 closure; no Phase-4 route
authorized). Timing note for the record: this rule was written and merged
without access to the P1 verdict, but the h17 variant runs were already in
flight — the rule's authority rests on owner ratification, not on the
minutes between the two merges.

Under §Decision item 3, the fail branch applies: the paper narrows to DSA
scintillation plus CHIME upper limits and diagnostics, and any future passing
route (the plan's conditional Phase 4 included) is a future-paper lane.
**Execution of the narrowing awaits owner ratification of this record.**

## Owner amendment (2026-07-15, in-session direction)

The owner declines to ratify the fail-branch narrowing: obtaining a solid
CHIME scintillation measurement remains an active goal of this paper. In
consequence:

1. **§Decision item 1 ("P1 is the final CHIME scintillation recovery attempt
   within the scope of this paper") is revoked.** §Decision item 3's
   narrowing is not executed; Discussion/synthesis prose stays frozen.
2. P1's own result stands untouched: a mechanism-level `DOCUMENTED-FAIL`,
   indexed in the pinned pipeline inventory (FLITS PR #179, pin PR #50).
   P1 additionally refuted the second-stage FFT-leakage origin hypothesis —
   windowing left the common-mode amplitude unchanged (0.586 → 0.62–0.68),
   placing the structure upstream of fine channelization, in the baseband
   within each 390.625 kHz coarse channel.
3. The successor direction space is therefore the remaining product-changing
   routes from the common-mode research record: **external instrumental
   characterization** (steady calibrator through the identical baseband +
   upchannelization path) and **voltage-domain cross-statistics** (separate
   the multiplicative common bandpass from source-flux modulation before
   detection). Each requires a predeclared experiment record with frozen
   gates before any burst data is inspected, and each must confront the
   recorded S/N caveat (burst ≈ 5 % above background in the retained product;
   scintillation signature ≈ 0.75 % of total intensity against the 59 %
   common-mode term).
4. The paper's scope decision is deferred until the sanctioned successor
   route(s) resolve or the owner closes the campaign by a further edit to
   this record.
