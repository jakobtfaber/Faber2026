<!-- wayfinder:map -->
# Map: Repair and independently validate the expanded foreground catalog

Tickets live in [`tickets/`](tickets/). This map plans the route. It does not
authorize scientific adoption or Figure 3 promotion.

## Destination

The expanded catalog is a reproducible audit product: deterministic catalog
matches, explicit quality and error fields, correct mass and radius conventions,
and independently checked census redshifts and verdicts. Figure 3 consumes a
versioned derivative of that authority and reaches the manuscript only after
independent numerical, provenance, and owner visual checks.

## Notes

- **Standing delegation (owner, 2026-07-20):** [delegated decision authority](standing-delegation-2026-07-20.md)
  covers only tickets recorded open at `main` commit `33e9e1ce3570`; it permits
  evidence-backed recommendations without per-ticket approval but does not
  close tickets or waive independent validation, owner visual review, Figure 3
  promotion, trust-promotion, or redshift/budget re-adjudication gates.
- `intervening_census_registry.csv` remains the classification and budget
  authority. Crossmatches may flag conflicts; they may not silently change a
  verdict.
- Query states are `matched`, `unmatched`, `outside_footprint`,
  `ambiguous`, `access_denied`, or `query_error`. Missing coverage, denied
  access, and failed queries are different states.
- Cluver et al. (2014) coefficients `-2.54, -0.17` are the resolved-source
  relation, Equation 1, for rest-frame color. No colorless fallback is allowed.
- Moster et al. (2013) uses redshift-dependent Table 1 parameters and accepts
  stellar mass in solar masses. Every interface names linear versus logarithmic
  units.
- The reported halo radius is `R200c`: mean enclosed density 200 times the
  critical density. Concentration is not needed to compute it.
- Dutton and Macciò (2014) concentration uses its published redshift evolution
  and mass in units of `10^12 h^-1 M_sun` when a scale radius is requested.
- Stern et al. (2012) yields a luminous active-galaxy selection only within
  `W2 <= 15.05` Vega. A blue color does not prove starlight dominance.
- Cluster rows do not pass through a galaxy stellar-mass relation.

## Decisions so far

- [Fail-close the invalid expanded-catalog validation](tickets/expanded-foreground-catalog-repair-01-fail-close-validation.md)
  — the superseded validation is explicitly failed, its defects are
  machine-readable, and the gate exits nonzero until a rebuilt catalog and
  independent report pass.
- [Set the catalog crossmatch and quality contract](tickets/expanded-foreground-catalog-repair-02-set-crossmatch-contract.md)
  — accepted the deterministic nearest-match, ambiguity, query-state, frozen
  snapshot, provenance, error, and catalog-native quality contract already
  merged in dsa110-FLITS PR #213 and reverified on current pipeline
  `origin/main` at `f3c8d22a9088`.
- [Set the stellar-mass, halo-mass, and radius authority](tickets/expanded-foreground-catalog-repair-03-set-physics-authority.md)
  — after the crossmatch ticket resolved, accepted the census-mass authority,
  redshift-dependent Moster `M200c`, critical-density `R200c`, conditional
  diagnostic Cluver value, explicit-null uncertainty, and cluster `M500/R500`
  boundaries already merged in the same pipeline pull request.
- [Independently verify foreground redshifts and verdicts](tickets/expanded-foreground-catalog-repair-06-verify-redshift-verdicts.md)
  — all stored verdict and budget arithmetic reproduces, but 0/52 rows has a
  complete host-plus-candidate source chain; retain the legacy adjudications and
  keep Figure 3 blocked pending frozen provenance and independent replay.
- [Restore the repository knowledge-base launcher](tickets/expanded-foreground-catalog-repair-10-restore-knowledge-base-launcher.md)
  — restored the package and tests deleted by an Overleaf sync; indexing and
  live full-text retrieval work again without changing source or ranking rules.
- [Freeze candidate-redshift source evidence](tickets/expanded-foreground-catalog-repair-08-freeze-candidate-redshift-provenance.md)
  — froze a 52-row candidate provenance ledger with stable source identifiers
  and SHA-256 hashes for all 46 adopted candidate redshifts; verdicts and budget
  flags are preserved, and Figure 3 remains governed by the later independent
  replay and owner-review gates.
