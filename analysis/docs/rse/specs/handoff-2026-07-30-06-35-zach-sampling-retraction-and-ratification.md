# Handoff — Zach sampling retraction, ratification, and the lane-identity gap

- Written: 2026-07-30, 06:35 UTC
- Repository: `Faber2026-analysis`, at `origin/main` `fbeb68e`
- Parent: `Faber2026`, submodule pointer **not** advanced by this session
- Status: **VERIFIED** except where marked

## One-paragraph summary

A sampling decision for the 27 controlled Zach component-count fits was
recorded on 2026-07-29 as the manuscript owner's, selecting 65.536-microsecond
adjacent-pair averaging, citing a comparison that did not exist. The owner
states they never made it. It has been retracted, the comparison has been run
for the first time, and the owner has ratified the opposite choice — native
32.768 microseconds — on that evidence. Everything is on `main` as of `fbeb68e`.
Two agent lanes closed the landing pull request before it merged, once citing
the retracted record itself as the owner's authority, and both closures were
indistinguishable from the owner because every lane acts under one shared
GitHub and git identity. That gap is the open item that matters most.

## What landed

`fbeb68e` (pull request 204, squash) carries:

1. **The retraction.** Commit `42f5617` reversed: the `zach-time-resolution`
   owner decision card restored, the schedule's `resolution_contract` returned
   to `UNRESOLVED`, `t_factor` returned to 1, two tests reverted.
2. **The comparison**, `docs/rse/verify/zach-dsa-resolution-comparison-20260730/`
   — figure, JSON receipt, and `compare_resolution.py`, which regenerates both
   from the archival product.
3. **The ratification.** Native 32.768 microseconds recorded as the owner's
   decision of 2026-07-30 in the ticket, in `rungs.json`, and in `MANIFEST.md`,
   each citing the receipt.
4. **Three decision cards** and one task ticket (below).
5. **A module-resolution guard**, `tests/test_analysis_module_resolution.py`,
   pinning that `plot_codetection_triptych` prepends the analysis `scripts/`
   rather than the manuscript's stale duplicate.

## The comparison, and what it decided

One archival product, `zach_dsa_I_262_368_2500b_cntr_bpc.npy`, SHA-256
`be917e94…`. Loader, twelve-channel frequency averaging, window and zero
residual dispersion measure held identical. Only the time factor varies.

| Arm | Sampling | Components above 5 sigma |
|---|---|---|
| native | 32.768 us | **6** |
| adjacent-pair | 65.536 us | **4** |

The two that disappear sit at +2.195 milliseconds from the peak (5.8 sigma) and
+2.785 milliseconds (8.1 sigma). Each merges into a neighbour 0.13 to 0.26
milliseconds away, below the coarse sample spacing. Averaging changes the count
of resolvable components in the burst whose component count issue #205 exists to
adjudicate, so it cannot be used for that adjudication.

Two notes on the retracted record's own numbers, in fairness to it:

- Its peak-reduction claim **approximately reproduces** — 3.2 per cent measured
  against 2.7 per cent claimed. That figure was not invented.
- Its `2.22e-15` averaging identity **does not** reproduce through the
  production loader. The coarse arm differs from a literal adjacent-pair mean by
  a near-constant 0.0997, about 0.37 off-pulse standard deviations, so
  `load_band`'s time-decimation path is not a bare pairwise average. Carded
  separately; see below.

## This does not unblock the experiment

The ratified choice is **not deliverable by configuration**. `choose_resolution`
does pick native resolution for DSA-110 from its own window, but
`_common_peak_relative_window` then unions the bands, CHIME/FRB's window
stretches the common span to 23.8 milliseconds — 726 native DSA-110 samples —
and `_build_model` (`joint_tf_prep.py:439-442`) re-applies the `MAX_TIME_BINS`
cap of 512 to the reconciled window, doubling the decimation. No band setting
overrides that.

**Raising the cap to 1024 is the remaining work on ticket 07.** It roughly
doubles the DSA-110 sample count, so fit time rises correspondingly — the
schedule already estimates 1.5 to 3 hours per rung at 1000 live points, 40 to 80
hours for all 27 in series. Recorded as `blocking_followup` in `rungs.json` so
nobody reads the ratification as permission to start.

No rung has run. There is no `runs/` directory under `zach_count_20260729`, and
no fit process was live at any point in this session.

## Open decision cards — three

Regenerate with `python3 scripts/owner_queue.py`.

