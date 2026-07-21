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

## Route

1. [Fail-close the invalid validation](tickets/expanded-foreground-catalog-repair-01-fail-close-validation.md)
   — remove the current Ready/Verified state before any repair is interpreted as
   accepted science.
2. [Set the crossmatch and quality contract](tickets/expanded-foreground-catalog-repair-02-set-crossmatch-contract.md)
   — require nearest-match selection, ambiguity accounting, catalog-native flags,
   and query-error visibility.
3. [Independently verify redshifts and verdicts](tickets/expanded-foreground-catalog-repair-06-verify-redshift-verdicts.md)
   — check each adopted host/candidate redshift, uncertainty, classification,
   verdict, and budget flag against its cited evidence and the census rules.
4. [Set the mass and radius authority](tickets/expanded-foreground-catalog-repair-03-set-physics-authority.md)
   — separate descriptive photometry from adopted stellar masses, halo masses,
   cluster masses, and the critical-density radius convention.
5. [Set the Figure 3 regeneration gate](tickets/expanded-foreground-catalog-repair-04-set-figure-3-gate.md)
   — replace the external input with a versioned derivative and stage, review,
   then promote exact bytes.
6. [Set the independent release gate](tickets/expanded-foreground-catalog-repair-05-set-independent-validation-gate.md)
   — require a second implementation path and evidence that does not reuse the
   builder's result columns.

## Decisions already fixed by evidence

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

## Out of scope

- Changing foreground redshifts or budget eligibility without a separate,
  evidence-backed adjudication record. Independent verification is required here.
- Treating GSC `Class 3` (non-star) as a secure galaxy classification.
- Replacing adjudicated stellar masses solely because new WISE photometry exists.
- Promoting Figure 3 without manuscript-owner approval.
