# Jointmodel Pair Fit-Quality Flags

During visual review of the data/model/residual triptychs, current
beta-campaign fit artifacts were flagged as missing visible sub-burst
structure.

## Red-capable check

The diagnostic check compares band-integrated data peaks against model peaks
in the rendered/cropped frame. A data peak is "unmatched" when no model peak
lies within 0.25 ms.

Observed output on 2026-07-07:

```text
whitney_fine DSA-110
data peaks  [0.001, 0.329]
model peaks [-0.065]
unmatched   [0.329]

zach DSA-110
data peaks  [0.343, 2.899]
model peaks [0.408]
unmatched   [2.899]

hamilton CHIME/FRB
data peaks  [-0.732, -0.425]
model peaks [-0.425]
unmatched   [-0.732]
```

`johndoeII` was also flagged from visual review and fit metadata in the first
pass: the beta-campaign artifact was `_C2D1`, so the DSA side was represented
by only one model component even though the DSA dynamic spectrum shows
multi-component burst structure. That flag is now retired. The promoted
beta-native product is `_C2D2`; scratch pilots on 2026-07-07 gave nearly
identical PPC residuals for C2D2 and C2D3 (`chi2_C/D ~= 1.095/1.234` vs
`1.094/1.231`), so the simpler C2D2 model was adopted. The simple
band-integrated peak check did not split the DSA structure cleanly for this
row, so the original flag was intentionally metadata/visual rather than an
unmatched-peak claim.

## Interpretation

- `whitney_fine`: the current beta-native `_C2D2` artifact has two DSA
  components in metadata, but one is effectively degenerate for the visible
  sub-burst structure (`t0_D1 ~= 6.87 ms`, `zeta_D1 ~= 48.2 ms`; `t0_D2 ~=
  28.56 ms`, `zeta_D2 ~= 0.033 ms`). The rendered model therefore does not
  account for both visible DSA sub-bursts.
- `zach`: only a `_C1D1` beta-native artifact is present locally; it captures
  the leading DSA structure but misses the trailing DSA components.
- `hamilton`: the current shared-zeta fit behaves as a one-component CHIME
  model and misses the leading CHIME component.
- `wilhelm`: the current shared-zeta fit misses leading DSA structure and has a
  coherent bright-pulse residual. This should be described as residual
  pulse-profile structure within the beta≈4 exponential/EMG-preferred branch,
  not as evidence that the EMG/exponential branch is disfavored.

Retired flag:

- `johndoeII`: fixed by the promoted beta-native `_C2D2` product
  (`beta=3.936`, `alpha=4.07` as a railed-hi limit, `tau_1GHz=2.219 ms`,
  `chi2_C/D=1.09/1.23`). The old `_C2D1` product is superseded.

## Required follow-up

The remaining flagged bursts need multiplicity or residual-structure re-fitting
before their current data/model/residual triptychs are treated as accepted model
figures. Until then, keep those generated figures as diagnostics only.
