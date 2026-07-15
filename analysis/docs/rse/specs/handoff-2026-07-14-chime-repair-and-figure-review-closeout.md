# Handoff: CHIME artifact repair and figure-review closeout

---

**Date:** 2026-07-14 19:28 PDT  
**Author:** Codex  
**Status:** durable closeout handoff; science and figure decisions remain open  
**Faber2026 base at audit:** `995940abb406f929add771c57b5d7f16f5bed345`  
**Pinned FLITS revision:** `91a5120ed702d04530b9c3aae32d53a3861e87bd`  
**Handoff branch:** `agent/handoff-chime-repair-closeout-20260714`  
**Publication PR:** [Faber2026 #42](https://github.com/jakobtfaber/Faber2026/pull/42)  
**Scope:** CHIME-only scintillation inventory and diagnostics, artifact repair,
figure-review governance, PR #36/#37 disposition, and remaining branch/worktree
boundaries. DSA-110 scientific adjudication is explicitly out of scope.

---

## Executive status

The artifact-repair and consolidation program is complete. The scientific
result is not a CHIME detection:

> **There are zero qualified CHIME scintillation-bandwidth measurements.**

There is also no qualified Oran CHIME detection and no Oran CHIME measurement
bundle. Oran's qualified DSA artifact is a separate instrument-specific result
and cannot be transferred to CHIME.

The repaired CHIME inventory, portable manifests, retained diagnostics, failed
qualification gates, trigger-calibration campaign, and manuscript report are
merged and pinned. The rejected July figure packet is archived without merge.
The durable figure-review contract is merged. Faber2026 has no open pull
requests at this handoff's audit point.

The remaining work is deliberately split:

1. **Scientific redesign:** devise a CHIME estimator/product route that passes
   qualification at the low modulation seen in the real product.
2. **Owner decision:** choose the intended Figure 1 product before generating
   or promoting replacement figures.
3. **Historical cleanup:** adjudicate old dirty worktrees and divergent FLITS
   branches separately. They are not blockers for the published inventory and
   must not be deleted blindly.

## Strict status table

| Work item | Status | Closure evidence or next gate |
|---|---|---|
| Consolidate CHIME diagnostics and artifacts | **completed** | FLITS PR #174 merged as `91a5120`; portable inventory and artifact bundles are on FLITS `main` |
| Publish the CHIME-only qualification report | **completed** | Faber2026 PR #41 merged as `fbea846`; report records zero qualified measurements |
| Pin Faber2026 to the consolidated FLITS revision | **completed** | Faber2026 `pipeline/` records `91a5120`; pin verified and submodule registration restored |
| Preserve rejected July figures | **completed** | PR #36 closed without merge; annotated archive tag peels to `ba63448` and contains the packet manifest |
| Publish durable figure-review governance | **completed** | PR #37 merged as `995940a`; active-lane inventory reconciled |
| Produce a qualified CHIME scintillation bandwidth | **open scientific work** | A new or revised route must pass null, low-modulation recovery, stability, and visual-review gates |
| Select the Figure 1 product | **decision pending** | Owner chooses `fig1-gallery`, a triptych design, or a precisely specified alternative by stable candidate ID |
| Promote replacement figures | **blocked by science and owner decisions** | Exact candidate bytes require accepted science, explicit approval, receipts, tests, and rendered-manuscript inspection |
| Remove old figure-approval worktrees | **decision pending** | v1-v3 contain 126/11/100 dirty paths; inspect and classify before deletion |
| Retire remaining FLITS historical branches | **decision pending** | Prove content integration or unique-work preservation lane by lane; do not infer from branch ancestry after squash merges |

Do not flatten the last five rows into “completed.” Artifact preservation and
scientific qualification are different closure conditions.

## Authoritative revisions and publication chain

### Faber2026

| Item | Revision | Meaning |
|---|---|---|
| Current audited `main` | `995940abb406f929add771c57b5d7f16f5bed345` | PR #37 merge; durable review contract and current active-lane state |
| CHIME inventory report | `fbea8460b364c62a1b4411684f9105920617224e` | PR #41 merge |
| Figure approval gate | `ee14f329c0093fa2aeca600aa7d9b045a3984787` | PR #35 merge |
| Archived rejected packet | tag `archive/rejected-figure-candidates-20260714` | Annotated tag object `2b22834`; peels to packet commit `ba63448` |
| Rejected source revision | `fcc67fba6ce28830ab65677b6ccba91c77c0426a` | Comparison source only; not approved |

### dsa110-FLITS

| Item | Revision | Meaning |
|---|---|---|
| Consolidated FLITS `main` | `91a5120ed702d04530b9c3aae32d53a3861e87bd` | PR #174 merge; canonical CHIME inventory and repaired artifacts |
| PR #174 source head | `691dc7d355e7506cceea621818309934904fb2d1` | Squash/merge source branch; remote still exists at audit time |
| A1 remote head | `1e58c96e6cdea034ecc20f3b6d658d95ec977d81` | Completed trigger-calibration development history; changes consolidated through PR #174 |
| Recovered notebook replay | `7db0d4633c11b60dcdac8cd260ebbb5334243265` | Contains CHIME replay evidence plus unique DSA/Oran work; preserve pending DSA adjudication |
| Reference-arc rescue | `9237e4c982b46f1993363cb3242298a81f3b7dd2` | Historical rescue evidence; preserve pending a separate audit |

The parent gitlink, not whichever FLITS checkout happens to be open, is the
manuscript's pipeline authority. At this handoff it records exactly `91a5120`.

## Canonical CHIME artifact map

All paths below are relative to the Faber2026 root unless stated otherwise.

### Human and machine entry points

- Human report:
  `docs/rse/specs/report-chime-scintillation-inventory-2026-07-14.md`
- Durable figure-review contract:
  `docs/rse/specs/handoff-2026-07-14-figure-review-and-replacement.md`
- Owner-facing lane control surface: `docs/rse/ACTIVE_LANES.md`
- FLITS inventory overview: `pipeline/analysis/chime-scintillation/README.md`
- Machine-readable qualification inventory:
  `pipeline/analysis/chime-scintillation/INVENTORY.yaml`
- External-input provenance:
  `pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml`

### Repaired or consolidated experiment bundles

| Route | Canonical result | Published outcome |
|---|---|---|
| H0 rank-1 smoke test | `pipeline/analysis/chime-scintillation/experiments/h0-smoke/README.md` | Exact reconstructed diagnostic; low-band on/off width-ratio gate fails |
| A1 additive covariance | `pipeline/analysis/chime-scintillation/experiments/a1-covariance/README.md` | Held-out covariance and recovery gates fail |
| H2 rank-2 calibration | `pipeline/analysis/chime-scintillation/experiments/h2-calibration/README.md` | Missing PNGs regenerated; multiple qualification gates still fail |
| H3 stationary-kernel whitening | `pipeline/analysis/chime-scintillation/experiments/h3-scallop/README.md` | Held-out kernel and injection recovery fail |
| B3 polarization cross-ACF | `pipeline/analysis/chime-scintillation/experiments/b3-highband-crossacf/RESULT.md` | Off-pulse coherence remains; every `m=0.3` injection cell fails |
| B4 four-stream cross-ACF | `pipeline/analysis/chime-scintillation/experiments/b4-fourstream-crossacf/RESULT.md` | Null passes, but recovery fails in the real product's modulation regime |
| Notebook replay | `pipeline/analysis/chime-scintillation/experiments/notebook-replay/RESULT.md` | Falsified: inherited window is off-pulse and controls reproduce the scale |
| A1 trigger calibration | `pipeline/analysis/chime-scintillation/experiments/trigger-calibration/RESULT.md` | Campaign reproducible; calibrated trigger has zero power in all eight alternative cells |

The trigger bundle also contains:

- `validation.json` — independent aggregate validation;
- `artifact-manifest.json` — repository-relative artifact paths and SHA256
  hashes;
- all 68 cell checkpoints;
- aggregate report and three reviewed diagnostic figures.

## Scientific adjudication

### Route-by-route outcome

| Route | Decisive result | Qualification status |
|---|---|---|
| H0 | Low-band on/off width ratio `1.658` fails; high band `2.218` passes | diagnostic only |
| A1 covariance | Held-out covariance and width/coverage/modulation recovery fail | diagnostic only |
| H2 | Injection, window, time-split, comb, held-out-kernel, and manual-review gates fail | diagnostic only |
| H3 | Held-out kernel and injection recovery fail; whitening is not applied on-pulse | diagnostic only |
| B3 | 11/12 off-pulse controls retain coherent structure; all `m=0.3` injection cells fail | diagnostic only |
| B4 | Null passes; `m=0.15–0.30` recovery fails; observed product has only `m≈0.15–0.17` | diagnostic only |
| Notebook replay | Inherited window is off-pulse; 24 controls reproduce the fitted scale | falsified |
| A1 trigger | 1% threshold `Delta ln Z = 59699.69283336272`; zero escalation probability in all eight power cells | completed failed design |

Retained fitted values such as the H2 widths (`38.616 kHz` at `523.268 MHz`
and `64.989 kHz` at `723.076 MHz`) and the B4 Lorentzian remain useful
diagnostics. Their precision does not promote them to measurements.

### Minimum gate for a future CHIME claim

A future route must, at minimum:

1. use an on-pulse window proven against the retained data product;
2. pass real-background and matched off-pulse null controls;
3. recover injected structure at or below the real product's modulation
   (`m≈0.15–0.17`), not only at easier high-modulation settings;
4. demonstrate stability across time/frequency splits and defensible mask or
   kernel choices;
5. preserve portable input and artifact provenance with hashes;
6. pass independent visual review without overriding quantitative failures;
7. distinguish a fitted diagnostic scale from a qualified decorrelation
   bandwidth in machine-readable status.

Until this gate is satisfied, the manuscript cannot claim a CHIME bandwidth,
a CHIME two-screen inference, or a CHIME Oran detection.

## Figure-review disposition

### PR #36: rejected candidate packet

- Closed without merge.
- Archived at `archive/rejected-figure-candidates-20260714`.
- Remote tag was verified to peel to
  `ba63448d8ed5f3561f2cc52ed9484ab7a1bd85bc`.
- The archived
  `figure_review/batches/2026-07-14-replacement-review/manifest.json` was
  verified present.
- Local and remote PR branches were deleted after archive verification.
- The PR worktree was removed.
- All 39 candidates remain `needs_revision`; the archive must never be treated
  as an approval packet.

### PR #37: durable review workflow

- Rebased/reconciled with current `main`, substantially rewritten, and merged
  as `995940abb406f929add771c57b5d7f16f5bed345`.
- Records the zero-qualified-measurement CHIME boundary and separates it from
  Oran's DSA qualification.
- Preserves rejected-batch provenance and the three independent gates:
  reproducibility, scientific validity, and explicit owner approval.
- Local and remote PR branches were deleted after merge verification.
- The PR worktree was removed.

### Promotion contract

New figure candidates must be rendered into an isolated batch. They must not
overwrite protected targets. Promotion requires an explicit decision for the
stable candidate ID and a hash-bound approval receipt. Then run:

```bash
python3 scripts/figure_review.py verify
make test-science
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Inspect the compiled PDF, not only the source asset or filename.

## Validation completed

The final PR #37 revision and merged root were checked with:

- `make test-science`: **54 passed, 1 documented xfail**;
- `python3 scripts/figure_review.py verify`: **passed**;
- clean `latexmk` manuscript build: **31 pages**;
- `git diff --check`: **passed**;
- fresh GitHub checks on PR #37: **all passed**;
- `agent-closeout-check`: **passed**;
- PR #37 head verified as an ancestor of Faber2026 `main`;
- PR #36 archive tag and packet manifest verified after branch deletion;
- Faber2026 open-PR inventory: **empty**.

FLITS PR #174's integration validation, recorded in the canonical inventory,
included the focused legacy, cross-ACF/replay, and trigger-calibration tests and
portable artifact/hash checks. The parent report is pinned to that merge.

## Live repository and worktree state

This section is a snapshot from 2026-07-14 19:28 PDT. Re-fetch before acting.

### Faber2026

- Root checkout was clean and synchronized at `995940a` before creating this
  handoff branch.
- `pipeline/` is registered and checked out at `91a5120`.
- No open Faber2026 PRs existed at audit time.
- PR #36 and #37 source branches and worktrees are gone.
- Three older dirty approval experiments remain:

| Worktree | Branch | Dirty paths | Disposition |
|---|---|---:|---|
| `Faber2026-figure-approval` | `ms/figure-approval-gate-20260714` | 126 | preserve; not authoritative |
| `Faber2026-figure-approval-v2` | `ms/figure-approval-gate-20260714-v2` | 11 | preserve; not authoritative |
| `Faber2026-figure-approval-v3` | `ms/figure-approval-gate-20260714-v3` | 100 | preserve; not authoritative |

These worktrees contain modified or staged manuscript assets and gate
experiments. The merged v4 implementation in PR #35 supersedes them, but that
does not authorize deletion of their dirty state.

### Separate dsa110-FLITS clone

The standalone clone at
`/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/dsa110-FLITS` is not
the clean publication surface:

- local `main` is `fed4a02c`, **26 commits behind** `origin/main` `91a5120`;
- it has one modified path: `docs/entire-tracing-checkpoints.md`;
- do not fast-forward or clean it without first preserving/classifying that
  modification;
- use the clean Faber2026 `pipeline/` checkout at `91a5120` for read-only
  reproduction, or create a new isolated FLITS worktree from `origin/main` for
  development.

Relevant remaining FLITS refs:

| Ref/worktree | Live state | Required handling |
|---|---|---|
| remote `agent/chime-artifact-consolidation` at `691dc7d` | merged by PR #174 | safe deletion candidate after a final remote/head check |
| remote `a1/trigger-calibration` at `1e58c96` | consolidated through PR #174 | prove patch equivalence before deletion |
| local `a1/trigger-calibration` / `flits-a1-trigger` at `9ca0368` | clean but **24 commits behind its remote** | do not resume or delete as if it were the remote-complete campaign |
| remote `reval/p0-provenance` at `9b7ebe0` | post-merge branch history | separate provenance cleanup lane |
| local `reval/p0-provenance` at `e2f6ca8` | stale relative to remote | do not overwrite remote state |
| `flits-reland` at `dad9786` | one modified tracing-doc path | preserve pending dirty-state adjudication |
| `dsa110-FLITS-scint-revalidation` at `565ccf0` | 625 ahead / 631 behind `origin/main`, one modified tracing-doc path | historical divergent lane; audit before any merge or deletion |
| remote `scint/recovered-notebook-replay` at `7db0d46` | contains unique DSA/Oran commits | preserve until DSA work is separately published or archived |
| remote `scint/reference-arc-rescue` at `9237e4c` | rescue history | preserve pending a focused audit |

Many additional historical FLITS worktrees remain. They were not created by
this repair and were not included in its deletion authority.

## Repowire state

At the handoff audit:

- Repowire was installed at `/Users/jakobfaber/.local/bin/repowire`;
- the unified WebSocket daemon service was running and responding at
  `http://127.0.0.1:8377`;
- one of two peers was online;
- Codex hooks were installed;
- Claude Code hooks were reported not installed.

This is operational context, not proof that a future session is registered.
Run `repowire status` again when resuming.

## Next actions, in order

### 1. Resolve the owner-gated Figure 1 decision

Choose the intended product by stable candidate ID:

- `fig1-gallery`;
- a triptych-based design; or
- a precisely specified alternative.

Do not generate broad replacement families until this product decision is
recorded.

### 2. Design the next CHIME qualification route

Start from the canonical inventory and failed-gate evidence, not from an old
notebook or a visually promising fitted scale. The design must target recovery
at the observed low modulation. Create a new experiment ID and isolated output
root; do not overwrite any retained diagnostic bundle.

### 3. Revalidate figure science before presentation

Once the scientific inputs are accepted:

1. freeze the adopted-DM catalog;
2. revalidate DM application and each retained fit;
3. render an isolated candidate batch;
4. request explicit decisions by stable candidate ID;
5. promote only the exact approved bytes in a separate focused PR;
6. compile and inspect the manuscript.

### 4. Clean FLITS publication branches conservatively

The first easy candidate is the merged PR #174 source branch. The A1 branch is
more complicated because the local worktree is far behind its remote. Compare
the remote campaign content against `91a5120` at the tree/path level before
removing either ref. Squash/merge history means `git branch --merged` and
`git cherry` alone are not sufficient proof.

### 5. Adjudicate historical dirty worktrees separately

Inventory v1-v3 figure-approval changes and the FLITS tracing-document dirt.
Partition salvageable source/evidence from generated or superseded outputs.
Only then create focused archive/cleanup commits or remove worktrees with an
explicit recorded proof.

## Resume checklist

From the Faber2026 root:

```bash
git fetch origin
git status --short --branch
git rev-parse origin/main
git submodule status pipeline
gh pr list --repo jakobtfaber/Faber2026 --state open
gh pr list --repo jakobtfaber/dsa110-FLITS --state open
repowire status
```

Verify the scientific entry points:

```bash
sed -n '1,220p' docs/rse/specs/report-chime-scintillation-inventory-2026-07-14.md
sed -n '1,280p' docs/rse/specs/handoff-2026-07-14-figure-review-and-replacement.md
sed -n '1,220p' pipeline/analysis/chime-scintillation/README.md
```

Before changing a historical worktree, run a raw porcelain status and record
every path. Do not rely on compact output alone for dirty-path counts:

```bash
git -C <worktree> status --porcelain=v1
```

## Non-negotiable cautions

- A precise diagnostic width is not a qualified bandwidth.
- A completed calibration campaign can validly conclude that a trigger is
  unusable.
- Oran DSA qualification is not Oran CHIME qualification.
- Passing tests do not imply scientific validity or owner approval.
- Never promote rejected PR #36 bytes or relabel its decisions.
- Do not resume the stale local A1 worktree as if it contained the remote
  completed campaign.
- Do not fast-forward or clean the mixed-dirty standalone FLITS clone without
  classifying `docs/entire-tracing-checkpoints.md`.
- Do not delete recovered-notebook or reference-arc branches until their unique
  DSA/rescue content is separately resolved.
- Keep `pipeline/` pin changes out of figure-only PRs.

## Handoff completion condition

This handoff is complete when its publication PR is recorded here, the document
is merged to Faber2026 `main`, the source branch is removed, and `main` is clean
and synchronized. GitHub and git history remain the authority for the resulting
merge commit. The science and owner decisions above intentionally remain open
after handoff publication.
