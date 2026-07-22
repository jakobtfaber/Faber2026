# Ratify the fit re-trust validation contract

- Type: `wayfinder:grilling` (HITL)
- Status: resolved (2026-07-22)
- Assignee: —
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

The trust reset (2026-07-06) revoked every burst-data fit; re-entry runs
through a validation contract whose draft terms are: (i) verified input-data
lineage (gen-2+, checksum-provenanced), (ii) synthetic-injection recovery of
known truth under each candidate geometry, (iii) a prior-rail is model-family
rejection, never a quotable limit, (iv) posterior-predictive check pass,
(v) an independent cross-check itself produced under this contract — never
inherited from the revoked campaign. (Legacy code: plan §V, item V1.) Does the
owner sign these five terms as the binding ADR — amended or as-is — so the
scattering re-fit and scintillation measurement campaigns can produce citable
numbers? Include the companion input question: the check on whether the CHIME
dynamic spectra feeding the scattering fits share the gen-1 de-chirp defect
lineage (legacy V2) — is that check a precondition written into the contract,
or a parallel task?

## Decision — 2026-07-22 (manuscript-owner checkpoint receipt)

Owner ratified the fit re-trust checklist as binding for future fit campaigns,
with one amendment: synthetic-injection recovery is not required as a
standalone step. The remaining required steps are:

1. Verified gen-2+ input-data lineage with checksum provenance.
2. Prior-rail used only for model-family rejection, never as a quoted limit.
3. Posterior-predictive check pass.
4. Independent cross-check produced under this contract.

The CHIME dynamic-spectrum de-chirp defect lineage check is a precondition
before any CHIME-based fit is trusted.

Known-truth injection calibration is required for any new estimator, any
materially changed likelihood or forward model, any model-selection procedure,
and any component-count-setting statistic. It is not required as a standalone
step for re-trusting the existing fit path.

Owner receipt: [Manuscript-owner governance receipt — 2026-07-22](https://github.com/jakobtfaber/Faber2026-analysis/pull/46#issuecomment-5050854194).
