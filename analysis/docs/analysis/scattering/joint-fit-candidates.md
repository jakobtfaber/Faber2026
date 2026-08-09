# Current joint-scattering fit candidates

No panel is displayed here yet. The manuscript owner sees a panel only after
its exact reproduction receipt passes the figure-review gate.

## Current candidate set

| Burst | Fit | Job | Model-grid SHA-256 | Status |
|---|---:|---:|---|---|
| Oran | C1D1 | 171 | `b550ddf48d8d922751735fda8fdff0aa5dfd1287d67c8d4ac19ee7b76382ffa6` | candidate; owner pending |
| JohnDoeII | C1D2 | 175 | `2095a1891531c14714d83334abee134c3ad54293c3385994296ff4c4c282dea6` | candidate; owner pending |
| Zach | C2D3 | 178 | `eda4e8f5d4d67f6dd96d307719bb292de9215e0fc0352ff7f5e94c7dc99eb408` | candidate; owner pending |

The external authority is
`$FABER2026_RESULTS_LIBRARY/scattering/jointmodel/latest/manifest.json`
(SHA-256
`dcacdba56ebeb4b123a362fb31eeff23ba220196fe0cc7774b8288a66fdbc52a`).
“Latest” means newest promoted diagnostic artifact, not scientific acceptance.

## Production chain

1. h17 jobs 171, 175, and 178 fitted joint CHIME/FRB and DSA-110 time-frequency
   data with component counts C1D1, C1D2, and C2D3 and gain prior scale 100.
2. The original fits recorded their configurations, result summaries, samples,
   inputs, and environment. They did not record a sampler seed, and executed
   fitting code included modified or untracked files. Exact fit regeneration is
   therefore impossible; these fits remain diagnostic.
3. A deterministic median-parameter reconstruction produced the preserved model
   grids. The renderer hash-checks each model grid and fit summary before use.
4. `scripts/plot_codetection_triptych.py` aligns both bands using the fitted
   dominant arrival times and measured inter-instrument offset, crops the
   observed on-pulse union with CHIME-width padding, and renders data, model,
   and noise-normalized residual columns on identical grids.
5. A fixed source timestamp and SVG hash salt make PDF, PNG, and SVG output
   byte-stable. Two fresh renders matched all nine preserved output hashes.

## Deprecated-panel lessons applied

- Reject components whose fitted arrival lies outside the fitted window.
- Do not compare evidence values across distinct posterior modes.
- Do not treat a very broad, low-fluence component as a resolved pulse.
- Keep component counts in the manifest synchronized with the actual artifact.
- Preserve enough time padding to avoid clipping delayed structure.
- Inspect residual morphology even when a reduced residual statistic is near
  one.

Zach C2D4 job 180 remains a deprecated comparison: its fourth DSA component is
a broad, low-fluence pedestal, and C2D3 job 178 has higher evidence on the
mode-continuous gain-prior arm. It must not reappear as the active candidate.

## Trust boundary

Panel-byte reproduction can pass while fit trust remains pending. Owner visual
review may accept or flag panel morphology, but it cannot repair the absent fit
seed or non-versioned executed code. No candidate is compiled into the
manuscript, and no fitted value is promoted by this page.
