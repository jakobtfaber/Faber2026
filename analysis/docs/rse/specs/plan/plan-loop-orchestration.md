# Plan: loop-oriented project orchestration

---
**Date:** 2026-07-12  
**Status:** Active architecture; implementation begins with control-plane and
repository-state setup  
**Authority:** The owner delegated routine orchestration, execution,
validation, and task-scoped publication to the agent. Return to the owner only
for scientific or scope choices that cannot be resolved by the recorded gates.
**Related plans:**
[circulation readiness](../plan/plan-circulation-readiness.md),
[trust-reset re-validation](../plan/plan-trust-reset-revalidation.md)
---

## Purpose

Run the remaining Faber2026 work as a coordinated set of bounded loops rather
than as loosely connected agent tasks. Each loop has one authoritative work
surface, explicit inputs and outputs, a stopping condition, and a reducer that
records its state. Scientific qualification happens before fleet execution;
manuscript restoration consumes frozen evidence rather than live analysis
state.

The paper's north star remains: use the twelve CHIME/FRB--DSA-110
co-detections to combine dispersion, scattering, scintillation, and foreground
information and determine where propagation effects arise along each
sightline.

## Operating rules

1. **One controller, separate workers.** A clean Faber2026 control worktree
   owns the dependency graph, journal, owner view, and decisions. Scientific
   code runs in clean dsa110-FLITS worktrees. Manuscript edits run in a separate
   clean Faber2026 worktree.
2. **One writer per shared surface.** Workers return structured checkpoints;
   only the controller updates the shared journal and readiness board. Fleet
   workers write burst-specific outputs; a reducer writes campaign summaries.
3. **Qualify, then scale.** No estimator or correction is run across the
   twelve-burst fleet until it passes the single-target method gate.
4. **Failure is an output.** Every scientific iteration terminates as
   `measurement`, `upper_limit`, `diagnostic_only`, `unavailable`, or
   `blocked`, with a reason and provenance. A clean non-measurement verdict is
   successful execution.
5. **Evidence precedes prose.** A manuscript claim is restored only from a
   frozen evidence record whose required strands are trusted.
6. **No mixed-lane cleanup.** Existing dirty files are preserved and
   partitioned by intent before branch switching, rebasing, regeneration, or
   commit.
7. **Owner interruption is exceptional.** Ask the owner only when a gate
   exposes materially different scientific interpretations, the CHIME stopping
   rule is exhausted, a scope change is required, or an irreversible outward
   action falls outside the standing authorization.

## Control and execution surfaces

| Surface | Location | Responsibility |
|---|---|---|
| Program controller | `Faber2026/.worktrees/loop-orchestration` | Dependency state, journal reduction, owner view, decisions, links to artifacts |
| Existing dirty checkout | Faber2026 repository root | Preserve and partition pre-existing manuscript, board, DM, scintillation, and historical lanes; no new science |
| CHIME method worktree | Dedicated dsa110-FLITS worktree based on the qualified correction branch | Correction experiments, tests, injection recovery, Freya qualification |
| Reference-analysis worktree | `~/Developer/scratch/worktrees/flits-scint-rescue` | Read-only recovered CANFAR-era reference implementation and comparison |
| Fleet worktree | New dsa110-FLITS worktree created only after the method gate passes | Twelve-burst qualification and campaign reduction |
| CHIME compute/data | `h17:/data/research/astrophysics/frbs/chime-dsa-codetections/` | Voltage/single-beam inputs, baseband container, expensive regeneration |
| DSA data authority | CANFAR, accessed through the verified `h17` CADC-proxy path | Authoritative twelve-burst DSA scintillation NPZ products |
| Local staged science data | `~/Data/Faber2026/dsa110/` | Local fitting, tests, diagnostic rendering, non-overwriting staged products |
| Sightline ledger | Dedicated clean Faber2026 evidence worktree | Twelve machine-readable evidence cards and human-readable summaries |
| Manuscript restoration | Dedicated clean Faber2026 manuscript worktree | Claim-scoped LaTeX, figure/table integration, compilation, consistency audit |

Proposed future worktree names are descriptive, not commitments. Create them
only when their prerequisite gate opens, from the then-current canonical base.

## Loop R: repository-state recovery

**Iteration unit:** one dirty-state lane in the current Faber2026 checkout.

**Initial lanes:**

1. Board and journal deployment infrastructure.
2. DM campaign plus deliberate pipeline gitlink state.
3. DM-host and foreground planning.
4. Scintillation diagnostic deck and its generated inputs.
5. Historical Figure 1 and SkillOpt artifacts requiring a keep/drop decision.

**Iteration:** inventory paths -> identify producer and dependencies -> classify
state and collision risk -> run scoped validation where applicable -> move the
lane to a focused branch/worktree or preserve it as explicitly pending -> run
closeout -> update the controller.

**Stop:** every dirty path has a named lane and disposition; the canonical
checkout can be returned to a normal branch without destroying or conflating
work.

## Loop S0: bounded CHIME method recovery

**Calibration target:** Freya, because it exposes the known instrumental ACF
failure and already has paired corrected/uncorrected products.

