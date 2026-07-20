# Research: CHIME 2L manuscript reconciliation

**Date:** 2026-07-17
**Scope:** Internal codebase and pinned upstream FLITS evidence
**Codebase state:** Faber2026 `03b2f0fa`; dsa110-FLITS remote `main` at
`17d9d26675702e9f8917da655621bef3231f0ddb`

## Question / Scope

Determine the exact merged dsa110-FLITS revision for PR #192, what its
injection-validated window campaign permits the manuscript to claim, and how
to replace the rejected DSA-only summary without promoting unreviewed figure
bytes. Figure 1, `sections/toa.tex`, and scattering-refit products are out of
scope.

## Codebase Findings

- Faber2026 currently pins FLITS `5fb387ede57c9654a404ffd597d0f89a097d73b7`,
  before PR #192. A fresh fetch from the submodule's configured
  `https://github.com/jakobtfaber/dsa110-FLITS.git` remote resolves `main` to
  merge commit `17d9d26675702e9f8917da655621bef3231f0ddb`; its parents are
  `5fb387e...` and reviewed campaign head `ae67bdf...`.
- The merged campaign's `validation.json` is closed with an injection-gate
  pass, 24 standard/high-resolution records, one measurement, and 23
  diagnostic-only records. The one promoted record is `chromatica_hi`
  (FRB 20240203A): its artifact and figure gates both pass, four subbands are
  resolved at 623.6--749.2 MHz, and its within-band slope is
  `alpha = 3.0877 +/- 0.9918`. The other records fail or have inconclusive
  artifact/support/visual gates and must remain diagnostic.
- The manuscript still says that no CHIME bandwidth survives and that all
  twelve bursts are diagnostic (`sections/results.tex:285-302`), and its
  hand-written table encodes an older campaign (`sections/results.tex:304-334`).
- The compiled summary is DSA-only (`sections/results.tex:243-252`) even
  though the owner has now rejected that concept and requested a joint
  DSA+CHIME summary. The living inventory also describes the included figure
  as DSA-only (`docs/rse/specs/notes/figure-wishlist.md:19-28`).
- Exact-byte owner approval is mandatory. A new candidate cannot be promoted
  or included by an agent: `figure_review/README.md` requires a candidate PR,
  explicit owner decision, and a separate promotion PR. Therefore the current
  rejected inclusion must become a placeholder while a new joint candidate is
  reviewed.
- A scientifically honest joint summary is reproducible from committed,
  pinned JSON: the qualified DSA FRB 20220506D validation record and the
  qualified CHIME FRB 20240203A campaign record. These are different bursts,
  so the figure must not connect them with a frequency-scaling law or use them
  for a two-screen inference.

## Synthesis

Pin FLITS at the PR #192 merge commit, derive the manuscript table directly
from its 24 campaign records, and revise the prose to report exactly one
qualified CHIME sightline while preserving the 23 diagnostic-only record
statuses. Remove the rejected DSA-only figure from the compiled manuscript and
replace it with an explicit owner-review placeholder. In a separate
candidate-only change, generate a two-panel summary containing only the
qualified DSA and CHIME measurements. Promotion remains blocked solely on
owner review of those exact bytes.

## References / Sources

- `sections/results.tex:175-334`
- `docs/rse/specs/notes/figure-wishlist.md:19-43`
- `figure_review/README.md:1-55`
- `pipeline/analysis/window-tuning-campaign-2026-07-17/results/validation.json`
- `pipeline/analysis/window-tuning-campaign-2026-07-17/results/chromatica_hi_campaign.json`
- `pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/results/oran_qualified/validation.json`
- [dsa110-FLITS PR #192](https://github.com/jakobtfaber/dsa110-FLITS/pull/192)
