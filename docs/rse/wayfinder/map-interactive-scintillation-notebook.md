<!-- wayfinder:map -->
# Map: Interactive Scintillation Analysis Notebook

Tickets live in [`tickets/`](tickets/). A ticket is claimed by writing an assignee into its header; blocking uses the `Blocked by:` header line (local markdown tracker — no native dependency links). The frontier = open tickets with no open blockers and no assignee.

## Destination

An interactive Jupyter notebook (`notebooks/scintillation_interactive_walkthrough.ipynb`) that converts the canonical CHIME/FRB and DSA-110 scintillation analysis workflow into a step-by-step interactive walkthrough: loading Stokes-I burst data, performing multi-sub-band ACF scintillation bandwidth fits and modulation index calculations from 400 MHz to 1530 MHz, plotting diagnostic figures, and fitting the frequency scaling power law \(\Delta\nu_d \propto \nu^\alpha\) to obtain \(\alpha\).

## Notes

- **Domain:** FRB scintillation, 2D auto-correlation functions (ACF), sub-band Lorentzian/Gaussian fitting, modulation index calculation, power-law frequency scaling fit (\(\alpha\)).
- **Standing Context:** [`CONTEXT.md`](../../../CONTEXT.md), `pipeline/scintillation/scint_analysis/`, and `analysis/scintillation-dsa-lorentzian-2026-07-07/`.
- **Skills:** `/grilling`, `/domain-modeling`, `/research`, `/prototype`.
- **Data paths:** DSA-110 Stokes-I cubes under `~/Data/Faber2026/dsa110/DSA_bursts/` and CHIME under `~/Data/Faber2026/chimefrb/CHIME_bursts/`.

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- [Locate canonical scintillation code, routines, and burst data](tickets/scint-notebook-01-locate-canonical-scintillation-code-and-data.md) — Canonical Python modules located in `pipeline/scintillation/scint_analysis/` (`core.py`, `analysis.py`, `fitting_2d.py`); CHIME and DSA-110 `.npz`/`.npy` data product paths cataloged.
- [Define notebook structure and interactive execution flow](tickets/scint-notebook-02-define-notebook-structure-and-execution-flow.md) — Established 6-stage sequential cell structure for single-event execution using Python config dicts combined with interactive `ipywidgets` controls in `notebooks/scintillation_interactive_walkthrough.ipynb`.
- [Define sub-band ACF and fitting contract](tickets/scint-notebook-03-define-subband-acf-and-fitting-contract.md) — Ratified Lorentzian ACF fitting with zero-lag noise spike masking (`first_fit_lag=1`) and equal S/N sub-band partitioning (4 sub-bands for CHIME, 2 for DSA-110).
- [Define modulation index and error analysis](tickets/scint-notebook-04-define-modulation-index-and-error-analysis.md) — Adopted canonical `analysis.py` ACF-fitted $m(\nu)$ sub-band amplitude with leastsq covariance error and profile-domain sliding $m(t)$.
- [Define alpha power law fit and visualization specification](tickets/scint-notebook-05-define-alpha-power-law-fit-and-visualization.md) — Confirmed ODR log-log power-law fit ($\nu_{\text{ref}} = 600\text{ MHz}$) and 3-tier dynamic spectrum, $\Delta\nu_d(\nu)$, and $m(\nu)$ multi-panel summary figure layout.

## Not yet specified

- **Interactive Widget Scope:** Interactive `ipywidgets` controls for dynamic lag masking and sub-band boundary tuning vs cell-based configuration dictionaries.
- **Export & Production Pipeline Sync:** Re-exporting modified fit parameters back into the pipeline's canonical JSON validation schemas.

## Out of scope

- **Automated batch pipeline refactoring:** Updating background pipeline execution across all cataloged events (notebook is focused on interactive walkthrough and verification).
- **Polarization scintillation:** Polarimetric scintillation / RM synthesis (scope is Stokes-I total intensity).
