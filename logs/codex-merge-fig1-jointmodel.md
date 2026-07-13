## 1. Layout approaches

### Approach A — 4×3 gallery with two-dimensional model contours

Retain the current twelve-cell, MJD-ordered gallery. Each cell shows the observed CHIME/FRB and DSA-110 waterfalls exactly as now, with the accepted joint two-dimensional model drawn as sparse contours over the data.

- **Page real estate:** Best. Preserves the existing full-width figure and readable time–frequency structure.
- **Model fidelity:** Conveys component locations, widths, scattering tails, and frequency-dependent morphology, though not detailed amplitude agreement.
- **Trust-reset risk:** Manageable if overlays are gated per burst. A missing overlay must explicitly mean “no accepted model,” not “zero model.”
- **Reproduction cost:** Lowest. Extend the existing gallery renderer with model arrays and contour drawing; reuse the joint-fit artifact loader.
- **Limitation:** Residual defects are less obvious than in a triptych, so residuals remain an appendix concern.

### Approach B — paired data and model columns for every burst

Replace each current cell with a compact `data | model` pair, retaining the shared frequency axis and omitting residuals. Use a 3×4 or 4×3 outer grid.

- **Page real estate:** Poor. Twenty-four waterfalls plus marginals either require a landscape/two-page figure or substantially narrower panels.
- **Model fidelity:** Stronger than contours because data and model remain visually independent.
- **Trust-reset risk:** Moderate. The model looks authoritative even when only diagnostic; missing or rejected models create conspicuous holes.
- **Reproduction cost:** Moderate. Much of `plot_codetection` can be reused, but its three-column layout and repeated marginals need simplification.
- **Limitation:** At ordinary two-column print width, time structure is likely to be crushed—the owner’s primary visual constraint.

### Approach C — data gallery plus one accepted exemplar triptych

Keep the twelve-burst data gallery as panel (a), then place an accepted `data | model | residual` exemplar—nominally Whitney only after its multiplicity problem is repaired—as panel (b), either below it or on the facing page under one figure number.

- **Page real estate:** Moderate to high; likely a two-page continued figure.
- **Model fidelity:** Excellent for the exemplar, absent for the other eleven bursts.
- **Trust-reset risk:** Lowest, because only one fully accepted fit is promoted.
- **Reproduction cost:** Low. It composes two existing products rather than creating a new visualization.
- **Limitation:** Does not meet the stronger interpretation that the first figure should show the models for the sample.

## 2. Recommended approach

Use **Approach A: the existing 4×3 gallery with sparse two-dimensional model contours**, subject to a strict artifact-eligibility gate.

This is the only approach that introduces sample-wide model information without sacrificing the observed structural resolution. It is also reversible: removing the contours recovers the current trust-reset-safe figure without changing the data preparation or layout.

Model eligibility should require both:

1. the fit has passed the manuscript’s current V1/re-validation contract; and
2. its morphology audit has no unresolved component-count or coherent-residual flag.

Under the current fit-quality note:

- **Chromatica:** data only; no jointmodel-pair artifact exists and its prior fit was gate-FAIL.
- **Whitney, Hamilton, Wilhelm:** data only until their unresolved morphology flags are repaired and reviewed.
- **Zach and JohnDoeII:** their old flags are retired, but only the promoted `_C2D4_cwin` and `_C2D2` products may be considered.
- **All other bursts:** overlay only if the live re-validation roster explicitly marks the exact artifact accepted. Historical campaign PASS/MARGINAL labels alone are insufficient under `CONTEXT.md`.

If that gate currently leaves no formally revalidated fits, the design remains valid but the manuscript change is blocked at the model-artifact gate; the data-only figure should remain in place until at least the intended overlays are cleared.

## 3. Per-panel recipe

Each burst cell should contain:

