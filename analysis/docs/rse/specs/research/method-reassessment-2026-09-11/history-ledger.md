# History ledger: two-band scattering re-fit campaign, since 2026-07-01

Compiled 2026-09-11 for the method-reassessment review. Read-only evidence
gathering; every entry is sourced to a specific path. Nicknames map to FRB
names via `analysis/docs/rse/control/board/claims-audit.md`: zach=20220207C,
whitney=20220310F, oran=20220506D, isha=20221113A, wilhelm=20221203A,
phineas=20230307A, freya=20230325A, johndoeII=20230814B, hamilton=20230913A,
mahi=20240122A, chromatica=20240203A, casey=20240229A.

## Chronological ledger

**2026-07-06: rail-taxonomy fragmentation.** Three different, conflicting
definitions of "railed" existed in production code at once (`grade_beta_campaign.py:65`,
`sim_gate.py:72`, `gate_joint_committed.py:47-55`). Cause: code bug, no single
source of truth. Fix: ADR-0008 + unified `flits/fitting/rails.py::classify_rail`.
Validated: `test_rails.py` regression guard vs. a committed classification.
Status: resolved per plan (landing not independently reconfirmed here).
Evidence: `analysis/docs/rse/specs/plan-trust-reset-revalidation.md:39-40,435-548`.

**2026-07-06: mislabeled posterior-predictive check.** What was recorded as
"PPC" was actually a per-band OLS-gain chi-square statistic, not a real
posterior-predictive check. Cause: methodology/model-class labeling error.
Fix: new `analysis/ppc.py` (replicated-data chi-square + lag-1 autocorrelation)
wired via `analysis/ppc_joint.py`; old statistic renamed
`*_ols_gain_chi2.json`. Validated: toy tests on well- and mis-specified models.
Status: resolved per plan. Evidence: `plan-trust-reset-revalidation.md:44,587-690`.

**2026-07-06: tau injection-recovery offset.** Injection-recovery calibration
for the scattering time tau showed a stable ~2.47-2.50x ratio offset from
truth; only linearity had been checked, not absolute accuracy. Cause:
sampler/estimator or definitional mismatch (tau or C1 convention vs.
tau*Delta-nu_d=1), unresolved. Fix: none yet; xfail test added pending root
cause. Status: open. Evidence: `plan-trust-reset-revalidation.md:45,548-587`.

**2026-07-06: gamma_D prior pile-up.** The gamma hard prior bound (-5,5)
caused 5 of 8 committed energies rows to pile within 0.15 of -5. Cause: prior
too narrow. Fix: GAMMA_FLOOR=-10 relaxation diagnostic rerun, not yet a
citable refit. Status: open. Evidence: `plan-trust-reset-revalidation.md:48-49,1238-1293`.

**2026-07-06: coverage-check gap.** `fit-verify.js` globbed only
`*_fit_results.json`, silently missing `*_joint_gate.json`. Cause: code bug.
Fix: glob list extended, `--list-coverage` dry run added. Status: resolved.
Evidence: `plan-trust-reset-revalidation.md:50,690-707`.

