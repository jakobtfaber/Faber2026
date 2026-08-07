# ApJ 02 and 04 blocker audit

**Date:** 2026-07-22  
**Status:** execution decision support only; no scientific or visual gate closes here

## Current authoritative chain

Reviewed against `analysis` `origin/main` at `b6023c1`, a descendant of
`8337c23`. Ticket 16 is resolved. The remaining chain is:

`RFI 01a → RFI 01 → RFI 01b → RFI 02 → RFI 03 → RFI 04 → RFI 05 → 17 → 02 → 04`

In plain terms: accept preservation limits; freeze a stable bandpass; build the
benchmark; choose and blind-test a cleaner; ratify its use boundary; rebuild
all inputs and rerun; ratify the CHIME scintillation method; then close the
scintillation-to-scattering interface.

## Existing lane that can shorten the route

Remote branch `codex/prototype-chime-rfi-preservation-gates` at `cd5b67bd`
contains twelve commits absent from current parent `origin/main`. It records:

- a controlled known-truth preservation review (`4e79b50d`);
- several automated-cleaner failures, preserved fail-closed;
- an owner-approved five-range Zach CHIME/FRB manual channel map
  (`e1c46097`);
- exact effective-mask materialization and fail-closed autocorrelation-function
  consumers (`3e41d845`; pipeline commits `4ac08c8`, `5a49278`);
- a checksummed Zach raw-coordinate certificate (`1250b26a`); and
- a checksummed all-event raw-product audit (`89cedc4e`, corrected by
  `cd5b67bd`).

The branch is not safe to merge wholesale. It is 64 parent commits behind and
12 ahead, changes ticket and map headers, advances the pipeline submodule, and
its worktree contains active uncommitted experiments. The uncommitted automated
row and voltage candidates are rejected or incomplete evidence, not a cleaner.

## Smallest safe integration

1. Start a clean branch from current `origin/main`.
2. Transplant only committed evidence, code, tests, and immutable certificates
   from the lane above. Reconcile ticket and map prose separately against
   current main. Do not copy the dirty experiment tree or its notebook
   checkpoint.
3. Rebase the two pipeline mask commits onto current pipeline main and rerun
   their focused and affected tests before advancing the submodule pin.
4. Decide whether the recorded owner-approved manual-map route remains the
   current authority. If yes, the committed Zach evidence can remove the RFI
   01a and RFI 01 decisions and can make automated-cleaner comparison and blind
   validation conditional on a demonstrated residual time-local bias. This is
   a route change, not proof that current authoritative RFI 03–05 passed.
5. Keep bandpass qualification as a hard gate. Existing Zach evidence shows
   bandpass correction is necessary but its training-half gain estimate varies
   by about 29%; no passing RFI 01b artifact was found.

## Work that cannot be collapsed

- The accepted route and authoritative ticket dependency headers must agree.
  Current main still requires RFI 01b–05 in sequence.
- A stable, frozen bandpass model must pass predeclared training and validation
  limits.
- Zach still needs adopted dual-band dispersion measures, standardized dynamic
  spectra, and validated burst models before a meaningful masked
  autocorrelation-function stability check.
- Only Zach CHIME/FRB has a branch-recorded approved manual map. The other 23
  event/instrument maps remain unapproved. Diagonal and time-local interference
  is not solved by a one-dimensional channel map.
- The all-event raw-product certificate reduces discovery and checksum work,
  but eleven non-Zach records still await owner review and do not establish
  authoritative dispersion measures.
- Ticket 17 still requires DSA-110 central-channel remediation, one
  authoritative dispersion measure per burst, regenerated products and
  checksums, the full campaign rerun, and fresh owner review.

## Ticket decisions

**Ticket 02:** still blocked. Fastest safe path is to integrate and reconcile
the clean committed Zach/manual-mask lane before building any replacement
infrastructure. That can remove duplicated prototype and mask work. It cannot
replace bandpass qualification, full-input remediation, the campaign rerun, or
fresh owner review.

**Ticket 04:** cannot proceed yet. Ticket 02 still has no ratified product
interface. After ticket 02 ratifies remediated outputs, ticket 04 still must
freeze product formats, quality flags, and censoring; keep scintillation
geometry as prior odds only; remove the retired autocorrelation-evidence
trigger from live code; and calibrate the surviving posterior-predictive
trigger's false-escalation rate.

## Evidence surfaces

- Current tickets: `docs/rse/wayfinder/tickets/02-*`, `04-*`, `17-*`, and
  `rfi-validation-*` on `analysis/origin/main@b6023c1`.
- Zach baseline:
  `docs/rse/specs/validation-zach-chime-preprocessing-baseline.md`.
- Candidate integration branch:
  `origin/codex/prototype-chime-rfi-preservation-gates@cd5b67bd` in the parent
  repository.
- Effective-mask validation on that branch:
  `docs/rse/specs/validation-effective-acf-bad-channel-mask.md`.
- Raw-product audits on that branch:
  `docs/rse/specs/research-zach-dedispersion-reference-frequencies.md` and
  `docs/rse/specs/research-sample-raw-products-time-axes.md`.
