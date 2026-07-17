# Checklist — supersession sweep when the CHIME 2L estimator finalization lands

Owner directive 2026-07-17: when the estimator-finalization PR merges into
dsa110-FLITS (official campaign rerun through the enforced off-purity gate
`eb61267` + config-path `grid_regularization`, with the injection harness and
`window_campaign_2L` table committed), the repo carries presentational and
canonical surfaces that become **not-current** and must be confirmed, updated,
or banner-marked superseded. This list is the sweep contract; execute it in the
same lane as the manuscript rewrite.

Trigger: FLITS finalization PR merged + Faber2026 pin bump to (or past) it.

## Execution status (2026-07-17)

| Item | Status | Resolution |
|---|---|---|
| 1 | completed | Results, Discussion, and the generated CHIME gate table now report the one qualified `chromatica_hi` record and 23 diagnostic records. |
| 2 | completed | All twelve ledger strands point at PR #192 evidence; Chromatica is trusted, Freya preserves its historical negative result plus the final diagnostic outcome, and Hamilton is explicitly unphysical-suspect. Generated views were refreshed. |
| 3 | validated; promotion pending | The DSA-only figure is removed from compiled TeX and replaced by a joint-summary placeholder. A candidate-only PR is required before exact-byte owner approval and later promotion. |
| 3b | diagnosed; stale panels removed | The six July-7 DSA-only ACF floats are no longer compiled. PR #192 supplies 24 hash-reviewed CHIME ACF renders but no matching post-finalization DSA rerun, so honest joint replacements are blocked on new DSA products plus exact-byte owner approval. |
| 4 | completed | The DSA catalog remains explicitly provisional; Results now says Oran is the only certified DSA-band point, not the sole certified scintillation result in the sample. |
| 5 | completed | `outputs/scintillation-acf-review/index.html` carries a fixed SUPERSEDED banner pointing to the final campaign. The packet bytes otherwise remain archival. |
| 6 | completed | The technical-review triage has a dated status note replacing the stale S16/S17 current-state framing. |
| 7 | completed | The referee matrix marks scintillation partially completed while keeping the remaining scattering/two-screen/turbulence/energy gates blocked. |
| 8 | completed | The parent catalog indexes the final campaign, and dsa110-FLITS PR #199 merged as `8f5f06a4` with the in-submodule Results Library pointer. The manuscript intentionally retains the reviewed science pin `17d9d266`. |
| 9 | decision pending | Do not rebake or deploy a joint-summary deck before exact-byte figure approval. The compiled manuscript intentionally retains a placeholder. |
| 10 | decision pending | `stash@{0}` was inspected read-only and contains the pre-2L board/output lane. It was not popped or dropped; owner sign-off is required for destructive stash disposition. |

## Must update (canonical / compiled surfaces)

1. **Manuscript prose** — `sections/results.tex` L177, L212, L285–302,
   `tab:chime_scint_gates` (L304–334); `sections/discussion.tex` L52–62. The
   compiled "no CHIME-band decorrelation bandwidth survives / all twelve
   demoted" conclusion is contradicted by the validated rerun (detection triad
   zach / chromatica / freya; hamilton unphysical-suspect; whitney not clean).
2. **Evidence ledger** — `docs/rse/evidence-ledger.toml`: all twelve
   `scintillation_chime` strands currently record `unavailable` / "campaign
   OPEN per the 2026-07-15 owner amendment". Update zach/chromatica/freya to
   the earned status from the official rerun (with commit pin), annotate
   hamilton as suspect, leave true non-detections explicit. Regenerate views
   (`python3 scripts/sync_state.py`) — the drift gate blocks the PR otherwise.
3. **Scint summary figure** — `figures/dsa_lorentzian_summary.pdf` /
   `fig:dsa_scint_gamma` (results.tex L243–252): owner ruling 2026-07-17
   (recorded in the fig1-model-toa batch manifest) — replace with a joint
   DSA+CHIME measurement figure; never resubmit DSA-only. Owner ruling
   2026-07-17 (chat): this figure — **compiled figure 7** — must not remain
   in the manuscript; replacement is mandatory, not optional.