**2026-07-06: no in-repo builder for CHIME scattering cubes.** The 24
`*_32000b_cntr_bpc.npy` cubes have no in-repo builder; it lives off-repo on
h17/arc. Cause: data/provenance gap. Fix: locate and capture the builder, or
mark `UNVERIFIED_BUILDER`, with hash cross-checks. Status: open at
plan-writing. Evidence: `plan-trust-reset-revalidation.md:34-38,755-894`;
`docs/rse/control/BOARD.md:38-39` still carries this as an open,
unchecked item ("do the dynamic spectra feeding the scattering fits share
the gen-1 de-chirp defect?").

**2026-07-06: wave-1 trust reset.** Every beta/tau/alpha, multiplicity, and
PPC scattering result for all 12 sightlines was revoked. Cause: process-level
(unreliable rail taxonomy plus unverified inputs above), not a single defect.
Fix: none yet; scattering marked `blocked` pending a from-scratch re-fit
campaign and geometry-model selection. Status: open, still current as of
2026-09-11 (git log shows `docs/rse/control/evidence-ledger.toml`, which
generates the claims-audit ledger, has had no commits since 2026-07-20).
Evidence: `analysis/docs/rse/control/board/claims-audit.md` (scattering rows
for every sightline).

**2026-07-06: chromatica gate FAIL.** chi-square-reduced approx 11.6 (CHIME)
/ 9.3 (DSA); model panel flat against strongly structured data. Cause:
model-fit quality (excluded from all citable products). A later note flags a
possible cross-generation quoting artifact (committed gate says MARGINAL on
an older mixed-legacy fit vs. this FAIL on the beta-campaign fit) that has
not been root-caused. Status: open/unresolved diagnosis. Evidence:
`analysis/scattering/studies/beta-campaign/CAMPAIGN_REPORT.md:53,63-64`;
`plan-trust-reset-revalidation.md:1335-1354`.

**2026-07-06: ADR-0007 re-open trigger.** 10 of 12 posteriors railed at the
thin-screen ceiling beta=4 under the pass-1 campaign. Cause: model-class
inadequacy (thin-screen family cannot resolve these sightlines). Fix:
ADR-0007 amendment proposing an extended-medium (uniform-line-of-sight) PBF
kernel, beta-coupled. Status: open, design not yet validated. Evidence:
`CAMPAIGN_REPORT.md:56-59,111-113`.

**2026-07-15: modulation-index gate inconsistency.** The scintillation
modulation-index gate (m<=1.5) is logically inconsistent with the two-screen
bound of sqrt(3)~1.73; 6 of 12 CHIME rejections cite this gate. Cause:
prior/gate-definition inconsistency with the surviving model class. Fix:
none yet, deferred. Status: open. Evidence:
`analysis/docs/technical_review_triage_2026-07-15.md:59-60`.

**2026-07-15: phantom DM_int sightlines.** Six sightlines (zach, isha,
wilhelm, freya, hamilton, johndoeII) showed nonzero intervening DM with no
confirmed foreground system. Cause: code bug (an empty registry silently
fell back to a legacy CSV in `sightline_budget.foreground_unified`). Fix:
FLITS PR #183, registry made authoritative, regression + parity tests added.
Status: resolved. Evidence: `technical_review_triage_2026-07-15.md:109-113`.

**2026-07-17: no trustworthy post-PL-PBF figure inputs.** All 11 fit JSONs
on hand predated the PL-PBF rejection (no beta posterior); the expected
Whitney C2D2 JSON was missing; other dumps were mistagged. Cause:
data/provenance gap from the model-class change. Fix: disconnect stale
Figure 2 and Figures 11-16 inputs, mark manifest rows unembedded. Status:
resolved by fail-closed removal. Evidence:
`analysis/docs/rse/specs/research-post-pl-pbf-figure-reconciliation-2026-07-17.md:13-40`.

**2026-07-18: PL-PBF rejected campaign-wide.** Three-way test: casey
delta-ln-evidence +3.3, wilhelm -3.3 vs. production EMG, with the PL-PBF
shape parameter railed high in both. Cause: model class (physical heavy-tail
inner-scale model does not explain the anomaly). Fix: PL-PBF dropped;
production EMG limits stand. Status: resolved (rejected). Evidence:
`analysis/docs/rse/specs/handoff/handoff-2026-07-18-14-51-jointtf-plpbf-campaign.md`;
memory note `plpbf-rejected-emg-stands`.

**2026-07-18: 12/12 mass-refit landscape.** After PL-PBF's rejection, a
fresh refit round classified the sample as 4 interior / 3 ceiling-adjacent /
3 ceiling-rail / a new floor-rail class (hamilton, whitney). This
classification does not match the pass-1 campaign table below (which puts
hamilton and whitney at railed-hi, i.e. ceiling). The two classifications
have not been reconciled in any document read this session. Status: open
discrepancy. Evidence: `docs/rse/control/BOARD.md:117-124` (Scattering
re-fit campaign section) vs. `CAMPAIGN_REPORT.md:48-51`.

**2026-07-18 14:08: scheduler stall.** `fit_pool.sbatch` had no `--mem`
directive; job 120 claimed the whole node's memory ledger, serializing 14
pending jobs against 38 idle CPUs. Cause: code bug (Slurm resource request).
Fix: `MinMemoryNode=2048` set, job requeued; 33 minutes lost, no artifacts
lost. Status: resolved. Evidence: readiness journal, 2026-07-18 14:08.

**2026-07-18 15:24: dipole-mask discriminant.** The casey (+5537) and
wilhelm (+731) free-alpha wedges were tested for peak association by masking
the brightest component. Casey: +3540/+3795 of the wedge survives masking
(peak-associated, diagnostic-only significance). Wilhelm: +634/+586 survives
(intrinsic, robust to excision). Cause: n/a, this is a diagnostic result
identifying two-screen chromaticity as the shared mechanism with different
per-burst origins. Status: resolved (mechanism identified), feeds the
two-screen charter below. Evidence: readiness journal, 2026-07-18 15:24.

**2026-07-18 16:04: scintillation-leakage mechanism ruled out.** Injection
test with real two-component scintillation bandwidth and real channelization:
6/6 recover alpha~4, bias <= 0.003 at modulation index 1. This is a
static-control, noise-level result and is a *different* test from the two
other "6/6"-shaped results in this campaign (see Patterns, below); do not
conflate them. Status: resolved, scintillation-gain leakage excluded as the
wedge mechanism. Evidence: readiness journal, 2026-07-18 16:04;
`analysis/docs/rse/specs/research/evidence/free-alpha-diagnostic-2026-07-22/source/PLPBF_FITTER_PROVENANCE.md:208`
("6/6 recover alpha ~ 4; max bias = 0.017").

**2026-07-18 16:14: two-screen forward model chartered.** Owner selected
Option A: a physically-tied two-thin-screen model as the surviving hypothesis
for the casey/wilhelm wedges, gated behind a pre-registered Stage-0
falsifier before any real-data fit. Evidence:
`analysis/docs/rse/specs/notes/charter-two-screen-forward-model-2026-07-18.md`.

**2026-07-18 17:09: zach C2D4 off-window ghost.** A fourth fitted component
had t0 = -1.36 ms against a fitted window of [0, 5.9] ms, a ghost outside
the data. Cause: sampler/prior bug, an unbounded t0 prior exploited by the
gain marginal likelihood. Fix: new guardrail, bound t0 priors to the fitted
window. Status: resolved (result adjudicated invalid). Evidence: readiness
journal, 2026-07-18 17:09.

**2026-07-18 17:42: root cause: t0-prior bug.** `burstfit.build_priors` set
t0 = init +/- 2*max(tau,10), an untethered +/-20 ms window inherited by every
joint fit. Cause: code bug in prior construction. Fix: campaign-wide
off-window audit (26 of 51 JSONs flagged), bounded re-run grid approved,
prior-fix PR ordered before any re-run. Status: resolved via fix and
remediation reruns (below). Evidence: readiness journal, 2026-07-18 17:42.

**2026-07-19 14:06: two-screen Stage-0 falsifier FAILS.** All grid points
gave the wrong sign: casey +0.17/+0.42/+0.56, wilhelm +0.90/+1.45/+1.68,
monotonic in the screen-ratio parameter r: same-alpha two-screen mixing
biases the free-alpha diagnostic upward, opposite the observed sub-4 wedges.
Cause: model class (rung-1 two-screen mixing cannot reproduce the anomaly).
Status: rung-1 falsified; rung-2 (independent beta for the second screen)
condition met, owner decision pending; **note a discrepancy**:
`analysis/docs/rse/specs/handoff/handoff-2026-07-19-23-24-jointtf-grok-harvest-revalidation.md`
describes this Stage-0 result as "16/16 wrong-sign FAIL," while the
readiness journal and the charter's own grid (3 r-values x 2 bursts = 6
points) both give 6/6. The two counts have not been reconciled. Separately,
that same handoff notes `TWOSCREEN_FITTER_PROVENANCE.md` still read PENDING
after the result was reported, on a detached/dirty h17 worktree, with the
compute session ending in an `error` outcome: the Stage-0 result itself is
flagged there as "not independently revalidated." Status: open. Evidence:
readiness journal 2026-07-19 14:06; handoff-2026-07-19-23-24, lines 23-166.

