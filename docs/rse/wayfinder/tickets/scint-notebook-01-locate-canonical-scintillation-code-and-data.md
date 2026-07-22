<!-- wayfinder:ticket -->
# Ticket: Locate canonical scintillation code, routines, and burst data

- Type: research
- Status: resolved
- Assignee: research-agent
- Blocked by:
- Map: [`../map-interactive-scintillation-notebook.md`](../map-interactive-scintillation-notebook.md)

## Question

What are the canonical Python source files, modules, function signatures, and data product paths across `pipeline/scintillation/scint_analysis/` and `analysis/scintillation-*/` for loading Stokes-I burst data, calculating 2D ACFs, fitting scintillation bandwidths \(\Delta\nu_d\), calculating modulation index \(m\), and performing power-law fits across 400 MHz – 1530 MHz?

## Resolution

Identified canonical modules and data paths:
1. **Modules & Functions**:
   - `pipeline/scintillation/scint_analysis/core.py`: `DynamicSpectrum.from_numpy_file()`, `find_burst_envelope()`, `mask_rfi()`, `subtract_poly_baseline()`.
   - `pipeline/scintillation/scint_analysis/analysis.py`: `calculate_acf()`, `calculate_acfs_for_subbands()`, `_fit_acf_models()` (Lorentzian & Gaussian models), `modulation_index_over_time()`, `attach_modulation_index_frequency()`, `estimate_gamma_scaling()`.
   - `pipeline/scintillation/scint_analysis/fitting_2d.py`: `fit_2d_scintillation()` (global 2D ACF joint fit).
2. **Data Paths**:
   - CHIME (400–800 MHz): `~/Data/Faber2026/dsa110/scintillation-data/{nickname}_chime.npz` (staging at `/data/research/astrophysics/frbs/chime-dsa-codetections/upchan_codetections/{nickname}_chime_upchan.npy`).
   - DSA-110 (1280–1530 MHz): `~/Data/Faber2026/dsa110/scintillation/data/{nickname}.npz` and `~/Data/Faber2026/dsa110/DSA_bursts/{nickname}_dsa_I_*_2500b_cntr_bpc.npy`.

Authority correction: [Choose canonical input, preprocessing, and burst-envelope contract](scint-notebook-06-choose-canonical-input-preprocessing-and-envelope-contract.md) supersedes any interpretation that all listed products are interchangeable or authoritative. The CHIME/FRB source is a three-file upchannelized set; the DSA-110 source is the CANFAR dynamic-spectrum NPZ.