3b. **Compiled figures 11–16 — superseded item, updated post-#124.** The six
   DSA-only ACF grids (`sections/dsa_scint_acf.tex`) were removed from the
   appendix by PR #124 (provenance note retained in `appendix.tex`; the
   source file is kept but no longer input). Compiled figures 11–16 are now
   the six `figure*` envs of `sections/jointmodel_pairs.tex` (twelve
   per-burst `figures/jointmodel_pair/<nick>_jointmodel_pair.pdf` panels).
   Owner ruling 2026-07-17 (chat): these joint time–frequency model fits are
   ALSO outdated — they predate the approved PL-PBF kernel change — and must
   be replaced with post-PL-PBF production refit panels once the
   joint-tf-fits refit campaign lands. Any DSA+CHIME ACF appendix
   replacement additionally stays blocked on the post-finalization DSA rerun
   per the #124 provenance note.
3c. **Compiled figure 2** — `fig:codetection-triptych-whitney`
   (`scripts/plot_codetection_triptych.py`). Owner ruling 2026-07-17 (chat):
   same PL-PBF supersession — its joint-fit content is pre-PL-PBF and the
   figure must be regenerated at the refit pin (the joint-tf-fits lane was
   already editing the producer when the ruling landed).
4. **`dsa_scint_provisional_table.tex`** — frozen 2026-07-07 DSA Lorentzian
   catalog (only oran certified). DSA side is not superseded by the CHIME 2L
   work itself, but the caption's "sole certified measurement in the sample"
   framing is; re-caption at minimum, regenerate if the DSA roster changes.

## Must banner / annotate (presentational surfaces)

5. **`outputs/scintillation-acf-review/`** — 2026-07-13 review packet
   (slides + `index.html`). Contains `freya_chime_instrumental_origin.png`:
   the freya-CHIME-is-instrumental conclusion is overturned by the 2L
   resurrection. Keep as archive; add a SUPERSEDED banner to `index.html`
   pointing at the finalized campaign results.
6. **`docs/technical_review_triage_2026-07-15.md`** — S-items premised on
   "no certified Δν_d" (e.g. S17 positive-control framing, the m ≤ 1.5 gate
   discussion citing six-of-twelve CHIME rejections). Append status notes;
   do not rewrite history.
7. **`docs/referee_response_status_2026-07-09.md`** — SCI row marks the
   scint/turbulence sections BLOCKED on "running that campaign"; the campaign
   has now partially run. Update the status wording.
8. **`pipeline` `analysis/RESULTS_LIBRARY.md`** — add the finalized campaign
   entry; mark the 2026-07-07 DSA Lorentzian entry with its vintage relative
   to the rerun.
9. **Board decks / gh-pages** — fit-input and ACF decks deployed pre-rerun;
   rebake + redeploy after the new ladder figures exist.

10. **Parked stash lane** — main-checkout `stash@{0}` "board-strand-redesign +
   scint-acf outputs lane (parked on main-switch 2026-07-13)" holds pre-2L
   scint-ACF output edits. Adjudicate at sweep time: extract anything still
   wanted, else drop with the owner's sign-off; never pop over main.

## Explicitly archival — do NOT edit

Dated experiment/handoff/plan specs under `docs/rse/specs/` (e.g.
`experiment-freya-chime-instrumental-origin.md`,
`report-chime-scintillation-inventory-2026-07-14.md`, the chime-scint
experiment series): timestamped lane records. History, not current claims.

## Already adjudicated (no action)

- `figure_review/batches/2026-07-17-fig1-model-toa/` — rejected wholesale,
  hash-bound decisions in its manifest (fig6/oran concept rulings included).
- `sections/appendix.tex` oran qualified-scintillation figure — removed
  (PR #116) with its ledger consumer retired.
