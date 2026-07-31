# Remaining science questions — evidence probes, 2026-07-31

**Status:** RESEARCH ONLY. This note records two read-only probes. It does not
admit a result, promote trust or provenance, or change the manuscript, registry,
appendix, receipt state, or parent pin.

**Snapshot:** clean analysis worktree based on `711c47c1f89c0ebc5cdcae98cb403708a312ae3c`.
Required knowledge-base searches ran first with `FABER2026_ROOT` set to the
canonical parent checkout and returned no results; exhaustive source and Git
history reads followed.

## 1. FRB 20230307A cluster and intervening column

### Observed and cited facts

- Ticket 06 records the 2026-07-22 probabilistic-crossing result as intervening
  dispersion-measure percentiles `203, 255, 322 pc cm^-3`:
  `docs/rse/wayfinder/tickets/06-adjudicate-phineas-halo-mass-prescriptions.md`
  and commit `be2131b76771d6291dfd18784eaa1c3f08636272`.
- The current `scripts/dm_budget_uncertainty.csv` records `217, 281, 354`
  pc cm^-3. Thus the registry shorthand `281 (+73/-64)` is the rounded
  `p50=281`, `p84-p50=73`, `p50-p16=64` from that row; it is not a different
  interval convention.
- Git history gives a two-step reconciliation. Between `be2131b` and the parent
  of `c8ec78c`, the producer added an equal-weight modified-NFW/beta-profile
  mixture and revised the beta calculation; with the old cluster point, the
  full row moved from `203,255,322` to `202,260,329`. Commit
  `c8ec78ceeeb37505b5343aeb0ad0a51671658640` then replaced the fixed
  modified-NFW cluster point in `scripts/dm_budget_intervening_systems.csv`
  from `183.674227906529` to `224.719617368599 pc cm^-3`; its clean-room
  validator replaced the approximation `M200=1.3 M500` with an NFW
  `M500c`-to-`M200c` conversion at declared concentration `c200=4`. The full
  row moved from `202,260,329` to `217,281,354`. Commit
  `9890aa8cc299fc2696348327a1c2efe14c80fdbe` restored those producing
  artifacts without changing the resulting row.
- The earlier ticket result and the current registry result therefore belong
  to different producer states. `281 (+73/-64)` incorporates both the later
  profile-mixture implementation and the later mass-conversion change.
- Historical `9890aa8` receipt identities for the `217,281,354` row are:
  output `scripts/dm_budget_uncertainty.csv` SHA-256
  `b111b4f82daaf016e80722236c9e5551398c6f31a7bfca3cdab6da24944554a5`;
  producer `scripts/dm_budget_uncertainty.py` SHA-256
  `8fdf8ac94e42eb8164ffc827cc683bd4961e7932ec12e55edc960f2dc743ff73`;
  input `scripts/dm_budget_intervening_systems.csv` SHA-256
  `1b52874a5f1262ce5542b157ee1dc366f5e90186e898096ff70095d95fea6bba`;
  input `scripts/phineas_halo_crossing_probability.json` SHA-256
  `3362019a776cf799bcb53f6b7bfda2363217f130323a57351fd9ff9f029c6951`;
  and input `scripts/phineas_halo_crossing_inputs.csv` SHA-256
  `2657115881a91261b547c1c1233508e8c03b2758d2aa365b30f89f944b507891`.
- At snapshot `711c47c`, the retained historical CSV bytes are unchanged, but
  the live producer is a different surface: SHA-256 `43823c73...`, output
  `foregrounds/results/propagation/host_dm_diagnostic.csv`, no profile
  averaging, and current intervening input SHA-256 `0dd74d3c...` with cluster
  point `216.915467424`. It does not produce or validate the historical
  `217,281,354` row.
