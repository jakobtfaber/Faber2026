# Implementation Summary: Effective ACF bad-channel mask

---
**Date:** 2026-07-22
**Author:** Codex
**Status:** Complete
**Plan Reference:** [plan-effective-acf-bad-channel-mask.md](plan-effective-acf-bad-channel-mask.md)
---

## Overview

Implemented a fail-closed ACF mask boundary. The materialized mask is exactly
`not source_valid OR owner_manual`; the pipeline verifies its two file hashes,
frequency-value digest, event, instrument, approval evidence, row counts, and
union arithmetic before use. The Zach CHIME/FRB artifact was owner-approved,
materialized, and wired on 2026-07-22.

## Plan Adherence

All three phases were implemented. One necessary refinement was added: cached
pipeline runs revalidate artifact file hashes without reapplying the
full-resolution mask to an already downsampled spectrum. The cache fingerprint
already includes the configured expected hashes.

## Phases Completed

### Phase 1: Exact-union materialization

- Added source-valid hash validation and exact set-union construction.
- Added deterministic Boolean `.npy` output plus JSON provenance.
- Retained legacy manual-only draft validation; draft effective science masks
  are forbidden.

### Phase 2: ACF-boundary enforcement

- Added the shared pipeline consumer.
- Applied it before grid regularization and downsampling in both preparation
  paths.
- Added cache-time artifact revalidation.
- Bypassed legacy statistical channel-row promotion when the verified artifact
  is marked authoritative; retained source and bandpass-validity masks remain.
- Activated the required gate for Zach CHIME/FRB; exact artifact paths and
  hashes were added only after owner approval and materialization.

### Phase 3: Hardening and reproduction

- Verified the analytic union test goes red when one source-invalid row is
  omitted from the expected set, then restored it to green.
- Exercised file tampering, wrong event, draft status, frequency drift, missing
  artifact, exact retained-value preservation, and pre-downsample ordering.
- Reproduced with the committed `pipeline/uv.lock` in a fresh environment.

## Files Modified

### Parent repository

- `scripts/manual_bad_channels.py`
- `tests/test_manual_bad_channels.py`
- `analysis/rfi/manual-bad-channels/README.md`
- `docs/rse/specs/research-effective-acf-bad-channel-mask.md`
- `docs/rse/specs/plan-effective-acf-bad-channel-mask.md`
- `docs/rse/specs/validation-effective-acf-bad-channel-mask.md`

### Pipeline submodule

- `scintillation/scint_analysis/bad_channel_mask.py`
- `scintillation/scint_analysis/tests/test_bad_channel_mask.py`
- `scintillation/scint_analysis/freya_scintillation.py`
- `scintillation/scint_analysis/pipeline.py`
- `scintillation/configs/bursts/zach_chime.yaml`

## Verification Results

- Parent full suite: `295 passed, 1 xfailed`.
- Pipeline locked clean environment: `264 passed, 2 skipped, 1 xfailed`.
- Focused locked clean environment: parent `7 passed`; pipeline affected
  `42 passed` after the authoritative-mask test was added.
- Ruff on every changed Python file: passed.
- `git diff --check` in both repositories: passed.
- Shared Conda environment full pipeline run: `259 passed`; four failures were
  solely the absent optional `dynesty` package. Those five nested-evidence tests
  passed in the locked environment with the declared `nested` extra.

## Reproducibility

Code bases at start: parent `5f204398`, pipeline `ab6af1f`. Pipeline implementation
commit: `4ac08c8`. Test data are analytic in-memory arrays; no random seeds or
external data are used by the new tests. Environment authority is
`pipeline/uv.lock`.

Commands:

```bash
repro_env=$(mktemp -d /tmp/faber-effective-mask-repro.XXXXXX)
UV_PROJECT_ENVIRONMENT="$repro_env" uv sync --frozen --extra nested --group test
"$repro_env/bin/python" -m pytest ../tests/test_manual_bad_channels.py -q
"$repro_env/bin/python" -m pytest scintillation/scint_analysis/tests -q
```

## Remaining Work

No mask implementation work remains. The Zach mask gate now passes with the
approved artifact. A complete Zach ACF run still requires the standardized
`zach_chime.npz` input, which was not present on h17 during this approval step.

## References

- [Research](research-effective-acf-bad-channel-mask.md)
- [Plan](plan-effective-acf-bad-channel-mask.md)
- [Validation](validation-effective-acf-bad-channel-mask.md)
