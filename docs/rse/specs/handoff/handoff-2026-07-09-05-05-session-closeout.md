# Handoff: session closeout — near-miss taxonomy, the mahi mislabel, and the red pin

---
**Date:** 2026-07-09 05:05
**Author:** AI Assistant
**Status:** Handoff
**Branch:** `docs/handoff-closeout-2026-07-09` (off `origin/main`)
**Pin:** `pipeline` gitlink = `6c87890` on `main`; bump to `b6d2d14` staged in **#68, awaiting review**

Supersedes `handoff-2026-07-09-04-14-mahi-tns-mislabel-and-red-pin.md`, whose action
items 1–3 are done. That document's *Learnings* section is still accurate.

---

## Task(s)

Started as one question — *"is gertrude the only co-detection we missed?"* — and each
answer exposed a larger defect underneath.

| Task | Status | Notes |
|------|--------|-------|
| Correct the co-detection near-miss taxonomy | ✅ Complete | Faber2026 **#60**. Four near-misses, not one. |
| Complete the catalog's `chime_event_no` column | ✅ Complete | `~/Data`, outside git. 15 of 16 filled. |
| Correct the `FRB 20240119A` mislabel of mahi | ✅ Complete | dsa110-FLITS **#146** merged. |
| Regenerate the stale `joint_fit_summary.md` | ✅ Complete | dsa110-FLITS **#147** merged. Pin's branch green. |
| Bump the `pipeline` gitlink off the red commit | 🔄 **Blocked on review** | Faber2026 **#68**. Verified, all checks green, `BLOCKED` on required approval. |
| Who owns the nickname↔TNS map | 📋 `@decision` | See Action Items. |
| Does mahi have a registered TNS name | 📋 `@decision` | TNS unreachable from here. |
| Do the four near-misses need a manuscript sentence | 📋 `@decision` | Referee-facing. |

**Current Workflow Phase:** Validate

## Critical References

1. **`~/Developer/scratch/2026-06/_downloads-import/text-corpus/DSA-110_CHIME Codetections - DSA-CHIME Burst Properties.csv`**
   — the authoritative co-detection sheet. 16 rows, all with CHIME event IDs; candname date
   matches MJD date on every row. **The three derived sheets beside it are corrupted.**
2. **`pipeline/configs/bursts.yaml`** — the burst registry. Correct where the sheets are not.
3. **`~/Data/Faber2026/dsa110/catalog/dsa110_frb_catalog_README.md`** — the near-miss taxonomy
   and a warning against the derived sheets. Original at `.dsa110_frb_catalog.csv.bak-2026-07-09`.

## Recent Changes

**Merged, Faber2026:** #60 (near-miss correction across two handoffs + journal), #65 (the 04:14 handoff).
**Merged, dsa110-FLITS:** #147 (`results/joint_fit_summary.md` regenerated), #146 (`galaxies/foreground/vo/test_cli.py:235` docstring).
**Open, Faber2026:** **#68** — `pipeline` gitlink `6c87890 → b6d2d14`, one line.
**Outside git:** `~/Data/.../dsa110_frb_catalog.csv`, six `chime_event_no` cells filled or corrected.

## Verification State / Known-Broken

