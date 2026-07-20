# Research: JointTF v2 triptych replacement

**Date:** 2026-07-20  
**Scope:** Internal codebase and live h17 artifacts  
**Codebase state:** Faber2026 `dc7866e6`; h17 fitting worktree `d292f4b`

## Question / Scope

Determine whether current full data/model/residual triptychs exist for the
candidate JointTF v2 counts, how to reconstruct them without rerunning the
sampler, and how to retain older figures without confusing their status.

## Codebase Findings

- The renderer consumes paired `jointmodel` NPZ and `joint_fit` JSON files and
  requires data/model shape identity (`scripts/plot_codetection_triptych.py:148-170`,
  `scripts/plot_codetection_triptych.py:236-265`).
- It renders data, model, and normalized residual columns in PNG, PDF, and SVG
  (`scripts/plot_codetection_triptych.py:366-407`).
- The active roster used older counts for oran, johndoeII, and zach; the v2
  validation instead supports candidate C1D1, C1D2, and C2D3 on the `s2=100`
  arm (`docs/rse/specs/validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md:44-90`).
- Live h17 had the saved fit JSON and posterior samples but no matching v2
  model dumps. `dump_jointmodel.py` can deterministically evaluate model grids
  at posterior medians. Zach additionally needs the fine, independent DSA-110
  window used by job 178.
- The v2 fits sampled dispersion offsets and remain owner-pending. They cannot
  silently replace adopted-DM production artifacts; the roster must mark this
  boundary explicitly.

## Synthesis

Reconstruct the candidate model dumps from the saved medians, render the
full triptychs with the existing renderer, mark their status and provenance in
the roster, and move the older outputs into a count-labeled historical folder.
Owner full-size review subsequently found only three DSA maxima in the job-180
C2D4 display. Independent inspection confirmed that its fourth DSA component
has only 3.1% of recovered DSA fluence and a roughly 350 ms width, so it behaves
as a broad pedestal rather than a resolved pulse. Job 180 also has lower log
evidence than C2D3 job 178 by 10.1. Therefore C2D3 job 178 is the active zach
candidate; retain C2D4 job 180 only as a labeled diagnostic comparison. Do not
compile the candidates into the manuscript or infer count adoption from display
status.

## References / Sources

- `scripts/plot_codetection_triptych.py`
- `scripts/jointmodel_triptych_manifest.yaml`
- `tests/test_codetection_triptych.py`
- `docs/rse/specs/validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md`
