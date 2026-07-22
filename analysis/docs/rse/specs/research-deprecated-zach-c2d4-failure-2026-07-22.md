# Deprecated Zach C2D4 failure audit

**Verdict:** reject job 180 as a fit and as a review candidate. Retain it only
as failure evidence for the controlled C2D4 rerun.

## Producing artifacts

The audit uses the archived h17 job-180 fit, 36,243 weighted posterior samples,
model grid, and complete standard-output/error logs. Their hashes are recorded
in
[`audit.json`](../../../figure_review/audits/2026-07-22-deprecated-zach-c2d4/audit.json).
The C2D3 comparison is the exact s2=100 candidate already certified for
diagnostic rendering.

The job ran on `lxd110h17` with 400 live points, four workers, C2D4, and fixed
gain-prior variance 100. The recorded working directory and reconstructed
argument vector are in
[`provenance.json`](../../../figure_review/audits/2026-07-22-deprecated-zach-c2d4/provenance.json).

The original fit is not reproducible. It recorded no sampler seed, used an
untracked fit driver from a dirty checkout, and did not bind source, input, or
environment hashes at run time. Post-hoc hashes identify the surviving files
but cannot retroactively prove their job-time identity.

## Reconstructed failure

The posterior samples reproduce every stored 16th, 50th, and 84th percentile
exactly. All four DSA-110 arrival medians lie inside the 0–5.89824 ms fitted
window, so this particular failure is not an off-window component.

The fourth DSA-110 component is not a resolved fourth pulse:

- width parameter: **350.235 ms**;
- fitted-window span: **5.89824 ms**;
- width/window ratio: **59.380**; and
- modeled DSA-110 fluence fraction: **0.0308183**.

It is therefore a broad, low-fluence pedestal. The posterior-sample
reconstruction supplies the width; the independently produced model grid
supplies the fluence fraction.

The pedestal lowers the DSA-110 reduced residual statistic from 1.213 for C2D3
to 1.130 for C2D4, while leaving the CHIME/FRB statistic at 2.025. A reduced
residual statistic near one is therefore not sufficient evidence of a resolved
component.

## Evidence comparison

C2D3 and C2D4 use the same fixed gain-prior variance and beta bounds. Their
common beta and 1-GHz scattering-time medians differ by only 0.064 and 0.170
combined posterior standard deviations, respectively, so this is a
mode-continuous same-arm comparison. Within that limited comparison,

\[
\ln Z_{\mathrm{C2D4}}-\ln Z_{\mathrm{C2D3}}=-10.1023.
\]

This does not overturn the owner's data-only C2D4 morphology assignment. It
shows that job 180 failed to represent the visually identified fourth pulse;
its extra degree of freedom collapsed into a pedestal instead. The replacement
C2D4 fit must resolve a fourth pulse rather than reproduce this mode.

## Frozen rerun guards

The machine-readable audit defines the controlled-run guards:

1. component arrivals must lie within fitted support;
2. any component at least five times broader than the fitted window and at
   most 5% of modeled band fluence is flagged as a pedestal;
3. fit summary, posterior, model grid, and review manifest must agree on
   component counts;
4. evidence values are compared only across matching likelihood, gain-prior,
   support, and posterior modes; and
5. residual morphology is inspected even when a scalar residual statistic is
   close to one.

The width and fluence thresholds are deliberately far from job 180's values:
59.4 window widths and 3.08% fluence. Crossing either threshold is a diagnostic
flag, not automatic component-count adjudication.

## Independent check

Two independent producing artifacts agree on the failure:

- weighted posterior reconstruction reproduces the fit-summary width
  quantiles exactly; and
- direct integration of the separately generated model grid gives the fourth
  component's 3.0818% fluence fraction.

Synthetic tests independently assert the broad/low-fluence guard, valid
same-mode evidence comparison, and fail-closed component-count behavior. No
deprecated image was reopened for owner review.
