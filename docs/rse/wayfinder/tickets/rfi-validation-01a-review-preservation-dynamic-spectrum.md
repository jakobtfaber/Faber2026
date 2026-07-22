# Review the RFI preservation limits on a controlled dynamic spectrum

- Type: `wayfinder:prototype` (HITL)
- Status: open
- Assignee: Codex
- Blocked by: [Build the verified Zach CHIME preprocessing baseline](16-build-verified-zach-chime-preprocessing-baseline.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Do the proposed signal-preservation limits look scientifically appropriate
when applied to a controlled Zach dynamic-spectrum example?

Build a development-only review artifact without opening any sealed test data.
Use a burst-like injection with known truth and synthetic interference, then
show:

1. the injected truth dynamic spectrum;
2. the same injection with synthetic interference;
3. the output of the current rejected cleaner, used only as an illustrative
   candidate;
4. the output-minus-truth residual and explicit mask; and
5. concise pass/fail annotations for every proposed preservation limit.

Include the time profile and fluence by broad frequency slice beside the
dynamic spectra where needed to make hidden redistribution visible. Bind the
source, injection, random seed, code, environment, and output hashes. The
artifact is diagnostic only: it cannot validate the cleaner or admit science.

Resolution requires owner review of the figure and either acceptance or
revision of the proposed preservation limits.

## Observed-event supplement — 2026-07-21

Owner requested the candidate cleaner applied to a real sample event. The
supplement uses Zach's observed CHIME/FRB Stokes-I product. It loads numerical
samples only from public training columns `[55,137)` and configured burst
columns `[232,248)`; the full file is read only as bytes for its checksum. It
does not read the public validation interval or the sealed test interval.

- Figure: [real Zach method comparison](../../verify/rfi-real-event-review-20260721/real_zach_rfi_method_comparison.svg)
- Machine record: [JSON](../../verify/rfi-real-event-review-20260721/real_zach_rfi_method_comparison.json)
- Exact script: [`review_real_zach_rfi_cleaner.py`](../../../../scripts/review_real_zach_rfi_cleaner.py)
- Remote evidence: `/data/Faber2026/evidence/rfi-real-event-review-20260721/`
- Reproduction: pinned `baseband-analysis` container runs `run-7` and `run-8`
  have byte-identical output manifests. Recomputed cleaner masks and bandpass
  arrays are byte-identical to the earlier audit-v2 products.

Result: the cleaner retains 50,238 of 55,744 measured frequency rows and drops
5,506 rows (9.88%). On retained rows, its values equal the bandpass-only result
exactly; the maximum absolute difference is `0.0`. The visible effect is thus
support removal. Because the observed event has no known truth, this supplement
does not establish whether the removed rows are interference or signal and does
not validate the cleaner. Relative product time and provisional dispersion
measure `262.368 pc cm^-3` are diagnostic only; the arrival-time audit remains
open.

Owner review remains required before this ticket can close.
