---
kind: review
title: "Scattering method reassessment: independent Codex review — BLOCK"
comments: none
---

**Verdict: BLOCK for the reviewed state.** The study establishes useful examples of model mismatch and a real production discontinuity. Incorrect truth definitions, unsupported causal conclusions, and an incomplete implementation specification prevent approving the decision memo as completed scientific validation. Family 3 remains a reasonable *provisional recommendation*, not a validated measurement method. No fitted value is ready for manuscript promotion.

## Prioritized findings

Paths prefixed `E/` refer to `analysis/docs/rse/specs/research/method-reassessment-2026-09-11/` in the repository identified below.

### 1. Block — the injected “mean delays” do not exist

**Sources:** `E/injection_recovery.py:112`, `:121`, `:202`, `:217`, `:405`; `E/decision-memo.md:152`; `E/make_report.py:173`.

`pbf_thick` has asymptotic density proportional to t^(-3/2). Its first moment, the integral of t times that density, diverges. Dividing its scale by 1.2337 cannot make its mean equal the requested tau. Its integral over positive time is also **2**, not 1 (independently integrated: 2.0000000000002207). The two-screen control contains a thin kernel with tail t^(-3.67/2), whose mean also diverges; production's own docstring acknowledges this at `analysis/scattering/scat_analysis/burstfit.py:220`.

Consequently, the memo's “index of the summed mean delays, 4.16” is undefined. The classifier instead reports **4.00**, the first screen's exponent, as the composite truth; its tau comparison uses only the first screen's 0.6 ms scale. The generated table and red truth marker propagate those definitions. Numerical posterior locations remain observations for these exact toy arrays, but neither composite coverage nor mean-delay recovery has the stated meaning.

**Fix:** define a finite, explicit target statistic and verify the named medium kernel, or retain these as generic heavy-tail/composite stress tests with mean-delay and composite coverage claims removed. If the injected arrays change, rerun their cases; if only the interpretation changes, regenerate the classifications, report and figures without asserting a physical mean. Do not silently relabel old numerical outputs as a corrected physical model.

### 2. Must-fix — bin-centre sampling is only part of the discontinuity

**Sources:** `E/kernel_switch_check.py:63`, `:68`, `:71`, `:74`; `E/decision-memo.md:54`, `:72`, `:351`; `analysis/scattering/scat_analysis/turbulence.py:39`; `analysis/scattering/scat_analysis/burstfit.py:772`.

The quoted 17.0%/5.2%, −0.381/−0.303 samples and 1.37%/3.32% reproduce. But the two model evaluations also change alpha: its left limit at beta=3.98 is **4.020202**, while the right branch uses **4.0**. Thus tau at each observing frequency changes too. A sampling-only fix cannot guarantee the proposed 0.1% continuity threshold. Holding the analytic kernel and time grid fixed, this alpha jump alone changes the CHIME profile by **0.350% of global peak**, or **0.526%** for the normalized middle channel.

The reported before/after errors also use different comparisons: the first is the raw maximum over all channels; the latter normalizes areas and selects one middle channel. The 0.04% comparison comes from the code audit's best-scaled root-mean-square error on a different, resolved grid; it is not the same statistic as these maximum residuals. “Two to three hundred times” is not an established common-metric result.

**Fix:** distinguish sampling, finite-window normalization, kernel switching and alpha switching; compare consistent channels, normalization and error metrics. Specify continuity of the complete forward model, including alpha, across both resolved and unresolved regimes. Retain the closure-test hold.

### 3. Must-fix — “never visited” and the asserted trapping mechanism exceed the saved evidence

**Sources:** `E/decision-memo.md:94`, `:235`, `:243`; `E/production_path_injection.py:133`, `:137`; `E/kernel_switch_check.py:82`.

The original weighted posterior has positive mass at beta≥3.99: **4.51175600146337e-105** for exp-a3.0 and **2.7312399084559325e-79** for exp-a4.0. Such values require original samples on the exponential branch. The zero in `mass_above` is a finite equal-weight resampling result, not proof of no proposals or no visits.

