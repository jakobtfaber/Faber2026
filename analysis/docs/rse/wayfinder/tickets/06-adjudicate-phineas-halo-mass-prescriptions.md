# Adjudicate the conflicting halo-mass prescriptions on the phineas sightline

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: Codex
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

Two manuscript surfaces assign opposite virial-crossing verdicts to the same
two phineas (FRB 20230307A) foreground halos (objs 983 at b=122 kpc and 832
at b=159 kpc): the census geometry flags call them non-piercing exceptions
(b/R_vir ≈ 1.05–1.7), while the budget contributor chain has them
contributing ≈8.9+13.9 pc cm⁻³ — if the census flags govern, phineas
DM_int ≈ 218 rather than 241. This is the borderline-b/R_vir
mass-conditionality problem the technical review flagged (legacy S12
escalation, triage addendum 2026-07-15). Which mass prescription governs —
census flags, budget chain, or the probabilistic route (Monte-Carlo halo mass
from the stellar-mass relation + photo-z scatter → P(b < R_vir) → mixture
DM_int in the forward model, which prevents borderline zeros/values reading
as measurements)? The answer fixes the budget table, the phineas host-DM
posterior, and whether the probabilistic machinery must be built before
submission.

## Independent validation — 2026-07-22

Clean-room replay: [Phineas owner-adjudication validation](../../specs/reproducibility-phineas-owner-adjudication.md).

- The approved point calculation is understood and independently reproduces:
  `243.2445 -> 243 pc cm^-3`.
- The scientific binary crossing verdict is not independently valid: source
  photometry is absent, the calculation uses redshift-zero Moster parameters,
  and mass plus photometric-redshift uncertainty was not propagated.
- Object 983 changes from non-crossing to crossing at its reported
  one-standard-deviation lower photometric redshift under the published
  redshift-dependent relation. The canonical 832 object has only `0.056 dex`
  halo-mass margin above the boundary.
- Provisional answer: build the probabilistic route before freezing the
  Phineas foreground and host-dispersion headline. Ticket remains open for
  owner adjudication.
