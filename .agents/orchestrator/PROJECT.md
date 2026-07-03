# Project: Ponytail Refactoring Cleanup

## Mission
Refactor codebase according to Ponytail audit recommendations and verify all tests pass without regression.

## Architecture & Code Layout
- Target package: `pipeline/`
- Target files:
  1. `pipeline/scattering/scat_analysis/pool_utils.py` (simplify `build_pool()` logic)
  2. `pipeline/scattering/configs/bursts/copy_yaml.py` (replace `/arc/home/...` hardcoded host paths with relative repo paths)
  3. `pipeline/scripts/dev/create_dummy_db.py` (remove 12-line copyright header)
  4. `pipeline/scattering/scat_analysis/burstfit_init.py` (remove duplicate `"estimate_spectral_index"` in `__all__`)

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Baseline Test Run | Inspect 4 target files & existing test suite | none | IN_PROGRESS |
| 2 | Refactoring Implementation | Perform ponytail cleanups across 4 files | M1 | PLANNED |
| 3 | Verification & Auditing | Review code, run tests, challenge & forensic audit | M2 | PLANNED |

## Interface Contracts
- Preserve all public signatures and behavior in modified files.
