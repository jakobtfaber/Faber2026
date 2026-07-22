# Merged Fig. 1 design proposal — co-detection gallery × joint 2-D model

## 1. Layout approaches

**A — Model-audit overlay gallery (extend current Fig. 1 in place).** Keep the 4×3 data gallery geometry exactly; add per-band model curves from the promoted jointmodel NPZs: band-summed model profile in the profile strip and time-averaged model spectrum in the right marginal, dashed in the band color; optionally one 2-D model contour per band (50% of band model peak) on the waterfall, QA-gated. Chromatica stays data-only.
- Real estate: zero change. Model fidelity: 1-D marginals (+ optional contour); full 2-D stays in whitney exemplar + appendix. Trust-reset risk: lowest — reuses the morphology-audit framing already shipped (results.tex:199–205, appendix captions). Reproduction: small — extend `scripts/plot_codetection_gallery.py`, no pipeline pin bump.

**B — Data|model paired cells.** Each cell: profile strip spanning two waterfall mini-columns (data | model, shared frequency axis and color scale), spectrum marginal with both curves. Needs a full-page `figure*[p]` or rotated figure since cells double in width.
- Real estate: full page. Fidelity: highest (frequency-dependent broadening visible in 2-D). Trust-reset risk: higher — revoked 2-D products become the headline visual. Reproduction: moderate (hybrid of gallery windowing + `codetection_plots` drawing). Conflicts with the full-structural-resolution constraint: half-width cells ≈ 0.8 in ≈ 240 px @300 dpi against up to ~1000 display columns.

**C — Two-figure spread.** Fig. 1 unchanged (data-only); Fig. 2 immediately after mirrors the 4×3 geometry with model waterfalls; chromatica cell hatched "no accepted joint fit".
- Real estate: +1 page. Fidelity: full 2-D at full resolution. Trust-reset risk: most visible (a dedicated model figure) but cleanly severable if V1 changes fits. Fails the owner's literal ask — models are not *in* the first figure.

## 2. Recommended approach

**A**, with the 2-D element supplied by (i) the QA-gated single model contour and (ii) the whitney triptych retained in results as the early full-2-D exemplar. A is the only approach satisfying both hard constraints at once — models in the central figure AND full structural resolution — while confining trust-reset exposure to the already-precedented "morphology audit, no parameters quoted" framing. Fully reversible: if V1 re-validation changes a fit, only the overlay curves regenerate; data layer and geometry untouched. B is the natural post-V1 upgrade path.

## 3. Per-panel recipe (approach A)

Cell geometry unchanged (profile strip / stacked CHIME+gap+DSA waterfall / spectrum marginal).
- **Waterfall:** data only; magma, 1–99.5 pct clip, gray masked channels, hatched 0.80–1.31 GHz gap. Optional: one contour per band at 50% of the band's model peak, ~0.4 pt light cyan — adopt only after a 12-panel print-scale QA sheet.
- **Profile strip:** data profiles unit-peak (DSA black, CHIME `#4477aa`); model band-summed profile per band, same color, dashed, lw ≈ 0.7, α ≈ 0.8, normalized by the *same per-band data peak* so amplitude mismatch stays visible (mirrors the `per_band_marginals` dashed-model convention in `codetection_plots`).
- **Spectrum marginal:** data on-pulse spectra as now; model time-averaged spectrum, dashed same-color, same normalization.
- **Annotation:** no τ, α, β, χ², or component-count numerals (all Wave-1 revoked). Only "†" after the TNS title on flagged fits (whitney, hamilton, wilhelm per `jointmodel-pair-fit-quality-flags.md`) and "(no accepted joint fit)" on chromatica.
- **Alignment:** per band, place the model in that band's peak-relative frame by matching the NPZ data-profile peak to the gallery data-profile peak (no cross-band TOA alignment needed); model curves span only the fit crop window and end where it ends.

## 4. Time-window rule (CHIME-width padding)

Per band b ∈ {C, D} on the display grid: `(lo_b, hi_b, pk_b) = onpulse_span(profile_b)` (existing threshold max(8% peak, off-pulse median+4σ), 1 ms boxcar, 2 ms gap-merge). Peak-relative spans `s_b±`; union `U− = min_b s_b−`, `U+ = max_b s_b+`.

- CHIME width `W_C = (hi_C − lo_C)·dt_C` (includes the scattering tail down to threshold).
- Pad `P = clip(W_C, 1.5 ms, 15 ms)`.
- Window `[U− − P, U+ + P]`, clamped to the product extent (≈ ±40 ms); raise the hard clamp 25 → 35 ms so the rule, not the clamp, governs.