- The second confirmed cluster is `WHL J115048.0+714428`, not the Wen--Han
  near-miss `J115128.2+713637`. The frozen registry gives `z=0.1893` and
  `b=614.3 kpc` but no adopted `M500` or `R500`; it is absent from Wen & Han
  2024. Exact local sources are rows 53 of
  `foregrounds/census/data/intervening_census_registry.csv` and
  `foregrounds/census/data/candidate_redshift_provenance.csv`, plus
  `docs/rse/specs/research-v4-census-gap-extension.md`. The frozen WHL12 source
  payload is keyed in
  `foregrounds/census/data/candidate_redshift_source_payloads_2026-07-22.json`.
  Existing authority treats it as confirmed but budget-ineligible because its
  sourced geometry is missing. No primary-source evidence read here adjudicates
  whether it is a distinct physical halo or a catalog-level duplicate/fragment
  of the budgeted Wen--Han system; that ambiguity is preserved.

### What this does not establish

This history explains the numerical transition; it does not independently
validate the corrected `224.7196` cluster point, the equal profile weighting,
or the admitted scientific meaning of `281 (+73/-64)`. It also does not assign
a column to WHL J115048.0+714428. The exact runtime environment and a complete
producer invocation/output receipt for the historical `9890aa8` row were not
found. The current diagnostic is a separate, fail-closed result surface.

### Scientific falsifiers

- The current interval is falsified if a clean reproduction from the pinned
  inputs and declared model yields percentiles other than `217,281,354` beyond
  the producer's rounding rule.
- The one-cluster budget is falsified if primary catalog/source adjudication
  establishes WHL J115048.0+714428 as a distinct cluster with sourced
  `M500/R500`, `b/R500 <= 1`, and a positive column under the declared cluster
  model.
- Conversely, the claimed second-cluster systematic is falsified if primary
  source and spatial/redshift adjudication establishes it as the same physical
  system already represented by `J115120.4+714435, 1254337`.

### Admission and provenance blockers

1. Immutable environment identity and exact invocation for historical producer
   SHA-256 `8fdf8ac9...` at the `c8ec78c`/`9890aa8` state.
2. A receipt binding that environment; producer commit and bytes; intervening
   CSV, probabilistic-halo JSON, and probabilistic-halo input CSV; and output
   CSV bytes, with each path and role explicit.
3. Independent scientific review of the corrected cluster point and the
   equal-weight profile mixture.
4. Primary-source identity/geometry adjudication for WHL J115048.0+714428,
   including sourced `M500/R500` or an explicit duplicate decision.

### Executable next checks

All prerequisites for this history comparison exist locally:

```bash
git diff be2131b76771d6291dfd18784eaa1c3f08636272..c8ec78ceeeb37505b5343aeb0ad0a51671658640 \
  -- scripts/dm_budget_intervening_systems.csv \
     scripts/dm_budget_uncertainty.csv scripts/dm_budget_uncertainty.py
git show c8ec78ceeeb37505b5343aeb0ad0a51671658640:scripts/dm_budget_uncertainty.csv \
  | rg 'FRB 20230307A'
```

No producer rerun is prescribed: the exact environment receipt is absent.

**Verdict:** numerical discrepancy reconciled as version drift; cluster science
and admission remain unresolved.

## 2. Host dispersion measure and the TNG calibration

### Observed and cited facts

- The canonical first-party reproduction package named by Connor et al. (2025)
  is <https://github.com/liamconnor/frb_baryon_connor2024>. The paper's code
  availability statement identifies that repository. Its inspected immutable
  revision was `c8ca7cccc22828270291b039963a316b5e35d04f`.
- The source artifact exists at `src/tng_params_new.npy`. It first entered the
  repository in commit `48b5637de79a256fa4aee6c884b00db86fd25f83`
  (2024-10-15); its Git blob is
  `19942072b759fc836fef62d0d265a7f3260f56c9` and SHA-256 is
  `e4e1aa68ae4367bb698df5ca1cc93d9eaaeba23f73bef2435f4aee0ef5674625`.
  The blob is unchanged at the inspected revision.
- First-party `src/frbdm_mcmc_jit.py` defines the six columns as
  `[A, mu_dmx, mu_dmigm, sigma_dmx, sigma_dmigm, rho]` and loads this file.
  The artifact is a `(12,6)` little-endian NumPy `float64` array on the redshift
  grid `0.1,0.2,0.3,0.4,0.5,0.7,1.0,1.5,2,3,4,5`.
