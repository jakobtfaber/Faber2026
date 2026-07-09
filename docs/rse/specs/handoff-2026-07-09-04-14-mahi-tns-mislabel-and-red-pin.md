# Handoff: the mahi/nikhil TNS mislabel, and the `pipeline` pin is red

---
**Date:** 2026-07-09 04:14
**Author:** AI Assistant
**Status:** Handoff
**Branch:** `docs/handoff-mahi-tns-and-pin-red` (off `origin/main` @ `733a369`)
**Commit:** `733a369` — *docs: mark B4 done in referee-response matrix (#62)*
**Pin:** `pipeline` gitlink = `6c87890`

---

## Task(s)

This session began as a question — *"is gertrude the only co-detection we missed?"* — and
turned into three findings, each strictly bigger than the last.

| Task | Status | Notes |
|------|--------|-------|
| Correct the co-detection near-miss taxonomy | ✅ Complete | Faber2026 **#60** merged. Four near-misses, not one. |
| Complete the catalog's `chime_event_no` column | ✅ Complete | `~/Data`, outside git. 15 of 16 filled. |
| Correct the `FRB 20240119A` mislabel of mahi | 🔄 In Progress | dsa110-FLITS **#146** open, blocked on #147. |
| Regenerate the stale `joint_fit_summary.md` | 🔄 In Progress | dsa110-FLITS **#147** open, CI running. |
| Decide who owns the nickname↔TNS map | 📋 Planned | `@decision` — see Action Items. |

**Current Workflow Phase:** Validate

## Critical References

Read these three, in order, before touching anything:

1. **`~/Developer/scratch/2026-06/_downloads-import/text-corpus/DSA-110_CHIME Codetections - DSA-CHIME Burst Properties.csv`**
   — the authoritative co-detection sheet. 16 rows, all with CHIME event IDs. Its candname
   date matches its MJD date on every row. **The three smaller sheets beside it are corrupted**
   (see Learnings).
2. **`pipeline/configs/bursts.yaml`** — the burst registry. Correct where the sheets are not.
3. **`~/Data/Faber2026/dsa110/catalog/dsa110_frb_catalog_README.md`** — now documents the
   near-miss taxonomy and warns off the derived sheets. Original catalog preserved at
   `.dsa110_frb_catalog.csv.bak-2026-07-09`.

## Recent Changes

**Merged (Faber2026 #60):**
- `docs/rse/specs/handoff-2026-07-09-03-05-closeout-b3-parity-and-pin-misfire.md` — added a
  Correction subsection to §1; the open action item now names all four near-misses.
- `docs/rse/specs/handoff-2026-07-08-08-55-open-author-decisions.md:141` — inline correction
  where the bad "rejected/no-baseband" phrasing originated.
- `docs/rse/journal.jsonl` — append-only, so the erroneous `03:02:03` entry stands with a
  correction appended after it.

**Open (dsa110-FLITS, both based on `fix/budget-table-data-post-igm-lognormal`, the pin's branch):**
- **#146** `galaxies/foreground/vo/test_cli.py:235` — docstring named `FRB 20240119A` as the
  dropped sightline. It is mahi (`FRB 20240122A`). Docstring only.
- **#147** `results/joint_fit_summary.md` — regenerated from the in-repo generator.

**Outside git:**
- `~/Data/Faber2026/dsa110/catalog/dsa110_frb_catalog.csv` — six `chime_event_no` cells filled
  or corrected (benjy `-`→226301826, phineas, pingu, mahi, chromatica, casey).

## Verification State / Known-Broken

> **The `pipeline` pin is red, and I previously told the owner it was green. That was wrong.**

- **`Tests` on `6c87890` = FAILURE.** `test_joint_summary_reproducible.py::test_summary_matches_generator_output`,
  1 failed / 557 passed / 12 skipped. `6c87890` is the exact commit `origin/main`'s `pipeline`
  gitlink points at. Reproduced locally; deterministic, not flaky.
- **Why the earlier "green" claim was wrong:** `6c87890` has two workflow runs — `Claude Review`
  (success) and `Tests` (failure). `gh run list --limit 1` shows whichever sorts first. A prior
  session read "success" and stopped. **Always filter by `workflowName`.**
- **Faber2026 `origin/main` itself is green:** `latexmk` exit 0, 47 pp, 0 undefined refs;
  `tests/test_dm_budget_uncertainty.py` 10 passed. The manuscript is not affected by the red pin.
- **#146 is red only because it inherits #147's failure.** Its own diff is a docstring.
- **Uncommitted / unpushed:** the shared checkout
  (`~/Developer/repos/.../Faber2026`, branch `ms/appendix-c-sync-pr40`) has **another agent's
  live edits** — `sample_table.tex`, `scripts/make_sample_table.py`, `sections/toa.tex`, a
  modified `pipeline` gitlink, and several untracked handoffs. **Separate lane. Do not touch,
  do not commit, do not clean.** All of this session's work was done in isolated worktrees.
- **Unverified:** `FRB 20240122A` is the pipeline's own date-derived designation for mahi. I
  could **not** confirm TNS registration — `wis-tns.org` returns 404 even for a known-good
  control, so the probe was uninformative. mahi's `tns_name` is blank in the DSA master
  spreadsheet, consistent with "not yet registered." **I did not fill that cell.**

## Learnings

- **The co-detection sheet has 16 rows and every one carries a CHIME event ID.** The accept
  criterion is `Processed baseband? = Yes`. Twelve pass. The four that fail are excluded on
  **data availability, never astrophysics**:

  | burst | candname | event_no | why excluded |
  |---|---|---|---|
  | gertrude (FRB20220726A) | `220726aabn` | 237537161 | baseband **exists**; no signal in it |
  | pingu (FRB20230712A) | `230712aadj` | 302686966 | baseband **and** intensity missing |
  | FRB20220912A2 | `221025aanu` | 247683525 / …548 / …922 | repeater; correct event id undetermined |
  | benjy | `220521aaat` | 226301826 | CHIME fine; **DSA has no voltage data** |

  A prior session (mine) called gertrude a "rejected, no-baseband candidate." Both halves were
  wrong: pingu is the no-baseband case, and benjy — whose catalog `-` I read as "no event ID" —
  has event 226301826. Corrected by #60.

- **The word "real" did damage.** "9 real CHIME IDs" meant only *non-empty and not the literal
  `-`* in the catalog CSV. It was a property of a broken file, and it read as a property of the
  sample. Say what the predicate is.

- **The derived co-detection sheets are corrupted two independent ways.**
  `DSA_CHIME_BurstProps.csv` and `DSA110_CHIME_Codetection_BurstProperties_Short.csv` have the
  **MJD column rotated by one row** across their last five entries (`FRB 20230814B` paired with
  MJD 60369.37, which is casey's burst). Rows 1–7 are fine. They also **label mahi
  `FRB 20240119A`** — a name that belongs to `nikhil` (`240119aacg`, MJD 60328.605, DM 483, not
  a co-detection). The mislabeled row carries **mahi's own RA/Dec** (39.7665, +71.017861), so it
  is mahi's row under the wrong name.
  `chimedsa_burst_specs.csv`, which `pipeline/CLAUDE.md:53` names as *the* nickname↔TNS map,
  inherits the same bad cell.

- **That mislabel already cost a real run.** `vo/test_cli.py`'s docstring records that the
  foreground summary once "silently shrank the denominator from 12 to 11" for "the FRB 20240119A
  case." The dropped sightline was mahi — the one target with **zero** foreground candidates
  (`results/sightline_dm_scattering_budget.md`, count `0`). The bad name propagated from sheet →
  run → test docstring, where it sat waiting to be re-derived.

- **`mergeable: MERGEABLE` ≠ green, and `mergeStateStatus: CLEAN` ≠ green either** when a repo
  runs several workflows. Check every `statusCheckRollup` entry by name.

- **The pin is not on `agent/sightline-halo-grid-figure`.** That branch tops out at `f9e1c24`.
  `6c87890` lives on `fix/budget-table-data-post-igm-lognormal`. `git merge-base --is-ancestor`
  caught this before I branched off the wrong line — run it every time.

## Reproducibility & Data State

- **Environment:** conda `py312` for the manuscript scripts; conda `flits` (or CI's nox) for the
  pipeline. Agent-safe invocation:
  `env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" /opt/anaconda3/bin/conda run --no-capture-output -n py312 …`
- **Data:** `~/Data/Faber2026/dsa110/catalog/dsa110_frb_catalog.csv` (92 rows, 15 with
  `chime_event_no`). Backup `.dsa110_frb_catalog.csv.bak-2026-07-09`.
- **Determinism check performed:** `gen_joint_summary.py::render()` is byte-stable across two
  module loads and emits no timestamp. Safe to commit its output.
- **In-flight:** dsa110-FLITS #147 CI (`Tests`, ~3 min). #146 stacked behind it.

## Action Items & Next Steps

1. [ ] **Merge dsa110-FLITS #147** once `Tests` is green. It regenerates
   `results/joint_fit_summary.md` and turns the pin's branch green for the first time since
   `826ba36`. Verify by `workflowName`, not by the first run in the list.
2. [ ] **Merge dsa110-FLITS #146** (docstring). It should go green automatically once #147 lands.
3. [ ] **Do not bump the `pipeline` gitlink as a side effect.** Per `CLAUDE.md`, that is its own
   reviewed step. Both PRs land on the pin's *branch*; `origin/main` keeps pointing at `6c87890`
   until someone deliberately bumps it. When bumping, first run
   `git merge-base --is-ancestor 6c87890 <new>`.
4. [ ] **`@decision` — who owns nickname↔TNS?** `pipeline/CLAUDE.md:53` points at
   `chimedsa_burst_specs.csv`, which is gitignored *and* carries the wrong TNS for mahi.
   `configs/bursts.yaml` has no TNS names at all, so the CSV cannot simply be deprecated.
   Something must own that mapping. This is a design call, deliberately left to the owner.
5. [ ] **`@decision` — does mahi have a registered TNS name?** If `FRB 20240122A` is confirmed on
   TNS, fill `frb_name`/`tns_name` for `240122aaag` in the catalog. If it is unregistered, leave
   blank and say so in the README.
6. [ ] **`@decision` — do the four near-misses deserve a sentence in the manuscript?** A referee
   who finds the catalog will ask why the sample is twelve and not sixteen. The honest answer is
   one clause per row (see Learnings). Candidate home: `sections/toa.tex`.
7. [ ] Faber2026 **#59, #63, #64** are open and belong to **another agent**. Leave them.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` — #147 changes a
science-facing results artifact, and the next session should confirm the regenerated summary
against the committed JSONs before the pin is ever bumped to include it.

## Other Notes

- The `johndoeII` demotion in #147 (trusted, α = 1.37 sub-Kolmogorov → superseded by the
  2026-07-07 beta-native C2D2 fit, which rails high at β = 4) is **asserted by the committed
  JSONs, not by me.** The summary had simply lagged since `826ba36`. Manuscript exposure is nil:
  Faber2026 cites johndoeII only as figure panels plus a
  `% TODO(disc-johndoeii): Interpret after revalidation` at `sections/discussion.tex:75`.
- Two memory files were written this session:
  `codetection-near-misses-are-four.md`, and the pre-existing
  `pipeline-pin-lives-off-flits-main.md` proved its worth twice.

---

**Handoff created by AI Assistant on 2026-07-09**
