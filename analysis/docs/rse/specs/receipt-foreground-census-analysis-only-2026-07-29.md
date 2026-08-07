# Receipt: analysis-only foreground census validation and Figure 3 review binding

- Date: 2026-07-29
- Issue: Faber2026 #206, foreground catalog validation and Figure 3 approval
- Objective: replace the stale, failed expanded-foreground release gate with an
  independent validation that reads only `analysis/`, and bind manuscript-owner
  review to the exact Figure 3 bytes the manuscript installs.
- Phase: verification and replacement. No promotion, no retirement of data, no
  submodule pointer change, no commit, no push.
- Status: **VERIFIED** for the validation work. Figure 3 remains unapproved;
  that is an owner decision, not a verification result.

## Source snapshot

| Item | Value |
|---|---|
| Manuscript (`Faber2026`) | `d4eebe4f87d0c99a432539912704383f1c5b0708`, branch `main` |
| `analysis` submodule | `a762ece30da414e1dacf72c730bcc2cc5a08c5c5`, branch `main` |
| `analysis` working tree | dirty; a concurrent worker is mid-reorganisation (see below) |
| Installed Figure 3 | `figures/sightline_halo_grid.pdf`, SHA-256 `281e4bf4c9d910c070cb822195a743920a7ecf14e249c924521e359a9d788a75` |
| Verification time | 2026-07-29 |

Every hash recorded here was computed from bytes on disk, not inferred from a
commit, because the working tree is shared and dirty.

### Concurrent work not touched

Another worker is moving `galaxies/foreground/` into
`foregrounds/{census,propagation,visualization,tests}/` and `figure_review/`
into `figure_review/{artifacts,decisions}/`, across roughly 420 paths. None of
those renames were reverted, re-staged, or duplicated. The work recorded here
sits on top of that layout.

## Why the previous gate was stale

`docs/rse/specs/validation-expanded-foreground-independent-release-gate.json`
declared every replay against the `dsa110-FLITS` repository at pipeline commit
`99e60c3a`, reached through a `pipeline/` git submodule. That submodule no
longer exists: `.gitmodules` records `analysis/` as the only submodule, and
there is no `pipeline/` directory. The gate additionally bound

