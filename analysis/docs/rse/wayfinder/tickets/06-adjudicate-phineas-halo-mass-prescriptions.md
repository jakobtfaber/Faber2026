# Adjudicate the conflicting halo-mass prescriptions on the phineas sightline

- Type: `wayfinder:grilling` (HITL)
- Status: resolved (2026-07-22)
- Assignee: Codex controller
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
- Provisional answer at that stage: build the probabilistic route before
  freezing the Phineas foreground and host-dispersion headline.

## Resolution — 2026-07-22

Adopt the probabilistic route. The apparent binary conflict mixed two radius
definitions: the census flag tests `R200c`, while the modified-NFW gas model is
truncated at its Bryan--Norman virial radius. The dispersion model now uses the
radius that bounds its gas profile and reports `R200c` crossing separately as a
geometry sensitivity.

From `2^18` deterministic uncertainty draws per object:

- canonical `832`: `P(b<R200c)=0.8641`,
  `P(b<Rvir_mNFW)=0.9944`;
- object `983`: `P(b<R200c)=0.2170`,
  `P(b<Rvir_mNFW)=0.5104`.

Non-crossing draws contribute exactly zero. The two mixture distributions are
convolved into the Phineas foreground model; its intervening-dispersion
percentiles are now `203, 255, 322 pc cm^-3`. The implementation, frozen input
hashes, checks, and limitations are recorded in
[the probabilistic-crossing research note](../../specs/research-phineas-probabilistic-crossing-model.md).

Decision authority: the ticket's standing owner delegation, reinforced by the
owner's 2026-07-22 request to resolve this directly or through Repowire. Focused
physical, convergence, artifact, and independent Monte Carlo checks pass.

Ticket 07 was resolved earlier on 2026-07-22. This rerun preserves its accepted
priors and headline logic while replacing only the Phineas binary-halo input.
