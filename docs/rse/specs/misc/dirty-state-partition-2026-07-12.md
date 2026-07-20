# Dirty-state partition: legacy manuscript checkout

**Observed:** 2026-07-12  
**Checkout:** `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026`  
**Branch:** `ms/dm-host-posteriors-pdfs`  
**Rule:** preserve all paths until their lane is independently validated and
landed or explicitly retained as pending.

## Base-state finding

The checkout branch is an ancestor of current `origin/main`: zero commits
ahead and 43 behind. Its committed DM-host work is already contained in main.
Some apparent dirt is therefore base drift rather than unique work:

- the checked-out `pipeline` commit is `75cb2a8`, exactly the gitlink recorded
  by `origin/main`; the parent branch merely records the older `2934f44` pin;
- `scripts/journal-append.sh` has the same blob as `origin/main` (the apparent
  change is inherited mode/base drift).

Neither path needs to be republished from this checkout. Do not create a
pipeline-pin commit from the apparent parent diff.

## Lane B0: board and journal control surface

**State:** coherent active implementation; not in `origin/main` in this form.  
**Likely producer:** `claude-fable-5/owner-view-board`.  
**Disposition:** preserve as a synchronized lane, transplant onto current
main, validate rendering/deployment boundaries, then publish separately.

Paths:

- `.gitignore`
- `docs/rse/board/readiness.html`
- `docs/rse/board/owner-view.json`
- `docs/rse/journal-protocol.md`
- `docs/rse/journal.jsonl`
- `scripts/render_journal_panel.py`
- `scripts/deploy-board.sh`

Notes:

- `readiness.html` is generated from the owner view and journal and must not be
  committed independently of its sources and renderer.
- `journal.jsonl` contains 102 appended entries relative to the legacy base and
  is a live multi-writer surface; merge by append semantics, never by replacing
  a newer canonical tail.
- `scripts/journal-append.sh` is already represented by current main and is not
  part of the unique transplant.
- The deploy script is scoped to the `board/` directory on `gh-pages`; the
  root scattering deck is a separate lane.

## Lane D0: DM campaign evidence and planning

**State:** substantive active science artifacts; FLITS implementation already
exists at the main-recorded `75cb2a8` pin.  
**Disposition:** preserve documents, producer, and contact sheets together;
revalidate plan status against the completed adaptive campaign before
publishing any stale "in progress" language.

Paths:

- `docs/rse/specs/plan/plan-dm-measurement-methods.md`
- `docs/rse/specs/research/research-dm-measurement-methods.md`
- `docs/rse/decks/dm-campaign-2026-07/dm-battery-arrival_regression-contact-sheet.png`
- `docs/rse/decks/dm-campaign-2026-07/dm-battery-dm_phase_published-contact-sheet.png`
- `docs/rse/decks/dm-campaign-2026-07/dm-battery-dm_power_published-contact-sheet.png`
- `docs/rse/decks/dm-campaign-2026-07/dm-battery-dmphase_variant_intree-contact-sheet.png`
- `docs/rse/decks/dm-campaign-2026-07/dm-battery-dmpower_variant_intree-contact-sheet.png`
- `scripts/plot_codetection_gallery_arrivaldm.py`

The `pipeline` gitlink is not unique lane work; it is already equal to
`origin/main`.

## Lane D1: DM-IGM and foreground follow-up planning

**State:** substantive planning/research, partly scoped and partly requiring
revalidation against current main.  
**Disposition:** preserve on a documentation/research branch; do not launch
the optional per-system PDF figure until its three recorded owner choices are
resolved or made unnecessary by manuscript scope.

Paths:

- `docs/rse/specs/plan/plan-dm-foreground-system-pdfs.md`
- `docs/rse/specs/plan/plan-dm-igm-pdf-connor2024.md`
- `docs/rse/specs/research/research-dm-igm-pdf-connor2024.md`

## Lane S0: CHIME campaign plan

