# Research: Wayfinder blocker execution routes

**Date:** 2026-07-22
**Scope:** Internal codebase, live Git/GitHub state, configured local storage,
and read-only remote evidence checks
**Codebase state:** `Faber2026-analysis` `eb550d9`; manuscript parent pins
`pipeline` `ab6af1f7`

## Question / Scope

Determine the shortest fail-closed route that removes every current Wayfinder
blocker, separates autonomous work from required owner action, avoids duplicate
concurrent execution, and lands validated ticket resolutions on `origin/main`.

## Codebase Findings

### Tracker and concurrency

- The tracker is local Markdown. A frontier ticket is open, unblocked, and
  unassigned (`docs/agents/issue-tracker.md:22-40`).
- Pull request 6 merged a detailed radio-frequency-interference validation and
  input-remediation route. The board still named the deleted older tickets
  17–22 and needed reconciliation with that live route.
- The clean campaign worktree is
  `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-unblock`.
  The canonical checkout carries separate archive work and must not be reused.
- **Obtain the exact DSA-110 detection denominator** is complete on
  `codex/resolve-dsa-denominator`; the count is 64 detections under a finite-MJD
  rule. It needs review and publication, not duplicate execution.
- Local commit `8049634` on `codex/repository-archive-audit` claims to resolve
  **Freeze the anonymous nine-sightline expanded-survey query corpus**, but is
  invalid and must not merge: required surveys are absent, 34 queries silently
  hit a 500-row cap, scientific selection rules are bypassed, provenance fields
  are missing, and no independent replay exists.

### Zach preprocessing and CHIME scintillation

- The Zach baseline implementation is complete: 7 parent checks and 15 pipeline
  checks passed; the nominal 65,536-position grid and explicit missing-data mask
  passed (`docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:27-58`).
- The current radio-frequency-interference routine failed held-out and
  stationarity checks. Science use remains no-go
  (`docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:82-115`).
- Owner review on 2026-07-22 accepted the diagnostic, while clarifying that the
  figure is before the bad-channel mask. This closes the baseline review only;
  it does not approve a final science mask.
- The merged route proceeds through controlled-spectrum review, an acceptance
  contract, bandpass stabilization, a frozen benchmark, cleaner comparison,
  blind validation, cleaning-boundary ratification, full input remediation and
  campaign rerun, then CHIME-method ratification.

### Free-alpha diagnostic and coupling design

- The multi-component-leakage blocker on **Decide how the free-alpha diagnostic
  is reported in the paper** is stale. The landed bounds are: secondary-only
  bias no lower than -0.430; heavy-tail plus secondary no lower than -0.856;
  scintillation-gain leakage at most 0.02 in absolute value. None reproduces the
  observed approximately -1.6 shift
  (`docs/rse/specs/notes/report-jointtf-mechanism-closure-2026-07-18.md:30-47`).
- The ticket can resolve fail-closed: free alpha is a nonphysical model-mismatch
  diagnostic, excluded from physical parameter tables, screen inference,
  abstract, and headline claims.
- **Close the scintillation-to-scattering coupling design** remains blocked by
  CHIME-method ratification (`docs/rse/wayfinder/tickets/04-close-scint-scattering-coupling-design.md:3-25`).

### Trust and component-count chain

- **Overhaul the trust assessment** requires a populated results registry before
  adjudication (`docs/rse/wayfinder/tickets/13-overhaul-trust-assessment.md:32-42`).
- The registry still calls itself population pass 1
  (`docs/rse/control/results-registry.toml:30-33`). Live parsing finds 61 rows:
  14 trusted, 40 pending, 7 revoked; 49 rows lack pipeline pins and 15 input
  exceptions retain incomplete lineage.
- The registry correctly keeps the defective scintillation campaign pending and
  identifies its input defects (`docs/rse/control/results-registry.toml:630-647`).
- The five-term fit contract is not fully implemented in FLITS: rail logic is
  duplicated, absolute recovery still accepts a constant bias, and the generic
  posterior-predictive check has no production fit caller. Input certification
  must be a contract precondition, not parallel work.
- Component count changes materially alter fitted physics. A held branch at
  `rse/jointtf-grok-harvest-revalidation` contains useful independent harvest
  evidence, but its six commits mix old-monorepo paths and contain a Zach-count
  contradiction. Port selected evidence only; do not merge the branch wholesale.

### Expanded foreground catalog

- Host-side provenance is absent. Existing copied values are not the
  source-bearing Verdi authority required by
  `docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-07-freeze-host-redshift-provenance.md:10-16`.
- Candidate provenance is already frozen for all 52 rows, including stable
  source evidence for 46 adopted redshifts.
- The anonymous corpus must implement the complete survey matrix and the search
  contract at
  `docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-14-freeze-anonymous-nine-sightline-query-corpus.md:13-27`.
- Protected evidence needs authenticated MAST CasJobs exports and CADC evidence.
  A current CADC identity may truthfully produce `access_denied`; only an
  administrator can grant `CFIS-read`
  (`docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-15-freeze-protected-nine-sightline-query-evidence.md:13-22`).
- Independent replay must not import producer selection or verdict functions
  (`docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-16-independently-replay-nine-sightline-query-corpus.md:13-21`).

## Synthesis

The shortest robust route has four parallel lanes:

1. Validate the merged interference-cleaning route, record the pre-mask owner
   clarification, correct the board, and execute the route in dependency order.
2. Close the stale free-alpha blocker immediately; finish the registry and trust
   decision; then implement the fit contract and count gate.
3. Reject the invalid anonymous-corpus closure, produce complete anonymous and
   protected corpora, independently replay them, then repeat all 52 redshift
   source chains.
4. Review already-completed concurrent branches, publish only valid scoped
   commits, and merge after independent checks.

Autonomous work stops only at exact recorded owner or external gates. Advance
approval cannot replace inspection of an artifact that did not yet exist.

## Absolutely non-autonomous elements

1. Owner hash-bound visual review of derived-input data cards, all 36 remediated
   waterfalls, required fit diagnostics, and the both-band autocorrelation
   functions.
2. Any unresolved dispersion-measure choice that changes the adopted catalog or
   cannot be settled by the predeclared independent methods.
3. Row-level scientific trust promotion after the completed ledger packet.
4. Final per-burst morphology/component-count adoption when it changes a
   manuscript-facing result.
5. The unpublished source-bearing Verdi host-redshift table or extract, if it
   is not recoverable from owner-controlled storage or correspondence.
6. MAST login or multi-factor authentication if no reusable browser session
   exists.
7. Granting `CFIS-read`; only a CFIS administrator can do that. The agent will
   record authenticated denial in the meantime.
8. Any newly discovered conflict whose resolution changes a foreground
   redshift, identity, duplicate disposition, budget flag, trust state, or
   manuscript claim.
9. Final CHIME-method and two-Lorentzian-table scientific ratification.

## References / Sources

- `docs/agents/issue-tracker.md`
- `docs/rse/control/BOARD.md`
- `docs/rse/control/results-registry.toml`
- `docs/rse/specs/validation-zach-chime-preprocessing-baseline.md`
- `docs/rse/specs/notes/owner-data-review-findings-2026-07-18.md`
- `docs/rse/specs/handoff/handoff-2026-07-19-stratified-restart.md`
- `docs/rse/specs/notes/report-jointtf-mechanism-closure-2026-07-18.md`
- `docs/rse/specs/handoff-2026-07-21-21-46-repeat-redshift-source-verification.md`
- `docs/rse/wayfinder/standing-delegation-2026-07-20.md`