The +3.7 log-likelihood difference is a conditional optimization at two fixed beta values, freeing tau and arrival times while holding widths and dispersion parameters fixed. It does not integrate the nuisance-parameter volume, quantify posterior odds, or diagnose the random-walk bounding mechanism. A narrow branch with a better conditional optimum need not dominate the marginalized posterior. The beta clip at 3.99 does not itself prohibit entry: the model dispatches to the analytic branch before that power-law-kernel clip matters.

**Fix:** report negligible sampled posterior weight and a better conditional optimum; label missed-mode/trapping as a hypothesis. A definitive mechanism needs branch-restricted posterior integrations or controlled sampler/initialization comparisons. No long fits are required merely to narrow the present claim.

### 4. Must-fix — the study does not “clear inference,” establish calibration, or isolate the residual bias

**Sources:** `E/decision-memo.md:17`, `:130`, `:259`, `:279`; `E/injection_recovery.py:165`, `:212`, `:274`; `E/production_path_injection.py:90`; `analysis/scattering/studies/beta-proof-of-concept/run_beta_poc.py:92`; `analysis/CONTEXT.md:494`; `analysis/docs/rse/wayfinder/map-apj-submission.md:116`.

The nine thin-screen recoveries use a shared simulator/fitter implementation, a proper gain prior, a continuous kernel and a shared residual dispersion measure. Production differs in these respects. Nine selected cases covering truth nine times in their 95% intervals is useful limited recovery evidence, not interval calibration; six configurations share one noise seed, with only one configuration repeated across four seeds.

Both production thin controls inject with the **same production forward model** used for fitting. A truth-versus-fit half-sample convention mismatch therefore cannot explain their residual beta offset as written. Raising tau changes the whole pulse and its identifiability; these two runs do not separate noise, nuisance-prior volume, gain marginalization, sampling error and resolution. The isolated control's 0.10-to-0.03 change is real; its causal attribution remains unverified.

The controls demonstrate that selected mismatches *can* produce rails. They do not assign causes to the actual railed sightlines, as charter deliverable 3 requests. The broad “cleared inference/model-class effect” statements in CONTEXT and the map compound this overclaim.

**Fix:** state limited self-consistency and synthetic counterexamples. Keep actual sightline causes unresolved; explicitly defer or amend that charter deliverable. Carry uncertainty into the decision card, CONTEXT and map. Describe the bias reduction without claiming its cause has been isolated.

### 5. Must-fix — the proposed headline path is not wired by the cited production switches

**Sources:** `E/decision-memo.md:301`, `:330`; `E/code-audit.md:81`; `analysis/scattering/studies/joint-refits/run_joint_fit.py:144`; `analysis/scattering/scat_analysis/burstfit_joint.py:970`, `:1062`; `analysis/radio_pipeline/fitting/joint_burst.py:594`, `:685`.

The campaign's `--alpha-lo/--alpha-hi` options are deprecated aliases mapped into beta bounds. They do **not** enable an independent alpha<4 exponential model. `--gain-s2` routes to the multi-component beta-coupled likelihood, also changing the shared frequency-dependent width setup. The separate `radio_pipeline` implementation has a shared tau-at-1-GHz/free-alpha law; its mere existence does not implement or validate this memo's stated per-band headline contract on the campaign path.

The specification leaves the within-band tau law and corresponding priors unclear. The tested harness also uses one width law and one residual dispersion measure, unlike the proposed independent per-band nuisance parameters. Evidence sensitivity on that harness cannot validate the eventual different model. The memo invokes the referee's six checks but omits an explicit competing-geometry requirement from its actionable specification; per-sightline injection also should not be called rank-based calibration without the required repeated-generative experiment.

**Fix:** name the actual intended entry point and specify the per-band/reference-frequency parameterization, within-band law, nuisance parameters, priors and remaining implementation/validation work. Keep family 3 provisional and map every claimed acceptance check to evidence or a deferred gate. Do not imply the existing flags produce it.

### 6. Must-fix — the published low-tau truth labels are wrong

**Sources:** `E/injection_recovery.py:363`; `E/decision-memo.md:118`, `:136`, `:203`, `:218`; `E/make_report.py:144`, `:152`.

