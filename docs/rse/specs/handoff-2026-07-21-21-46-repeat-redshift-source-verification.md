# Handoff: Repeat source-level redshift verification

---
**Date:** 2026-07-21 21:46 PDT
**Author:** AI Assistant
**Status:** Handoff — blocked
**Branch:** `research/zach-redshift-catalogs`
**Commit:** `ec8fc025`

---

## Tasks

| Task | Status | Notes |
|---|---|---|
| Repeat source-level redshift verification | Blocked | Do not claim or launch the research subagent until all recorded blockers close. |
| Freeze candidate-redshift source evidence | Completed | All 52 registry rows are represented; 46 adopted candidate redshifts have frozen source identifiers and hashes. |
| Freeze authoritative host-redshift evidence | Blocked on owner input | Needs the source-bearing Verdi host-redshift table or minimal extract. |
| Independently replay the completed nine-sightline query corpus | Blocked | Depends on the anonymous and protected query corpora, which first depend on an owner-approved search contract. |

**Current Workflow Phase:** Wayfinder research, blocked before independent replay.

## Workflow Artifacts

**Research documents:**

- [research-expanded-foreground-redshift-verdict-audit.md](research-expanded-foreground-redshift-verdict-audit.md) — earlier 52-row audit; arithmetic reproduced, but 0/52 rows then had a complete host-plus-candidate source chain.
- [research-nine-sightline-catalog-coverage-replay-2026-07-21.md](research-nine-sightline-catalog-coverage-replay-2026-07-21.md) — clean-room replay of current stored-row arithmetic and explicit inventory of the missing expanded query corpus.
- [research-zach-intercatalog-redshift-discrepancy-2026-07-21.md](research-zach-intercatalog-redshift-discrepancy-2026-07-21.md) — source-row verification and unresolved WISE--PS1--STRM discrepancy for Zach.

**Plan and validation documents:**

- [plan-expanded-foreground-catalog-repair.md](plan-expanded-foreground-catalog-repair.md) — implementation plan for the broader catalog repair.
- [validation-expanded-foreground-photometry-and-morphology-catalog.md](validation-expanded-foreground-photometry-and-morphology-catalog.md) — intentionally failed superseded validation; not evidence of current trust.

## Critical References

- `docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-09-repeat-redshift-source-verification.md:1` — named ticket, current blockers, and the exact 52-row question.
- `docs/rse/wayfinder/map-expanded-foreground-catalog-repair.md:1` — destination, standing limits, and decisions already recorded.
- `docs/rse/specs/research-nine-sightline-catalog-coverage-replay-2026-07-21.md:124` — missing expanded-survey coverage, provenance gaps, and reproducible replay state.

## Recent Branch State

- `docs/rse/specs/research-nine-sightline-catalog-coverage-replay-2026-07-21.md:25` — pinned input hashes and the nine-sightline, 50-finite-host-row scope.
- `docs/rse/specs/research-nine-sightline-catalog-coverage-replay-2026-07-21.md:71` — independent verdict and budget calculation: 50/50 stored verdicts and 50/50 flags reproduce.
- `docs/rse/specs/research-nine-sightline-catalog-coverage-replay-2026-07-21.md:124` — no uniform expanded-survey query artifact exists.
- `docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-13-set-nine-sightline-search-contract.md:1` through `expanded-foreground-catalog-repair-16-independently-replay-nine-sightline-query-corpus.md:1` — newly explicit dependency chain.
- No scientific or tracker content was changed in the handoff session before this document. The removed original worktree was replaced with `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-zach-redshift-catalogs-handoff` on the existing branch.

## Reproducibility and Data State

- **Seeds:** None. The offline replay uses no random numbers.
- **Environment:** Offline replay: fresh Python 3.13.9 virtual environment, standard library only. Live diagnostic: clean `conda run -n py312`, Python 3.12.13. Pipeline environment is `pipeline/environment.yml`, SHA-256 `f4c5b36c9502f1386c7ca5d0a0cde3a8aea967068175698333fc7ab8d4762e6e`.
- **Repository revisions:** Parent branch `ec8fc025`; pipeline submodule pin `ab6af1f713496abd2ff2d71bf11edf4100871e94`.
- **Core input hashes:** Registry `8e1998fd41b42e982cb2cdf4967e69eb028df1037caa1cf061578bb6ec2cab97`; candidate provenance ledger `ccc8427786455d498bfd668c878ef0395fbb143a1f2f0939630e5fec68138803`. Full hash table: `research-nine-sightline-catalog-coverage-replay-2026-07-21.md:25`.
- **Zach protected export:** `docs/rse/specs/research/evidence/zach-intercatalog-redshift-2026-07-21/zach_foreground_jfaber.csv`; 5,230 bytes; SHA-256 `d2fcc7fb2db3f1a627b1716ec7cf70d87456eacc57d1ef27d22c7f9bee6105f1`.
- **Offline replay entry point:** `scripts/replay_nine_sightline_catalog_coverage.py --mode offline`. Exact commands and expected output are at `research-nine-sightline-catalog-coverage-replay-2026-07-21.md:154`.
- **In-flight jobs:** None.