- a parent commit `bbda8025` that `main` has long passed,
- an installed Figure 3 SHA-256 `cd719ef2…` that the manuscript no longer
  carries (pull request #282 rebuilt the figure), and
- a review batch path that the ongoing reorganisation has moved.

The practical consequence was worse than a failing gate: running the validator
raised `FileNotFoundError` and exited before evaluating anything. A gate that
raises reads as a broken tool rather than a refused release.

**Retirement changed the provenance binding, not the science.** The four
registry-replay input files the gate pinned reproduce byte-for-byte from
`analysis/` alone:

| File | SHA-256 |
|---|---|
| `foregrounds/census/data/intervening_census_registry.csv` | `96bfd32302b00df943ba998ba3bf6557f3d8c06d882079cad1a5c9846d47d06a` |
| `foregrounds/census/data/census_masses/census_duplicates.csv` | `336e4023dbf046762477c724e57365c29a3ecabb982f6978e635fb0d05d47e45` |
| `foregrounds/census/data/candidate_redshift_provenance.csv` | `0a2ba35f3dd7dfdcc855d4d589e062c08e5788e135970802cb7b7b798c47afe7` |
| `foregrounds/census/data/frozen_census/ps1_strm_resolution.csv` | `18947acafc02b9781c4ac9612b9570d02eedd46c0115c9f73b5f3d79ec2c354e` |

A test asserts this equality, so the claim is re-checkable rather than asserted
once.

## What replaced it

`scripts/validate_foreground_census_analysis_only.py` — six checks, all reading
only `analysis/`. The validator recomputes derived quantities from committed
source columns rather than echoing stored values back.

| Check | What it establishes |
|---|---|
| `sourced_redshifts` | All 12 host redshifts trace to the frozen Verdi and Law host-redshift extracts, 9 rows and 3 rows respectively, joined on the source event designation rather than the transient name, because three events were renamed after publication. All 46 adopted candidate redshifts carry a frozen source row with a source identifier, a row hash, and a query-response hash, and none was adopted from a record that states no catalog redshift exists. |
| `hostless_fail_closed` | The 6 redshiftless candidate rows are never confirmed, never budget-eligible, never promoted to the census tier, and each carries a provenance record saying why. The 3 sightlines without an established host redshift (`freya`, `mahi`, `wilhelm`) carry no point-estimate redshift, are labelled diagnostic-only in the coverage table, and draw no foreground system. Where a system's geometry is flagged, the stated reason is checked against the data rather than trusted. |
| `deterministic_matching` | The committed Figure 3 input rebuilds byte-identically from its committed sources across two consecutive builds. All 7 cross-listing deduplications reproduce from the coordinates by great-circle separation and carry written evidence; no duplicate survives into the figure and no canonical member was dropped. 192 catalog cross-matches were audited: each records a separation, a candidate count, a response snapshot hash, and a retrieval time; every multi-candidate match records the runner-up separation and adopted the nearer source; every ambiguous match shows at least two candidates. |
| `survey_coverage` | 12 sightlines × 5 surveys = 60 coverage rows, no duplicates, no gaps. Each row's sexagesimal coordinates reproduce the burst roster's decimal degrees to better than one part in a million. Both survey footprint files hash as recorded; the remaining coverage claims declare an all-sky contract or an unavailable footprint rather than implying a footprint they do not have. |
| `mass_radius_conventions` | Halos use `M200c` from the abundance-matching relation the catalog records as `Moster13_Table1_redshift_dependent`, with `R200c` defined at 200 times the critical density under Planck18; clusters use catalog `M500` and `R500` and are explicitly marked as outside the halo convention. All 25 halos with a mass and radius have their radius independently recomputed from their mass and redshift, agreeing to better than 0.1 per cent. No row carries both conventions, and no drawn row uses an undeclared radius definition. |
| `census_matches_figure3` | The census input carries 12 host rows matching the burst roster in name, position, and redshift. All 24 drawn systems are confirmed non-duplicate census systems with matching type, redshift, and impact parameter, and no confirmed non-duplicate system is missing. Figure 3 regenerates deterministically from the committed input, and its extracted content is identical to the installed manuscript figure. |

Machine-readable receipt:
`docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/validation.json`,
which pins the SHA-256 of all ten census inputs.

## Panel accounting

The census has twelve sightlines; the figure draws nine. Three panels are
omitted because those sightlines have no established host redshift, so neither
the host marker nor the foreground redshift cut can be placed — the plotting
module documents this and the validator now asserts that the omitted set is
exactly `freya`, `mahi`, `wilhelm` and nothing else. Of the 24 census systems,
22 are drawn; the two withheld are `phineas/J114928.5+712526, 1253366` (its
catalog redshift is −0.0001, which is not a foreground redshift) and
`phineas/WHL J115048.0+714428` (no sourced cluster geometry). Both are flagged
in the input rather than silently dropped, and neither is budget-eligible.

## Commands and results

```
python3 scripts/validate_foreground_census_analysis_only.py \
  --output docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/validation.json
# status: passed - all six checks

python3 -m pytest tests/test_validate_foreground_census_analysis_only.py -q
# 43 passed

python3 -m pytest tests/test_expanded_foreground_independent_release_gate.py -q
# 10 passed  (was 7 failed, 3 passed before this work)
```

## Verification method

The validator passing is not by itself evidence — a check that asserts nothing
also passes. Every check is therefore paired with a mutation test that corrupts
one committed input in one specific way and asserts that the matching check
rejects it: a deleted provenance record, a redshift drifted from its source, a
confirmed system with no redshift, a fabricated deduplication separation, a
cross-match that hid its runner-up, a footprint hash that does not match its
file, a halo radius inflated by five per cent, a cluster radius written in
megaparsecs, a dropped sightline panel, a system drawn with no census row. Two
mutations initially failed to trigger a rejection; both were validator gaps, and
both were closed:

1. AllWISE has no multi-candidate matches at all, so the runner-up assertion was
   vacuous for that survey. Ambiguous-match auditing was added and the tests
   moved to unWISE, which does have them.
2. The dropped-panel case was not covered, so a twelfth panel could have gone
   missing behind the diagnostic-only rule. An explicit panel-roster assertion
   was added.

Independent reproduction was used where it was available: two consecutive
builds of the Figure 3 input, two consecutive renders of the figure, and the
recomputation of every halo radius from first principles.

## Figure 3 reproduction

The installed figure is byte-identical to the render the figure workflow
produced and left staged on 2026-07-28:

| Artifact | SHA-256 |
|---|---|
| Installed `figures/sightline_halo_grid.pdf` | `281e4bf4c9d910c070cb822195a743920a7ecf14e249c924521e359a9d788a75` |
| `figure_review/artifacts/staging/fig3_halo_grid/figures/sightline_halo_grid.pdf` | `281e4bf4c9d910c070cb822195a743920a7ecf14e249c924521e359a9d788a75` |

So the manuscript installs exactly what the workflow rendered from the
committed census input. The validator asserts this equality, and a test
confirms that a single tampered byte breaks it.

A fresh render in this session does not reproduce those bytes:

| Artifact | SHA-256 | Renderer |
|---|---|---|
| Installed and staged | `281e4bf4…` | matplotlib 3.10.9 |
| Local render from the committed input | `b1cea618…` | matplotlib 3.10.6 |

The extracted text is identical, only one of the fifty PDF streams differs, and
that difference is confined to text baseline offsets and legend box geometry. A
rasterised comparison at 200 dots per inch differs in 0.79 per cent of pixels,
all of them glyph edges; no data marker, circle, or line moved. This is a
renderer-version difference, not a scientific one. Byte-level re-rendering here
would require matplotlib 3.10.9, which this environment does not have; that
limitation is stated rather than worked around, and the staged-render identity
above makes it immaterial.

## Owner-review binding

`docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/owner-review.json`
binds the review to SHA-256
`281e4bf4c9d910c070cb822195a743920a7ecf14e249c924521e359a9d788a75` — the bytes
the manuscript actually installs — with a rendered preview of those exact bytes
alongside it.

This matters because the retired gate bound approval to candidate
`3dece7e3…` in the `2026-07-26-fig3-no-diamonds` batch. Those are not the bytes
the manuscript now carries, so approving them would not have approved the
published figure.

**The review batch was not created.** `scripts/figure_review.py new-batch`
requires `--pipeline-revision`, which names the retired `dsa110-FLITS`
repository; creating a batch would mean either supplying a dead revision or
changing a shared review surface that other work is currently reorganising.
That change is left to the owner. The record above binds the bytes in the
meantime.

## Changes made

| Path | Change |
|---|---|
| `scripts/validate_foreground_census_analysis_only.py` | new — the analysis-only validation |
| `tests/test_validate_foreground_census_analysis_only.py` | new — 43 tests, mostly mutation tests |
| `docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/validation.json` | new — machine-readable receipt with all input hashes |
| `docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/owner-review.json` | new — hash-bound owner-review record |
| `docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/installed-figure3-preview.png` | new — preview of the exact installed bytes |
| `docs/rse/specs/validation-expanded-foreground-independent-release-gate.json` | retired and superseded; prior status preserved under `retired_state`; nothing promoted |
| `scripts/validate_expanded_foreground_independent_release_gate.py` | reports the supersession instead of raising; a missing declared input now fails closed instead of raising |
| `tests/test_expanded_foreground_independent_release_gate.py` | rewritten as the retirement contract |
| `docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-05-set-independent-validation-gate.md` | current state updated |

Nothing outside `analysis/` was modified. `figures/sightline_halo_grid.pdf` was
read, never written.

## Failures and retries

The first validator run failed on two of its own defects, both fixed: the
module search path did not include the repository root, and the mass and radius
convention check did not exempt rows whose geometry is deliberately withheld.
Two mutation tests then failed for the reasons recorded under verification
above.

## Preliminary, blocked, and stale findings

- **Stale, now corrected:** the retired gate's binding to pipeline `99e60c3a`,
  parent `bbda8025`, and installed Figure 3 `cd719ef2…`.
- **Blocked:** creating the Figure 3 review batch, for the reason above.
- **Noted, not acted on:** `foregrounds/census/data/frozen_census/bursts.csv`
  carries `n_foreground_halo` and `n_foreground_cluster` columns that disagree
  with the census (for example `whitney` records 4 and 3 where the figure draws
  1 system). Nothing reads these columns — no code, no manuscript section — so
  they are dead fields rather than a live inconsistency. Removing them is a data
  change and outside this phase.
- **Noted, not acted on:** the frozen Verdi extract's `mapped_tns` column holds
  the as-published identifiers `FRB 20230325A`, `FRB 20230913A`,
  `FRB 20240203A`, which the corrected roster supersedes. This is correct for a
  frozen source record; the validator joins on `source_event` instead and a test
  fixes that choice.

## Owner approvals

None sought or granted during this work. The one owner decision this leaves
open is the Figure 3 visual approval, bound above to exact bytes.

## Actions still prohibited under this receipt

Promoting Figure 3, declaring the foreground census scientifically trusted,
closing issue #206, committing, pushing, and modifying shared control
registries under `docs/rse/control/`.

## Final disposition

The stale validation is replaced. The census passes an independent,
analysis-only check whose assertions are demonstrated to bite. One gate remains,
and it is the same one the retired gate carried: manuscript-owner visual
approval of Figure 3 — now bound to the bytes the manuscript actually installs
rather than to a superseded candidate.
