# Figure wishlist — Faber2026

**Status:** living inventory
**Date:** 2026-07-17
**Purpose:** single list of figures we intend to put in the manuscript but have
not yet (re)inserted under the trust-reset / V-ladder gates.

Manuscript placeholders are live draft `\fbox` floats in the tex (see below).
Do **not** `\includegraphics` a revoked product into a live float until its
gate clears — on-disk PDFs under `figures/` may be campaign-era.

**Related:** `CONTEXT.md` (trust / revoked artifacts) ·
`docs/rse/specs/plan-circulation-readiness.md` ·
`docs/rse/specs/decision-d2-d5-scattering-design-locks.md` (D2–D5 presentation) ·
`repro_manifest.csv` (producers for existing files)

---

## Already in the manuscript (not wishlist)

| Label | File (typical) | Section |
|-------|----------------|---------|
| `fig:codetection-gallery` | `codetection_gallery.pdf` | §Obs data |
| `fig:ne2025_mw` | `ne2025_mw_characterization_nside32.pdf` | §Obs-MW |
| `fig:sightline_halo_grid` | `sightline_halo_grid.pdf` | §Obs-FG |
| `fig:assoc-cards-grid` | `association_cards/` | §ToA / appendix |
| `fig:jointmodel-pair-*` | `jointmodel_pair/` | App morphology audit (no τ/β quotes) |
| `fig:clusters_icm` | `clusters_icm.pdf` | App / dominant systems |
| `fig:dm_host_posteriors` | `dm_host_posteriors.pdf` | App C |

---

## Wanted — restore / add (gated)

| ID | Intended label | Role | Gate | On-disk candidate | Ms placeholder |
|----|----------------|------|------|-------------------|----------------|
| W1 | `fig:budget` | Measured-vs-predicted scattering budget (τ overlay on intervening predictions) | V1 + C + plan D1 | `sightline_dm_scattering_budget.pdf` (measured side revoked) | `sections/results.tex` §budget |
| W2 | `fig:jointmodel_montage` | Joint two-band model/data/residual montage for the sample | V1 + C | `jointmodel_montage.pdf` (revoked fits) | `sections/observations.tex` §obs-scatt |
| W3 | `fig:scint-qualified-summary` | Qualified DSA+CHIME scintillation measurements, kept separate by burst | Exact-byte owner approval | New joint candidate required; the 2026-07-17 owner decision rejected the DSA-only `dsa_lorentzian_summary.pdf` concept | `sections/results.tex` §results-scintillation |
| W4 | `fig:subband_tau_validation` | Sub-band EMG τ-slope diagnostic grid (D3: diagnostic only) | V1 | `subband_tau_validation_grid.pdf`, `chime_subband_compare.pdf` | `sections/results.tex` §results-alpha (+ Methods TODO) |
| W5 | `fig:scint_screens` | Two-screen / screen-attribution summary (CHIME+DSA τ·Δν_d) | B5 + V1 scint + A1 | `codetection_scint_excess.pdf` (and related wilhelm scint PDFs) — regenerate | `sections/results.tex` §results-scintillation |
| W6 | *(CHIME ACF gallery)* | Per-burst CHIME-band ACF diagnostics (peer of App DSA ACF) | Owner decision after PR #192 campaign review | PR #192 records 24 reviewed standard/high-resolution products; only `chromatica_hi` is a measurement | no manuscript slot yet |
| W7 | *(joint DSA+CHIME ACF gallery)* | Replace the removed July-7 DSA-only appendix panels with post-finalization, status-labeled two-band diagnostics | New DSA rerun + exact-byte owner approval | PR #192 supplies 24 hash-reviewed CHIME renders; no matching post-finalization DSA products exist at pin `17d9d266` | `sections/appendix.tex` §scintillation ACF diagnostics |

---

## Optional / decide later

| ID | Candidate | Role | Notes |
|----|-----------|------|-------|
| O1 | `galaxies_cgm.pdf` | Curated CGM/halo diagnostic | Census lane cleared (V4); not currently cited. Include only if it adds beyond `fig:sightline_halo_grid`. |
| O2 | `pbf_shapes.pdf`, `wilhelm_pbf_evidence.pdf` | PBF family illustration | Useful Methods/App figure after geometry selection; do not quote revoked β. |
| O3 | `toa_crossmatch_analysis_premium.pdf`, `systematics_check_matrix.pdf` | Association / systematics | V6 association is live; include only if prose needs them. |
| O4 | Fixed-band energy companion plot | LF-comparable \(E_{\rm iso}\) | `TODO(energies-fixed-band-variant)` — optional under V3; not required. |
| O5 | ΔDM CHIME–DSA agreement | Per-telescope DM_obs | V6 documented agreement; figure only if not already covered by cards/tables. |
| O6 | `fig:foreground_dm_pdfs` | Per-system PDFs for all foreground galaxies/clusters in `DM_int` | Scoped in `plan-dm-foreground-system-pdfs.md`. Needs per-halo MC (not just sightline-sum smear). Owner decisions open. |

---

## Dropped (do not restore under old name)

| Former | Why |
|--------|-----|
| `fig:alpha_pbf` | Retired with free-α framework (`tab:alpha` → `tab:beta`). |
| `fig:whitney_mult` | Outdated multiplicity-bias demo (owner 2026-07-10). Appendix `fig:jointmodel-pair-*` panels cover morphology audit; any future demo figure needs a re-validated product, not `whitney_multiplicity.pdf`. |

---

## Placeholder convention in tex

**Live draft boxes** (compile into the PDF as empty framed floats with labels):

```latex
\begin{figure*}
  \centering
  \fbox{\parbox{0.92\textwidth}{\centering\vspace{1.6cm}
  \textbf{[DRAFT PLACEHOLDER --- fig:NAME]}\\[0.6em]
  …role + gate + candidate file…\\
  \vspace{1.6cm}}}
  \caption{… \emph{Draft placeholder --- …}}
  \label{fig:NAME}
\end{figure*}
```

Do **not** `\includegraphics` a revoked campaign PDF into the live float until
the gate clears. When a gate clears: swap the `\fbox` for the trusted PDF,
drop the draft italic from the caption, update D2–D5 vocabulary, check this
list off.

**Note:** draft boxes are intentional development scaffolding; strip them
before circulation / submission (referee M9).
