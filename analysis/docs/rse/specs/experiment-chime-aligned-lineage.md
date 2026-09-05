# CHIME aligned cross-lineage verification

## Question and fixed criteria

Compare the six historical failures (casey, freya, isha, mahi, phineas,
whitney) and four native low-signal events (isha, mahi, oran, phineas): seven
unique events. The governing P2.3 criterion is an absolute residual lag less
than five **native** samples: 12.8 microseconds at 2.56 microseconds/sample.

Before calculating a residual lag, establish each input's sample coordinates
from producing metadata or independently validated reconstruction: capture clock, crop start, centering translation,
dispersion measure, frequency reference, sampling interval and integration
response. Bind these to the actual array hashes. A timestamp for the burst
alone does not establish the timestamp of sample zero in a centered cube.

For a comparison against coarse references, place profiles on overlapping physical time coordinates, with a common
frequency support and dispersion convention. Integrate the finer samples over
the reference integration intervals; do not stretch records to equal lengths.
Use nonperiodic placement and retain missing coverage. Measure the residual
cross-correlation only after this independently established alignment. Quantify
timing uncertainty, including crop, placement, reference response and noise;
interpolating coarse samples alone does not establish microsecond precision.
The integer-lag calculation must satisfy the original less-than-five-sample
bound; report independent alignment checks and the scope of that result.
Missing coordinates, insufficient signal or
unresolved uncertainty produce an inconclusive result, not a zero lag.

Correctness anchors for a coarse-reference alignment implementation: analytic pulses
with known unequal sample intervals and crop offsets must recover zero after
metadata placement; an injected physical delay must survive that placement;
missing origins and nonoverlapping records must never pass. Positive lag means
the native profile arrives later. No peak or correlation optimum from the
tested profile may also define its timing alignment.

## Initial execution prerequisite audit

The available native NPY headers supply shape and dtype, not the historical
crop/centering origin. Searches of the repository and the h17 metadata,
scripts, results and relevant provenance have not located a hash-bound origin.
The independent upchannelized products have per-channel capture counters and
generation logs. Their dispersion measures differ from those in the native
filenames. Oran has a July 7 reference despite exclusion from the old script.

The initial read-only prerequisite audit ran on h17 before a lag estimator.
Record every input hash, shape, cadence and metadata identity. Preserve the
six historical unaligned failures as unresolved at that stage. Its archived
output explicitly leaves aligned lags null; it is not the final execution result.

## Pilot-informed reconstruction protocol

Independent review found a second route: shared off-pulse noise identifies
the native sample translation without using a burst peak. The archived
`tiedbeam_power` product matches voltage reconstruction at its stored
dispersion measure with K = 1/2.41e-4 and no inter-channel phase translation
for tested Casey, isha and phineas channels. This distinguishes the actual
processing from an archived function's `time_shift=True` default.

The final reference is generated directly from the canonical singlebeam
voltages, in memory, at the native filename's dispersion measure on the
package's K convention. Apply only the intrachannel Fourier de-chirp; no
inter-channel circular phase shift. Subtract any recorded input voltage DM.
This creates a fresh native-resolution independent reference, avoiding the
old upchannelized references' coarse time response. Those old products remain
provenance context, not the numerical reference for this execution.

Pilot work found disagreeing early samples in oran and phineas. Preserve those
findings rather than treating a later match as proof of the complete cube.
Use native samples [4096,8192) to locate a translation by normalized noise
correlation; validate it on untouched [8192,12288). Require both correlations
at least 0.95 and every alternative more than two samples away below 0.5.
These are conservative identity checks, not noise-derived significance levels.
Do not use the test pulse [12800,19200) to choose translation, channels or DM.

Use every nonconstant native channel, requiring complete finite support and presence in the canonical H5,
and report all exclusions and missing H5 channels. Normalize each pair using
its training interval only, then average common channels. Measure pulse lag
over [-32,+32] native samples; test positive and negative injected delays.
Report full common-band and separate below/above-600-MHz lags. Require
abs(lag)<5, no search-boundary optimum, at least 16 matched channels, all live
native channels represented, and both subbands. Check that the reconstructed
400-MHz origins agree across channels to at most 1.1 native samples (one-bin
integer placement range plus numerical margin). This is a consistency bound,
not a confidence interval.

Shared raw noise can itself force a zero correlation lag even if a weak,
broad pulse changes. Therefore zero lag alone is never an acceptance gate.
Require every matched channel's untouched validation and pulse samples to
agree pointwise after training-only affine normalization:
`max(abs(native-reference)/(1+abs(reference))) <= 64*float32_epsilon`
(7.62939453125e-6). This fixed numerical-equivalence tolerance accommodates
float32 power storage and normalization; it is not a universal Fourier error
bound or a timing confidence interval. Do not widen it on failure. Validate
against fresh-environment reconstruction and independently implemented phase
and waveform calculations. Weak broad pulse shifts and pulse removal must
fail this gate even when ordinary correlation returns zero.

Report `heldout-waveform-identity-pass` only within this held-out central-window
scope, with zero-lag evidence as a consequence of waveform agreement. Constant
native rows have no timing information and are reported separately; partial
finite nonconstant rows remain required support. Always report first/last-4096
noise agreement and missing reference edge coverage separately. The result
does not certify complete-window provenance, low-signal detection probability,
the raw archive, or fit/manuscript readiness. Native edge discrepancies and
owner raw-layer spot-check remain separate unresolved gates.

For the four low-signal events, additionally report nonoverlapping native
profile means at fixed widths 1, 4, 16, 64, 256 and 1024 samples. At each width
use the median and 1.4826 times median absolute deviation for noise, and report
the maximum in the central 20% and outer 2%. These are descriptive diagnostics
over multiple widths, not calibrated detection probabilities or replacements
for the original native-sample acceptance test. A broad signal can inflate the
noise estimate; radio interference can also produce a high maximum.

## Reproducibility

Runners: `analysis/scripts/audit_chime_alignment_inputs.py` for the initial
audit and `analysis/scripts/verify_chime_voltage_lineage.py` for the final
native-resolution reconstruction. Both stream over SSH and write only to
standard output; no h17 writes. The local receipt retains results, runtime,
code/lockfile identities, exact commands, independent checks and unresolved
gates. Neither production runner uses random numbers.
