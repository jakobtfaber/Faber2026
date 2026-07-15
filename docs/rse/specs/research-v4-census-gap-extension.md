# Research: V4 census-gap extension

**Date:** 2026-07-15
**Scope:** internal codebase and captured catalog provenance
**Codebase state:** Faber2026 `ca31149`; dsa110-FLITS `4e951c8`

## Question / Scope

Determine how to promote three discovery-stage systems that were omitted from
the frozen 49-row validation registry without changing the adopted
intervening-DM model. The systems are WISEA J044538.83+701843.3 toward
FRB 20221113A, WISEA J211150.32+724807.8 toward FRB 20220506D, and
WHL J115048.0+714428 toward FRB 20230307A.

## Codebase Findings

- The registry builder currently emits only rows present in the frozen
  `foreground_final.csv`, `foreground.csv`, and `foreground_validated.csv`
  triplet. Missing source files cause a direct fallback to the checked-in
  registry, so discovery-only systems cannot enter either path
  (`pipeline/galaxies/foreground/census_registry.py:85-163`).
- Budget eligibility is stricter than registry membership. Inconclusive rows
  never enter the budget; confirmed clusters enter only when a finite
  `b/R500 <= 1` is available (`pipeline/galaxies/foreground/census_registry.py:76-82`).
  Therefore the two weak-redshift galaxies and the WHL12 cluster can be
  represented without changing Table 4.
- The foreground table is generated from structured JSON, while a parity test
  ties its registry-resident object IDs and verdicts back to the committed CSV
  (`pipeline/galaxies/foreground/foreground_table_emitter.py:1-18`,
  `pipeline/galaxies/foreground/test_foreground_table_emitter.py:40-90`).
- The manuscript currently says the validation handoff evaluated 35 catalog
  candidates (28 physical systems) and that FRB 20221113A has no surviving
  candidate (`sections/observations.tex:298-314`; generated table comment in
  `pipeline/galaxies/foreground/foreground_table_emitter.py:65-67`). Those
  statements become false once the extension is represented.
- The adopted cluster model requires Wen & Han (2024) `M500` and `R500`.
  WHL J115048.0+714428 has a captured WHL12 identity/redshift but no values in
  the adopted source, so treating its BCG stellar mass as an isolated-galaxy
  SHMR input would be physically invalid. Appendix B is the appropriate place
  to disclose this unmodeled cluster-scale systematic
  (`sections/appendix.tex:33-68`).

## Captured provenance

- The earlier discovery output records WISEA J044538.83+701843.3 at
  RA=71.411807 deg, Dec=70.312048 deg, discovery `z=0.0474889`, and
  `b=16.1795 kpc`. Its GLADE distance flag does not satisfy the frozen
  validation hierarchy; verdict: inconclusive.
- The continuation handoff records WISEA J211150.32+724807.8 at approximately
  `b=208 kpc`. Its only redshift is a low-quality WISExSCOS-grade photo-z and
  its PS1 colour is outside the adopted Taylor calibration; verdict:
  inconclusive.
- The earlier discovery output records WHL J115048.0+714428 at
  RA=177.69998 deg, Dec=71.74124 deg, `z=0.1893`, and `b=613.99 kpc`.
  It is a WHL12 cluster absent from the adopted Wen & Han (2024) registry;
  verdict: confirmed catalogued cluster, budget-ineligible because its adopted
  `M500`, `R500`, and hence `b/R500` are unavailable.
- A live NED query was attempted on 2026-07-15 through `astroquery` and timed
  out after 60 seconds. No verdict is upgraded on the basis of that failed
  handshake.

## Synthesis

The narrow fix is an append-only adjudication layer loaded by the registry
builder after the frozen census. It should contain the three rows, preserve
their captured provenance, assert unique stable keys, and derive
`budget_eligible` through the existing gate. The generated table and manuscript
counts then update, while Table 4 remains byte-identical. No richness-to-mass
relation should be introduced in this change.

## References / Sources

- `pipeline/galaxies/foreground/census_registry.py`
- `pipeline/galaxies/foreground/foreground_table_emitter.py`
- `pipeline/galaxies/foreground/test_census_registry.py`
- `pipeline/galaxies/foreground/test_foreground_table_emitter.py`
- `sections/observations.tex`
- `sections/appendix.tex`