**2026-07-19 14:06: sampler mode-trapping in the count wave.** hamilton
C5D1 fell 41 log-evidence units below C4D1 in the same floor mode (rejected);
C4D2 flipped hamilton to a healthy high mode but the cross-mode evidence
comparison (-1600) is invalid by protocol, forcing a profiled-gain fallback.
phineas C4D4 mode-trapped to a floor solution (beta 3.018) against a healthy
production value (beta 4.043). Cause: sampler (mode-trapping, invalid
cross-mode evidence comparison). Status: hamilton resolved via fallback;
phineas open/suspect. Evidence: readiness journal, 2026-07-19 14:06.

**2026-07-19 14:20: two confirmed off-window ghosts in production.** oran
C2D1 (t0=-5.23, ghost fluence 3.0 vs. real 2.5) and johndoeII C2D2 (t0=-6.16,
ghost fluence 26.2 vs. real 8.4, severe). Cause: same t0-prior bug as above.
Fix: bounded (v2) re-runs approved and merged as FLITS PR #205 (t0-clamp).
Validated: direct visual vetting found no real pre-window structure in
either burst. Status: resolved via v2 reruns. Evidence: readiness journal,
2026-07-19 14:20.

**2026-07-19 22:11: v2 rerun mode jump.** zach C2D3 with gain-prior variance
s2=10 produced a mode-jump into D4 that was ruled invalid; s2=100 was kept
instead. Cause: sampler. Status: resolved by parameter choice, but leaves
zach's second-screen multiplicity question open (see 2026-07-22). Evidence:
readiness journal, 2026-07-19 22:11.

