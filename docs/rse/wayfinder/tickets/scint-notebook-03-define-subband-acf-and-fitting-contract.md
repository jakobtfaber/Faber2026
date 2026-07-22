<!-- wayfinder:ticket -->
# Ticket: Define sub-band ACF and fitting contract

- Type: grilling
- Status: resolved
- Assignee: antigravity
- Blocked by: [`scint-notebook-01-locate-canonical-scintillation-code-and-data.md`](scint-notebook-01-locate-canonical-scintillation-code-and-data.md)
- Map: [`../map-interactive-scintillation-notebook.md`](../map-interactive-scintillation-notebook.md)

## Question

How will frequency sub-band boundaries, 2D ACF calculation, zero-lag noise spike removal, and Lorentzian vs. Gaussian model fitting options be parameterized and verified across CHIME (400–800 MHz) and DSA-110 (1280–1530 MHz) data?

## Resolution

Ratified sub-band ACF and fitting contract:
1. **Sub-band Boundary Partitioning**:
   - **CHIME (400–800 MHz)**: 4 sub-bands partitioned dynamically by **equal integrated Signal-to-Noise Ratio (S/N)** (cumulative fluence quantiles across the on-pulse spectrum) rather than equal frequency width.
   - **DSA-110 (1280–1530 MHz)**: 2 sub-bands partitioned dynamically by **equal integrated S/N**.
   - Interactive `ipywidgets` controls allow toggling between equal S/N quantiles and uniform frequency width.
2. **Zero-Lag Noise Spike Masking**:
   - `first_fit_lag = 1` bin (omitting \(\Delta\nu = 0\) zero-lag bin to prevent noise bias in ACF fits).
3. **ACF Model Fitting**:
   - **Default Model**: Lorentzian (\(C(\Delta\nu) = m / (1 + (\Delta\nu/\gamma)^2)\) where \(\gamma = \Delta\nu_d\) HWHM).
   - **Optional Model**: Gaussian (\(C(\Delta\nu) = m \exp(-\Delta\nu^2 / (2\sigma^2))\) where \(\Delta\nu_d = \sigma \sqrt{2 \ln 2}\)).
