# Validation report: Effective ACF bad-channel mask

> Validated against `plan-effective-acf-bad-channel-mask.md` and
> `implement-effective-acf-bad-channel-mask.md` at parent `5f204398` and
> pipeline implementation commit `4ac08c8` on 2026-07-22.

## Overall Status: PASS — implementation validated; Zach approval pending

## Implementation Status

- Exact-union materializer: complete.
- Fail-closed ACF consumer: complete in both preparation paths.
- Cache revalidation: complete.
- Legacy statistical channel-row promotion: bypassed for authoritative maps.
- Zach CHIME/FRB required gate: active.
- Owner approval/materialization of the five current Zach draft ranges: not
  part of this implementation and still pending.

## Automated Verification Results

- PASS — parent full suite: `295 passed, 1 xfailed`.
- PASS — pipeline full suite in locked clean environment:
  `264 passed, 2 skipped, 1 xfailed`.
- PASS — focused parent suite: `7 passed`.
- PASS — focused pipeline mask suite: `8 passed`.
- PASS — affected pipeline suite: `63 passed` in the shared environment.
- PASS — Ruff on all changed Python paths.
- PASS — `git diff --check` in both repositories.
- PASS — live Zach config gate: `ValueError: bad-channel mask requires
  mask_path and provenance_path`.

The shared `py312` environment lacks the declared optional `dynesty` package,
causing four unrelated full-suite failures. All affected nested-evidence tests
and the complete suite passed in a fresh environment created from `uv.lock`
with `--extra nested`.

## Correctness Evidence

The independent criterion is exact Boolean set equality, not a regression
baseline:

```text
effective_bad = (not source_valid) OR owner_manual
```

Synthetic truth contains two source-unavailable rows and two manual rows with
one overlap; the materialized effective set contains exactly three rows. A
deliberate expected-set mutation that omitted one source-unavailable row failed
at the exact index, proving the test detects the omission.

The integration case assigns extreme values 100 and 200 to masked rows before
two-channel averaging. The prepared values are exactly `[2, 5, 8]`, proving
those rows are excluded before downsampling rather than leaking into the ACF
input.

## Code Review Findings

- Retained values are copied exactly; only mask support changes.
- Draft maps cannot create an effective science artifact.
- Wrong event, instrument, frequency values, row count, approval status, mask
  hash, provenance hash, or union counts fail closed.
- The source-valid array remains a distinct authority input but is guaranteed
  to appear in the materialized union.
- Automated RFI candidates remain outside the science mask, matching the
  rejected-method decision.
- Both ACF preparation paths bypass the legacy automatic row masker when the
  verified mask is authoritative.

## Manual Testing Required

- Review and approve or revise Zach’s five draft ranges.
- Materialize the approved artifact on the analysis host.
- Add its exact mask and provenance hashes to `zach_chime.yaml`.
- Then inspect the first post-mask dynamic spectrum before accepting any ACF.

## Recommendations

### Critical

- Do not bypass `required: true` or use `--allow-draft` to make an ACF run.

### Follow-up

- Activate the same required gate event by event after each owner map is
  approved and materialized.

## References

- [Plan](plan-effective-acf-bad-channel-mask.md)
- [Implementation](implement-effective-acf-bad-channel-mask.md)
- [Research](research-effective-acf-bad-channel-mask.md)