**2026-07-22: Zach C2D4 job 180 deprecated.** The prior production run
could not be promoted or copied forward; it required reconstruction under
frozen, reproducible-run guardrails (hash-pinned inputs, deterministic
double execution) before any new panel could be trusted. Cause: downstream
of the t0-prior/mode-jump lineage above. Status: open at plan-writing,
resolved operationally by the controlled-rerun infrastructure that produced
the 2026-09-04 decision below. Evidence:
`analysis/docs/rse/specs/plan-controlled-joint-scattering-reruns-2026-07-22.md:35-67`.

**2026-07-23: controlled-rerun panels reproduce but fail scientific
review.** Oran C1D1, JohnDoeII C2D2, and Zach C2D4 all passed exact
byte-for-byte reproduction against their receipts. Full-size inspection and
receipt-bound diagnostics did not support automatic admission for any of the
three; each was marked "revise." Cause: model/fit adequacy, not
reproducibility. Status: pending owner decision (resolved 2026-09-04, below).
Evidence:
`analysis/docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-06-admit-new-panels.md:92-113`.

**2026-09-04: owner rejects all three controlled-rerun panels.** Owner
decision during the queue walkthrough: revise Oran C1D1, JohnDoeII C2D2, and
Zach C2D4; admit none to independent review. Stated reason (verbatim):
"Every model family fails its prior-edge diagnostic and retains additional
crop, component-width, low-fluence or structured-residual defects. Exact
reproduction proves identity, not scientific adequacy." Cause: model class /
fit adequacy across every family tried, not a single bug. Effect: scientific
trust, fitted values, and manuscript promotion remain blocked for all three
sightlines. Status: open (revision, not resolution). Evidence:
`analysis/docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-06-admit-new-panels.md:11-68`;
`docs/rse/verify/joint-scattering-controlled-rerun-06-owner-review-20260723/README.md`
and `decision-packet.json` (sha256 hashes recorded in the ticket).

**Ongoing, undated: release gate still fails closed.** Independent of
scattering-specific defects, `analysis/ADVERSARIAL_REVIEW_BLOCKERS.md`
records the release gate as `failed`/`fail_closed`
(`expanded-catalog-gate-not-passed`, `source-verification-incomplete` at
46/52, stale figure-3 registry snapshot, missing figure-3 owner approval).
This blocks promotion of any scattering figure regardless of fit quality.
Cause: process/pin-lag, not a data defect. Status: open. Evidence:
`analysis/ADVERSARIAL_REVIEW_BLOCKERS.md:15-26,78-83`.

**Current state, 2026-09-11.** `docs/rse/control/board/claims-audit.md`
(generated from `evidence-ledger.toml`, unmodified since 2026-07-20 per git
log) still lists the `scattering` strand as `blocked` for all 12 sightlines
except chromatica, which is `documented_fail`. No sightline's scattering
result has been promoted to trusted since the wave-1 reset.

## 12-sightline status table

Primary source: `analysis/scattering/studies/beta-campaign/CAMPAIGN_REPORT.md`
(pass-1, locked 2026-07-06), the last full, per-burst chi-square-reduced
table in the repository. All 12 rows are currently trust-state `blocked` or
`documented_fail` in `claims-audit.md` regardless of the numbers below; "fit
class" here means the last recorded rail/gate class, not a current scientific
verdict.