Edge cases: scattering tails above threshold sit inside U, sub-threshold tail bleeds into the pad — intended, since P scales with the tail; multi-component complexes are merged into one span (gap ≤ 2 ms) so W_C covers the complex, wider separations extend U directly (zach's trailing DSA cluster); DSA-only structure outside the CHIME span enters via the union, padding stays W_C beyond it; low-S/N CHIME (oran) — if smoothed CHIME peak S/N < 5, use `P = clip(max(W_C, W_D), 1.5, 15)`; keep `WINDOW_MS_OVERRIDES` as the QA escape hatch. Versus the current `pad = min(max(1.5, 0.35·union), 8)`: systematically wider for scattered bursts — exactly the owner's rule.

## 5. Resolution rule

- **Time:** DSA native 32.768 µs; CHIME ×13 → 33.28 µs to match. This is "full structural resolution" for display — the narrowest resolved sub-bursts (~100–300 µs) get ≥3–10 columns. Never return to the 163.84 µs grid.
- **Frequency:** 512 ch/band (CHIME f×2, DSA f×12), unchanged.
- **Print/PDF:** panels ≈ 1.55 in → ~465 px @300 dpi, faithful to ~15 ms windows at 33 µs; the new padding rule can reach 30–70 ms, so raise waterfall rasterization to 600 dpi (text stays vector; PDF remains well under 10 MB).
- Model overlays are vector curves — resolution-free; interpolate the NPZ model onto the display grid only if the contour option is adopted.

## 6. Manuscript placement

- **Fig. 1 slot** (`sec:data`, label `fig:codetection-gallery` kept): replaced in place by the overlay version; delete "No model curves are overlaid." (observations.tex:54) and update observations.tex:31–36 to point at the model audit.
- **Results:** `fig:jointmodel-pair-whitney` stays in `sec:results-alpha` as the early full-2-D data/model/residual demonstration.
- **Appendix `app:jointmodel-pairs`:** unchanged — residuals appear only there.
- **Caption sketch (delta):** "…masked channels are gray. Dashed curves show the band-summed profile and time-averaged spectrum of the joint two-band model (Section~\ref{sec:jointfit}) for the eleven bursts with an accepted joint fit; as in Appendix~\ref{app:jointmodel-pairs}, these are morphology-audit renderings that validate the adopted component multiplicity, and no fitted scattering or turbulence parameter is quoted from them. Panels marked † have a known unmodeled sub-component (Section~\ref{sec:multicomp}); FRB 20240203A has no accepted joint fit and is shown without model curves."
- **Cross-refs:** caption → `sec:jointfit`, `sec:multicomp`, `app:jointmodel-pairs`; `sec:multicomp` gains a back-pointer to the † panels.

## 7. Implementation sketch

- Extend `scripts/plot_codetection_gallery.py` (single producer, no pipeline pin bump) with `--models/--no-models` plus a checked-in manifest `scripts/jointmodel_manifest.yaml` (nick → NPZ path + suffix + flag). Required because the 11 accepted NPZs are split: 5 promoted in `figures/jointmodel_pair/fit_artifacts/` (whitney chime2resolved, zach C2D4_cwin, johndoeII C2D2, hamilton, casey), 6 in untracked scratch `~/Developer/scratch/flits-local-runs/data/joint` (per `pipeline/analysis/scattering-refit-2026-06/plot_jointmodel_pair.py`). Promote the six into `fit_artifacts/` (or `~/Data`) first — REPRODUCE.md-grade reproducibility cannot depend on scratch.
- Reuse gallery helpers (`block_mean`, `onpulse_span`, `load_band`) unchanged; model loading mirrors `plot_jointmodel_pair._band`; band-sum + `np.interp` onto the display time base after per-band peak alignment. Do not import `codetection_plots` for the overlay (~40 lines suffice).
- Window rule: replace the pad expression in `render()`, add the CHIME-S/N fallback, bump the clamp.
- Chromatica: manifest `model: null` → skip overlays, annotate title.
- Tests: extend `tests/test_codetection_gallery.py` — manifest completeness (11 entries + explicit chromatica null), alignment unit test, padding-formula tests.
- Approach-B upgrade path post-V1: `codetection_plots.plot_codetection(columns=("data","model"))` per burst inside the gallery grid.

## 8. Risks / open decisions (owner)

1. **Trust-reset exposure:** Fig. 1 will display Wave-1-revoked fit products (as morphology audits). Confirm this framing is acceptable pre-V1, or hold overlays behind V1 and land the window/resolution changes now — the halves are severable.
2. **Flagged trio (whitney/hamilton/wilhelm):** dagger-flagged overlays (uniform, honest) vs omitting their curves vs blocking Fig. 1 on re-fits. Recommendation: dagger now, re-render when re-fits land.
3. **Chromatica:** accept 11 models on 12 bursts with an explicit "no accepted joint fit" tag, or sequence a chromatica joint-fit lane first (delays the figure).
4. **Padding cap:** uncapped P = W_C leaves heavily scattered CHIME panels (e.g. phineas) mostly empty context; the proposal caps P at 15 ms — confirm "roughly equal" tolerates the cap.
5. **Contour + artifact promotion:** adopt the 2-D contour only if the print-scale QA sheet reads clean; promoting six scratch NPZs (~3 MB) into the repo is required — confirm tracking them is acceptable.

Proposal also saved to the plan file. Note: `ExitPlanMode` is not available in this session's toolset, so plan mode remains active — design pass complete, nothing modified.