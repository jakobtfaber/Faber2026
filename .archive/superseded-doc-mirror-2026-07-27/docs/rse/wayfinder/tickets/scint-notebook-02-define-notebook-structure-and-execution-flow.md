<!-- wayfinder:ticket -->
# Ticket: Define notebook structure and interactive execution flow

- Type: grilling
- Status: resolved
- Assignee: antigravity
- Blocked by: [`scint-notebook-01-locate-canonical-scintillation-code-and-data.md`](scint-notebook-01-locate-canonical-scintillation-code-and-data.md)
- Map: [`../map-interactive-scintillation-notebook.md`](../map-interactive-scintillation-notebook.md)

## Question

What exact cell structure, module imports, interactive parameter inputs, diagnostic plot checkpoints, and cell-by-cell progression will `notebooks/scintillation_interactive_walkthrough.ipynb` use to guide a step-by-step manual review?

## Resolution

Aligned notebook architecture and execution contract:
- **Target File**: `notebooks/scintillation_interactive_walkthrough.ipynb`
- **Scope**: Single burst event per run (configurable via event nickname).
- **Configuration Mode**: Default configuration defined via a Python dictionary in Cell 2, with interactive `ipywidgets` controls (sliders/dropdowns) enabling dynamic tuning of dictionary values prior to calculation cells.
- **Sequential Cell Progression**:
  1. *Setup & Imports*: Load `pipeline.scintillation.scint_analysis` modules (`DynamicSpectrum`, `analysis`, `fitting_2d`) and styling.
  2. *Event & Config Selection*: Define nickname and config dict (sub-band count, lag cutoffs, fit model).
  3. *Data Loading & Pre-processing*: Load CHIME + DSA dynamic spectra, apply RFI masking and off-pulse baseline subtraction, display dynamic spectra & burst profiles.
  4. *Sub-band 2D ACF & Bandwidth Fits*: Calculate ACFs per sub-band, mask zero-lag noise spike, fit ACF model (Lorentzian/Gaussian), plot ACF + fit overlays.
  5. *Modulation Index Calculation*: Calculate \(m(t)\) profile and sub-band \(m(\nu)\), plot modulation index spectrum.
  6. *Multi-Band Power-Law Scaling (\(\alpha\)) Fit*: Combine CHIME (400–800 MHz) + DSA-110 (1280–1530 MHz) sub-band \(\Delta\nu_d(\nu)\) points, fit \(\Delta\nu_d \propto \nu^\alpha\) via ODR / 2D joint fit, and output publication-style figure.
