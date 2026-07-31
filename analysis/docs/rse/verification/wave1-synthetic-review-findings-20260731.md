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