**Iteration unit:** one materially distinct correction hypothesis.

**Iteration:** pin inputs and hashes -> produce non-overwriting corrected and
control products -> run synthetic injection recovery -> run off-pulse null,
stability, residual-kernel, and signal-retention gates -> render a standard
diagnostic -> record verdict and failure reason.

**Pass:** all mandatory gates pass without promoting provenance or erasing real
burst structure. Freeze the method and its configuration; open Loop S1.

**Stopping rule:** no more than three materially distinct correction
hypotheses without an explicit scope decision. Parameter tuning inside one
hypothesis does not reset the count.

**Failure branch:** if the stopping rule is exhausted, present the owner with
the evidence-backed choice between (a) moving to an earlier/rawer CHIME data
stage and (b) narrowing the paper to DSA scintillation plus CHIME
limits/diagnostics. Do not continue indefinite correction search.

## Loop S1: twelve-burst scintillation qualification

**Prerequisite:** Loop S0 PASS and frozen method commit.

**Iteration unit:** one co-detected burst.

**Iteration:** resolve pinned CHIME and DSA inputs -> verify provenance -> apply
the frozen method -> calculate candidate ACF components -> apply injection,
null, stability, residual, bandwidth, modulation, and uncertainty gates ->
render a standardized contact panel -> emit a machine-readable classification
and artifact hashes.

Workers write only burst-specific prefixes. A single reducer produces the
twelve-burst table, contact sheet, exclusions, and campaign summary.

**Stop:** all twelve bursts have terminal classifications, including explicit
non-measurements where required.

## Loop E: sightline evidence ledger

**Iteration unit:** one of the twelve FRB sightlines.

Each record contains association, per-telescope DM provenance, host-redshift
status, Galactic prediction, foreground coverage and systems, host-DM
posterior, DSA scintillation, CHIME scintillation or limit, scattering status,
energy status, citable statements, and blockers.

Each strand carries one state: `trusted`, `diagnostic`, `upper_limit`,
`unavailable`, or `blocked`. Missing evidence is never encoded as zero.

Each rendered card ends with: "For this sightline, the current evidence
supports ___, but does not yet distinguish ___."

This loop may begin with already restored association, foreground, and DM
strands while later fields remain blocked. It is updated only from frozen,
pinned artifacts.

**Stop:** all twelve records validate against one schema and every proposed
event-level manuscript statement maps to trusted evidence.

## Loop M: manuscript claim restoration

**Iteration unit:** one claim or tightly coupled claim cluster.

**Iteration:** select withheld claim/TODO -> enumerate required evidence
strands and applicable burst subset -> check ledger states -> if all pass,
write the smallest supported statement and record artifact provenance; if any
fail, retain the slot and name the blocker -> regenerate only required
figures/tables -> compile and run consistency/provenance tests -> review and
commit the scoped change.

Association, census, and DM-budget consistency work may run before S1.
Scintillation, scattering, energetics, screen attribution, and the final
physical synthesis remain gated by their evidence strands.

**Stop:** every manuscript result is either supported by a frozen evidence
record or explicitly withheld; the final consistency and referee passes find
no unsupported analysis-derived claims.

## Loop C: controller reduction

This continuous loop receives structured worker checkpoints:

```text
loop, iteration, state, artifact, verdict, next_gate, owner_decision_required
```

At natural boundaries it updates the dependency state, journal, owner view,
and links to results. It does not reinterpret scientific failures as task
completion. `blocked`, `diagnosed`, `validated`, and `decision pending` retain
their strict meanings.

## Concurrency and gates

```text
Loop R: repository recovery ------------------------------+
                                                           |
Loop S0: CHIME method recovery -- PASS --> Loop S1 fleet --+-->
                         |                                 |   Loop E ledger
                         +-- stopping rule --> scope call -+       |
                                                                  v
Loop E: trusted-strand scaffold ------------------------------> Loop M claims
                                                                  |
                                                                  v
                                                       final referee/release
```

Start R, S0, and the trusted-strand portion of E concurrently. Start a limited
M pass only for already trusted association/census/DM claims. S1 cannot start
before S0 passes. Scattering geometry, two-screen interpretation, energetics,
and the final synthesis remain downstream of their explicit evidence gates.

## Decisions intentionally deferred

- Exact A1 two-screen escalation thresholds until the surviving CHIME
  information is known.
- Final agent assignments and concurrency count.
- Detailed h17/CANFAR command scripts until the method contract is frozen.
- Whether a failed S0 leads to earlier-voltage recovery or a DSA-centered paper.
- Final paper title and ambition after the CHIME gate.

## Program success criteria

1. The owner can recover project state from the control document, owner view,
   and twelve sightline cards without reconstructing agent history.
2. Every scientific fleet result descends from a method that passed its
   qualification gate.
3. Every manuscript claim maps to pinned evidence and an explicit sample.
4. Dirty repository lanes are preserved and separately closed.
5. CHIME recovery terminates in either a qualified method or a documented
   scope decision; it cannot remain an open-ended debugging campaign.
6. Final manuscript regeneration succeeds from a clean clone at the reviewed
   FLITS pin.
