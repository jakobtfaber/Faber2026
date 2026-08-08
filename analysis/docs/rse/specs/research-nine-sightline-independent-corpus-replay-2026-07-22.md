# Independent replay: frozen nine-sightline catalog corpora

Date: 2026-07-22

Disposition: **pass; corpus and production-registry semantics independently replay**

The separate Python/Astropy/NumPy replay in
[`replay_frozen_nine_sightline_corpora.py`](../../../scripts/replay_frozen_nine_sightline_corpora.py)
does not import either producer. Its frozen result is
[`replay.json`](evidence/nine-sightline-independent-replay-2026-07-22/replay.json).

## Reproduced evidence

- Anonymous corpus: all 618 archive members, 135 cells, 115,713 exact-cone
  rows, 1,516 separate guard rows, and terminal states of 37 matched, 31
  unmatched, and 67 outside-footprint cells. Every referenced byte hash,
  pagination state, normalized row count, and unrounded 15-arcminute boundary
  passes.
- Coverage: all 36 DR9, XMM-Newton, Chandra, and Swift exposure-aware cells
  replay from frozen native evidence. DR9 and Swift use independent FITS/WCS
  positive-pixel calculations; Chandra uses the complete count-bound ObsCore
  table and spherical polygon/cone intersections; XMM uses the complete
  intersect-query response. Every inside/outside state and evidence count
  reproduces.
- Protected MAST corpus: all nine SQL and CSV hashes, 26,540 raw rows, 20,788
  exact-cone rows, 5,752 rectangle-only rows, all 210 native columns, and all
  242 WISE identifiers shared by multiple optical objects. The replay derives
  those groups from raw rows and confirms every group remains ambiguous.
- CADC/CFIS: query, response, and VOSpace handshake hashes pass. The frozen
  authenticated result remains `access_denied`, never `unmatched`.

## Roster agreement

Both corpora contain Casey, Chromatica, Hamilton, Isha, JohndoeII, Oran,
Phineas, Whitney, and Zach. The anonymous normalized key `johndoeii` case-folds
to the protected/Verdi display label `johndoeII`. The replay records this case
alias explicitly and reports no identity conflict. No scientific authority
field changed.

## Production-registry replay

The separate replay pins pipeline commit
`f3c8d22a9088914e0179cfecf1ee4086777dc927`. All 52 candidate-provenance
identities match all 52 registry objects. The 49 rows with finite host redshift
reproduce every stored verdict and budget flag; all seven duplicate
separations reproduce. Wilhelm remains a real foreground object but its host
redshift is blank, so it is outside finite-host arithmetic. JohndoeII has no
selected foreground candidate. Registry objects are candidates, not one slot
per search sightline; literal roster equality would be the wrong invariant.

## Commands

```bash
python3 scripts/replay_frozen_nine_sightline_corpora.py \
  --output docs/rse/specs/evidence/nine-sightline-independent-replay-2026-07-22/replay.json
pytest -q tests/test_replay_frozen_nine_sightline_corpora.py
```

The replay exits zero with no errors after all
corpus byte, coordinate geometry, state, SQL-bound, rectangle-containment,
ambiguity, stored-verdict, budget, and duplicate checks pass.
