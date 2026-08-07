# Implementation Plan: Wayfinder blocker execution routes

---
**Date:** 2026-07-22
**Author:** AI Assistant
**Status:** Approved
**Related Documents:**
- [Research: Wayfinder blocker execution routes](research-wayfinder-blocker-execution-routes-2026-07-22.md)
---

## Overview

Execute every autonomous blocker-removal step in isolated ticket branches,
retain every science gate, and merge only independently validated results. Each
Wayfinder ticket is resolved by a separate agent session. The orchestrator owns
dependency ordering, review, pull requests, and final merge verification.

**Goal:** Close every executable blocker and leave only exact owner/external
gates, each attached to a completed review artifact.

## Current State Analysis

- Pull request 6 merged the current interference-cleaning and input-remediation
  route; `docs/rse/control/BOARD.md` still references deleted older tickets.
- `docs/rse/wayfinder/tickets/16-build-verified-zach-chime-preprocessing-baseline.md:36-49`
  is complete except for owner review, now supplied.
- `docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:82-115`
  rejects current science use and requires a replacement RFI method.
- `docs/rse/control/results-registry.toml:30-33` is incomplete.
- `docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-09-repeat-redshift-source-verification.md:3-15`
  is blocked by host provenance and the independently replayed query corpus.

## Desired End State

- Every tracker dependency points to an existing ticket.
- Every resolved ticket contains its evidence, exact decision, and map pointer.
- Every analysis or data product has hashes, commands, revisions, and explicit
  trust status.
- Invalid or partial query corpora remain rejected.
- `origin/main` contains each reviewed resolution; no work remains only on a
  local branch.

## What We're NOT Doing

- No data deletion, replacement, or overwrite.
- No automatic scientific trust promotion.
- No manuscript submission or Figure 3 promotion.
- No force-push, branch deletion, or shared-history rewrite.
- No silent redshift, budget, component-count, or dispersion-measure change.

## Implementation Approach

1. One ticket per agent session and branch.
2. Test the tracker or scientific invariant before changing it.
3. Use committed fixtures for offline tests; network acquisition is a separate,
   receipted step.
4. Independent validators do not import producer selection/verdict code.
5. Re-read ticket and map immediately before claim and resolution.
6. Merge in dependency order after checks and closeout.

## Implementation Phases

### Phase 1: Repair tracker route and close the Zach baseline

**Objective:** Reconcile the tracker with the merged route and record the
completed owner review without granting science trust.

**Tasks:**

1. Add `tests/test_wayfinder_certified_data_route.py` with assertions that every
   merged route ticket and `Blocked by` target exists, ticket 16 is resolved,
   and ticket 02 depends on complete input remediation and campaign review.
2. Run:

   ```bash
   python3 -m pytest -q tests/test_wayfinder_certified_data_route.py
   ```

3. Preserve the detailed route merged by pull request 6. Remove the board's
   stale reference to deleted tickets 17–22 and link the live route.
4. Resolve **Build the verified Zach CHIME preprocessing baseline** with the
   accepted no-go/current-next-method decision and the owner's
   pre-bad-channel-mask clarification. Add its map gist.
5. Re-run the focused test; expect pass.
6. Run `git diff --check` and commit only Phase 1 paths.

### Phase 2: Publish completed concurrent work

**Objective:** Land valid completed work without duplicating it.

**Tasks:**

1. Review `codex/resolve-dsa-denominator` against `origin/main`.
2. Reproduce the count in a clean environment:

   ```bash
   env -i PATH=/usr/bin:/bin /usr/bin/python3 -c \
     'import csv; p="docs/rse/claude-science/frames/resolve-dsa-110-trial-count-denominator-27fa6148/artifacts/dsa110_frb_catalog.csv"; rows=csv.DictReader(open(p)); print(sum(bool(r["mjd"]) and 59611 <= float(r["mjd"]) < 60370 for r in rows))'
   ```

   Expected: `64`.
3. Open a focused pull request and merge after checks.
4. Mark local commit `8049634` rejected in review evidence. Do not push or merge
   its false ticket closure.

### Phase 3: Close free-alpha reporting

**Objective:** Remove the stale leakage blocker with a fail-closed reporting
decision.

