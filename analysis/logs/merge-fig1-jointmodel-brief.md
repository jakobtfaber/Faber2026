# Design brief: merge Fig. 1 gallery + joint 2D fit figures

## Goal
Propose a concrete manuscript figure strategy that merges:
1. **Current Fig. 1** — `figures/codetection_gallery.pdf` (`fig:codetection-gallery` in `sections/observations.tex`), produced by `scripts/plot_codetection_gallery.py`: 4×3 gallery of 12 CHIME–DSA co-detections; stacked bands on one frequency axis with hatched gap; profile strip + spectrum marginal; **no model overlays** (trust-reset-safe data-only).
2. **Later joint 2D fit figures** — appendix `sections/jointmodel_pairs.tex` / `figures/jointmodel_pair/*_jointmodel_pair.pdf`: per-burst data|model|residual triptychs from `pipeline/flits/batch/codetection_plots.py::plot_codetection`.

Owner intent: **the first central figure should include the burst models**. Showing morphology + the joint 2D model early helps the reader before scattering/results sections.

## Hard visual constraints (owner)
- Show data at **full structural resolution** (do not crush time/freq so structure is lost).
- Off-pulse padding on **either side** for DSA-110 and CHIME should be **roughly equal to the total burst width at CHIME** — enough context, not a huge empty window; burst fully visible with structural complexity.
- Current gallery already adapts window from on-pulse spans + pad, clamps to ±25 ms, and block-averages (~33 µs, 512 ch/band). Revisit whether that matches the CHIME-width padding rule and whether full-res means native or display-averaged.

## Context / tension
- Original plan `docs/rse/specs/plan-unified-12burst-figure.md` explicitly forbade fit/model overlays under CONTEXT.md fit-trust reset.
- Owner now wants models in the central first figure — design must say how this interacts with trust reset (e.g. only PASS fits, caption caveats, keep residuals in appendix, chromatica gap 11-vs-12, flagged fits in `docs/rse/specs/jointmodel-pair-fit-quality-flags.md`).
- Whitney is the results-section exemplar (`fig:jointmodel-pair-whitney`); full set in appendix.
- Gallery includes **chromatica**; jointmodel pair set currently **11 bursts** (no chromatica panel).

## Deliverable (design only — no code, no file edits)
Write a structured proposal with:

1. **2–3 concrete layout approaches** (trade-offs: page real estate, model fidelity, trust-reset risk, reproduction cost).
2. **Recommended approach** with rationale.
3. **Per-panel recipe**: what is shown (data / model overlay / model column / residual?), axes, color scale, annotation (τ, α, component count?).
4. **Time-window rule** implementing the CHIME-width padding requirement precisely (formula + edge cases: scattering tails, multi-component, DSA-only structure outside CHIME span).
5. **Resolution rule**: native vs block-average; separate CHIME/DSA; print/PDF limits.
6. **Manuscript placement**: what replaces Fig. 1; what remains in appendix/results; caption sketch; cross-refs.
7. **Implementation sketch**: which scripts/APIs to reuse (`plot_codetection_gallery.py` vs `codetection_plots.plot_codetection` vs new hybrid); data/model artifact paths; chromatica handling.
8. **Risks / open decisions** for the owner (≤5 bullets).

Be concrete and manuscript-aware. Prefer reversible, surgical changes. Do not implement.
