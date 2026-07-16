# Handoff: results library catalog-YAML reshape

---
**Date:** 2026-07-15 19:18
**Author:** AI Assistant (Grok session)
**Status:** Handoff — Phase A partial implemented; resume on `cursor/results-library-catalog-yaml-7b14`
**Branch:** `cursor/results-library-catalog-yaml-7b14` (off synced `main`)

---

## Task(s)

Results library reshaped so campaigns live in `scripts/results_library_catalog.yaml` and the builder only load/validate/probe/link/emit.

| Task | Status | Notes |
|------|--------|-------|
| Refactor to catalog-YAML shape | ✅ Complete | Data in YAML; builder loads/validates/probes/links/emits |
| Repo pointer INDEX | ✅ Complete | `docs/rse/specs/results-library-INDEX.md` |
| Commit / PR results-library files | 📋 In progress | Focused branch; pathspec-only |
| Phase A finish (pointers, DATA_LOCATIONS, producers) | 📋 Planned | Parent stubs + FLITS DATA_LOCATIONS; producers deferred |
| Phase B physical separation | 📋 Planned | Needs dedicated PRs; do not mix with manuscript science |

**Current Workflow Phase:** Implement (Phase A).

## Critical References

1. `scripts/results_library_catalog.yaml` — **only place to add/edit campaigns**
2. `scripts/build_results_library_inventory.py` — loader, validation, probe, symlink, INDEX emit
3. `docs/rse/specs/plan-results-library-2026-07-15.md` — done vs open vs Phase B
4. `scripts/results_library.py` — path helper (`DEFAULT_LIBRARY`, `results_slot`, `require_results_library`)

## Design decisions

1. **Catalog is data** — campaign list lives in YAML; Python only orchestrates.
2. **Single builder source** — always run from git checkout; never a library-side copy.
3. **Root discovery** — default `Path(__file__).resolve().parents[1]`; `FABER2026_ROOT` / `--root`.
4. **Trust closed set** — tags must appear in `trust_legend` or build exits non-zero.
5. **Do not add** `pipeline/galaxies/foreground/results_library.py` — one helper in parent `scripts/` only.
6. External runs: catalog uses `external_paths` with `{env, default}` and `{path}` specs.

## Refresh

```bash
python3 scripts/build_results_library_inventory.py --dry-run
python3 scripts/build_results_library_inventory.py --link --force
```

## Action Items

1. [x] Sync `main` to `origin/main`
2. [ ] Pathspec commit + PR (tooling + docs)
3. [ ] Parent `RESULTS_LIBRARY.md` pointers
4. [ ] FLITS `DATA_LOCATIONS.md` section + pipeline pointers (no pin bump)
5. [ ] Do not start Phase B; leave producers open

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` after PR.