- **Observed waterfall:** the current combined CHIME/FRB and DSA-110 dynamic spectrum on one frequency axis, with the 0.80–1.31 GHz gap hatched.
- **Model representation:** three thin contours at 30%, 60%, and 90% of the model’s per-band peak. Normalize contour levels separately by telescope because the two bandpass-corrected products do not share an absolute plotted amplitude scale.
- **Profile strip:** retain the observed DSA-110 black and CHIME/FRB blue profiles. Add the model profiles as thin dashed lines in the corresponding band colors.
- **Spectrum marginal:** retain observed spectra; do not add model spectra because the narrow marginal would become illegible.
- **Residuals:** omit from Figure 1. Keep full whitened residual panels in the appendix.
- **Axes:** shared time axis in milliseconds and frequency axis in GHz; retain the drawn-to-scale band separation and hatching.
- **Data color scale:** preserve the current per-band robust 1st–99.5th-percentile normalization. Contours, rather than a second image layer, prevent the model from changing the data contrast.
- **Annotations:** TNS name plus a small `model contours` key once for the whole figure. For data-only cells, use a restrained `model not accepted` tag.
- **Do not annotate:** fitted \(\tau\), \(\alpha\), \(\beta\), rail class, reduced \(\chi^2\), or component count. Those quantities add clutter and, more importantly, exceed what the morphology figure is entitled to claim during the fit-trust reset.

The caption should call the overlays “accepted joint-model morphology contours,” not “best fits,” unless the corresponding fit lane has been fully restored.

## 4. Time-window rule

Determine the window from observed data, independently of the fitted model.

For each telescope \(b\in\{C,D\}\), let its data-derived structural interval relative to its own profile peak be

\[
S_b=[s_{b,-},s_{b,+}],
\]

using the current smoothed, noise-thresholded `onpulse_span` rule, including above-threshold runs separated by at most 2 ms. Define the total CHIME structural width

\[
W_C=s_{C,+}-s_{C,-}.
\]

Then form the observed union

\[
S=[S_-,S_+]
=\left[
\min(s_{C,-},s_{D,-}),
\max(s_{C,+},s_{D,+})
\right],
\]

and use the display window

\[
T_{\rm display}
=
\left[
S_- - P,\;
S_+ + P
\right],
\qquad
P=\max(W_C,1.5\,{\rm ms}).
\]

Thus each side receives off-pulse context approximately equal to the full CHIME burst width, with a 1.5 ms floor for extremely narrow bursts.

Edge handling:

- **Scattering tails:** the structural interval must include contiguous statistically significant tail emission. Do not let the fitted model alone enlarge the window. If the observed tail reaches the product boundary, mark the panel for manual review rather than silently treating the crop as complete.
- **Multi-component bursts:** merge significant runs separated by at most 2 ms. More widely separated significant components still enter through the minimum and maximum bounds of the full detected-component set; do not select only the run containing the highest peak.
- **DSA-only structure outside the CHIME span:** the union expands to contain it, after which a full \(W_C\) of padding is added beyond that DSA structure. This is essential for Zach’s trailing DSA complex.
- **Weak CHIME detection:** if \(W_C\) is unstable or below two display samples, use the vetted CHIME component interval from a data-only manual mask—not the model—or fall back to \(P=1.5\) ms and flag the panel for visual review.
- **Product limits:** clip only at the available \(\sim81.9\) ms product boundary. Retire the unconditional \(\pm25\) ms clamp when it would violate the padding rule; retain per-burst overrides solely as reviewed exceptions.
- **Time alignment:** keep the caption’s current statement that each band is referenced to its own profile peak unless the joint-fit artifacts provide a validated shared physical time origin. Apply each model to the same per-band shift as its corresponding data.

## 5. Resolution rule

“Full structural resolution” should mean **no averaging coarser than the physical structure or the printed raster can display**, not necessarily dumping every native sample into the PDF.

Use:

- **DSA-110 time:** native 32.768 \(\mu\)s; no time averaging.
- **CHIME/FRB time:** average 13 native samples to 33.28 \(\mu\)s, matching DSA-110 to within 2%.
- **DSA-110 frequency:** average 12 native channels to 512 displayed channels.
- **CHIME/FRB frequency:** average 2 native channels to 512 displayed channels.
- **Models:** apply exactly the same block averaging and cropping as their corresponding data before calculating contours and marginal profiles.
- **Residual appendix:** retain the resolution of the existing jointmodel-pair products unless a flagged feature is demonstrably lost; central-figure display choices should not silently redefine diagnostic residual products.

At a roughly 1.5–1.7 inch cell width, 600 dpi provides about 900–1000 horizontal pixels, so the \(\sim33\,\mu\)s time grid remains useful for the expected few-to-tens-of-milliseconds windows. Rasterize waterfall image layers at 600 dpi inside the PDF; keep axes, text, hatching, profiles, and model contours as vectors. Do not embed native 6144-channel DSA arrays merely to inflate PDF size without visible information.

