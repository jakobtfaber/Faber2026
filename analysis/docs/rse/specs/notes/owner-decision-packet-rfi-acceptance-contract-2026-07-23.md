# Owner decision: CHIME RFI acceptance contract

**Status:** decision pending

**Ticket:** [Define the CHIME RFI-cleaning acceptance contract](../../wayfinder/tickets/rfi-validation-01-define-acceptance-contract.md)

## What is already settled

The owner accepted the manual Zach channel map and the
uncertainty-normalized signal-preservation limits. The reviewed automated
candidate failed and remains rejected. No cleaner or science result is
admitted.

## Recommended remaining contract

Accept all five fail-closed rules:

1. remove at least 90 percent of injected contaminant excess power and identify
   at least 95 percent of contaminated samples;
2. falsely reject no more than 1 percent of truth-clean, source-valid samples
   overall and 2 percent in any broad frequency slice or time block;
3. retain at least 95 percent of otherwise usable samples in the quiet raw-file
   test and 80 percent in the interference-heavy raw-file test;
4. require each contiguous time half and every required file and frequency
   slice to pass independently; and
5. require the already accepted protected-measurement limits, with missing or
   invalid measurements treated as failures rather than passes.

Rate estimates include sample counts and 95-percent confidence intervals.
Their conservative confidence bound must pass. The interval method is frozen
with the benchmark before cleaner comparison and must account for correlated
time-frequency samples through frozen independent clusters or a cluster
bootstrap.

Before comparison, also freeze truth labels, injected-power references,
source-valid and otherwise-usable denominators, all masks and exclusions,
frequency/time edges, minimum support, measurement applicability, and the
reference uncertainty used for normalized shifts. Candidate-inflated
uncertainty cannot make a result pass.

## Required blind scope and review

Tune only on Zach training and validation intervals. Blind evidence must also
pass on Zach's sealed test interval and two preselected untouched raw CHIME
files with quiet and interference-heavy conditions. Frozen known-truth
contaminants and protected bursts are injected into every held-out raw
background; unlabelled native samples do not supply truth labels.

Every predeclared contaminant class and protected-signal parameter stratum
with sufficient frozen support must pass independently. Pooled success cannot
rescue a failed stratum.

Before cleaner ratification, inspect:

- a complete threshold/result table by file, time half, and frequency slice;
- matched no-removal, bandpass-only, and candidate data/mask panels;
- known-truth contamination and false-removal overlays;
- protected-measurement shifts in units of measurement uncertainty; and
- exact source, split, code, configuration, environment, order, and rerun
  provenance.

## Decision requested

Accept or change the proposed numerical envelope, including whether retaining
only 80 percent of otherwise usable data in the interference-heavy file is an
acceptable cost. The definitions and anti-pooling safeguards above are
mandatory mechanics, not cleaner approval.

Acceptance closes only the contract ticket and unblocks bandpass
qualification. Cleaner validation, sealed-test execution, full-sample use, and
science admission remain later gates.
