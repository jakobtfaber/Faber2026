# Validation report: Effective ACF bad-channel mask

> Validated against `plan-effective-acf-bad-channel-mask.md` and
> `implement-effective-acf-bad-channel-mask.md` at parent `5f204398` and
> pipeline implementation commit `4ac08c8` on 2026-07-22.

## Overall Status: PASS — implementation and Zach artifact validated

## Implementation Status

- Exact-union materializer: complete.
- Fail-closed ACF consumer: complete in both preparation paths.
- Cache revalidation: complete.
- Legacy statistical channel-row promotion: bypassed for authoritative maps.
- Zach CHIME/FRB required gate: active.
- Owner approval/materialization of the five Zach ranges: complete on
  2026-07-22.
- Effective union: 9,792 source-unavailable rows plus 490 manual rows, zero
  overlap, 10,282 total bad rows, and 55,254 retained rows.

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
- PASS — approved mask SHA-256:
  `5de1bd08ff2ea0a3aa8b3ea37f609e6c7530ae14869d4d5e5361609c9adb8038`.
- PASS — provenance SHA-256:
  `6501fe1bb15a96629e80e6f60d8e206bc955adad144c0128f91b2237033087ee`.
- PASS — real consumer replay included every source-unavailable and approved
  manual row, retained 55,254 rows, and left every retained value unchanged.

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

## Manual Testing

- COMPLETE — owner reviewed and approved the regenerated Zach before/after
  dynamic-spectrum artifact.
- COMPLETE — approved map was materialized on h17 and exact hashes were added
  to `zach_chime.yaml`.
- COMPLETE — the real artifact was replayed through the ACF mask consumer.
- PENDING OUTSIDE THIS ARTIFACT GATE — inspect the first full post-mask ACF run
  after the standardized `zach_chime.npz` input is restored or rebuilt.

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