- A direct value comparison against `TNG_MU_IGM` and `TNG_SIG_IGM` in
  `scripts/dm_budget_uncertainty.py` found maximum absolute differences
  `4.922634744275456e-09` and `4.839823819491329e-09`, respectively. Both
  columns agree at absolute tolerance `1e-8`; they are not byte-identical
  because the local arrays were rounded to eight decimal places. All 12 local
  redshifts equal the first-party ordering exactly. First-party
  `src/frbdm_mcmc.py` sets `figmTNG=0.797`; local `FIGM_TNG=0.797` matches.
  The comparison ran with Python `3.13.9`, NumPy `2.3.5`, on
  `macOS-27.0-arm64`; this is the comparison environment, not the array's
  producing environment.
- The first-party repository supplies `requirements.txt` at the inspected
  revision, SHA-256
  `8263d7e2ea51c9bc9327ee6f2a8747f42dce2ca28bf556883309b51b1df6b440`.
  It documents an install environment, but it is not a receipt for the original
  TNG fit. `src/proc_TNG.py` writes `tng_params_new_morehalo.npy`, not the
  committed `tng_params_new.npy`; commit `48b5637` only adds the binary. Thus
  the exact producer command, original simulation inputs, and producing
  environment for the source array remain unidentified.
- Local `foregrounds/results/propagation/host_dm_receipt.json` remains
  `fail_closed`. It binds the local host run and inputs but still labels the TNG
  calibration source missing because the external artifact and comparison are
  not yet incorporated into a reviewed receipt. Current local producer bytes
  have SHA-256 `43823c73...` and last changed in analysis commit
  `a4b78b77c10bb0c3d3bf9f21e5887eafc3e1d7d8`; that Git history does not prove
  the commit or environment in which the recorded outputs were generated.

### What this does not establish

The semantic match closes the narrow transcription question only. It does not
reproduce the TNG fit, establish the source array's producing environment, or
admit any host-dispersion result. It does not cure the separate intervening
column blocker for FRB 20230307A.

### Scientific falsifiers

- The transcription is falsified if an independently fetched artifact at the
  named immutable revision does not have SHA-256 `e4e1aa68...` or if columns 2
  and 4 disagree with the embedded arrays by more than the declared `1e-8`
  rounding tolerance.
- The calibration lineage is falsified if the Connor package or its primary
  paper defines different column semantics or a different redshift ordering.
- Any host result depending on this calibration is falsified if reproduction
  from the original TNG inputs yields materially different `mu_IGM` or
  `sigma_IGM`; no materiality threshold has yet been owner-defined.

### Admission and provenance blockers

1. A repository receipt that freezes URL, revision `c8ca7ccc`, artifact path,
   Git blob, SHA-256, shape/dtype, column semantics, and the `1e-8` comparison.
2. Exact producer commit/command, original simulation inputs, and environment
   for the external array, or an explicit owner decision that the published
   immutable binary is the accepted calibration authority.
3. A rerun receipt binding the admitted local producer commit, environment,
   input hashes, calibration receipt, and host outputs.
4. Cluster/intervening closure for FRB 20230307A and owner admission review.

### Executable next check

The immutable URL and revision now exist, so the source/transcription check is
executable without changing repository state:

```bash
tmp=$(mktemp -d /tmp/faber-tng-check.XXXXXX)
git clone --quiet https://github.com/liamconnor/frb_baryon_connor2024.git "$tmp/repo"
git -C "$tmp/repo" checkout --quiet c8ca7cccc22828270291b039963a316b5e35d04f
shasum -a 256 "$tmp/repo/src/tng_params_new.npy"
```

The value comparison must read columns 2 and 4 and require absolute tolerance
`1e-8`. No host-posterior rerun is prescribed until admission specifies the
external-array authority and captures the missing receipts above.

**Verdict:** canonical immutable source located and transcription semantically
matched; host-dispersion science and admission remain unresolved.

## 3. Energetics owner gate only

No energetics probe was performed. The owner must define the scientific
comparison, minimum roster, and acceptable calibration-transfer policy before
work can test a population claim. Existing source:
`energetics/studies/burst-energies/README.md`; queue authority:
`docs/rse/control/program-state.toml` (`owner_view.component` named
`Energies`). No comparison, roster, calibration, or next command is inferred
here.
