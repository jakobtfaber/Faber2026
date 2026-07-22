<!-- wayfinder:ticket -->
# Ticket: Define modulation index and error analysis

- Type: grilling
- Status: resolved
- Assignee: antigravity
- Blocked by: [`scint-notebook-03-define-subband-acf-and-fitting-contract.md`](scint-notebook-03-define-subband-acf-and-fitting-contract.md)
- Map: [`../map-interactive-scintillation-notebook.md`](../map-interactive-scintillation-notebook.md)

## Question

What exact formulation for modulation index \(m = \sigma_I / \bar{I}\), noise bias subtraction, and uncertainty propagation will be implemented and visualized across sub-bands in the notebook?

## Resolution

Ratified modulation index and error analysis contract matching `pipeline/scintillation/scint_analysis/analysis.py`:
1. **Sub-band Modulation Index \(m(\nu)\)**: Extracted via `_fit_acf_models()` as the fitted zero-lag ACF component amplitude (with synthetic off-pulse noise-template and self-noise subtraction). Stderr errors (`mod_err`) derived via `leastsq` covariance refinement.
2. **Frequency Spectrum Reporting**: `attach_modulation_index_frequency()` packages sub-band \(m(\nu)\) and error bounds for visualization.
3. **Temporal Modulation Index \(m(t)\)**: `modulation_index_over_time()` computes sliding-window \(m(t) = \sigma_I / \langle I \rangle\) across profile gates.