- [Resolve Zach's inter-catalog redshift discrepancy](tickets/expanded-foreground-catalog-repair-11-resolve-zach-intercatalog-redshift.md)
  — the authenticated row confirms the low value is extrapolated `z_phot0`
  from a PS1 object sharing its WISE source with a closer QSO-classified PS1
  neighbor; retain both STRM estimates pending separate adjudication.
- [Expand and independently replay catalog coverage for nine host-redshift sightlines](tickets/expanded-foreground-catalog-repair-12-expand-nine-sightline-catalogs.md)
  — stored verdicts, budget flags, and duplicate separations replay, but the
  original search aperture and required expanded-survey corpus are absent; keep
  authority closed and continue through the explicit contract, corpus,
  protected-export, and independent-replay tickets.
- [Set the nine-sightline search-region and candidate-selection contract](tickets/expanded-foreground-catalog-repair-13-set-nine-sightline-search-contract.md)
  — use frozen burst centers, a fully paginated 15-arcminute galaxy cone, a
  separate 5 proper Mpc cluster search under Planck18, geometry-first candidate
  admission, catalog-native `R500` for the budget gate, preserved raw query
  evidence, and fail-closed classification, identity, ambiguity, duplicate, and
  redshiftless-cluster rules. This is a new audit contract, not the historical
  aperture.
- [Freeze authoritative host-redshift evidence](tickets/expanded-foreground-catalog-repair-07-freeze-host-redshift-provenance.md)
  — the supplied Verdi archive is hash-frozen as a minimal comparison, but its
  two drafts conflict, two sightlines are absent, four identifiers differ, and
  every row lacks a host identifier and row-level uncertainty. Authority stayed
  closed until the later owner decision named the current table.
- [Obtain the authoritative host-redshift ledger](tickets/expanded-foreground-catalog-repair-17-obtain-authoritative-host-redshift-ledger.md)
  — the manuscript owner approves the current `verdi2025.tex` table entries as
  authoritative; the older `test.tex` is superseded, blank cells remain blank,
  and absent Zach and Whitney rows continue through a separate source ticket.
- [Source the Zach and Whitney host redshifts](tickets/expanded-foreground-catalog-repair-18-source-zach-whitney-host-redshifts.md)
  — Law et al. (2024) Table 2 identifies the two hosts and Table 3 gives
  spectroscopic redshifts `0.043040` and `0.477958`; exact source extracts and
  hashes are frozen, with row-level uncertainty explicitly unavailable. Census
  adoption remains with the later adjudication ticket.
- [Freeze the anonymous nine-sightline query corpus](tickets/expanded-foreground-catalog-repair-14-freeze-anonymous-nine-sightline-query-corpus.md)
  — resolved after independent review. Exact admission contains 109,117
  records; 1,474 guard-only rows are separate. Official Legacy Survey, XMM,
  Chandra, and Swift coverage evidence is frozen and replays with zero errors.
- [Freeze protected query evidence](tickets/expanded-foreground-catalog-repair-15-freeze-protected-nine-sightline-query-evidence.md)
  — froze nine authenticated uncapped WISE--PS1--STRM responses, 20,788 exact
  cone rows, every shared-WISE ambiguity, exact queries and job metadata, and a
  current authenticated CADC `access_denied` receipt for CFIS. Credentials and
  scientific authority fields are absent from the evidence.

## Open route

The map remains open. Remaining strict dependency order:

Tickets 14 and 15 are resolved. Next:

1. [Independently replay both corpora](tickets/expanded-foreground-catalog-repair-16-independently-replay-nine-sightline-query-corpus.md).
2. After independent replay and the now-resolved host-source ticket,
   [repeat source-level redshift verification](tickets/expanded-foreground-catalog-repair-09-repeat-redshift-source-verification.md).
3. After ticket 09 and the now-resolved physics-authority ticket,
   [set the Figure 3 regeneration and promotion gate](tickets/expanded-foreground-catalog-repair-04-set-figure-3-gate.md).
4. Only after the Figure 3 gate resolves,
   [set the independent validation and release gate](tickets/expanded-foreground-catalog-repair-05-set-independent-validation-gate.md).

## Out of scope

- Changing foreground redshifts or budget eligibility without a separate,
  evidence-backed adjudication record. Independent verification is required here.
- Treating GSC `Class 3` (non-star) as a secure galaxy classification.
- Replacing adjudicated stellar masses solely because new WISE photometry exists.
- Promoting Figure 3 without manuscript-owner approval.
