# Geometry-constrained joint burst fitting

Status: validated on injected data only. Real-event results remain provisional
until reviewed timing, crop, component, and clock inputs are complete and the
owner approves the review packet.

## Physical coordinate

The fit has one absolute dispersion measure. Each matched physical component
has one latent, unscattered arrival time at the terrestrial geocenter,
referenced to 400 MHz. For instrument \(i\) and channel frequency \(\nu\),

\[
t_i(\nu)=t_{\mathrm{geo},400}
 + d_i + c_i
 + K_{\mathrm{DM}}(\mathrm{DM}-\mathrm{DM}_{\mathrm{product},i})
   (\nu^{-2}-400^{-2}).
\]

\(d_i=-\boldsymbol r_i\cdot\hat{\boldsymbol n}/c\) is the station delay.
Topocentric arrival time therefore equals geocentric arrival time plus station
delay. \(c_i\) is a zero-mean clock-error nuisance term. Seconds and megahertz
are used internally. The reported arrival time is the modeled unscattered
component center, not the scattering-shifted peak.

The GCRS and ITRS calculations independently check the observable
CHIME/FRB–DSA-110 baseline delay. Geometry and clock uncertainties must both be
present. Agreement with geometry never certifies the input voltage state.

For Casey, the provisional owner-adopted Gaussian clock prior has a 1 ms
standard deviation on the inter-site difference. The model uses independent
station nuisance terms, so each receives \(1/\sqrt{2}\) ms; their quadrature
difference remains exactly 1 ms. Each station-delay term receives an
owner-adopted Gaussian standard deviation of 0.5 us. This is separate from the
independent-projection agreement check. These priors permit inference but are
not measurements of either station's absolute UTC accuracy.

## Data contract

Each band remains on its reviewed native frequency and time grid. Products
record:

- explicit valid pixels and accepted channel support;
- authoritative channel centers and widths;
- exact nanosecond crop origin, shape, sample interval, and noise-estimation
  pixel mask;
- per-row off-pulse noise;
- input, coherent-correction, residual-correction, and product dispersion
  measures;
- raw and accepted-support input hashes.

The dispersion identity is exact:

\[
\mathrm{DM}_{\mathrm{input}}+
\mathrm{DM}_{\mathrm{coherent}}+
\mathrm{DM}_{\mathrm{residual}}=
\mathrm{DM}_{\mathrm{product}}.
\]

The model evaluates only
\(\mathrm{DM}_{\mathrm{absolute}}-\mathrm{DM}_{\mathrm{product},i}\).
Builders use fractional, non-wrapping shifts. They never incoherently
dedisperse archival CHIME/FRB arrays.

## Model

Matched components share the latent arrival time and a continuous
frequency-dependent width law. They retain band-specific amplitudes, spectral
envelopes, masks, noise, and response. Unmatched components are local nuisance
components and do not constrain geometry. Event configuration lists only
plausible one-to-one, time-order-preserving associations.

Two baseline families are compared: Gaussian components and the same
components convolved with a shared scattering law. Per-channel gains are
integrated out with a proper Gaussian prior. Nested sampling fits every
morphology–association combination. Evidence weights form the reported
dispersion-measure and arrival-time posterior mixture, including association
uncertainty.

No common-grid stitching, circular rolling, independent band centroid shift,
or free residual drift is allowed.

## Reviewed execution

The single public command is:

```bash
python scripts/run_one_event_absolute_dm_workflow.py \
  --config analysis-configs/absolute-dm/casey.json
```

Formal execution requires locked band-specific crop bounds, off-pulse padding,
time and frequency bin factors, frequency-grid and valid-mask hashes,
crop-origin and off-pulse-mask hashes,
component windows, association hypotheses, clock
uncertainties, and acceptance thresholds. Any drift fails before sampling.
The locked environment supplies `dynesty` 3.1 and rejects imports from a
retired editable FLITS checkout.

Input preparation fails before data processing when reviewed clock or
station-delay uncertainties are absent. It performs one CHIME/FRB coherent
anchor evaluation. Fully coherent bracketing evaluations remain a post-fit
acceptance step.

Review uses three immutable configuration states:

1. Blocked: only high-resolution preparation and proposals are allowed.
2. Reviewed: fit grids, component windows, associations, priors, and array
   hashes are locked; execution remains disabled.
3. Authorized: an explicit note creates a new binding and enables execution.

Transitions always write a new configuration. Authorization changes the event
binding, so preflight, DSA-110 audit, both high-resolution product builders,
fit-grid materialization, and geometry are rebuilt before fitting.

Preparation is two-pass. A high-resolution diagnostic establishes the
component widths needed to review frequency averaging. Reviewed factors then
materialize separate fit-grid observations; only those observations define the
final component sample coordinates. Formal time averaging is forbidden because
the likelihood evaluates bin centers and does not integrate over averaged-bin
duration. Frequency averaging requires complete rectangular support and
analytic residual intra-bin smearing below 0.10 fit sample and 0.05 of the
narrowest reviewed component width.

Canonical outputs are `fit-result.json`, `posterior.npz`,
`model-products.npz`, `geometry-constraint.json`, `run-provenance.json`, and
`review-packet.pdf`. `oracle-verification.json` is the compact fail-closed
receipt for the posterior lower bound, median, and upper bound. Posterior
samples never enter JSON. Results remain provisional until owner visual
approval.

## Acceptance

Execution fails on a dispersion-measure posterior at a prior boundary,
inadequate residuals, missing timing uncertainty, changed frequency or support
identity, incomplete crops, or exactly-once dispersion failure. Final review
also compares the posterior median and bracketing dispersion measures against
fully coherent CHIME/FRB evaluations and exactly-once DSA-110 corrections.
The packet shows the posterior-median spectra separately from the fit-coordinate
data, model, and residual so unlike time coordinates are never overplotted.

Post-fit resolution convergence is mandatory. The proposed frequency factor is
compared with half that factor. Both fits must pass; dispersion-measure medians
must differ by at most 0.5 combined posterior standard deviations and
0.005 pc cm^-3; arrival times by at most 0.5 combined posterior standard
deviations; 68% interval-width ratio must lie in 0.8–1.25; morphology and
association weights may differ by at most 0.10 in summed absolute weight.
Material movement becomes a systematic uncertainty; it is never silently
accepted.
