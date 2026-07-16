# Handoff: open FLITS results-library docs PR (GH_TOKEN)

---
**Date:** 2026-07-16 03:10 UTC  
**Author:** Cloud agent (`bc-84d7cd80-c9d4-4976-b95b-9ad940277b14`)  
**Status:** Handoff — Faber2026 Phase A PR open; FLITS docs branch pushed; **FLITS PR not created** (install token 403). Owner saved `GH_TOKEN` secret — **needs a new agent run**.  
**Branch (Faber2026):** `cursor/results-library-catalog-yaml-7b14` @ `c1c48cc`  
**PR (Faber2026):** https://github.com/jakobtfaber/Faber2026/pull/102 (draft, OPEN)  
**Branch (FLITS):** `cursor/results-library-data-locations-7b14` @ `9b6ceaf` — **no PR yet**

---

## Task for the next cloud agent

**Primary:** Create the dsa110-FLITS pull request for the already-pushed docs branch, using the environment secret `GH_TOKEN`.

**Secondary (only if needed):** Confirm `GH_TOKEN` is visible in the new run; update Faber2026 PR #102 body with the FLITS PR URL; do **not** bump the Faber2026 `pipeline/` gitlink.

### Exact first commands

```bash
# 1. Confirm secret landed in THIS run (do not print the value)
test -n "$GH_TOKEN" && echo "GH_TOKEN=set len=${#GH_TOKEN}" || echo "GH_TOKEN=MISSING — stop; recheck Cloud Agents Secrets"

# 2. Create FLITS PR from the existing branch tip
gh pr create --repo jakobtfaber/dsa110-FLITS \
  --base main \
  --head cursor/results-library-data-locations-7b14 \
  --title "Document results library inventory pointers" \
  --body "$(cat <<'EOF'
## Summary

Adds a **Results library** section to `DATA_LOCATIONS.md` and pointer stubs:

- `analysis/RESULTS_LIBRARY.md`
- `results/RESULTS_LIBRARY.md`

These document the external navigable inventory at `~/Data/Faber2026/results-library/` (catalog/builder live in Faber2026). No fit products are relocated (Phase B stays separate).

## Related

Faber2026 catalog-YAML PR: https://github.com/jakobtfaber/Faber2026/pull/102

## Note

Do **not** bump the Faber2026 `pipeline/` gitlink until this merges; pin bump is a separate reviewed step.
EOF
)"
```

Compare link if `gh pr create` still fails:  
https://github.com/jakobtfaber/dsa110-FLITS/compare/main...cursor/results-library-data-locations-7b14?expand=1

### After FLITS PR exists

1. Comment or update Faber2026 PR #102 with the FLITS PR URL (ManagePullRequest / `gh pr edit` on Faber2026).
2. Leave Faber2026 `pipeline` submodule pin at `af78543` — **no pin bump**.
3. Stop. Do not start Phase B or producer wiring unless the owner asks.

---

## Current Workflow Phase

Implement → almost closed for Phase A docs. Remaining gate: **FLITS PR create** (auth), then human review of #102 + FLITS PR.

**Recommended skill:** Direct execution (`gh pr create`). No need to re-run `implementing-plans` unless #102 needs code changes.

---

## Workflow Artifacts

| Doc | Path |
|-----|------|
| Plan | [`plan-results-library-2026-07-15.md`](plan-results-library-2026-07-15.md) |
| Implement summary | [`implement-results-library-2026-07-15.md`](implement-results-library-2026-07-15.md) |
| Prior handoff (catalog reshape) | [`handoff-2026-07-15-19-18-results-library-catalog-yaml.md`](handoff-2026-07-15-19-18-results-library-catalog-yaml.md) |
| Repo pointer | [`results-library-INDEX.md`](results-library-INDEX.md) |

---

## What already landed (do not redo)

### Faber2026 PR #102 — `cursor/results-library-catalog-yaml-7b14`

- `scripts/results_library_catalog.yaml` — 16 entries + closed `trust_legend`; schema `faber2026-results-library-catalog/v1`
- `scripts/build_results_library_inventory.py` — load → validate trust → probe → optional `--link` → emit INDEX/inventory
- `scripts/results_library.py` — `DEFAULT_LIBRARY`, `results_slot`, `require_results_library`
- `docs/rse/specs/plan-results-library-2026-07-15.md`, `results-library-INDEX.md`, prior handoff, implement note
- Parent stubs: `analysis/{dm-joint-phase-v2,provisional_propagation,v3_energetics}/RESULTS_LIBRARY.md`

Smoke (already green on this branch):

```bash
python3 scripts/build_results_library_inventory.py --dry-run   # exit 0
```

### FLITS branch — `cursor/results-library-data-locations-7b14` @ `9b6ceaf`

Pushed to `https://github.com/jakobtfaber/dsa110-FLITS.git`:

- `DATA_LOCATIONS.md` — new **Results library** section
- `analysis/RESULTS_LIBRARY.md`
- `results/RESULTS_LIBRARY.md`

Faber2026 submodule pin deliberately left at `af78543` (checkout restored after push).

---

## Auth context (why this handoff exists)

| Fact | Detail |
|------|--------|
| Symptom | `gh pr create` on FLITS → `GraphQL: Resource not accessible by integration (createPullRequest)` |
| Cause | Cursor sandbox `ghs_` install token can push but often lacks PR create, even when GitHub App shows PR write + All repos |
| Fix applied by owner | Cloud Agents Secrets: `GH_TOKEN=<PAT>` (Runtime Secret preferred) at [cursor.com/dashboard/cloud-agents](https://cursor.com/dashboard/cloud-agents) |
| Constraint | Secrets apply to **new** agent runs only — previous run still had `GH_TOKEN` unset |

If `GH_TOKEN` is still unset in the new run: stop and tell the owner the secret is not bound to this environment (wrong environment / team scope / not Runtime+env for this repo).

---

## Explicitly out of scope

- Phase B physical moves of fit trees
- First `results_slot(...)` producer import
- Adding `pipeline/galaxies/foreground/results_library.py`
- Bumping Faber2026 `pipeline/` gitlink
- Science-gate / manuscript G1–G7 work
- Re-writing catalog/builder unless #102 review demands it

**Provenance note:** Catalog/builder in #102 were reconstructed in-cloud from the prior handoff design (original Mac untracked files were not in the cloud clone). Behavior matches locked decisions; treat review comments on entry list as possible follow-ups, not blockers for the FLITS PR.

---

## Success criteria

- [ ] `test -n "$GH_TOKEN"` succeeds in the new run
- [ ] FLITS PR open from `cursor/results-library-data-locations-7b14` → `main`
- [ ] Faber2026 #102 references that FLITS PR URL
- [ ] `git -C pipeline rev-parse HEAD` still `af78543…` on Faber2026 (no pin bump)

---

## Pasteable kickoff prompt for the new agent

```text
Read docs/rse/specs/handoff-2026-07-16-03-10-flits-results-library-pr.md and do only the primary task: create the dsa110-FLITS PR from branch cursor/results-library-data-locations-7b14 using GH_TOKEN. Do not bump the Faber2026 pipeline pin. Update Faber2026 PR #102 with the FLITS PR URL when done.
```

---

**Handoff created 2026-07-16 03:10 UTC**