## 6. Manuscript placement

Replace the current `fig:codetection-gallery` artwork in the same early Observations location and retain the label. This minimizes cross-reference churn and preserves Figure 1 as the sample overview.

Keep:

- `fig:jointmodel-pair-whitney` in Results only after Whitney’s unresolved morphology flag is repaired; until then, Results should not describe it as validated.
- All accepted `data | model | residual` triptychs in Appendix `app:jointmodel-pairs`.
- Flagged triptychs out of the manuscript appendix until repaired; they may remain diagnostic artifacts.
- Chromatica as data-only in Figure 1 and absent from the jointmodel-pair appendix until an accepted model exists.

Caption sketch:

> Dedispersed total-intensity dynamic spectra of the twelve CHIME/FRB–DSA-110 co-detections, ordered by epoch. Each cell places both observing bands on a common frequency scale; hatching marks the unobserved interval. Solid profiles and waterfall colors show the observations. For bursts whose exact joint-fit artifacts have passed the fit re-validation and morphology audit, dashed profiles and contours at 30%, 60%, and 90% of the per-band model peak show the corresponding two-dimensional model. Cells marked “model not accepted” intentionally contain observations only. Times are relative to each band’s profile peak, and each spectrum is displayed at its instrument-optimized dispersion measure. Data and models are block-averaged to approximately \(33\,\mu\mathrm{s}\) and 512 channels per band for display. Full data/model/residual audits appear in Appendix~\ref{app:jointmodel-pairs}.

In Observations, replace “No model curves are overlaid” with one sentence explaining the eligibility rule. In Results, change the Whitney paragraph to avoid claiming validation until its replacement artifact clears the documented flag.

## 7. Implementation sketch

Use a **top-level hybrid renderer based on `scripts/plot_codetection_gallery.py`**, not twelve calls to `plot_codetection`.

- Preserve the gallery’s roster discovery, MJD ordering, observed-data loading, block averaging, adaptive windowing, shared frequency geometry, hatching, styles, and output triplet.
- Reuse `pipeline.flits.batch.codetection_plots.BandSpectrum` semantics and its residual/noise conventions, but do not reuse the complete `plot_codetection` figure builder; its three-column grids are the wrong layout for Figure 1.
- Extract or reuse only small plotting behavior already proven there: band-gap geometry, validity masks, time regridding when required, and model/profile array handling.
- Add a manifest keyed by burst nickname that records:
  - exact accepted fit JSON or staged artifact;
  - exact model/data array source;
  - model suffix, where applicable;
  - eligibility status and provenance;
  - optional reviewed time-window override.
- Load model artifacts from the same staged sources used to generate `figures/jointmodel_pair/*_jointmodel_pair.*`, rather than reconstructing models from rounded manuscript parameters. The committed fit provenance under `figures/jointmodel_pair/fit_artifacts/` and the beta-campaign fit JSONs should identify the exact source; any required posterior or prepared-array dependency outside the repository must be documented in `REPRODUCE.md`.
- Apply identical frequency ordering, block averaging, validity mask, time shift, and crop to data and model.
- Draw model contours directly in the gallery axes. Do not composite existing PNG/PDF triptychs.
- Treat missing, rejected, unresolved, or provenance-incomplete model artifacts as data-only cells. Never fall back to an older suffix automatically.
- Map `whitney_fine` to the displayed Whitney/TNS cell explicitly; do not rely on filename normalization.
- Chromatica remains a normal twelfth data cell with `model not accepted`; do not synthesize a placeholder model or silently reduce the sample to eleven.

## 8. Risks / open decisions

- **Trust gate:** Does the owner want Figure 1 to show only formally V1-restored models, or also provisional morphology-audit products? The recommendation is formally restored models only.
- **Partial overlays:** Is a mixed figure with data-only Chromatica, Whitney, Hamilton, and Wilhelm acceptable, or should publication wait until all twelve have accepted models?
- **Whitney cross-reference:** Its current Results language conflicts with the unresolved fit-quality flag; decide whether to remove the exemplar temporarily or prioritize its refit.
- **Model encoding:** Confirm sparse contours are sufficiently explicit for “include the burst models”; the alternative `data | model` layout materially reduces observed structural resolution.
- **Time convention:** A per-band peak origin is acceptable for morphology but cannot demonstrate cross-band arrival alignment. A shared time axis should be adopted only if validated absolute/reference-time metadata are available.