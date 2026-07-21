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
- Catalog states are `matched`, `unmatched`, `ambiguous`, or `query_error`.
  Missing data and failed queries are different states.
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

- [Independently verify foreground redshifts and verdicts](tickets/expanded-foreground-catalog-repair-06-verify-redshift-verdicts.md)
  — all stored verdict and budget arithmetic reproduces, but 0/52 rows has a
  complete host-plus-candidate source chain; retain the legacy adjudications and
  keep Figure 3 blocked pending frozen provenance and independent replay.
- [Restore the repository knowledge-base launcher](tickets/expanded-foreground-catalog-repair-10-restore-knowledge-base-launcher.md)
  — restored the package and tests deleted by an Overleaf sync; indexing and
  live full-text retrieval work again without changing source or ranking rules.

## Not yet specified

None. Remaining questions are explicit open child tickets.

## Out of scope

- Changing foreground redshifts or budget eligibility without a separate,
  evidence-backed adjudication record. Independent verification is required here.
- Treating GSC `Class 3` (non-star) as a secure galaxy classification.
- Replacing adjudicated stellar masses solely because new WISE photometry exists.
- Promoting Figure 3 without manuscript-owner approval.
