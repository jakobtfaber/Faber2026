# Sign off the dispersion-budget priors and the host-DM headline

- Type: `wayfinder:grilling` (HITL)
- Status: resolved (2026-07-22)
- Assignee: Codex
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

Accept or revise the current dispersion-budget priors and headline:

- diffuse gas: Walker et al. IllustrisTNG-300 intergalactic marginal, with
  $f_{\rm IGM}=0.76^{+0.10}_{-0.11}$; below redshift 0.1 its median follows
  the Macquart cosmological integral and its log-scatter is fixed at the
  redshift-0.1 boundary;
- Galactic disk: 30% lognormal width;
- Galactic halo: 40 pc cm⁻³ median, log-width 0.35 (approximately a factor-two
  two-standard-deviation range);
- intervening gas: log-widths 0.40 (measured mass), 0.69 (assumed mass), and
  0.30 (cluster).

Current headline: only FRB 20220310F has P(host DM < 0) above one half
(0.540; median -10 pc cm⁻³), so it is consistent with zero rather than a
physical negative column. FRB 20230814B has probability 0.185 and median
108 pc cm⁻³. The central-value change from the former arithmetic budget is
primarily the lower fitted $f_{\rm IGM}$, while the forward model supplies
the asymmetric intervals and negative-tail probabilities.

## Low-redshift sensitivity evidence

Owner approved a benchmark against the real-Local-Universe `pyhesdm` diffuse
map and the continuous-TNG total-cosmic catalog of Konietzka et al. The two
redshift-below-0.1 sightlines retain positive host medians under every model;
the largest P(host DM < 0) is 0.059. The `pyhesdm` hybrid shifts their host
medians upward by 8.6 and 8.1 pc cm⁻³. Thus the headline classification is
insensitive to the continuation.

- [Research assessment](../../specs/research-low-z-igm-dm-alternatives.md)
- [Reproducible benchmark](../../../../scripts/dm_budget_low_z_sensitivity.py)
- [Exact benchmark results and input hashes](../../../../scripts/dm_budget_low_z_sensitivity.json)

## Resolution (owner-approved, 2026-07-22)

Accept the full prior set above without changing the fiducial forward model.
In particular, retain the component-consistent Walker/Connor continuation
below redshift 0.1. Describe it as a continuation constrained by its
redshift-0.1 boundary, not as direct Walker calibration at lower redshift.

Accept the corrected headline:

- only FRB 20220310F has P(host DM < 0) above one half: 0.540, with observer-
  frame median -10 pc cm⁻³; call it consistent with zero, not physically
  negative;
- FRB 20230814B has probability 0.185 and median 108 pc cm⁻³;
- attribute the main central-value change from the old arithmetic budget to
  the lower fitted $f_{\rm IGM}$; attribute the asymmetric intervals and
  negative-tail probabilities to the forward model, not a generic
  “right-skew correction.”

The low-redshift benchmark is an external sensitivity check, not a replacement
fiducial. All tested 16th-percentile host bounds remain positive, and the
largest tested P(host DM < 0) is 0.059. The benchmark therefore does not alter
the headline classification. Manuscript execution must preserve the
continuation caveat and may cite the benchmark as sensitivity evidence.
