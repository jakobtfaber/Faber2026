# Charter: two-screen forward model (Option A — owner-approved)

---
**Date:** 2026-07-18 (evening)
**Author:** AI Assistant (team-lead session; compute agent: teammate "joint-tf-fits")
**Status:** CHARTERED — owner selected Option A of
`decision-two-screen-charter-2026-07-18.md` on 2026-07-18.
**Class:** model-change lane (same class and guardrails as the PL-PBF charter).
**Gating:** NON-GATING parallel lane — the count/TOA campaign (tasks #6/#10–#12)
proceeds independently; manuscript text proceeds on the interpret-only (B)
framing until this lane reports.

---

## 1. Hypothesis under test

The casey/wilhelm free-α wedges (+5537 / +731, chromatic-scaling anomalies with
all five single-screen mechanisms quantitatively excluded — see
`report-jointtf-mechanism-closure-2026-07-18.md` §2) are produced by **two
scattering screens** whose convolved pulse-broadening mixes across the
CHIME/DSA lever arm, mimicking a sub-4 effective index in a single-screen fit.

## 2. Model (rung 1 — the chartered fit)

Production EMG extended with a second thin-screen PBF:

- Pulse shape: Gaussian(σ) ⊗ exp(τ₁(ν)) ⊗ exp(τ₂(ν)).
- Both screens physically tied: τ_k(ν) = τ_k · ν^(−α) with α = 2β/(β−2)
  (UNCLAMPED, shared β) — no free scaling index anywhere.
- One extra parameter vs production: r = τ₂/τ₁ at 1 GHz (log-uniform prior;
  bounds set by teammate at kernel build, wide enough to rail-diagnose).
- Nested: r → 0 recovers production exactly ⇒ valid Bayes factor.
- Implementation note (teammate's call): the double-exponential convolution has
  a closed form (difference of two EMGs, scaled 1/(τ₁−τ₂)) — numerically
  guard the τ₁ ≈ τ₂ limit; no numerical convolution should be needed.

**Chromaticity mechanism to verify in injection, not assume:** with both
screens at the same α the composite width still scales exactly ν⁻⁴; the
anomaly must arise from shape non-self-similarity (σ and the time-bin do not
scale with ν, so the two-tail shape sampled by a mis-specified single-screen
fit changes across the band). Whether this reaches the observed −1.6 α-bias is
**testable before any real-data fit** — that is Stage 0 below and it is a
pre-registered falsifier of the whole hypothesis at this rung.

**Rung 2 (contingent, owner-gated, NOT chartered now):** independent β₂ for
the second screen (2 extra dof, still physical α₂ = 2β₂/(β₂−2)) — only if
rung 1 both collapses AND Stage 0 shows same-α mixing cannot reach the wedge.
Free-α is never promoted to a physical model at any rung.

## 3. Stages and pre-registered decision rules

**Stage 0 — wedge-reproduction falsifier (first, cheap):** inject rung-1
two-screen data (casey-like and wilhelm-like τ/σ/band configs, r grid ∈
{0.1, 0.3, 1.0}); refit with the free-α single-screen EMG diagnostic. PASS =
some injected config produces α-bias of order −1 or steeper (sign and rough
magnitude of the observed wedges). FAIL = max reachable |bias| ≪ 1.6 ⇒ rung-1
two-screen joins the elimination table as excluded; report to owner with the
rung-2 question; NO real-data fits.

**Stage 1 — recovery + null validation (PL-PBF pattern):**
(a) recovery grid: inject two-screen, fit two-screen; require β and r inside
90% CI across the grid; (b) null: inject single-screen production, fit
two-screen; require r at lower rail / τ₂ collapse with no spurious ΔlnZ > 5.
Identifiability of r against the gain marginal is the named risk — an
unconstrained-r collapse on injections stops the lane at this stage.

**Stage 2 — real data, casey + wilhelm ONLY:** three-way on identical data:
production / two-screen / free-α wedge (diagnostic yardstick). Mode-check
before any ΔlnZ read (healthy-β protocol). Pre-registered outcomes:
- **WIN** = ΔlnZ(two-screen − production) > 5 AND r constrained interior
  (both CI bounds off the rails). Secondary diagnostic: fraction of the free-α
  wedge absorbed (report; large absorption strengthens attribution, but the
  primary criterion is the nested Bayes factor alone).
- **COLLAPSE** = r railed / τ byte-identical to production (s_i precedent) ⇒
  quote a τ₂ upper limit; interpret-only appendix stands unchanged.
- Either outcome is publishable; interpretation matrix fixed here, before the
  fits run.

**Stage 3 — owner review.** Nothing sample-wide, no production-table writes,
no manuscript text, no pipeline-pin change until the owner reviews Stage 2
(win or collapse). Same review gate the PL-PBF verdict went through.

## 4. Standing guardrails (inherited)

Injection-validated kernel before real data; snapshot-before-overwrite;
visual vetting of every fit figure (data-vs-model + residual per band, CnDm
annotated) before publication; uniform methodology; journal every ≤10 min;
team-lead independently verifies all teammate numbers on disk before anything
is published; figures with every substantive step; deck updated promptly.

## 5. Cost & schedule

Kernel + Stage 0/1 ≈ 1 agent-day; Stage 2 ≈ 2 h wall per fit on h17 (measured
from PL-PBF). Runs alongside the in-flight count wave (zach 133/134, hamilton
127–129/132, phineas 120) — h17 queue now has headroom (--mem-per-cpu fix).

## 6. Provenance

Decision brief: `decision-two-screen-charter-2026-07-18.md` (Option A).
Evidence base: `report-jointtf-mechanism-closure-2026-07-18.md` §1–2.
FLITS-side artifacts land under `analysis/scattering-refit-2026-06/` with a
`TWOSCREEN_FITTER_PROVENANCE.md` mirroring `PLPBF_FITTER_PROVENANCE.md`.