**Tasks:**

1. In a separate ticket worktree, claim **Decide how the free-alpha diagnostic
   is reported in the paper**.
2. Preserve h17 job scripts, logs, and the six JSON products in a SHA-256 packet.
3. Add an independent parser test asserting the published bounds:

   ```python
   assert secondary_min_alpha_bias >= -0.430
   assert heavy_tail_secondary_min_alpha_bias >= -0.856
   assert abs(scintillation_gain_alpha_bias) <= 0.02
   ```

4. Record the decision: diagnostic-only; methods/appendix only; no physical
   table, screen inference, abstract, or headline use.
5. Update stale board text, ticket status, and map gist. Run the parser test,
   `git diff --check`, closeout, PR checks, and merge.

### Phase 4: Complete the trust and fit-contract chain

**Objective:** Replace the coarse revocation ledger with a complete row-level
contract, then implement the fit gates.

**Tasks:**

1. Add a registry audit test that parses
   `docs/rse/control/results-registry.toml` and fails on current rows containing
   `VERIFY:`, missing producing scripts, missing required pins, missing
   artifacts, or unexplained input exceptions.
2. Generate `docs/rse/control/RESULTS.md` deterministically from the TOML and
   wire the equality check into the repository test target.
3. Inventory every manuscript-facing number/table/figure/verdict. Keep any
   unresolved row `pending`; never infer trust from file existence.
4. Resolve **Overhaul the trust assessment** with proportional requirements:
   existing validated association/census/budget products retain their current
   state; fit products require certified inputs, injection recovery, unified
   rails, production posterior-predictive checks, independent cross-checks, and
   simulation-based calibration.
5. In a clean FLITS worktree, add tests that fail while rail classifiers differ,
   posterior-predictive checks lack production callers, absolute recovery bias
   remains accepted, or deterministic coverage is absent.
6. Implement the single rail authority, production posterior-predictive checks,
   absolute-recovery criterion, calibration coverage, and verification listing.
7. Merge the FLITS contract pull request before resolving **Ratify the fit
   re-trust validation contract**.
8. Selectively port and fix the independent count-harvest artifacts from
   `rse/jointtf-grok-harvest-revalidation`; rerun read-only harvest and seeded
   candidate comparisons on certified inputs.
9. Resolve **Adopt count-audit remediation as standing method**, then resolve
   **Decide whether the profile-component-count statistic blocks submission**:
   the count gate is mandatory for every cited fit-dependent scattering result.

**Verification:**

```bash
python3 -m pytest -q tests/test_results_registry.py
env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  /opt/anaconda3/bin/conda run -n flits python -m pytest -q \
  tests/test_rails.py tests/test_rails_is_ssot.py tests/test_ppc.py \
  tests/test_recovery_campaign.py
node .claude/workflows/fit-verify.js --list-coverage
```

### Phase 5: Rebuild and ratify CHIME/scintillation inputs

**Objective:** Produce certified both-band inputs and rerun the unchanged
scintillation gates.

**Tasks:**

1. Complete the controlled-spectrum review and freeze the measurable
   preservation/false-positive acceptance contract.
2. Stabilize the bandpass model; then build the frozen benchmark, compare
   candidate cleaners, blind-validate the selected cleaner, and ratify its
   science-use boundary.
3. Work **Remediate the scintillation inputs and rerun the campaign**:
   - start from the verified nominal grid and source mask;
   - freeze static missing, known bad-channel, and dynamic RFI masks separately;
   - train bandpass only on off-pulse data;
   - require disjoint held-out improvement and half-window stationarity;
   - reject truncation, zero-filled missing channels, unstable masks, and
     unproven operation order;
   - correct DSA central-channel interference;
   - write exact commands, builder revision, source/output hashes, channel maps,
     dispersion measure, and time-axis metadata.
4. Present twelve hash-bound data cards and 36 waterfalls for owner review.
5. Rerun the both-band scintillation campaign with the same predeclared gates.
   Regenerate checksums,
   `validation.json`, autocorrelation products, and figures.
6. Present both-band autocorrelation functions for owner review.
7. Resolve **Ratify the CHIME-band scintillation method** only after the final
   review; continue excluding the scattering-timescale/bandwidth product.
