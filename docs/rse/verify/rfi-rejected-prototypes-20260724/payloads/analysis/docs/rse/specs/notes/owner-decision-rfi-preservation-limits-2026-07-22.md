# Owner decision: controlled RFI preservation limits

**Gate:** scientific and visual review  
**Ticket:** [Review the RFI preservation limits on a controlled dynamic spectrum](../../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)  
**Scope:** synthetic diagnostic only; no sealed data; no cleaner validation; no science admission

## Evidence

- [Review panel](../../../verify/rfi-preservation-20260722/rfi_preservation_review.svg)
- [Measurements and limit checks](../../../verify/rfi-preservation-20260722/rfi_preservation_metrics.json)
- [Seed, environment, source, injection, and output hashes](../../../verify/rfi-preservation-20260722/manifest.json)
- Rebuild: `python3 scripts/build_rfi_preservation_review.py`

The controlled example uses the Zach frequency span and time cadence, a
two-component truth-known burst, Gaussian background, persistent narrow-band
emitters, bursty interference, and a weak spectral comb. The illustrative
candidate reproduces the rejected iterative frequency-row mean/standard-
deviation outlier rule and learns its mask only from declared off-pulse bins.

The cleaner masks 20 of 256 frequency rows. Detection and two-component count
survive, but five preservation checks fail. Median absolute shift is 4.13
measurement uncertainties; the largest shift is 11.30; only 28.6% of the seven
displayed measurements remain within one uncertainty. The broad-frequency
fluence panels expose loss hidden by unchanged detection and component count.

## Recommendation

**Accept the numerical limits unchanged, with one clarification:** ensemble
percentiles must be calculated separately for each protected measurement over
the predeclared injection ensemble. The seven heterogeneous measurements in
this single panel are a visual stress test, not the future acceptance ensemble.

Reason: the proposed limits reject a candidate that visibly redistributes
fluence while retaining detection and component count. Weakening them is not
supported by this evidence. This does not establish that they are sufficient;
the later frozen benchmark and blind tests remain mandatory.

## Minimal decision

Choose one:

1. **Accept recommended clarification.** Preserve the limits and apply ensemble
   summaries per protected measurement.
2. **Revise.** Name the limit, replacement value, and scientific reason.

Owner visual and scientific review is the only remaining gate for this ticket.

## Bound identity

- Seed: `2026072201`
- Truth SHA-256: `4ba148aff28cb82df7a964ffb7c4edc6c593b64dfc6ffed14a73fa3c2d257465`
- Contaminated input SHA-256: `290359611857a497d2f4dc06dde850b1c746fe7393baa3825e828bb39a2bb832`
- Source SHA-256: `b340e6bfbdf8d4f1269e2b25a0a2979f5c430cd5b626e8b59ee25739df111869`
- SVG SHA-256: `0b51659e4fd1172e34536538693f48bc950902cc7838a89768826dde25de3fc7`
- Metrics SHA-256: `ee5ada64517470c7b63bb1057e8ad951b6ecf65787e85ca32f128857195e8900`
