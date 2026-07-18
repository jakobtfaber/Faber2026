# Decision brief: two-screen chromaticity — charter a forward model, or interpret-only?

---
**Date:** 2026-07-18
**Author:** AI Assistant (team-lead session)
**Status:** DECISION PENDING (owner)
**Evidence base:** `report-jointtf-mechanism-closure-2026-07-18.md` §1–2; deck slide 6.

---

## The question

casey and wilhelm's τ(ν) demonstrably deviates from ν⁻⁴ (free-α wedges +5537 /
+731, both decisive), and every modeled single-screen explanation has been
quantitatively excluded (tail shape, injection biases, peak dipoles, scint-gain
leakage). The sole surviving hypothesis is **two-screen chromaticity**: two
scattering screens (e.g. host + Milky Way / intervening) whose different τ(ν)
laws mix across the 0.4–1.5 GHz lever arm, producing an effective sub-4 index in
a single-screen fit. Do we (A) charter a forward two-screen model, (B) write it
up as the interpreted hypothesis without a new model, or (C) defer until the
count/TOA campaign closes?

## What each option means

### Option A — charter the forward model (model-change class, like PL-PBF was)
Fit shape: two convolved PBFs, τ₁(ν)=τ₁ν^−4 ⊗ τ₂(ν)=τ₂ν^−4 with independent
amplitudes — 1 extra parameter vs production (τ₂/τ₁ at 1 GHz), α tied physical
on both screens, nested (τ₂→0 = production). Chartered exactly like PL-PBF:
injection validation → casey+wilhelm real-data three-way → owner review →
sample-wide only if it wins.
- **For:** it is the actual physical hypothesis; the PL-PBF lane just proved this
  loop runs end-to-end in ~1 day of compute; nesting gives a valid Bayes factor;
  a WIN converts both wedges into a physical measurement (screen ratio) and may
  resolve casey's peak-associated rail; a LOSS completes the elimination table
  with the last physical candidate and leaves "unmodeled systematic" as the
  honest conclusion.
- **Against:** two-screen convolution kernels + chromatic mixing is a genuinely
  harder kernel build than the PL-PBF's (product of exponentials in the Fourier
  domain is easy; validating identifiability of τ₂/τ₁ against the gain marginal
  is the real work); risks a τ₂-unconstrained collapse exactly like s_i (the
  wedge may be resolvable only with more lever arm than two bands provide);
  delays the TOA/manuscript closeout if treated as a gate.
- **Cost estimate:** kernel+injection ~1 agent-day; real-data fits ~2 h wall
  each on h17 (measured from PL-PBF); no manuscript dependency if run as a
  parallel lane.
- **Prior expectation, pre-registered honestly:** the scint two-band
  decomposition (FLITS PR #201) already supports two-screen structure in this
  sample, and Cordes §11.4 names multi-screen mixing as a standard sub-4 route —
  but the same PR's decomposition for these two specific bursts is diagnostic-
  grade, so a τ₂ upper-limit (collapse) outcome is live.

### Option B — interpret-only (systematics appendix)
Write the elimination chain + two-screen attribution as the appendix conclusion,
with the wedges quoted as model-selection diagnostics, production limits stand.
- **For:** zero new compute/build; manuscript unblocked now; the elimination
  table is already publication-grade and referee-defensible as far as it goes.
- **Against:** a referee can ask "you name two-screen — why didn't you fit it?";
  leaves the 7× casey/wilhelm wedge-magnitude difference and casey's
  peak-associated rail as unexplained loose ends; weaker than what the
  infrastructure demonstrably supports.

### Option C — defer
Close counts/TOA first; decide A-vs-B after.
- **For:** TOA table is the campaign deliverable; A is not on its critical path.
- **Against:** pure scheduling; decides nothing; the framing above doesn't
  improve with time (the inputs are complete now).

## Recommendation

**A, run as a non-gating parallel lane** (manuscript proceeds on B's text until
A reports; A's outcome upgrades or confirms the appendix). Rationale: the
marginal cost is small against today's demonstrated loop; either outcome is
publishable and referee-strengthening; and it is the only option that can turn
the +5537 anomaly into physics rather than a caveat. Guardrails carried over
from the PL-PBF charter: injection-validated kernel before real data; nested
comparison only; casey+wilhelm only before owner review; no production-table
writes; pre-registered interpretation matrix (win = screen ratio measured;
collapse = τ₂ upper limit, appendix unchanged).

## What is NOT being asked

No manuscript text changes, no pin bumps, no production-table changes, no
sample-wide runs — those all remain behind owner review regardless of A/B/C.