The short-tau cases inject **0.15 ms**, not 0.1 ms. The raw JSON, log and summary agree on 0.00015 seconds; rounded case IDs hide the distinction. At 1.4 GHz these correspond to **0.83, 1.04 and 1.15 samples** for beta=3.3, 3.67 and 3.9, so the figure's universal “square: sub-sample” label is also inaccurate.

The signal-to-noise=100 memo row uses gain scale 1, while its 30 and 300 rows use scale 10. The existing arm-a baseline gives the correctly matched row **3.666, 3.673, 3.680**. The figure already uses that baseline. Gain scale 1–100 spans **two decades**, not three.

**Fix:** use exact truth metadata for labels; describe short-tau cases as near one sample; use the matched baseline. There are **29 cases: 10/10/9** by arm; the arm-c table reuses a baseline, so its ten displayed rows do not imply a missing fit.

### 7. Must-fix — the documented rerun cannot reproduce the complete report safely

**Sources:** `E/decision-memo.md:364`; `E/kernel_switch_check.py:132`; `E/injection_recovery.py:325`.

The reproduction commands omit `kernel_switch_check.py`, which generates the four switch JSON products and the switch figure. A clean results directory therefore cannot reproduce those report sections. If the switch script is now run after all five production controls, `flip_check_from_posterior` rebuilds every case with default tau=0.05 ms, including the new **0.2 ms** control. It would compare that control's posterior against the wrong synthetic data. The current saved flip file contains four cases, so this is a reproducible future corruption risk rather than evidence that its current four rows are wrong.

The harness also omits a random state from `resample_equal`; sampler seeds alone do not fix the derived quantiles and stored shape samples. The reproduction claim needs that distinction.

**Fix:** pass each case's actual tau into the flip reconstruction, handle older records explicitly, include the switch command in the documented sequence, and seed resampling or use deterministic weighted summaries. Regenerate only affected derived products; preserve original fit outputs with their identities.

### 8. Should-fix — the code audit conflates historical and current defects

**Sources:** `E/code-audit.md:13`, `:52`, `:70`, `:81`; `analysis/scattering/studies/joint-refits/run_joint_fit.py:116`, `:392`; `analysis/scattering/studies/beta-campaign/sim_gate.py:42`.

Current campaign code accepts and forwards a seed; the controlled entry point requires it. The audit's “no seed passed by CLI” defect and proposed unseeded-repeat test are stale. The audit says the simulation gate “passed” without marking that as historical, while its current import path is broken as the later memo correctly reports. The proposed alpha-flag test cannot fit alpha<4 (finding 5).

**Fix:** state the revision/date for historical defects and update the current capability/falsifying-test table. Keep the simulation import repair as a follow-up, not a claimed working gate.

## What checked successfully

- All 29 harness records correspond to the executable inventory. Classification recomputation, saved shape quantiles, and 174 selected summary values agree. Generated harness table, production table, verdict section and switch section reproduce **exactly in memory**, without writing repository files.
- Nine thin-screen cases: truth inside 95% interval in 9/9 and inside 68% in 5/9. These counts mean how often the quoted posterior interval contains the injected value; their calibration interpretation is limited as above.
- Five current production summaries match the memo's rounded quantiles. All call totals are below the recorded 400,000 cap; logs show completed current cases after earlier interrupted attempts. This is not proof of posterior convergence.
- Direct Gaussian covariance calculation agrees with `band_loglike` to **1.8e-15**; no algebraic gain-marginalization error found. Noise/SNR construction, thin and exponential kernels, second-component construction, and edge-class bookkeeping are coherent for the stated toy experiment, subject to findings 1 and 4.
- Independently reran the lightweight branch and harness kernel checks. Existing production boundary tests: **4 passed**. They explicitly tolerate/pin the alpha jump and use resolved pulse parameters; they do not certify the proposed stronger gate.
- Inspected all four rendered SVG figures. Their plotted findings match the report, subject to the truth markers/labels above.
- Claims ledger still has eleven scattering rows `blocked` and chromatica `documented_fail`. The owner ticket records rejection of all three controlled panels. Manuscript and production files have no changes in this lane.

