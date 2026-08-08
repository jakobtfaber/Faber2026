# Handoff: controlled joint-scattering rerun paused at exact-support fix

---
**Date:** 2026-07-23 14:17 PDT  
**Author:** Codex  
**Status:** Paused safely; no fit jobs running; no panel admitted  
**Analysis branch:** `codex/handoff-joint-scattering-20260723`  
**Scientific lane:** deprecated Zach C2D4 audit, then seeded Oran C1D1, JohnDoeII C2D2, and Zach C2D4 fits

---

## Non-negotiable gate

No panel reaches owner review until its producing fit has:

1. exact hashed inputs, configuration, source revision, command, working directory, and runtime identity;
2. a clean-worktree seeded run;
3. a second seeded run from the same contract;
4. exact JSON/SVG byte agreement and canonical NumPy scientific-array agreement;
5. a complete reproduction receipt.

Even after reproduction passes, the receipt remains `scientific_trust=pending` and
`panel_review_eligible=false` until the analysis-side admission gate accepts it. No
figure from this session is review-ready.

## Safe pause state

- h17 `squeue`: empty at pause.
- GitHub Actions watcher: stopped locally; completed check state is recorded below.
- No manuscript or analysis figure was promoted, displayed, or approved.
- All failed or cancelled roots are review-ineligible. v2 Zach and all v3 roots
  have explicit diagnostic-only dispositions; the initial roots use
  `failure.json`; v2 Oran and JohnDoeII have incomplete receipts plus
  `review_eligible=false` orchestration records.
- Do not resume any old run root. The next campaign root must be fresh `v4`.

## Landed work

| Work | Repository | State | Evidence |
|---|---|---|---|
| Deprecated Zach C2D4 failure audit | Faber2026-analysis | merged | PR 53; merge `4a1fbcd5505a44d6345d5e92e86d5dcb04e457a4` |
| Controlled seeded runner | dsa110-FLITS | merged | PR 224; merge `67b73a85e10597f04a6b1480676267034bfecdac` |
| Preserve invoked virtual-environment interpreter | dsa110-FLITS | merged | PR 226; merge `08649392d9c9f1bfd21752c63f1a7330cd39fbe7` |
| Runner/control-board documentation | Faber2026-analysis | merged | PR 59; merge `7435c720e03f28ab5c9142976505f7f7b5c04d80` |
| Runtime-failure documentation | Faber2026-analysis | merged | PR 61; merge `471dadd1369ac3c8533d466c73b88b2da3477771` |
| Select joint resolution against final common windows | dsa110-FLITS | merged | PR 227; merge `31f7744758cc078168fef2b56052711a15df5115` |

PR 227 fixed three preprocessing failures:

- time and frequency resolution are searched jointly;
- a coarser time bin is retried when every frequency choice fails;
- selection is repeated against the exact reconciled two-band window.

It also keeps one- or two-bin final windows explicitly unqualified. Independent
review first broke that path, then verified the correction and boundary cases.

## Current open change: merge before any relaunch

Pipeline PR 228: <https://github.com/jakobtfaber/dsa110-FLITS/pull/228>

- Branch head: `8750f27a3b0d5b1f98d7190036fb6a465e2ce02f`
- Purpose: preserve the exact fitted noise support in the canonical model-grid
  packet. Clipped noise remains an arithmetic-only copy.
- Real Oran cross-check: all ten C/D support arrays match the resolved fit;
  the flagged CHIME channel remains exactly zero.
- Synthetic regression covers flagged `float32` support under both proper-Gaussian
  and ordinary least-squares gain models, including explicit dtype equality.
- Local validation: 841 passed, 0 failed, 8 skipped, 1 expected failure; 34 focused
  tests passed; Ruff clean.
- Independent adversarial review: PASS after finding and closing the dtype-coercion
  regression gap.
- Socket checks: pass.
- GitHub Python 3.12: passed in 9m40s.
- GitHub Claude review: failed before reviewing code with `is_error:true`; zero
  comments. This is an infrastructure failure, not a review verdict.

PR 228 is ready for merge except for the non-substantive Claude infrastructure
failure. Resume by merging with the existing standing authorization; record the
merge commit and use that exact commit for v4.

## Scientific configuration chosen

Use one campaign-wide preprocessing threshold:

```text
FLITS_SNR_TARGET=5.0
FLITS_JOINT_AUTO_TF=1
FLITS_ONPULSE_CROP=1
FLITS_ONPULSE_PAD=0.5
FLITS_MAX_CHANNELS=64
```

Why target 5:

- target 10 made Oran and JohnDoeII fail the integrated profile/channel gate;
- target 5 passes all six band products after the final-window resolution fix;
- target 4 was tested and rejected because Oran jumped discontinuously to a
  noisy, much finer solution rather than giving a stable compromise;
- the setting is common to all bursts and bands, not per-burst tuning;
- Oran remains a quality caveat: its CHIME choice is coarse, 16 channels by 5
  time bins. The fit must be judged scientifically after reproduction, not
  rationalized from gate passage alone.

Fixed fit controls:

| Burst | Components | Seed |
|---|---:|---:|
| Oran | C1D1 | 20220506 |
| JohnDoeII | C2D2 | 20230814 |
| Zach | C2D4 | 20220207 |

All use `nlive=1000`, `nproc=8`, `dlogz=0.5`, `sample=rwalk`, and fixed
`gain_s2=100`.

## Deprecated Zach audit result

The old Zach D4 result is not reusable science:

- fitted D4 width: 350.235 ms;
- plotted window: 5.89824 ms;
- width/window ratio: 59.3796;
- D4 fluence fraction: 3.08183%;
- CHIME C2 fluence fraction: 0.00125643%;
- evidence change: -10.1023, diagnostic-only.

Old artifacts remain hidden. The audit exists to prevent repeating the same
unsupported component behavior, not to seed a preferred answer.

## Attempt history and exact failure reasons

### Initial controlled roots: jobs 196-198

Root:
`/home/ubuntu/flits-controlled/joint-scattering-2026-07-22/{oran,johndoeII,zach}`

All stopped before scientific preprocessing because the frozen command used the
resolved base Python interpreter instead of the virtual-environment entry path.
Each root contains `failure.json`; no scientific output exists.

### v2 roots: jobs 199-201

Root:
`/home/ubuntu/flits-controlled/joint-scattering-2026-07-22-v2/{oran,johndoeII,zach}`

- Oran 199: stopped before sampling at target-10 signal-to-noise gate.
- JohnDoeII 200: stopped before sampling at target-10 signal-to-noise gate.
- Zach 201: passed target 10 and began sampling, then was cancelled when the
  common target and resolution-selection defect were established. Its
  `attempt-disposition.json` marks it incomplete and diagnostic-only.

### v3 roots: jobs 202-204

Root:
`/home/ubuntu/flits-controlled/joint-scattering-2026-07-22-v3/{oran,johndoeII,zach}`

Exact source: `31f7744758cc078168fef2b56052711a15df5115`.

- Oran 202: run A fit converged, then the output packet failed closed because the
  model-grid exporter changed a flagged CHIME noise value from zero to `1e-9`.
  `outputs_complete=false`; no reproduction run; no admissible result.
- JohnDoeII 203 and Zach 204: cancelled after their resolved supports proved they
  had the same flagged-CHIME condition and would deterministically fail after
  expensive sampling.
- All three have `attempt-disposition.json`, `scientific_trust=diagnostic-only`,
  and `panel_review_eligible=false`.

Do not reuse the Oran fit output even though sampling completed. Its controlled
packet is incomplete and its reproduction contract did not pass.

## Next execution: exact steps

1. Confirm PR 228 is still open and Python CI remains green.
2. Merge PR 228 and record its merge commit.
3. On h17, fetch `origin/main` in
   `/home/ubuntu/Developer/repos/github.com/jakobtfaber/dsa110-FLITS`.
4. Create three new detached, clean worktrees at the exact merge commit:

   ```text
   /home/ubuntu/Developer/worktrees/dsa110-FLITS-controlled-oran-20260723-v4
   /home/ubuntu/Developer/worktrees/dsa110-FLITS-controlled-johndoeII-20260723-v4
   /home/ubuntu/Developer/worktrees/dsa110-FLITS-controlled-zach-20260723-v4
   ```

5. Create new roots only:

   ```text
   /home/ubuntu/flits-controlled/joint-scattering-2026-07-23-v4/oran
   /home/ubuntu/flits-controlled/joint-scattering-2026-07-23-v4/johndoeII
   /home/ubuntu/flits-controlled/joint-scattering-2026-07-23-v4/zach
   ```

6. Use the v3 `build_contract.py`, configs, and batch script only as templates.
   Replace every source/root/revision reference with v4 values and retain target
   5. Recompute orchestration hashes. Old roots may appear only as provenance.
7. Run `uv sync --frozen --extra nested` in each worktree.
8. Independently audit clean source, exact interpreter, seeds/counts, controls,
   empty output roots, two-run checks, and fail-closed review status.
9. Submit all three. Record job IDs in each `logs/job-id.txt`.
10. Monitor gates, not images. On any deterministic shared defect, stop the other
    affected jobs and preserve dispositions before fixing it.
11. For each success, require:

    - run A preflight and post-preparation reverification;
    - complete five-role output packet;
    - archived run A;
    - run B from the same seed/contract;
    - canonical equality for weighted samples and model-grid NumPy arrays;
    - exact equality for summary, diagnostics, and SVG;
    - `reproduction_passed=true`.

12. Only after all checks, ingest the reproduction receipt into the analysis-side
    figure gate. Do not manually open or send a panel before admission.

## Documentation still to update after v4

Analysis-side active tickets remain the scientific truth surface:

- `docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-03-fit-oran-c1d1.md`
- `docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-04-fit-johndoeii-c2d2.md`
- `docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-05-fit-zach-c2d4.md`
- `docs/rse/control/BOARD.md`

Record v3 as diagnosed/failed, not completed. Close a production ticket only when
its v4 reproduction and analysis admission gates pass. Then refresh the knowledge
base with `make kb-index` if the semantic model cache is available; a missing local
ONNX cache must not block repository truth or scientific closeout.

## Repository and dirty-state boundaries

- Canonical manuscript checkout was already dirty on unrelated lanes: `README.md`,
  `analysis`, `pipeline`, plus several untracked paths. Do not sweep them into this
  handoff or a submodule-pointer commit.
- Pipeline implementation work used isolated worktrees under
  `/Users/jakobfaber/Developer/scratch/worktrees/`.
- The pipeline submodule pin in the manuscript repo is deliberate. Do not bump it
  as a side effect of this lane.
- The separate Overleaf checkout was not touched.

## Receiver summary

The provenance system is doing its job: it stopped three distinct wrong paths
before owner review. The immediate next action is PR 228 merge, then clean v4 fits.
Treat Oran's coarse CHIME support as an explicit scientific caveat. No current fit
or panel is trusted.