- **`origin/main` is green** — `latexmk` exit 0, 47 pp, **0 undefined refs in the final pass**
  (the log's 302 "undefined" hits are pre-BibTeX passes; do not read the whole log), `pytest
  tests/` 10 passed, cross-repo budget-table parity 5 passed.
- **`main`'s `pipeline` pin still points at `6c87890`, which is red.** `Tests` fails on that SHA
  (`test_joint_summary_reproducible`, 1 failed / 557 passed). #68 fixes it and is verified:
  fast-forward proven, fresh clone resolves the new pin, drift guard passes there.
- **#68 is `BLOCKED`, not failing.** All three checks are green (`table-parity`, both Socket
  Security). `main` now requires **1 approving review** (`requiresApprovingReviews: true`), landed
  by #63. An agent cannot self-approve. **This needs a human.**
- **Uncommitted / separate lane:** the shared checkout (`branch ms/appendix-c-sync-pr40`) carries
  another agent's live edits — `sample_table.tex`, `scripts/make_sample_table.py`,
  `sections/toa.tex`, a modified `pipeline` gitlink, several untracked handoffs — plus its
  worktree `/private/tmp/faber2026-ci-parity`. **Untouched. Do not sweep into a commit.**
- **Unverified:** `FRB 20240122A` is the pipeline's date-derived designation for mahi. TNS
  registration is **unconfirmed** — `wis-tns.org` 404s a known-good control, so the probe proved
  nothing. mahi's `tns_name` is blank in the DSA master spreadsheet. I did not fill it.

## Learnings

- **The co-detection sheet has 16 rows and all carry CHIME event IDs.** Accept criterion is
  `Processed baseband? = Yes`. Twelve pass. The four that fail are excluded on **data
  availability, never astrophysics**:

  | burst | candname | event_no | why excluded |
  |---|---|---|---|
  | gertrude (FRB20220726A) | `220726aabn` | 237537161 | baseband **exists**; no signal in it |
  | pingu (FRB20230712A) | `230712aadj` | 302686966 | baseband **and** intensity missing |
  | FRB20220912A2 | `221025aanu` | 247683525 / …548 / …922 | repeater; correct event id undetermined |
  | benjy | `220521aaat` | 226301826 | CHIME fine; **DSA has no voltage data** |

- **"9 real CHIME IDs" was a property of a broken file, not of the sample.** "Real" meant only
  *non-empty and not the literal `-`*. Name the predicate; don't let a parse detail masquerade as
  a physical count.

- **The derived sheets are corrupted two independent ways.** `DSA_CHIME_BurstProps.csv` and
  `DSA110_CHIME_Codetection_BurstProperties_Short.csv` have the **MJD column rotated by one row**
  across their last five entries (`FRB 20230814B` paired with MJD 60369.37 = casey's burst).
  They also label mahi **`FRB 20240119A`**, a name belonging to `nikhil` (`240119aacg`, MJD
  60328.605, DM 483, not a co-detection). The mislabeled row carries **mahi's own** RA/Dec
  (39.7665, +71.017861). `chimedsa_burst_specs.csv` — which `pipeline/CLAUDE.md:53` names as
  *the* nickname↔TNS map — inherits the bad cell.

- **That mislabel already cost a real run.** `vo/test_cli.py`'s docstring recorded that the
  foreground summary once "silently shrank the denominator from 12 to 11" for "the FRB 20240119A
  case." The dropped sightline was mahi — the one target with **zero** foreground candidates.
  The bad name flowed sheet → run → docstring, where it sat waiting to be re-derived.

- **Reading this repo's CI is a trap, three ways.** (a) dsa110-FLITS runs several workflows, so
  `gh run list --limit 1` may return `Claude Review` (green) while `Tests` is red — filter by
  `--workflow` or read every `statusCheckRollup` entry by `.name`. (b) `gh run rerun` replays the
  **original merge snapshot**, so a PR stacked on a since-fixed base stays red however often you
  rerun; use `gh pr update-branch`. (c) Workflows are `pull_request`-triggered, so merging into a
  non-default branch produces **no run at all** on the new head — verify that head locally.

- **`BLOCKED ≠ UNSTABLE`.** `UNSTABLE` means checks pending/failing. `BLOCKED` means checks are
  fine and a **required review** is missing. Distinguish before assuming something is broken.

- **The pin's commits are not on upstream.** `.gitmodules` points at `dsa110/dsa110-FLITS`, but
  neither `6c87890` nor `b6d2d14` is reachable from any branch there — both live only on the
  `jakobtfaber` fork. `git submodule update --init` still succeeds because GitHub serves the full
  SHA across the fork network. Resolvability therefore rests on fork-network SHA serving, not on
  any upstream ref. Relevant to #66's `clone_verified`. A `--depth 1` fetch of the SHA **fails**;
  a full fetch succeeds. Abbreviated SHAs are never fetchable.

## Reproducibility & Data State

- **Environment:** conda `py312` for manuscript scripts; conda `flits` / CI nox for the pipeline.
  `py312` lacks `pyarrow`, so two `vo/test_cli.py` parquet tests fail locally and pass in CI —
  **not** a regression. Agent-safe invocation:
  `env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" /opt/anaconda3/bin/conda run --no-capture-output -n py312 …`
- **Data:** `~/Data/Faber2026/dsa110/catalog/dsa110_frb_catalog.csv` — 92 rows, 15 with
  `chime_event_no`. `FRB20220912A2` deliberately blank (three candidate IDs).
- **Determinism checked:** `gen_joint_summary.py::render()` is byte-stable across module loads and
  emits no timestamp. Safe to commit its output.
- **In-flight:** none. All background tasks complete.

## Action Items & Next Steps

1. [ ] **`@human` — approve and merge Faber2026 #68.** It is verified and green; only the
   required approving review is missing. It moves the pin off a commit whose test suite fails.
   The one science-facing effect is the `johndoeII` demotion (trusted, α = 1.37 sub-Kolmogorov →
   superseded by the 2026-07-07 beta-native C2D2 fit, which rails high at β = 4). That demotion
   is **asserted by the JSONs committed at `826ba36`**, not by the PR; the summary had merely
   never been regenerated. No manuscript exposure.
2. [ ] **`@decision` — who owns nickname↔TNS?** `pipeline/CLAUDE.md:53` points at
   `chimedsa_burst_specs.csv`, which is gitignored *and* carries the wrong TNS for mahi.
   `configs/bursts.yaml` has no TNS names at all, so the CSV cannot simply be deprecated.
   Something must own that mapping.
3. [ ] **`@decision` — is `FRB 20240122A` registered on TNS?** If yes, fill `frb_name`/`tns_name`
   for `240122aaag` in the catalog. If not, leave blank and say so in the README.
4. [ ] **`@decision` — do the four near-misses earn a manuscript sentence?** A referee who finds
   the catalog will ask why twelve and not sixteen. One clause per row answers it. Candidate
   home: `sections/toa.tex`.
5. [ ] **`@separate-lane`** — Faber2026 **#66** and the `ci/table-parity-gate` worktree belong to
   another agent. Leave them.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` — #68 changes a
science-facing results artifact through the pin; a reviewer should confirm the regenerated summary
against the committed JSONs before approving.

## Other Notes

- `#63` made review a real gate on `main` mid-session. Every merge after it needs a human
  approval, so autonomous end-to-end merging is no longer available to agents on this repo. That
  is working as intended; plan around it rather than routing past it.
- Memory written this session: `codetection-near-misses-are-four.md`, and
  `pipeline-pin-lives-off-flits-main.md` extended with the three CI-reading traps.

---

**Handoff created by AI Assistant on 2026-07-09**
