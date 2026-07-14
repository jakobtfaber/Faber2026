# Handoff: figure review, scientific revalidation, and controlled replacement

**Date:** 2026-07-14  
**Repository:** `jakobtfaber/Faber2026`  
**Status:** figure-approval system completed; replacement-figure review and
scientific revalidation pending  
**Authoritative manuscript base:** `origin/main` at
`ee14f329c0093fa2aeca600aa7d9b045a3984787`  
**Authoritative gate change:** merged PR
[#35](https://github.com/jakobtfaber/Faber2026/pull/35)  
**Rejected comparison packet:** draft PR
[#36](https://github.com/jakobtfaber/Faber2026/pull/36), do not merge  
**Scope:** Figure 1, Figure 5, the scintillation summary and per-burst ACF
figures, the joint-fit and data/model/residual figure families, and the
qualified Oran scintillation visualization

## Executive summary

The July replacement figures must not be treated as accepted. They were
generated from revised DM and fit products, but the manuscript owner has
rejected their presentation and/or correctness as a set. Automated tests and
agent visual inspection were incorrectly allowed to stand in for owner review.
That process failure is now fixed.

Merged PR #35 installs a fail-closed figure gate and removes every disputed
candidate from the compiled manuscript. The current TeX source contains labeled
placeholders for the main-text slots and intentionally empty per-burst appendix
include files. The candidate PDF and PNG bytes remain available for comparison;
they are not compiled and are not approved.

Draft PR #36 freezes all 39 rejected candidates, previews, hashes, DM metadata,
and fit/scintillation provenance in an immutable review packet. Every candidate
in that packet is marked `needs_revision`. Keep this PR open as review history
and do not merge it. Corrected candidates must be rendered into a new batch with
new hashes; do not overwrite or relabel the rejected batch.

No figure should be promoted merely because its adopted DM matches the catalog,
its generator completes, its tests pass, or an agent judges it visually sound.
The required order is:

1. revalidate the scientific inputs and fit interpretation;
2. render an isolated candidate;
3. inspect the candidate by stable ID with its evidence;
4. record an explicit owner decision;
5. promote the exact approved bytes in a separate PR;
6. compile and inspect the resulting manuscript.

## What is authoritative now

| Item | Authoritative state | Meaning |
|---|---|---|
| Manuscript `main` | `ee14f329c0093fa2aeca600aa7d9b045a3984787` | PR #35 is merged; disputed figures are withheld. |
| Figure gate implementation | local commit `af06269d58be86615024226a0d008bc6f606b3a5`, merged by PR #35 | `scripts/figure_review.py`, slot registry, receipts, tests, and TeX placeholders are active. |
| Rejected source revision | `fcc67fba6ce28830ab65677b6ccba91c77c0426a` | PR #34 merged the replacement bytes that the owner subsequently rejected. Preserve for comparison only. |
| Rejected-candidate packet | draft PR #36, branch `review/figure-candidates-20260714`, commit `ba63448d8ed5f3561f2cc52ed9484ab7a1bd85bc` | Immutable record of 39 candidates, all `needs_revision`; never a promotion PR. |
| Pipeline revision used by rejected packet | `67bdd01418f5c4181902b499992746b965c83367` | Provenance anchor for the rejected joint-fit and scintillation products; not proof that their science or presentation is accepted. |
| Adopted-DM catalog in rejected packet | `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv`, SHA-256 `86f631aaedefc6a37571360b718589e864d80c05c7864ac1e4c21661367a11c8` | Frozen input to compare against. The hash does not independently establish that each adopted DM or its use in every figure is correct. |

The current compiled manuscript is intentionally incomplete as a figure
product. That is the correct fail-closed state, not a regression to fix by
blindly restoring old `\includegraphics` commands.

## Strict status

| Work item | Status | Closure condition |
|---|---|---|
| Install an owner-approval gate | **completed** | Merged PR #35; CI rejects unapproved protected inclusions. |
| Remove rejected figures from compilation | **completed** | Current TeX compiles placeholders/empty protected families. |
| Preserve rejected candidates and evidence | **completed** | Draft PR #36 contains the immutable review packet. |
| Decide Figure 1 product/layout | **decision pending** | Owner selects the intended main-text product before further polishing: compact gallery, per-burst triptych design, or a precisely specified alternative. |
| Revalidate adopted DMs and DM application | **pending** | Per-burst catalog values, input-product DMs, re-dedispersion offsets, and rendered labels/windows agree and are scientifically accepted. |
| Revalidate joint fits | **pending** | Each retained fit has correct inputs, DM lock, configuration, component count, residuals, and physical/morphology adjudication. |
| Revalidate scintillation fits | **pending** | Components, exclusions, lag convention, uncertainty convention, diagnostic/qualified status, and overlays are accepted. |
| Approve replacement layouts | **pending** | Owner explicitly approves individual candidates by stable ID. |
| Promote corrected figures | **blocked by the pending decisions above** | Exact approved bytes have receipts, compile successfully, and pass final manuscript visual inspection. |

Do not report the replacement effort as completed while any of the last five
rows remains unresolved.

## Root cause of the failed replacement

Three distinct gates were conflated:

- **Reproducibility:** the generator ran and the output could be traced to
  source products.
- **Scientific validity:** the DM, fit, components, residuals, and
  interpretation were correct.
- **Author acceptance:** the figure showed the intended product in the agreed
  format and was suitable for the paper.

Passing the first gate was treated as evidence for the second and permission
for the third. In addition, two different product families were treated as if
they were interchangeable:

- `joint-*` is the DM-locked joint-model audit family;
- `triptych-*` is the data/model/residual presentation family.

They can share upstream fit artifacts without being the same manuscript
figure. Figure 1 introduced a second ambiguity: the promoted compact
twelve-burst gallery did not resolve whether the agreed design was instead a
per-burst triptych presentation. Resolve that product decision first. Do not
polish both families in parallel and let the rendered result choose the paper's
design by accident.

## Protected figure inventory

Use stable IDs in reviews, notes, commits, and receipts. Do not use only
"Figure 10" or "Figure 22": numbering can change when floats or appendix
families move.

### Main-text and summary slots

| Stable ID | Current target | Required decision |
|---|---|---|
| `fig1-gallery` | `figures/codetection_data_grid.pdf` | Correct adopted DMs and dedispersion; choose the intended gallery/triptych product and layout. |
| `fig5-association` | `figures/association_summary.pdf` | Update all DM-dependent values and labels while preserving association-class semantics. |
| `fig6-scint-summary` | `figures/dsa_lorentzian_summary.pdf` | Approve included components, exclusions, fit convention, flags, and visual format. |
| `oran-qualified-scintillation` | `pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/results/oran_qualified/figures/oran_dsa_calibrated_measurement.png` | Keep numerical qualification separate from approval of the visualization. |

### Per-burst families

The protected families are:

- `dsa-acf-{nick}`: 12 DSA-110 scintillation ACF candidates;
- `joint-{nick}`: 11 DM-locked joint-model audit candidates;
- `triptych-{nick}`: 12 data/model/residual candidates.

The 12-event roster is:

| Nick | Event |
|---|---|
| `zach` | FRB 20220207C |
| `whitney` | FRB 20220310F |
| `oran` | FRB 20220506D |
| `isha` | FRB 20221113A |
| `wilhelm` | FRB 20221203A |
| `phineas` | FRB 20230307A |
| `freya` | FRB 20230325A |
| `johndoeII` / `johndoeii` | FRB 20230814B |
| `hamilton` | FRB 20230913A |
| `mahi` | FRB 20240122A |
| `chromatica` | FRB 20240203A |
| `casey` | FRB 20240229A |

The case difference for FRB 20230814B is real in the slot registry:
`dsa-acf-johndoeII` and `joint-johndoeII` use the uppercase suffix, while
`triptych-johndoeii` is lowercase. Do not normalize candidate IDs casually;
they are review and receipt keys. `chromatica` has ACF and triptych slots but
no `joint-chromatica` slot in the current 11-fit joint roster. Confirm that this
is a scientifically intentional exclusion before finalizing the family.

## Required scientific review

### DM review: Figure 1, Figure 5, joint fits, and triptychs

For each burst, establish all of the following from frozen evidence rather than
from the plotted label alone:

- adopted DM and uncertainty;
- adoption rule and whether the CHIME-primary choice is still intended;
- CHIME measurement and uncertainty;
- DSA measurement and uncertainty;
- input-product DM encoded in each waterfall/product;
- physical re-dedispersion offset applied to each product;
- whether the generator used the adopted DM, an independent-band DM, or a
  residual coordinate;
- time/frequency window after re-dedispersion;
- agreement among the catalog, fit artifact, annotation, caption, and plotted
  data.

Figure 5 needs a fresh end-to-end check because the DM measurements changed.
It is not enough to edit displayed numbers. Recompute or verify every derived
DM difference, uncertainty, category annotation, and any downstream quantity
that depends on those values.

The rejected packet contains a DM table for every relevant candidate and pins
the catalog hash. Use it to identify mismatches, not as automatic validation.
If the adopted catalog itself changes, create a new candidate batch and let its
new catalog hash propagate through every affected candidate and receipt.

### Joint-fit review

For each `joint-*` candidate:

- identify the exact CHIME and DSA input artifacts and hashes;
- verify both input-product DMs and the adopted DM lock;
- verify the actual fit artifact and configuration hash;
- inspect priors, bounds, component count, initialization, convergence, and
  parameter degeneracies;
- inspect residuals separately in each band and confirm the normalization and
  color scale are meaningful;
- distinguish a physically accepted scattering fit from a morphology-only
  audit product;
- reconcile the panel, fit roster, fit adjudication, caption, and manuscript
  claim;
- mark a fit `needs_revision` if its correctness cannot be demonstrated, even
  if the plot looks polished.

The rejected packet freezes these supporting files:

| Evidence | SHA-256 |
|---|---|
| joint render manifest | `0ab236d30ec0c3db450516a86f2147aaa803c49d844e00da9041e6ea5b7e7d19` |
| joint fit roster | `101fa5389692beadd9cf5ce06f0593dea0c43889a0ae0784eadbd7008ad20e40` |
| joint fit adjudication | `7ed91f3eab8f09f9f414254b138ae2baceecb7d92c0f89437760a366eb97877d` |

These are provenance anchors for the rejected batch, not endorsements.

### Scintillation review and format

For each `dsa-acf-*` candidate and the summary:

- verify sub-band edges and center frequencies;
- verify symmetric-lag ACF values, uncertainty construction, masks, and the
  zero/first-lag exclusion convention;
- review all Lorentzian components, including broader components and flags;
- verify narrow-track membership and whether every displayed point is
  diagnostic, qualified, excluded, or upper-limit information;
- verify the width convention and reported interval convention;
- trace PBF/scattering overlays to their source or state explicitly that no
  overlay is used;
- enforce the owner-approved common panel format only after the exact design
  is documented in the new batch or generator change;
- keep the qualified Oran measurement distinct from the broader diagnostic
  sample.

The rejected packet pins the scintillation component catalog at
`cb1686c76250e97d881fa4b9dcad8ace012004e5abdbc31abd444697ea74c16f`,
the fit catalog at
`15ac6736485b5baaa787c605a62bc2372fabf450caf0b8f3d9ef4febdf915346`,
and the Oran qualification JSON at
`e0c455e1c73e1a9bd24bbc833029cd5506d1d710fe18585251094b48d11e89f9`.
Any corrected upstream product requires a new batch and new hashes.

## Review packet and commands

The rejected comparison packet is locally available in the clean review
worktree:

```text
/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-figure-candidates/
  figure_review/batches/2026-07-14-replacement-review/
```

Open `index.html` for the candidate-by-candidate review page or
`contact-sheet.png` for a family overview. The manifest records source revision
`fcc67fba...`, pipeline revision `67bdd014...`, all evidence hashes, embedded DM
tables, and the owner rejection note. All 39 decisions are
`needs_revision`.

### Create a corrected batch

Render into an isolated directory that mirrors manuscript-relative targets.
Do not render directly over `figures/`.

```bash
python3 scripts/figure_review.py new-batch <new-batch-id> \
  --title "Corrected figure candidates" \
  --candidate-root /absolute/path/to/isolated/render-output \
  --pipeline-revision "<exact-FLITS-commit>" \
  --pipeline-repo /absolute/path/to/verified/FLITS-checkout
```

The command copies candidate bytes, calculates SHA-256 values, captures the
adopted-DM catalog hash and evidence, renders previews, and builds the review
page. A candidate PR may contain the immutable packet plus necessary generator
or provenance changes. It must not change TeX inclusions or promote bytes into
manuscript targets.

### Record decisions

Record one decision per stable candidate ID:

```bash
python3 scripts/figure_review.py decide <new-batch-id> joint-oran approved \
  --reviewer "Jakob Faber" \
  --note "DM lock, fit configuration, residuals, labels, and layout accepted"

python3 scripts/figure_review.py decide <new-batch-id> dsa-acf-zach needs_revision \
  --reviewer "Jakob Faber" \
  --note "Describe the exact scientific or presentation correction required"
```

Silence, a green check, opening or merging the candidate PR, and agent review
never imply `approved`.

### Promote approved bytes

Promotion belongs in a separate focused PR:

```bash
python3 scripts/figure_review.py promote <new-batch-id> joint-oran
python3 scripts/figure_review.py verify
make test-science
```

`promote` copies the exact approved bytes to the protected target and creates a
receipt under `figure_review/approval_receipts/`. The receipt binds reviewer,
decision, candidate hash, promoted hash, adopted-DM catalog hash, manuscript
source revision, and pipeline revision. Editing the promoted PDF afterward
invalidates the receipt and must fail verification.

After promotion, force a clean manuscript build and inspect the rendered PDF,
not only the source asset. Confirm float placement, captions, labels, page
breaks, legibility, and that the TeX inclusion chain points at the approved
bytes.

## Recommended review order

1. **Resolve Figure 1 format.** Decide whether the paper wants
   `fig1-gallery`, a triptych-based main-text product, or a specified hybrid.
2. **Freeze and revalidate the adopted-DM catalog.** Do this before regenerating
   Figure 1, Figure 5, joint fits, or triptychs.
3. **Review Figure 5 calculations.** Its purpose and derived values depend
   directly on the new DM measurements.
4. **Audit joint fits one burst at a time.** Approve the fit science before
   judging the final presentation family.
5. **Set the joint/triptych visual contract.** Fix axes, normalization, color
   scales, labels, residual convention, panel order, and caption content in a
   representative candidate; then apply consistently.
6. **Audit scintillation components and conventions.** Resolve scientific
   membership and flags before formatting the 12-panel family and summary.
7. **Set the scintillation visual contract.** Approve one representative ACF
   candidate, then render the family consistently without assuming that visual
   consistency approves each burst's science.
8. **Review outliers and exclusions individually.** In particular, preserve
   the distinction between diagnostic products and qualified measurements.
9. **Promote in small, family-scoped PRs.** A failure in one family should not
   drag unrelated figure bytes or the `pipeline/` gitlink into the change.

## Current TeX behavior

At `origin/main` after PR #35:

- Figure 1 is a labeled author-review placeholder in
  `sections/observations.tex`;
- Figure 5/association is a labeled placeholder in `sections/results.tex`;
- the DSA scintillation summary is a labeled placeholder in
  `sections/results.tex`;
- the representative main-text joint morphology slot is a labeled placeholder
  in `sections/codetection_triptychs.tex`;
- per-burst DSA ACF, joint-model, and appendix triptych include files are
  intentionally empty;
- the Oran qualification visualization has a labeled placeholder in
  `sections/appendix.tex`.

The manuscript prose and numerical tables were not blanket-reverted by PR #35.
That preserves the revised scientific work while withholding disputed visual
claims. Nevertheless, figure revalidation may expose a numerical or prose
change. If it does, change the affected science and prose explicitly; do not
force a figure to match an already-written claim.

## Validation already completed for the gate

PR #35 was validated with:

- `make test-science`: 54 passed, 1 documented expected failure, 2 existing
  warnings;
- four figure-approval tests, including a negative test proving that an
  unapproved protected inclusion is rejected;
- `python3 scripts/figure_review.py verify`;
- a forced LaTeX build producing a 31-page manuscript;
- passing GitHub root-science-tests, parity checks, and Socket checks;
- a passing repository closeout check.

This validation proves the gate works. It does not validate or approve any of
the 39 rejected candidates.

## Branch and worktree map

### Authoritative and active

| Path or ref | Use |
|---|---|
| `origin/main` at `ee14f32` | Authoritative manuscript and gate. |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-figure-candidates` | Clean rejected-candidate review worktree; branch `review/figure-candidates-20260714`; draft PR #36. |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-figure-approval-v4` | Clean implementation worktree for merged PR #35; useful only for history/comparison. |

### Abandoned implementation experiments: preserve, do not use

The following predate the final merged implementation and contain dirty or
staged experiments:

- `Faber2026-figure-approval` / `ms/figure-approval-gate-20260714`;
- `Faber2026-figure-approval-v2` / `ms/figure-approval-gate-20260714-v2`;
- `Faber2026-figure-approval-v3` / `ms/figure-approval-gate-20260714-v3`.

Do not merge, promote from, reset, clean, or delete them during figure work.
They are not authoritative. Their eventual removal is a separate dirty-state
cleanup decision.

### Root-checkout boundary

The canonical repository checkout at
`/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026` remains on
the stale branch `ms/validated-fit-figure-refresh-20260714`. It contains an
unrelated modified `docs/rse/journal.jsonl` and an untracked broader branch
consolidation handoff. Both are pre-existing shared work. Do not overwrite,
stage, commit, reset, or carry them into a figure PR without a separate
ownership/readiness decision.

## Failure modes and prohibitions

- Do not restore the PR #34 `\includegraphics` lines to make placeholders go
  away.
- Do not merge draft PR #36; it is rejected review history.
- Do not mutate the rejected batch or change its decisions to `approved`.
- Do not infer scientific validity from matching a catalog hash.
- Do not infer author approval from tests, agent review, a PR merge, or a
  visually consistent family.
- Do not treat `joint-*` and `triptych-*` as interchangeable.
- Do not update only the printed DM label when the underlying product or fit
  used another DM.
- Do not silently normalize stable IDs or filename case.
- Do not call diagnostic scintillation fits qualified measurements.
- Do not include a `pipeline/` submodule-pointer bump as a side effect of a
  manuscript figure promotion.
- Do not use broad generation or formatting commands in the dirty root
  checkout.
- Do not call the figure replacement complete until the rendered manuscript,
  not just the candidate assets, has been inspected.

## Checklist for the next agent

1. Fetch and verify `origin/main`; do not trust the stale root checkout.
2. Read this handoff, `figure_review/README.md`, `figure_review/slots.json`, and
   the rejected packet manifest.
3. Confirm PR #35 remains merged and PR #36 remains open, draft, and unmerged.
4. Work from a clean branch/worktree based on current `origin/main`.
5. Ask the owner only for the product decisions that cannot be inferred,
   beginning with Figure 1 layout; use stable candidate IDs in all questions.
6. Revalidate DM and fit inputs before generating presentation revisions.
7. Render outside manuscript targets and create a new immutable batch.
8. Present candidates for owner decision; record exact revision notes.
9. Promote only individually approved candidates in a separate family-scoped
   PR with receipts.
10. Run `python3 scripts/figure_review.py verify`, `make test-science`, a forced
    manuscript build, rendered-PDF inspection, and `agent-closeout-check`.
11. Commit only task-scoped paths; classify all remaining dirt; avoid a
    `pipeline/` gitlink change unless that is the reviewed task.

## Suggested resume prompt

> Continue the figure-review handoff. Start from current `origin/main`, leave
> draft PR #36 unmerged, and use the immutable rejected packet only for
> comparison. First help me decide the intended Figure 1 product using stable
> candidate IDs. Then revalidate the adopted DM and fit provenance before
> rendering a new isolated candidate batch. Do not promote anything without my
> explicit per-candidate approval.

