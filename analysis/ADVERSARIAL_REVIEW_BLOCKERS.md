# Adversarial review blockers

Do not open or merge the release-gate pull request until all items pass.

Source: independent adversarial review, 2026-07-24.
Independent discharge: 2026-07-26, against Faber2026 parent commit
`ac004ece8f22bce3b117099a2f23e05b5abe6528` and its pipeline gitlink
`78b448f05946923ef1c0acc19068fed313911ec6`.

Full evidence:
[`docs/rse/specs/receipt-independent-release-gate-discharge-2026-07-26.md`](docs/rse/specs/receipt-independent-release-gate-discharge-2026-07-26.md).

## Checklist

- [x] **Replay current 52/52 source verification with zero discrepancies; do
  not trust the stale 46/52 replay JSON.**
  Discharged as a verification task, but the result contradicts the
  expectation. Replayed independently in a clean checkout of the pinned
  pipeline commit: at `78b448f0` the current count is **46 of 52 with 6
  discrepancy rows**, not 52/52. The pinned 52/52 receipt was produced against
  `c913175e`, which is not an ancestor of the pipeline main line; it is a
  pre-landing form of the change that landed as `f5c1d1f3` (pipeline #231).
  The same replay returns 52/52 with zero discrepancies at `f5c1d1f3`. The
  shortfall is therefore a pin-lag, not a data defect, and is recorded as the
  `source-verification-incomplete` blocker rather than papered over. Clearing
  it requires a pipeline pin bump, which is an owner decision.

- [x] **Independently compute and pin SHA-256 hashes for the catalog,
  registry, source artifacts, replay reports, and Figure 3 input.**
  All twelve pinned artifacts were rehashed from bytes. Eleven matched. The
  nine-sightline registry replay report had drifted from
  `a3ebd607…` to `f6b5d7bf…` when main realigned it to the current parent pin;
  the gate now pins the current value. The pinned registry itself
  (`96bfd323…` at `78b448f0`) is now pinned by path and hash and checked
  against the pipeline repository rather than assumed.

- [x] **Independently rerun the calculations instead of trusting produced
  replay summaries.**
  Both replays were re-executed rather than read. The source replay was run at
  three commit bindings (`c913175e`, `78b448f0`, `f5c1d1f3`). The
  nine-sightline registry replay was re-executed against the pinned pipeline
  checkout and reproduced every reported field: 52 rows, 49 finite-host rows,
  7 duplicate checks passed, empty verdict and budget mismatch arrays, and all
  four input hashes. The verifier previously replayed only at its own
  hard-coded commit constants; it now accepts `--pipeline-commit` and
  `--analysis-commit`, and the gate drives it at the commits the gate declares.

- [x] **Byte-compare staged and installed Figure 3 artifacts and prove that no
  promotion occurred.**
  The superseded mismatched candidates are dispositioned. The current staged
  and installed files both hash to `281e4bf4…`; exact-byte owner visual approval
  remains queued in the Figure 3 Wayfinder decision card.

- [x] **Verify visual-review artifact bytes and the explicit current owner
  state that no drafted figure is approved; do not trust manifest strings
  alone.**
  Candidate bytes were rehashed and match the manifest and the gate. The
  manifest decision is `pending` with null reviewer, role, timestamp, and
  notes, and `protect_in_manuscript` is false. The owner's 2026-07-23
  approve-none decision is present verbatim and hash-pinned. The gate
  additionally requires reviewer identity, `manuscript_owner` role, timestamp,
  notes, and a promotion receipt whose promoted bytes equal the approved
  candidate before any approval is admissible.

- [x] **A passing release gate must require an empty blocker list.**
  Enforced, and covered by two tests: a `passed` status retaining blockers
  fails, and emptying the blocker list alone does not pass, because the
  underlying evidence checks still fail.

- [x] **Bind the report to current parent and pipeline commits.**
  The gate now records the current parent commit and pipeline pin, and the
  validator verifies them at run time against the manuscript checkout's `HEAD`
  and its `pipeline` gitlink rather than trusting the recorded strings.
  `analysis_base_commit` remains `fe73689c`, which is a verified ancestor of
  this branch whose three host-redshift inputs are byte-identical at the branch
  head, so the replay binding is content-stable.

## Remaining state

The gate remains `failed` and `fail_closed`. Four blockers stand:
`expanded-catalog-gate-not-passed`, `source-verification-incomplete`,
`figure3-registry-snapshot-stale`, and `figure3-owner-approval-missing`.
None is dischargeable by verification alone.
