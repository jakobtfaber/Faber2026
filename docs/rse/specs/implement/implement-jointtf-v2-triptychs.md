# Implementation Summary: JointTF v2 triptychs

---
**Date:** 2026-07-20  
**Author:** AI Assistant  
**Status:** Implemented; manual scientific review pending  
**Plan:** [plan-jointtf-v2-triptychs.md](../plan/plan-jointtf-v2-triptychs.md)
---

## Outcome

Generated full CHIME/FRB plus DSA-110 data/model/residual triptychs for candidate
oran C1D1, johndoeII C1D2, and zach C2D3 using the `s2=100` v2 results. Moved
the older C2D1, C2D2, and C2D4 triptychs into a count-labeled historical folder.

## Verification

- Model reconstruction: expected counts, finite values, aligned grids passed.
- Recovered reduced residual statistics:
  - oran: CHIME/FRB 1.162; DSA-110 0.939.
  - johndoeII: CHIME/FRB 1.058; DSA-110 1.153.
  - zach C2D3 job 178: CHIME/FRB 2.025; DSA-110 1.213.
- Repeated render: 9/9 PNG/PDF/SVG files byte-identical.
- Corrected zach render: C2D3 job 178 remained byte-identical after a fresh render.
- Figure guards after the correction: 20 passed.
- Root MkDocs review surface: strict build passed; one page, three concise
  headings, three manuscript-bound candidate figures, no analysis pages. The
  `pipeline` submodule remains untouched.
- Targeted tests: 26 passed; two existing Python escape-sequence warnings.
- Full root tests retain the two previously diagnosed pipeline campaign
  failures: the parent pins `c6111390` instead of expected `23fbd295`, and the
  pinned campaign lacks the required 24-record result set. This change does not
  modify the pipeline gitlink.
- Visual inspection: all three contain both bands and all three columns; no
  obvious crop or rendering failure. Scientific residual acceptance remains manual.

## Boundary

The active zach figure shows C2D3 job 178. Owner full-size review rejected C2D4
job 180 as the active display because its fourth DSA component is a broad,
low-fluence pedestal and the model is disfavored by 10.1 in log evidence. Job
180 is retained as a labeled non-latest comparison. The figures remain
`candidate-v2-owner-pending`. The source fits still lack
exact fit-generation reproducibility because no sampler seeds were recorded and
executed fitting code was modified/untracked. No manuscript promotion, count
adoption, production-table rewrite, or rung-2 launch occurred.

## References

- [Plan](../plan/plan-jointtf-v2-triptychs.md)
- [Research](../research/research-jointtf-v2-triptychs.md)
- `figures/codetection_triptych/jointtf-v2-provenance.json`
- `figures/jointmodel_pair/fit_artifacts/candidate-jointtf-v2/README.md`
