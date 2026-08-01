# Geometry-constrained joint burst fitting

Status: permanent interfaces validated on synthetic data only. No real-event or
manuscript authority changes in migration Wave 1.

## Physical coordinate

The fit has one absolute dispersion measure and one unscattered geocentric
arrival time per matched component, all referred to 400 MHz. For instrument
\(i\) and frequency \(\nu\),

\[
t_i(\nu)=t_{\mathrm{geo},400}+d_i+
K_{\mathrm{DM}}\left(\mathrm{DM}_{\mathrm{absolute}}
-\mathrm{DM}_{\mathrm{product},i}\right)
\left(\nu^{-2}-400^{-2}\right).
\]

In implementation, the final two factors are multiplied:
\(K_{\mathrm{DM}}=4148.808\ {\rm s\,MHz^2\,(pc\,cm^{-3})^{-1}}\).
Positive station delay \(d_i\) means the station records the wavefront after
the geocenter. The reported arrival time is the modeled unscattered component
center, not the observed peak of a broadened pulse.

Each station must supply geometric and clock uncertainties. Independent
geocentric and terrestrial coordinate calculations must agree within the
reviewed limit. Agreement with geometry never establishes the physical
dispersion state of voltage data.

The latent arrival time is stored as seconds from one integer-nanosecond UTC
epoch. Each band carries its own integer-nanosecond UTC origin; the likelihood
subtracts that origin before evaluating the band grid. Output summaries include
both epoch-relative seconds and nine-decimal UTC strings.
Each dispersion state also records the signed correction between the stored
product origin and this 400 MHz coordinate. The likelihood applies that
correction once.

## Observation and dispersion contract

CHIME/FRB and DSA-110 remain on separate native grids. Every observation
provides valid pixels, authoritative channel centers and widths, sample
exposures, a precise time origin, frequency frame, per-channel noise, gain
prior, and input hashes.

Dispersion is represented exactly once:

\[
\mathrm{DM}_{\mathrm{voltage}}+
\Delta\mathrm{DM}_{\mathrm{coherent}}+
\Delta\mathrm{DM}_{\mathrm{residual}}=
\mathrm{DM}_{\mathrm{product}}.
\]

The likelihood applies only
\(\mathrm{DM}_{\mathrm{absolute}}-\mathrm{DM}_{\mathrm{product},i}\).
The coherent anchor is a computational coordinate, not a measurement.
Circular placement and incoherent correction of archival CHIME/FRB NumPy
arrays are forbidden.

The model integrates over each actual channel width and time-bin exposure.
It never stitches bands or forces a common resolution.

Each reviewed association also names a native time window for every band
component. A matched latent center must lie in both of its declared windows;
an unmatched component is constrained to its own band window. This prevents a
component association from becoming a label-only permutation of the same
mixture.

## Pulse-broadening models

The production ladder is physically constrained:

1. unscattered Gaussian components;
2. an exponentially modified Gaussian at the square-law endpoint
   \(\beta=4\), where the pulse-broadening function is exponential and
   \(\tau\propto\nu^{-4}\);
3. a thin-screen power-law pulse-broadening function for \(2<\beta<4\), with
   both its tail and frequency scaling fixed by the same parameter,
   \(\alpha=2\beta/(\beta-2)\).

A freely varying frequency exponent inside an exponential kernel is diagnostic
only: its pulse shape assumes \(\beta=4\), so interpreting another exponent as
turbulence would be inconsistent.

The power-law kernel is causal and normalized. Its omitted probability beyond
finite support is analytic. Gaussian-convolution support uses a rigorous union
bound, so crop admission is based on a number rather than visual judgment.
Per-channel amplitudes are integrated out under a zero-mean normal prior.
Intrinsic widths and scattering times use log-uniform priors.

## Public workflow

The public execution surface is:

```bash
UV_PROJECT_ENVIRONMENT=.venv-dualband uv sync --locked \
  --group dualband
make review EVENT=synthetic
```

Execution uses that dedicated environment with `--no-sync`; a run never
changes its own environment. Python 3.12.13 and Dynesty 3.1.0 are required.

The dependency chain is:

```text
review -> verify -> fit -> observations
```

Each stage resumes only when request and product hashes agree. Changed or
partial products fail with an immutable receipt. Publication is atomic.
Accepted output names are:

```text
dualband-burst-models/<event>/
├── params.json
├── posterior.npz
├── model-products.npz
├── provenance.json
└── review-packet.pdf
```

The synthetic result may reach `provisional-owner-review`. Only an owner
decision can change an unchanged result to `accepted`; promotion does not
rerun inference.

## Admission boundary

Synthetic truth is fixed before sampling. Required checks include shared
dispersion measure and 400 MHz arrival-time recovery, geometry sign, complete
dispersion accounting, posterior bracketing, prior-edge mass, finite crop-tail
support, evidence uncertainty, valid-sample coverage, residual power,
structured residual correlation, immutable resume, and forbidden FLITS
runtime detection.

Wave 1 does not read real raw data, run Casey, change manuscript consumers, or
retire legacy code. Those actions require later migration waves.