## Final review gate coverage

| Gate | Result for this exact state |
|---|---|
| Equation / calculation | Gain likelihood checked; kernel discontinuity reproduced; mean-delay definitions fail. |
| Model / fit | Limited toy recovery checked. Production convergence, bias attribution, real-sightline causes and proposed headline implementation unvalidated. |
| Reference / history | Main current trust state and owner rejection checked; current audit has stale claims. Full historical/reference verification incomplete. |
| Independent no-context review | This fresh Codex reviewer did not implement or shape the submitted work. Initial verdict BLOCK. |
| Ticket acceptance | Audit, history, study and memo exist. Scientific findings require revision. Ticket 01 remains open, boxes unticked, decision card pending; do not mark acceptance complete. |
| Final-state approval | **Not granted.** Re-review all changed scripts, derived outputs, memo, decision card and tracked lane summaries after addressing findings. Filling the review placeholder is not approval. |
| Repository publication | This review does not approve the present state as completed work or authorize a scientific merge. Fix/review before the requested publication gate; a clearly labelled draft may communicate unresolved work only. |
| Manuscript promotion | Remains blocked. Methods text is a separate future change. Raw-data certification still requires the owner; this review does not certify it. |

## Unverified

No long fits, alternate-sampler runs, branch-restricted evidence integrations, real-burst reprocessing, or production-path calibration were run. Full weighted posterior samples are not retained in these evidence JSONs, preventing independent resampling/convergence reconstruction. The first four production records omit explicit injected tau metadata; code/logs identify the intended default, but no retained data hash proves those exact arrays.

The historical ledger was read in full and its central current-status claims checked; all historical fixes, archived outputs, population assertions, and cited physics literature were not independently revalidated. Browser search found Williamson's original paper; loading the original PDF timed out. Its exact geometric formula attribution remains unverified. Finding 1 follows directly from the implemented equation and does not depend on that attribution.

The 0.04% shape comparison is a prose-only code-audit measurement on a different grid, with no corresponding result JSON or runnable measurement retained in this evidence root. No reproducibility claim is made for it. The package's reproducibility commands were inspected, not executed as a long campaign.

## Reviewer and exact reviewed state

**Reviewer:** Codex, GPT-6 Astra, high reasoning, Traycer GUI harness; agent `940e86b7-c98a-4009-8aba-1fe337863ae3`, host `jakob-mbp`. Repository read-only by task scope; **not a claimed enforced read-only sandbox**. Traycer messaging worked; the headless/transport-unavailable wording in the prompt was stale. The assigning agent independently cross-checked numbers and supplied observations; every finding above was verified locally by this reviewer.

**Repository:** `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026`.

**Branch:** `method-reassessment-2026-09-11`; HEAD `237502d455dcdb9f691600b8773d589406962e52`; base main `3afb381dcf3e2923b5e087e888a14c957523649f`.

**Snapshot:** 2026-09-12T02:25:37.544998Z (2026-09-11 19:25:37 PDT), 62 files. Includes the entire evidence root except Python bytecode caches, the committed charter ticket, and uncommitted CONTEXT, journal, map and ticket-07 changes. `.hydradb-plugin-data/` is outside scope and untouched. No production/manuscript changes. See [exact paths, hashes and timestamps](initial-review-evidence/reviewed-state.json), [independent check script](initial-review-evidence/review-check.py), and [check results](initial-review-evidence/check-results.json). No reviewed file had changed at the end-of-review hash comparison.

The original review was conducted outside the repository and did not edit repository files. This is a copied receipt; its check script, results and reviewed-state manifest are reproduced under `initial-review-evidence/`.


## Revision response

The revised memo keeps family 3 provisional and actual-sightline diagnosis unfinished. Original fit outputs are preserved. Corrections remove undefined composite/mean-delay targets, qualify discontinuity and sampler claims, fix labels and reproduction, and update current capabilities. Final-state review approves provisional draft publication only; see [Claude final review](claude-final-review.md). Ticket 01 remains open and scientific validation is not approved. The original exact-state manifest and review checks remain in the Traycer review artifact.
