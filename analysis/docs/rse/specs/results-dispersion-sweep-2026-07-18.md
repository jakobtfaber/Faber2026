# Results dispersion sweep — 2026-07-18

Executes the BOARD.md §0 sweep task: inventory of result artifacts across the
repo, worktrees, `~/Data`, iCloud, and h17; classification current/science-ready
vs deprecated/draft, organized per manuscript section; quarantine **proposal**
(nothing moved — owner approval required). Registry updated in the same pass:
`section` field added to all 24 rows; Figure-1 generator resolved from
`figure_review/slots.json`.

## Locations swept

| Location | State |
|---|---|
| Repo `figures/`, root tables, `outputs/` | inventoried below |
| Repo git worktrees (9 registered) | 5 branches carry unmerged commits — disposition list below |
| `~/Developer/scratch/worktrees/` | Faber2026 + FLITS quarantine/readiness/scint worktrees (2026-07-17) + unrelated gpu-ffa set |
| `~/Data/Faber2026/` | `dsa110/` (burst products, flits-runs, refit-variants) + **`results-library/`** (see below) |
| iCloud `CHIME_DSA_Codetections/` | burst npys/pickles, waterfalls, dm_budget, scattering_results, archive — external store, not git |
| h17 (ssh ok) | `FABER2026-SCINT-HANDOFF.md` at `~`, `flits-venv` in scratch; FLITS_RUNS posteriors referenced by results-library as `external` |

## Key finding: `~/Data/Faber2026/results-library/`

A prior, substantially built organization system (generated 2026-07-16 from a
dedicated worktree): per-domain slots (dispersion, foreground, scattering,
scintillation, manuscript), **its own trust-tag vocabulary** (`live`,
`provisional`, `revoked-2026-07-06`, `diagnostic_only`, `external`,
`owner-approved-bytes`, …), materialize-vs-link slot modes with symlinks back
into the repo, and a review ledger. It overlaps the new results registry.

**Proposed division of labor (recommend adopting):** the registry
(`results-registry.toml`) is the *claim-level* canonical (what the manuscript
asserts, trust per claim); results-library remains the *byte-level* store
(artifact bytes, sizes, symlinks, HPC pointers). Registry `artifact` fields
point into the library where it materializes bytes. The library's index is
regenerated after the wf-13 trust overhaul so both speak the current ledger;
its trust vocabulary should be mapped onto the registry's three states
(trusted/revoked/pending) rather than maintained separately.

## Per-section classification (repo artifacts)

**Current / science-ready** (tex-referenced, lane cleared or actively pending):

| Section | Artifact | Note |
|---|---|---|
| §2 | `codetection_data_grid.*` (Jul 17) | fig1 candidate — bytes await hash-bound approval (pending) |
| §2.2 | `dm_measurements_table.tex` (Jul 15) | trusted |
| §2.4 | `ne2025_mw_characterization_nside32.*` (Jul 8) | trusted |
| §2.5 | `foreground_table.tex` (Jul 15), `sightline_halo_grid.*` (Jul 17) | trusted |
| §3.1/§4.1 | `sample_table.tex` (Jul 12), `association_summary.pdf`, `association_cards/` (Jul 8), `toa_offset_decomposition.pdf` (**Jul 18 — concurrent session**) | trusted |
| §4.2 | `budget_table.tex` (Jul 17), `dm_host_posteriors.*` (Jul 17) | trusted / priors pending (wf-07) |
| §4.3 | `chime_scintillation_campaign_table.tex` (**Jul 18 — concurrent session**), `outputs/scintillation-acf-review/` (**Jul 18**) | active scint-method lane — do not touch |
| App.B | `clusters_icm.*` (Jul 7) | trusted |

**Revoked but tex-referenced** (keep in place until campaign refill; registry
carries them `revoked`): `beta_table.tex`, `twoscreen_provisional_table.tex`,
`dsa_scint_acf/` (12), `jointmodel_pair/` (34), `codetection_triptych/` (36 —
only whitney referenced).

**Deprecated / draft — QUARANTINE PROPOSAL** (unreferenced in compiled tex,
superseded, or diagnostic drafts; move to `figures/archive/` or the
results-library `archive/` slot on owner approval):

1. `figures/codetection_gallery.*` (Jul 10) — superseded by
   `codetection_data_grid` (the locked fig1 product); unreferenced.
2. `figures/dm_subband_tilt.png`, `figures/dm_zoom_discriminate.png` (Jul 15)
   — DM-battery diagnostic drafts; unreferenced.
3. `figures/dsa_lorentzian_summary.{pdf,png}` (Jul 14) — unreferenced summary
   of the revoked DSA ACF lane.
4. `figures/prototypes/` — draft scratch.
5. `codetection_triptych/`: 35 of 36 files unreferenced (only
   `whitney_triptych.pdf` is; the set is wave-1 revoked regardless) —
   archive the unreferenced panels.

## Worktree/branch disposition (owner call per line)

Unmerged commits found on: `ms/quarantine-outdated-science-20260717` (**5
ahead** — quarantine work beyond merged PR #131 not landed?),
`ms/scint-joint-candidate-20260717` (4), `ms/post-pl-pbf-figure-reconciliation-20260717`
(2), `ms/toa-convention-audit-20260717` (1), `ms/remove-superseded-dsa-acf-20260717`
(1). Fully merged, worktrees prunable: `ms/review-prose-20260715`,
`ms/science-gates-g1a-20260715`. The detached `Faber2026-readiness-20260717`
worktree and the unrelated `gpu-ffa-*` set are outside manuscript scope.

## Registry VERIFY resolutions this pass

- `sample.gallery_fig1.producing_script` = `scripts/plot_codetection_data_grid.py`
  (from `figure_review/slots.json`; slots also define required provenance per
  figure — the registry population should mirror those fields).
- `figure_review/slots.json` names generators for the association summary
  (`scripts/plot_association_summary.py`) — fold into the cards row at next edit.
- h17 access confirmed; `FLITS_RUNS` joint-fit posteriors are the `external`
  slot the library already tracks.

## Still open after this sweep

Per-row md5s + pipeline pins (needs per-artifact regeneration receipts —
tier-2 gate build will mechanize); external-source query dates (census DR9/
DESI/NED/PS1-STRM — in FLITS provenance docs, pull at next population pass);
the five unmerged-branch dispositions above; owner approval of the quarantine
list; registry↔results-library integration decision.
