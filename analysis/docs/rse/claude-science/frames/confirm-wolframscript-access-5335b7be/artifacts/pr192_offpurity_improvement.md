# PR-192 estimator improvement — enforce the off-window purity gate

## Root cause (isolated 2026-07-17)
The chromatica collapse (alpha +1.87 manual -> -0.05 auto) was traced by
independent 2x2 isolation (`isolate2.py`) to the **off-pulse window**, NOT the
burst-window width:
- chromatica burst [184,198] + off **[20,175]** -> alpha=+1.87
- chromatica burst [184,198] + off **[269,452]** -> alpha=-0.05   (only off changed)

`window_optimize.select_windows` chose the off-window as the **single largest**
free run. For chromatica/zach/whitney the largest run is the *post-burst* region
carrying the scattering tail (standardized off_snr 6-11). That contaminated
reference corrupts de-scalloping + RFI statistics, which feeds the ACF. The code
already COMPUTED off_snr and its comment said "flag off_snr > ~3 as contaminated"
— but nothing acted on it.

## Fix (`window_optimize_offpurity_fix.py`, +29/-9 lines)
Enforce the gate: score every candidate off-run at the burst scale on the
internal standardized profile; take the **largest run whose off_snr <= OFF_SNR_MAX
(3.0)**; fall back to the least-contaminated run only if none pass. Plus adopt
`burst_core` (matched-significance envelope) as the ACF window instead of the
tail-expanded `burst_lims` (the PR's own comment already names burst_core the ACF
window; the driver was passing burst_lims).

## Targeted, not blunt
The gate changes the off pick for EXACTLY the three tail-contaminated bursts and
leaves the others untouched:
| burst | size-max off | gate-picked off | changed |
|---|---|---|---|
| chromatica | [269,452] | [0,131] | YES |
| zach | [0,163] | [334,486] | YES |
| whitney | [0,966] | [1110,1930] | YES |
| casey | [0,834] | [0,834] | no |
| freya | [0,227] | [0,227] | no |

## Result (off-fix + burst_core ACF window)
| burst | alpha (fixed auto) | prior manual | verdict |
|---|---|---|---|
| chromatica | **+1.66 +- 0.35** (4/4 res) | +1.87 (cf. +2.03) | RECOVERED |
| zach | **+2.05 +- 0.52** (3 res) | -1.42 (unphysical) | IMPROVED, now physical |
| whitney | n/a (2 res, m>1.2) | n/a | unchanged (never clean) |

Full 12-burst run (`all12_fixed.json`): chromatica and zach yield physical,
positive alpha with resolved ladders; freya/hamilton provisional (n=2, flagged P);
the rest remain unresolved or single-subband (casey/phineas/mahi/wilhelm/oran/
johndoeII/isha) — consistent with the sample never having clean multi-subband
scintillation outside chromatica/zach.

## Still open (honest limits)
1. `first_fit_lag`/grid: a "Frequency grid non-uniform" warning fires for several
   bursts (Delta nu_d overstated ~1.32x) — enable analysis.grid_regularization
   (issue #120) before quoting absolute gamma.
2. Some subbands show gamma jumping to ~20 (fit bound) or >1 m in one band while
   neighbors are clean (whitney 585 MHz, phineas). A per-subband physicality
   reject (already have M_PHYS=1.2 for alpha) should also gate the ladder plot.
3. Injection harness (the evidence PR-192 references but never committed) should be
   committed alongside this fix so the estimator is reproducibly validated.
