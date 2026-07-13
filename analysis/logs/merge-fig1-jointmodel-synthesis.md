# Synthesis: merge Fig. 1 gallery + joint 2D models

**Agents:** Codex `gpt-5.6-sol` medium → `logs/codex-merge-fig1-jointmodel.md`  
**Claude:** `claude-fable-5` xhigh → `logs/claude-merge-fig1-jointmodel.md`  
**Date:** 2026-07-11

## Consensus

Both recommend keeping the current **4×3 data gallery as Fig. 1**, adding **model overlays** (not full data|model|resid triptychs in the gallery), leaving residuals in `app:jointmodel-pairs`, extending `scripts/plot_codetection_gallery.py`, CHIME-width padding beyond the observed on-pulse union, and ~33 µs / 512-ch display with ~600 dpi waterfall rasterization. Chromatica stays data-only.

## Divergence

| Topic | Codex | Claude |
|-------|-------|--------|
| Model encoding | Sparse 2-D contours 30/60/90% + dashed profiles | Dashed profile + spectrum marginals; optional one 50% contour |
| Trust gate | Overlay only V1-accepted + morphology-clean; omit whitney/hamilton/wilhelm until fixed | Morphology-audit overlays with † on flagged trio; pre-V1 OK if caption says no parameters quoted |
| Pad formula | \(P=\max(W_C, 1.5\,\mathrm{ms})\), retire ±25 ms clamp | \(P=\mathrm{clip}(W_C, 1.5, 15)\), raise clamp to ±35 ms |
| Whitney | Results exemplar only after flag repaired | Keep Results triptych; dagger in gallery |

## Orchestrator recommendation

**Approach A hybrid:** keep gallery geometry; add dashed model profiles (and spectrum marginals); add sparse 2-D contours only after a print-scale QA sheet. Use CHIME-width padding \(P=W_C\) with a 1.5 ms floor; decide the 15 ms cap after one QA pass on heavily scattered bursts (phineas). Show models for the 11 jointmodel bursts with † on flagged fits; chromatica data-only. Keep appendix triptychs for residuals. Promote scratch NPZs into tracked `fit_artifacts/` before claiming REPRODUCE.md completeness.

Do not implement until owner picks the trust-gate and padding-cap decisions below.
