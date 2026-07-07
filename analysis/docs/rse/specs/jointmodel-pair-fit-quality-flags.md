# Jointmodel Pair Fit-Quality Flags

During visual review of the data/model/residual triptychs, four current
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

`johndoeII` is also flagged from visual review and fit metadata. Its current
artifact is `_C2D1`, so the DSA side is represented by only one model
component even though the DSA dynamic spectrum shows multi-component burst
structure. The simple band-integrated peak check does not split the DSA
structure cleanly for this row, so this flag is intentionally metadata/visual
rather than an unmatched-peak claim.

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
- `johndoeII`: the current `_C2D1` artifact uses only one DSA component; the
  DSA burst should be re-fit with higher DSA multiplicity.

## Required follow-up

These four bursts need multiplicity re-fitting before their current
data/model/residual triptychs are treated as accepted model figures. Until
then, keep the generated figures as diagnostics only.