| sightline (FRB) | fit class (pass-1) | chi2-reduced CHIME/DSA | source |
|---|---|---|---|
| freya (20230325A) | interior | 1.29 / 1.03 | CAMPAIGN_REPORT.md:42 |
| phineas (20230307A) | interior | 1.06 / 1.24 | CAMPAIGN_REPORT.md:43 |
| casey (20240229A) | ceiling-rail | 1.57 / 1.02 | CAMPAIGN_REPORT.md:44 |
| mahi (20240122A) | ceiling-rail | 1.04 / 0.90 | CAMPAIGN_REPORT.md:45 |
| oran (20220506D) | ceiling-rail | 1.02 / 1.22 | CAMPAIGN_REPORT.md:46 |
| isha (20221113A) | ceiling-rail | 1.05 / 0.91 | CAMPAIGN_REPORT.md:47 |
| johndoeII (20230814B) | ceiling-rail | 1.09 / 1.23 | CAMPAIGN_REPORT.md:48 |
| whitney (20220310F) | ceiling-rail* | 1.09 / 1.42 | CAMPAIGN_REPORT.md:49 |
| wilhelm (20221203A) | ceiling-rail | 1.57 / 6.73 | CAMPAIGN_REPORT.md:50 |
| hamilton (20230913A) | ceiling-rail* | 3.96 / 1.00 | CAMPAIGN_REPORT.md:51 |
| zach (20220207C) | ceiling-rail | 1.35 / 1.02 | CAMPAIGN_REPORT.md:52 |
| chromatica (20240203A) | gate-FAIL | 11.59 / 9.25 | CAMPAIGN_REPORT.md:53 |

\* hamilton and whitney are reclassified into an undefined new "floor-rail"
class in the 2026-07-18 post-PL-PBF mass-refit landscape (`docs/rse/control/BOARD.md:117-124`),
without a per-burst chi-square-reduced value recorded in any document read
this session. That reclassification has not been reconciled with the table
above; treat both as unresolved rather than picking one.

## Patterns

- **Prior misspecification: 5 entries.** t0-prior root cause (07-18, plus its
  three downstream ghost/reject entries: zach fine, oran, johndoeII) and the
  gamma_D floor pile-up (07-06).
- **Model class rejected or found inadequate: 6 entries.** PL-PBF campaign-wide
  rejection, two-screen Stage-0 wrong-sign falsification, ADR-0007 thin-screen
  ceiling trigger, chromatica gate FAIL, modulation-index/two-screen gate
  inconsistency, and the 2026-09-04 all-three-panels "every model family
  fails" rejection.
- **Code bugs: 5 entries.** rail-taxonomy fragmentation, mislabeled PPC,
  fit-verify.js coverage gap, DM_int registry-fallback bug, scheduler `--mem`
  stall.
- **Sampler behavior: 4 entries.** zach C2D3 mode jump, hamilton/phineas
  mode-trapping, tau injection-recovery offset (sampler-or-definitional,
  unresolved which).
- **Data/provenance gaps: 3 entries.** missing CHIME-cube builder, missing
  post-PL-PBF fit JSONs, Zach C2D4 job-180 non-promotable state.
- **Process/documentation, not a scientific defect: 2 entries.** the
  ADVERSARIAL_REVIEW_BLOCKERS pin-lag gate, and the Stage-0 count/status
  discrepancy (6/6 vs. "16/16," PENDING provenance file vs. reported result).
- **Watch for conflation:** three separate "6/6"-shaped results exist in this
  window with different meanings: scint-leakage exclusion (6/6 recover,
  bias<=0.003), the PLPBF-provenance static control (6/6 recover, bias<=0.017),
  and the two-screen Stage-0 falsifier (6/6, all wrong sign). None of these
  substitutes for the others.
- **Net effect:** zero sightlines have been promoted out of `blocked` on the
  scattering strand since the 2026-07-06 wave-1 reset; the only strand-level
  status change since is chromatica's `documented_fail`, unchanged since
  07-06.
- **Owner's question is not resolved by this ledger alone:** the entries
  split roughly evenly between prior/sampler/code defects (which argue for
  fixable engineering problems) and outright model-class rejections
  (PL-PBF, two-screen rung-1, and the blanket 2026-09-04 finding that every
  model family tried still fails), which argue for a structural mismatch;
  both patterns are present and neither dominates on count alone.