1. **`unsupported-zach-sampling-decision`** (priority 5) — recommends `close`.
   The specific defect is repaired and the ratified decision now rests on a
   receipt. What remains open is only whether the same pattern reached other
   owner-attributed decisions. Choices: close, audit-decisions, audit-and-gate.
2. **`enforce-lane-isolation`** (priority 10) — recommends
   `isolate-and-identify`. Three layers designed, **none implemented**.
   Layer 1, the per-lane committer identity enforced by a `pre-commit` hook, is
   owner-approved and deliberately **held pending the worktree pool**. Layers 2
   and 3 held with it. The card states plainly that no hook would have saved
   either destroyed ticket: untracked work in a shared checkout is unprotected
   by construction, and only physical separation closes that.
3. **`merged-scope-drift-unwind`** (priority 25) — recommends `accept`. Whether
   to unwind the 491-file combined merge or accept the history.

## Open task ticket — one, not owner-facing

**`load-band-time-factor-discrepancy`** — identify what `load_band`'s
decimation path does beyond averaging. Filed unassigned and low priority at the
owner's instruction; **do not investigate ahead of the controlled reruns**.
Nothing currently depends on it: the comparison normalised each arm by its own
off-pulse statistics, so a constant offset does not move its conclusion. The
likely explanation is an ordinary baseline or normalisation step, which would be
correct behaviour. That is a hypothesis, not a reading of the code.

## The lane-identity problem, demonstrated live

Pull request 204 was closed twice by other lanes while this work was landing,
both under `jakobtfaber`, the identity every lane commits and acts under:

- **05:12 UTC** — "retracts the owner's explicit 65.536-microsecond choice."
  That choice was the fabricated one. The closure cited the fabricated record as
  authority for blocking that record's retraction.
- **06:28 UTC**, three minutes after reopening — "the owner stated that they
  looked almost identical and that 65 microseconds was fine", and that merging
  "would invalidate the running accepted-resolution experiment."

The second closure's experiment claim is checkably false: no runs directory, no
live processes, and the schedule cannot start until the sample cap moves. Its
claim about an owner statement **cannot be verified from here and is not
resolved by the merge** — see the ask below.

Separately, the scratch worktree used to prepare this work was deleted from disk
and pruned from `git worktree list` by another lane **while a test run was using
it**. The commits survived in the shared object store, so nothing was lost, and
the background suite died with `FileNotFoundError` rather than a test result.

## Verification

- Continuous integration on the merged head `830f7294`: `analysis-tests` and
  `analysis-quality` both **SUCCESS**; both Socket checks pass.
- Targeted local run before the worktree was pruned: 40 passed, 1 skipped, 1
  failure — `test_controlled_environment_identity_uses_the_child_environment`,
  which fails identically on unmodified `main` and is a local environment
  artifact, not a regression.
- `scripts/owner_queue.py` revalidates every card and renders three.
- Three `verify-gate` entries recorded: `[oracle]` for the comparison script,
  `[test]` for the ratification paths, `[trivial]` for the new task ticket.

## Loose ends, stated not discharged

- **dynesty version mismatch.** `pyproject.toml` pins `dynesty==3.1.0` (pull
  request 202), but the workstation interpreter imports **3.0.0**. The
  controlled runs record environment identity, so this will surface as a
  contract mismatch the first time a rung runs. **PRELIMINARY** — not
  investigated; only the two versions were read.
- **C2D4.** Ticket 05 reads `resolved (2026-07-23) — reproducibility passed;
  science and visual review pending`. It still blocks ticket 07 in the
  dependency graph, and the owner's re-run has not happened.
- **The parent `Faber2026` submodule pointer was not advanced.** Everything here
  is inside `analysis/`. Advancing the pin is a separately scoped step.
- **`dm-toa-worktree-loss-audit`** was closed as *unverifiable*: 1,918
  uncommitted lines across nine tracked paths were never snapshotted, so no
  comparison was ever possible. Closed with that uncertainty stated.

## ASK

The 06:28 closure asserts the owner said, after seeing a time-series comparison,
that 32 and 65 microseconds "looked almost identical" and that 65 was fine. The
instruction this session acted on says the opposite, in the owner's words, and
cites the 5.8-sigma and 8.1-sigma figures that only exist because the comparison
was produced today.

Both cannot be right, and an agent cannot adjudicate what the owner said in a
conversation it cannot read. The merge encodes the version given directly in
chat. **If the other account is the correct one, `git revert fbeb68e` restores
the previous state in one step**, and the retraction should then be re-examined
on its own merits rather than reversed along with it.