**State:** active plan written before the loop-control consolidation. It
correctly requires terminal per-burst classifications, but its P4 campaign
sequence must be reconciled with the stricter single-target qualification gate
in `plan-loop-orchestration.md`.  
**Disposition:** preserve and fold into the bounded S0/S1 contract; do not run
the twelve-target P4d fleet until Freya passes the frozen-method gate.

Path:

- `docs/rse/specs/plan/plan-chime-scint-gamma-campaign.md`

## Lane S1: scintillation diagnostic deck

**State:** active generated diagnostic bundle; Freya CHIME remains
`diagnostic_only`, while the DSA component figures are separate qualified
inputs.  
**Disposition:** preserve producer/input/output relationships and validate the
deck as a diagnostic artifact. It must not be used to promote the failed CHIME
measurement.

Paths:

- `outputs/scintillation-acf-review/index.html`
- `outputs/scintillation-acf-review/scintillation-acf-review.pptx`
- `outputs/scintillation-acf-review/slide-01.png`
- `outputs/scintillation-acf-review/slide-02.png`
- `outputs/scintillation-acf-review/slide-03.png`
- `outputs/scintillation-acf-review/slide-04.png`
- `outputs/scintillation-acf-review/casey_dsa_acf_lorentzian_fits.png`
- `outputs/scintillation-acf-review/freya_dsa_acf_lorentzian_fits.png`
- `outputs/scintillation-acf-review/freya_chime_instrumental_origin.png`

## Lane H0: Figure 1 historical design and agent logs

**State:** implementation has landed on current main; these files are
historical design/review provenance rather than active code. The two local
Superpowers documents differ from the versions already tracked by main.  
**Disposition:** preserve until compared; publish only concise durable design
records, not automatically the raw transcripts or launch scaffolding.

Paths:

- `docs/superpowers/plans/2026-07-11-codetection-triptych-fig1.md`
- `docs/superpowers/specs/2026-07-11-codetection-triptych-fig1-design.md`
- `logs/claude-merge-fig1-jointmodel.md`
- `logs/claude-merge-fig1-jointmodel.stream.jsonl`
- `logs/codex-merge-fig1-jointmodel.md`
- `logs/launch-merge-fig1-agents.sh`
- `logs/merge-fig1-jointmodel-brief.md`
- `logs/merge-fig1-jointmodel-prompt-short.txt`
- `logs/merge-fig1-jointmodel-prompt.txt`
- `logs/merge-fig1-jointmodel-synthesis.md`
- `logs/merge-fig1-triptych-design.md`

## Lane G0: generated SkillOpt staging

**State:** generated offline staging/cache, 36 KiB; ownership and publish
value are not established.  
**Disposition:** preserve in place. Do not commit or delete without a later
explicit retention decision.

Paths:

- `.skillopt-sleep/staging/20260710-102357/backup/CLAUDE.md`
- `.skillopt-sleep/staging/20260710-102357/diagnostics.json`
- `.skillopt-sleep/staging/20260710-102357/manifest.json`
- `.skillopt-sleep/staging/20260710-102357/proposed_CLAUDE.md`
- `.skillopt-sleep/staging/20260710-102357/proposed_SKILL.md`
- `.skillopt-sleep/staging/20260710-102357/report.json`
- `.skillopt-sleep/staging/20260710-102357/report.md`

## Partition order

1. Land the loop-control architecture and this ledger.
2. Transplant and validate B0 without replacing newer journal entries.
3. Reconcile S0 with the bounded Freya gate; begin the FLITS method loop.
4. Preserve D0/D1 as evidence/planning branches and adjudicate stale status
   language before publication.
5. Validate S1 as diagnostic-only output.
6. Compare H0 against main and retain only durable records.
7. Leave G0 pending until a retention decision is useful.

## Stop condition

Every dirty path has a named lane above. Repository recovery is complete only
after each lane is either landed, moved to a focused branch/worktree, or
explicitly preserved as pending, and the legacy checkout can change branches
without data loss.
