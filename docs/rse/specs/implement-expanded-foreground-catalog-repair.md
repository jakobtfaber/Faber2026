# Implementation state: expanded foreground catalog repair

**Status:** calculation-complete; scientific promotion blocked.

## Completed

- Deterministic 3-arcsecond nearest-neighbor matching with identifier tie-break,
  explicit ambiguity, unmatched, and query-error states.
- Normalized, hash-pinned GSC 2.4.2, ALLWISE, CatWISE2020, and unWISE responses.
- Native quality flags, magnitude or flux errors, propagated W1-W2 errors, and
  explicit unavailable-uncertainty states.
- Corrected Moster inversion tolerance, `M200c` to Planck18 `R200c`, published
  Dutton–Macciò `h=0.671`, Cluver Equation 2 label and rest-frame gate, and
  Stern depth gate.
- Rebuilt 52-row catalog and 37-row Figure 3 input.
- Regenerated Figure 3 in review staging. Installed manuscript bytes unchanged.
- Independent calculation path: zero mismatches across 208 catalog responses,
  25 finite halo calculations, classifications, manifests, and Figure 3 input.

## Blocking gates

1. Freeze source-bearing evidence for all 12 host-redshift roster entries.
   Existing frozen values lack the required citation, measurement, row, release,
   retrieval, and hash fields. Three hosts have no redshift.
2. Repeat the source-level redshift and verdict validation.
3. Obtain manuscript-owner visual approval for staged Figure 3.
4. Promote the approved bytes, compile, and rerun the release gate.

No foreground redshift, candidate verdict, budget eligibility, or installed
manuscript figure was changed in this lane.
