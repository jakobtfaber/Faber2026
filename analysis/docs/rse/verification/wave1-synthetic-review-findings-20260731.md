# Wave 1 synthetic review findings — preserved receipt

Candidate reviewed: `1c1032e16627a769c2ee416f2ae2cf3ac40d1b80`;
tree `a490f7b4f6274263784462532e6cb37e63c54bd6`.
That candidate and all evidence generated from it are invalid. This receipt
preserves the independent findings verbatim before the replacement candidate
is frozen.

## Adversarial implementation review

**FAIL.** Commit/tree match requested pin. Prior mechanical defects repaired;
nine objective contract failures remain.

1. **[BLOCKING] Association hypotheses do not affect the likelihood.**
`_component_profile` never reads component matches. The fit loop changes only
association metadata; all hypotheses therefore receive identical models.

2. **[BLOCKING] Advertised power-law injection silently generates an exponential pulse.**
Schema permits `powerlaw` but provides no truth beta. Generator handles every
non-Gaussian choice through SciPy’s exponential model. Verification checks
scattering time but never beta.

3. **[BLOCKING] Input/preflight failures emit no failure receipt.**
Configuration, request hashing, and environment preflight occur before the
receipt-producing `try/except`. Dirty checkout, FLITS, wrong Python, wrong
sampler, or external editable-package failures escape receiptless.

4. **[BLOCKING] Partial-run resume is not environment-bound.**
Environment is checked only for the current invocation. Observation and fit
receipts omit environment-manifest identity. A fit produced under environment
A can resume verification under environment B; final provenance then falsely
records only B.

5. **[BLOCKING] No sampler checkpoint or interrupted-fit resume exists.**
Nested sampling runs monolithically. Posterior/receipt writing occurs only
after completion. Tests cover completed-stage reuse only. This does not
satisfy checkpoint identity or serial-versus-resume verification.

6. **[BLOCKING] Production deliberately violates the approved installation boundary.**
Documentation creates an environment with `--no-install-project`; Make
injects `PYTHONPATH`. Ticket 8 requires importing the installed checkout and
explicitly forbids `PYTHONPATH`.

7. **[BLOCKING] Missing uncertainty evidence still publishes as provisional.**
Calibration/resolution and intrinsic-lag classes are unreasoned `null`
values. Workflow nevertheless publishes `provisional-owner-review`. Ticket 7
says missing evidence fails unless a reviewed reason exists.

8. **[BLOCKING] Crop-tail admission is not a posterior bound.**
Workflow discards samples below an unreviewed weight threshold, then checks
only samples with minimum/maximum arrival time. Extremes in dispersion measure,
timing error, width, or their covariance can touch a boundary in another
sample and remain undetected.

9. **[BLOCKING] Owner acceptance has no immutable promotion receipt.**
Canonical construction hashes only companion products; canonical validation
never independently binds `params.json`. Promotion mutates that unbound file
in place. Status and owner identity can therefore be altered without
invalidating provenance.

## Independent scientific review

**FAIL** — critical: association hypotheses do not alter the physical
likelihood. Multi-component physics incomplete: no component amplitude
parameters; unit-area components are summed, then one channel gain scales the
whole sum. Unequal component strengths or spectra cannot be represented.
Unmatched band-local components are also forbidden.

High: uncertainty classes double-count correlated variance. Moderate:
log-prior boundary gate still uses linear-distance edges. Repaired and
verified: power-law normalization and near-`beta=4` continuity; log-uniform
sampling; zero-mean gain integral and gain-adjusted residual; explicit
time-origin correction and UTC consistency. Timing-origin sign still lacks
nonzero injected recovery; current test only perturbs metadata on zero-shift
data.

## Later candidate review retained for repair provenance

**FAIL / not eligible.** `84155c34` was invalidated by later uncommitted
edits. Supplied output binds `0370eb0`, not the candidate.

### Issues

- **[BLOCKING] Mutable science summary.** `params.json` is not content-bound;
  changing DM, ToAs, status, or owner can remain schema-valid and pass
  canonical validation.
- **[BLOCKING] Checkpoint reuse lacks provenance binding.** Existing Dynesty
  checkpoint path is restored without validating request hash or environment.
- **[BLOCKING] Promotion is not crash-safe.** Permanent receipt directory is
  created before its receipt; interruption leaves an unrecoverable path.
- **[BLOCKING] Crop-tail certificate is not mathematically sufficient.** It
  evaluates channel centers despite channel-width integration in the likelihood,
  and takes a maximum of individual component tails rather than their summed
  omitted flux. Independent edge evaluation found `1.73720087109e-05`, versus
  reported `8.04068053893e-06`.
- **[BLOCKING] Dynesty provenance checks version, not imported module origin.**

### Strengths

- No active FLITS imports.
- Native grids, 400 MHz timing convention, exactly-once dispersion state, and
  association/nuisance modeling are substantively present.
- Old synthetic output recovered the injected DM/ToA and geometric offset, but
  is stale evidence only.

These findings are retained as repair provenance for the replacement freeze and
full gate rerun.

## 336553b independent scientific review

**FAIL**

**[BLOCKING]** Power-law crop support is not rigorous near the allowed
\(\beta=4\) endpoint.

`workflows/dualband_burst_model.py:_power_law_tail_mass` uses
`np.isclose(beta, 4.0)` to substitute the exponential tail. The physical
power-law kernel uses the exponential only at exactly `beta == 4.0`.

Independent oracle: for allowed `beta=3.999999` and `cutoff/tau=100`:

- true declared power-law tail: `2.105013849018507e-12`
- code's exponential substitute: `3.720075976020836e-44`
- underbound: factor `5.66e31`

That invalidates the claimed rigorous crop-tail bound for supported power-law
fits (`workflows/dualband_burst_model.py:715`).

The fresh EMG synthetic output itself is otherwise correctly bound and
provenance-clean; this blocker is generic power-law support.

## 69b8e93 independent scientific review

**FAIL**

**[BLOCKING] PDF readability.** Page 2's Shared DM axis tick labels overlap
(`491.15491.20491.25…`), so the posterior scale is not legible in
`review-packet.pdf`.

All scientific-contract checks pass:

- Output and receipts bind cleanly to `69b8e938623a8de8fa488423c7fa162a9c80f9e8`.
- `beta=3.999999` tail equals the independent power-law reference exactly:
  `2.1050138490185069e-12`; exact `beta=4` gives
  `3.7200759760208361e-44`.
- Exact EMG channel-edge tail: `1.7372008711e-05`; recorded conservative bound:
  `3.9009799926e-05 < 1e-4`.
- Exactly-once DM identities, native grids, shared-DM/ToA recovery, geometric
  400 MHz sign, and provisional synthetic status all pass.