8. Resolve **Close the scintillation-to-scattering coupling design** with
   versioned posterior/limit inputs, calibrated escalation control, and
   scintillation geometry affecting prior odds only.

### Phase 6: Complete expanded-catalog evidence and replay

**Objective:** Freeze the complete source corpus and independently reproduce
all discovery and verdict inputs.

**Tasks:**

1. Search owner-controlled local/synced storage and correspondence for the
   source-bearing Verdi host table. If found, freeze original bytes, normalized
   ledger, schema, hashes, and join tests; otherwise stop only that ticket at the
   named owner-input gate.
2. Replace the rejected anonymous producer with complete survey-matrix tests.
   The test fails on any absent matrix cell, unreported truncation, missing guard
   ring, missing exact query/release/retrieval/hash, or collapsed error state.
3. Run the complete anonymous acquisition; preserve raw or canonical responses.
4. Use an existing logged-in MAST browser session for the nine protected
   CasJobs cones. Record account identity without secrets, SQL, context/table,
   job identifier, server time, native bytes, and hashes. If authentication
   requires user action, stop at that exact login gate.
5. Run authenticated CADC queries. If `CFIS-read` is absent, freeze a current
   authenticated `access_denied` receipt.
6. Assign **Independently replay the completed nine-sightline query corpus** to
   a separate research agent. It must not import producer selection/verdict
   functions.
7. Only after those blockers close, assign **Repeat source-level redshift
   verification** to another independent research agent for all 52 rows.
8. Any scientific difference becomes a separate owner-adjudication ticket; no
   authority field changes silently.

### Phase 7: Independent release validation and merge

**Objective:** Ensure every resolution is present and valid on `origin/main`.

**Tasks:**

1. For every ticket branch: code review, focused tests, full relevant tests,
   `git diff --check`, dirty-state classification, and closeout.
2. Run publish-policy admission and non-destructive push.
3. Open a focused ready pull request; wait for all required checks.
4. Re-read map/ticket on the PR head; verify no concurrent update was lost.
5. Merge through GitHub; fetch `main`; verify the merge commit and ticket status
   on `origin/main`.

## Success Criteria

### Automated Verification

- All tracker links and blockers resolve.
- Every ticket marked resolved has a resolution and map gist.
- Registry audit reports no unexplained current-row gaps.
- Scientific tests and independent replays pass from pinned inputs.
- All merged pull requests have passing checks.
- Feature commits are ancestors of `origin/main`.

### Manual Verification

- Owner approves the hash-bound input cards and required visual diagnostics.
- Owner adjudicates only exact remaining dispersion-measure, morphology/count,
  trust-promotion, or foreground-conflict packets.
- Owner completes authentication only when no reusable session exists.

### Reproducibility & Correctness

- Exact commands, revisions, hashes, masks, query bytes, and environments are
  recorded.
- Independent validators do not reuse producer decision logic.
- Missing access or evidence remains explicit and fail-closed.

## Risk Assessment

1. **Concurrent branch writes:** high impact. Mitigation: isolated worktrees,
   re-fetch before resolution, no force-push.
2. **Plausible but incomplete catalog corpus:** high impact. Mitigation: matrix,
   truncation, provenance, and independent-replay tests.
3. **Diagnostic result promoted as science:** high impact. Mitigation: explicit
   `pending`/`diagnostic_only` states and owner trust gate.
4. **Old monorepo paths reintroduced:** medium impact. Mitigation: selective
   porting and split-repository path tests.

## References

- [Research](research-wayfinder-blocker-execution-routes-2026-07-22.md)
- `docs/rse/control/BOARD.md`
- `docs/rse/control/results-registry.toml`
- `docs/rse/specs/handoff/handoff-2026-07-19-stratified-restart.md`
- `docs/rse/specs/validation-zach-chime-preprocessing-baseline.md`
- `docs/rse/specs/handoff-2026-07-21-21-46-repeat-redshift-source-verification.md`

## Review History

### Version 1.0 — 2026-07-22

- Direct-mode plan approved in advance by the owner.
- Incorporated independent trust, scintillation, and catalog blocker audits.
