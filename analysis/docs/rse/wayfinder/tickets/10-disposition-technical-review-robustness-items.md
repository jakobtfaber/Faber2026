# Disposition the technical-review robustness items for this submission

- Type: `wayfinder:grilling` (HITL)
- Status: resolved (2026-07-22)
- Assignee: Codex controller
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

The former deadline-reconciliation blocker closed on 2026-07-18. Dispositions
are decided on scientific need, not schedule.

The 2026-07-15 technical-review triage leaves a set of valid,
not-yet-dispositioned robustness items; decide in / out /
defer-with-stated-caveat for each on scientific need:

- **Intervening-scattering column** in the budget table: document the
  DM→scattering-measure→τ mapping with priors in an appendix, or drop the
  column until the scattering framework lands (triage recommends drop). (S14)
- **Modulation-index gate vs the two-screen √3 bound**: reframe the m ≤ 1.5
  gate's justification, or raise the bound and re-run the guard matrix,
  reporting any verdict changes. (S16)
- **Pulsar positive control** through the CHIME upchannelization chain: real
  new data product — needed for this submission, or does the injection
  battery suffice with clearer framing? (S17)
- **Cluster-aperture sensitivity**: recompute at 1.5·R_500 / R_200 with an
  envelope (machinery exists; the documented near-miss would be the sample's
  second-largest column). (S13)
- **Association robustness paragraph**: positive-residual mean (+2.4 ms,
  ≈2.4σ), declination-conditioned rate sensitivity sentence, repeater/
  clustering statement — cheap, likely all in. (S4/S5/S6)
- **Jackknife/masking specification** sentences. (S7)
- **Moderate campaigns**: coverage-calibrated DM uncertainties (S8),
  completeness/missing-halo systematic (S11), disk-model per-sightline
  comparison table (S15b), effective-index sensitivity variant + δDM prior
  tightening (S19) — which are scientifically warranted for this submission?

Resolution = a per-item disposition table; execution of the "in" items rides
the lane system.

- [Owner decision packet (ready for review)](../../specs/research-technical-review-robustness-dispositions-2026-07-22.md)

## Decision — 2026-07-22

Owner accepted the disposition table as a batch per `research-technical-review-robustness-dispositions-2026-07-22.md`.

| Review item | Disposition |
|---|---|
| S14 intervening-scattering column | Out |
| S16 modulation-index gate vs two-screen √3 bound | Defer into tickets 17 and 02 |
| S17 pulsar positive control through CHIME chain | Defer |
| S13 cluster-aperture sensitivity | In |
| S4 positive timing-residual mean | In |
| S5 declination-conditioned CHIME rate | In |
| S6 repeater/clustering statement | In, wording-level |
| S7 jackknife/masking specification | In |
| S8 coverage-calibrated DM uncertainties | Defer with caveat |
| S11 completeness/missing-halo systematic | In, through expanded-catalog repair |
| S15b per-sightline disk-model comparison | In |
| S19a effective-index sensitivity variant | Out |
| S19b broad δDM prior | In, at next trusted refit |

Execution follows the dependency-aware order in the decision packet.
