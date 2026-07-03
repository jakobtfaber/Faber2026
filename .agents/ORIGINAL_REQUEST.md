# Original User Request

## Initial Request — 2026-07-03T03:13:04Z

Refactor the codebase according to the Ponytail audit recommendations: removing redundant pool logic, updating hardcoded host paths, stripping verbose dev headers, and fixing duplicate export entries.

Working directory: /Users/jakobfaber/Developer/overleaf/Faber2026
Integrity mode: development

## Requirements

### R1. Code Refactoring & Ponytail Cleanup
Apply all targeted ponytail audit recommendations across the repository cleanly:
- `pipeline/scattering/scat_analysis/pool_utils.py`: Simplify `build_pool()` branching logic.
- `pipeline/scattering/configs/bursts/copy_yaml.py`: Replace hardcoded absolute host paths (`/arc/home/...`) with relative repository paths.
- `pipeline/scripts/dev/create_dummy_db.py`: Remove redundant 12-line copyright header from dev scratch script.
- `pipeline/scattering/scat_analysis/burstfit_init.py`: Remove duplicate `"estimate_spectral_index"` string in `__all__`.

### R2. Non-Breakage & Verification
Ensure all edits maintain existing behavior and pass all regression test suites.

## Acceptance Criteria

### Integrity & Quality
- [ ] All 4 ponytail findings refactored cleanly
- [ ] No collateral code modifications or unintended behavior changes
- [ ] Repository test suite passes without errors
