# Plan: Figure 1 observed-peak audit

Status: approved by the 2026-07-17 direct-execution instruction

## Goal

Produce a hash-pinned Figure 1 candidate using observed-profile timing only,
attach reproducible input/header/drift evidence at the current pipeline pin,
and preserve the fail-closed manuscript promotion boundary.

## Phase 1: correct and test the producer

1. Remove the joint-model scattering correction from
   `scripts/plot_codetection_data_grid.py`.
2. Make `load_row_bands` pass no extra time shift to `bands_archival`.
3. Replace model-ToA unit tests with a behavioral assertion that both fitted and
   non-fitted rows retain the observed-peak convention.
4. Update `repro_manifest.csv`, `REPRODUCE.md`, and Figure 1's required review
   evidence to describe the actual inputs and convention.

## Phase 2: preserve the audit evidence

1. Record the current parent/pipeline revisions and the 24 byte-pinned inputs.
2. Record DSA and CHIME raw-header band edges, sample intervals, and channel
   ordering for every row.
3. Preserve both residual-drift estimator results and the explicit all-panel
   validation failure; do not reinterpret unconstrained fits as passes.
4. Carry forward only the task-scoped Figure 1 owner decision from the untracked
   primary review batch. Do not copy unrelated rejected candidates.

## Phase 3: generate a candidate, not a promotion

1. Render PDF/PNG/SVG into a temporary candidate root under the clean Conda
   `flits` environment.
2. Create a one-candidate review batch with the exact current pipeline pin,
   candidate hash, preview, frozen DM catalog, input/header/drift evidence, and
   the previous owner notes.
3. Leave the decision pending and the science validation status blocked. Do not
   overwrite `figures/codetection_data_grid.pdf`, its approval receipt, or the
   manuscript caption without exact-byte owner approval.

## Phase 4: validate and publish the review branch

Run focused and full tests, validate the review packet, compile with `latexmk`,
run the manuscript consistency audit, visually inspect the preview, run
`agent-closeout-check`, commit task-scoped paths, push the named branch, and open
a ready-for-review PR. The PR is complete as a candidate/provenance artifact but
is not a compliant manuscript promotion.