## Verification State / Known-Broken

> **Known-broken / unverified:** The foreground catalog and Figure 3 are not trusted scientific artifacts. The named ticket remains open and blocked. Do not promote either artifact from this branch state.

- The offline replay exits 0 and reports `ok=true`: 50 finite-host rows across nine sightlines, zero stored-verdict mismatches, zero budget mismatches, and seven duplicate-separation checks passing.
- That result checks stored-row arithmetic only. It does not reproduce expanded-survey candidate discovery, coverage, identity selection, or source response bytes.
- The clean live Conda diagnostic timed out after 120 seconds and produced no replacement JSON. An earlier adapter-based diagnostic reproduced 44 selected source rows but was not independent; seven surrounding response sets drifted.
- `python3 scripts/validate_expanded_foreground_catalog_gate.py` intentionally exits nonzero against the superseded validation and reports its eight preserved defects.
- Focused checks last recorded: Ruff passed; byte compilation passed; `tests/test_expanded_catalog_validation.py` reported 3 passed.
- Host provenance is incomplete: the authoritative Verdi table or source-bearing extract is absent.
- WISE--PS1--STRM provenance is incomplete for the uniform nine-sightline corpus. The Zach export lacks embedded CasJobs query text, job identifier, and authoritative retrieval time.
- UNIONS/CFIS remains access-denied: the CADC identity works but is not a member of `CFIS-read`.
- `make kb-index` encountered a cold embedding cache and timed out after 120 seconds at 1,408/7,447 documents. No indexer remained running and no tracked index file changed. Refresh remains pending.
- Before this handoff file, the branch worktree was clean and matched `origin/research/zach-redshift-catalogs`. This handoff must be committed and pushed before another machine can see it.

## Learnings

- Candidate-side provenance is no longer the blocker. The remaining source-chain gap is the authoritative host-redshift evidence plus the new uniform query corpus.
- The named repeat-verification ticket cannot be claimed yet. Wayfinder requires all blockers closed before its `/research` subagent runs.
- The next actionable Wayfinder frontier is **Set the nine-sightline search-region and candidate-selection contract**. It is human-in-the-loop and was created after the standing delegation cutoff, so Codex cannot decide it alone.
- The search contract must define centers, angular or proper-radius apertures, galaxy versus cluster regions, quality cuts, identity and ambiguity handling, and duplicate rules. Choosing a radius now is a new search-policy decision, not reconstruction of a recorded aperture.
- Zach's two STRM estimates refer to the same requested PS1 object but use different catalog inputs. The WISE--PS1 row is extrapolated and shares its WISE source with a separate, closer PS1 object; preserve the disagreement as inconclusive.
- A blue WISE color, catalog non-detection, or failed query is not a secure galaxy classification. Preserve explicit `unmatched`, `outside_footprint`, `ambiguous`, `access_denied`, and `query_error` states.

## Action Items and Next Steps

1. [ ] Invoke Wayfinder on **Set the nine-sightline search-region and candidate-selection contract** and complete the required owner discussion. Do not infer the contract from the current registry.
2. [ ] Obtain and freeze the authoritative Verdi host-redshift table or a minimal extract containing FRB and host identifiers, redshift and uncertainty, measurement kind, bibliographic source, upstream row identifier, release or retrieval date, and SHA-256.
3. [ ] After the contract is approved, execute **Freeze the anonymous nine-sightline expanded-survey query corpus** and the owner-assisted **Freeze protected WISE--PS1--STRM and UNIONS/CFIS evidence**.
4. [ ] Run **Independently replay the completed nine-sightline query corpus** through a separate `/research` implementation that does not import the producing selection or verdict functions.
5. [ ] Only after every blocker closes, claim **Repeat source-level redshift verification**, launch its required `/research` subagent, and replay all 52 redshifts, uncertainties, verdicts, duplicate dispositions, and budget flags.
6. [ ] Route every scientific difference to a separate owner-approved adjudication. Do not silently change redshifts, verdicts, budget flags, trust state, or Figure 3.
7. [ ] Record the research resolution in the ticket, close it only after acceptance checks pass, append the map decision pointer, refresh the knowledge base, and run repository closeout checks.

**Recommended Next Skill:** `wayfinder` for the owner-approved search contract. Once the named ticket is unblocked, use `research` through the required independent subagent.

## Resume Prompt

> Read `docs/rse/specs/handoff-2026-07-21-21-46-repeat-redshift-source-verification.md`, then invoke Wayfinder on **Set the nine-sightline search-region and candidate-selection contract**. Preserve all fail-closed gates and do not claim **Repeat source-level redshift verification** until its blockers are resolved.

---

**Handoff created by AI Assistant on 2026-07-21.**
