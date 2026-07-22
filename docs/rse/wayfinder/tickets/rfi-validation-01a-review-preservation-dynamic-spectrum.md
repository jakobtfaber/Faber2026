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
