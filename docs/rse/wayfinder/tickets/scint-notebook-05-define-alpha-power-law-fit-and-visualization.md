<!-- wayfinder:ticket -->
# Ticket: Define alpha power law fit and visualization specification

- Type: grilling
- Status: resolved
- Assignee: antigravity
- Blocked by: [`scint-notebook-03-define-subband-acf-and-fitting-contract.md`](scint-notebook-03-define-subband-acf-and-fitting-contract.md), [`scint-notebook-04-define-modulation-index-and-error-analysis.md`](scint-notebook-04-define-modulation-index-and-error-analysis.md)
- Map: [`../map-interactive-scintillation-notebook.md`](../map-interactive-scintillation-notebook.md)

## Question

How will the combined multi-band scintillation bandwidth dataset \(\Delta\nu_d(\nu)\) from 400 MHz to 1530 MHz be fitted for power-law exponent \(\alpha\) (\(\Delta\nu_d(\nu) = \Delta\nu_0 (\nu/\nu_0)^\alpha\)), and how will the combined scintillation bandwidth and modulation index multi-panel plot be styled?

## Resolution

Ratified power-law fitting and multi-panel visualization contract matching `analysis.py` (`estimate_gamma_scaling`):
1. **Power-Law Scaling Fit**:
   - **Model**: \(\Delta\nu_d(\nu) = \Delta\nu_{\text{ref}} (\nu / \nu_{\text{ref}})^\alpha\) with \(\nu_{\text{ref}} = 600\text{ MHz}\).
   - **Fitting Engine**: Log-space Orthogonal Distance Regression (ODR) via `estimate_gamma_scaling()`, accounting for sub-band frequency spans and \(\Delta\nu_d\) error bounds.
   - **Reference Slopes**: Overlaid theoretical Kolmogorov (\(\alpha = 4.4\)) and thin-screen (\(\alpha = 4.0\)) power-law slope lines.
2. **Multi-Panel Summary Figure Layout**:
   - **Top Tier (Panels A1 & A2)**: Dynamic spectra for CHIME (400–800 MHz) and DSA-110 (1280–1530 MHz) with equal S/N sub-band boundary lines.
   - **Middle Tier (Panel B)**: Log-log \(\Delta\nu_d(\nu)\) vs frequency (400–1530 MHz) displaying sub-band points (4 CHIME + 2 DSA-110), best-fit \(\alpha\) power-law line, \(1\sigma\) error band, and theoretical reference slopes.
   - **Bottom Tier (Panel C)**: Modulation index spectrum \(m(\nu)\) from 400 MHz to 1530 MHz with strong scintillation threshold line (\(m=1\)).
