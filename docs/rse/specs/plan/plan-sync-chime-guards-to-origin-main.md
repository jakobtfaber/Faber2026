# Implementation Plan: Sync CHIME artifact-control guards to origin/main (Faber2026 + dsa110-FLITS)

---
**Date:** 2026-07-09
**Author:** AI Assistant (Claude, session 54fbfb21)
**Status:** Complete (manual verification pending: Overleaf pull)
**Related Documents:**
- [Assessment: ChatGPT scint de-combing review](../assessment/assessment-chatgpt-scint-decombing-review.md) *(untracked; committed by this plan)*
- [Experiment: freya CHIME instrumental origin](../experiment/experiment-freya-chime-instrumental-origin.md)

---

## Overview

The 2026-07-09 Claude Science session (a1d05406) implemented CHIME
artifact-control guards for the scintillation Lorentzian driver and committed
them **only locally**, as pipeline commit `17ad490` on top of the current pin
`79eaf7e`. Nothing has reached GitHub: the commit is in no remote ref, there is
no PR, the Faber2026 `pipeline` gitlink is dirty (uncommitted bump
`79eaf7e 17ad490`), and the session's assessment doc is untracked. The work
itself is verified (21/21 new tests pass locally; auditor findings confined to
chat prose).

This plan lands that work on `origin/main` of **both** repos — the guards on
`jakobtfaber/dsa110-FLITS` `main` via cherry-pick PR (mirroring the zach
FLITS #149 → pin-replay 79eaf7e → Faber2026 #71 precedent), and the pin bump +
assessment doc + repro-doc sync on `jakobtfaber/Faber2026` `main` via a
`#71`-style evidence PR — then verifies a fresh clone resolves the new pin, so
the user can pull `main` into Overleaf and recompile.

It also fixes the documented pin-reachability fragility: pin commits currently
exist on GitHub only as dangling fork-network objects (verified:
`git ls-remote origin` lists 143 refs; none contain `334cc74`/`79eaf7e`). Per
user decision (2026-07-09), the pin lineage gets a **persistent branch**
`pin/faber2026` on the `jakobtfaber/dsa110-FLITS` fork.

**Goal:** `origin/main` of both repos carries the guard work; the Faber2026
pin points at a reachable, correctly-messaged pin commit; a fresh
`git clone && git submodule update --init` succeeds; Overleaf pulls `main`
cleanly.

**Motivation:** Un-strand a $25/2.2 h verified work product; close the
reproducibility hazard before it bites a fresh clone; give Overleaf a clean
`main` to sync from.

## Current State Analysis

**Pipeline submodule (`pipeline/`, fork `jakobtfaber/dsa110-FLITS`):**
- HEAD detached at `17ad490` ("feat(scint): add CHIME artifact-control guards
  to Lorentzian driver (#149)"), parent `79eaf7e`, working tree clean.
- The `(#149)` subject reference is **wrong** — FLITS #149 is the zach C2D4
  beta promotion (merged 12:08Z), not the guards. The guards have no PR.
- `17ad490` diffstat (8 files, +1151/−4): new
  `scintillation/scint_analysis/chime_artifact_guards.py` (417 lines), new
  `scintillation/scint_analysis/tests/test_chime_artifact_guards.py` (210),
  new `analysis/scintillation-dsa-lorentzian-2026-07-07/test_driver_guards.py`
  (129), new `analysis/scintillation-dsa-lorentzian-2026-07-07/CHANGES-artifact-controls.md`,
  edits to `analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py`
  (+258), `.../README.md` (+38), `scintillation/scint_analysis/analysis.py`
  (+6), `scintillation/scint_analysis/pipeline.py` (+8).
- `17ad490` is **not** on GitHub (API 422); `79eaf7e`/`334cc74` are dangling
  fork-network objects in no ref.
- `334cc74` **is** an ancestor of fork `origin/main` (verified
  `merge-base --is-ancestor`); `79eaf7e...origin/main` is ahead 1 / behind 29.
  Every guard-touched pre-existing file is **byte-identical** between
  `79eaf7e` and `origin/main` (verified per-file `git diff --stat` empty), so
  the cherry-pick onto main is expected clean.
- FLITS CI: `.github/workflows/tests.yml` runs `uvx nox -s tests` (py3.12) on
  PRs and main pushes.

**Faber2026 super-repo:**
- `pipeline` gitlink dirty: `79eaf7e → 17ad490` (uncommitted).
- `docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md` untracked
  (content verified accurate against the session).
- `docs/rse/journal.jsonl` +5 uncommitted append-only lines (4 from the
  completed `repro-spine` lane, 1 from this session's review). Journal
  protocol (`docs/rse/journal-protocol.md`, "Commit policy") says the journal
  rides along with any doc/code commit.
- `REPRODUCE.md:27-34` is **stale** (confirmed): claims the pin sits "310
  commits along a divergent line, on the branch
  `fix/budget-table-data-post-igm-lognormal`" and that fixes are PR'd against
  that branch. That branch was merged into fork main (FLITS #151) and deleted;
  the pin base `334cc74` is now an ancestor of fork main, and no such branch
  exists on the remote.
- `REPRODUCE.md:150-158` documents the pin history ending at `79eaf7e`
  (Faber2026 #68, #71); `repro_manifest.csv` rows 5, 8, 9, 13 carry
  "pin now 79eaf7e" UPDATE notes (grep `79eaf7e` → 4 rows). Precedent
  `fd7a1ee` ("docs(repro): sync REPRODUCE.md + repro_manifest.csv to the
  current pin") requires the same sync for this bump.
- Branch protection on `main`: required check `parity`
  (`.github/workflows/table-parity.yml`), strict (branch must be up to date),
  1 review required — precedent PRs #71/#149 were owner-merged
  (`mergedBy: jakobtfaber`) without an approving review, i.e. admin merge.
- **Separate live lane (out of scope):** manuscript edits
  `sections/{results,discussion,appendix}.tex`, `bib/refs.bib` (+46), and
  untracked `sections/twoscreen_formalism.tex` (`\input` at
  `sections/appendix.tex:198`). `lane-liveness` verdict: **live**. Preserved
  untouched per user decision.

**Standing authorization:** repo `CLAUDE.md` grants cross-session push/PR/merge
without per-action approval; the `oneway-guard` hook may still surface one
Allow dialog (sticky window).

## Desired End State

**New behavior / state:**
- `jakobtfaber/dsa110-FLITS` `main` contains the guard commit (via merged PR).
- Fork branch `pin/faber2026` exists, pointing at the reworded pin commit
  `<PIN2>` (history: fork-main ancestry → `334cc74` → `79eaf7e` → `<PIN2>`).
- `jakobtfaber/Faber2026` `main` contains: gitlink → `<PIN2>`, the assessment
  doc, the journal lines, and REPRODUCE.md/repro_manifest.csv synced to
  `<PIN2>` (including the corrected stale paragraph).
- Local working tree: super-repo clean on `main` (except the preserved
  manuscript lane), submodule checked out at `<PIN2>`.

**Success looks like:**
- Fresh clone + `git submodule update --init pipeline` checks out `<PIN2>`
  without fetch errors.
- Overleaf pulls Faber2026 `main` and recompiles; PDF is **unchanged** (this
  sync touches no compiled `.tex` — the twoscreen lane, which does change the
  PDF, lands separately).
- `git status` in the super-repo no longer shows `pipeline` modified or the
  assessment doc untracked.

## What We're NOT Doing

- [ ] **Not** touching the live twoscreen manuscript lane
  (`sections/*.tex`, `bib/refs.bib`, `sections/twoscreen_formalism.tex`) —
  another session's in-flight work; it lands separately when its owner
  finishes.
- [ ] **Not** switching the pin to FLITS `main` (would drag 29 unrelated
  commits — V1 keystone, DM provenance, scattering manifest — into the pin;
  #71 precedent explicitly stays on-lineage).
- [ ] **Not** changing `.gitmodules` (URL stays `https://github.com/dsa110/dsa110-FLITS.git`;
  fork-network object sharing plus the new branch make the pin resolvable).
- [ ] **Not** fixing the casey CHIME configs' missing
  `grid_regularization`/`bandpass_normalization` blocks (13/14 configs demote
  to `diagnostic_only` by design; separate science decision).
- [ ] **Not** deleting or force-updating any existing remote branch; all
  steps are additive (new branches, new commits, revert-able merges).

**Rationale:** the user asked for a sync of the guard work; everything else is
either another lane's property or a separately-reviewed science decision.

## Implementation Approach

**Technical strategy:** mirror the zach precedent exactly — (1) guards land on
fork `main` via their own PR; (2) the pin lineage gets the same content as a
replay commit (already exists as `17ad490`; only the message is wrong, so
amend the subject → `<PIN2>`); (3) publish the pin lineage on a persistent
branch; (4) bump the Faber2026 gitlink via an evidence PR that replicates
#71's checks (ancestry, diff scope, parity byte-identity) and syncs the repro
docs, per `fd7a1ee` precedent.

**Key architectural decisions:**
1. **Decision:** cherry-pick `17ad490` onto fork `main` rather than merge the
   pin lineage into main.
   - **Rationale:** guard-touched files are byte-identical between `79eaf7e`
     and `origin/main`, so the pick is clean; merging the lineage would drag
     the replayed zach commit into main's history a second time.
   - **Trade-offs:** guards exist as two SHAs (main + pin), same as zach.
   - **Alternatives considered:** pin→main merge (history noise); rebasing the
     pin onto main (rewrites the pin lineage — forbidden).
2. **Decision:** amend `17ad490`'s subject (content unchanged) before
   publishing, producing `<PIN2>`.
   - **Rationale:** the `(#149)` reference is verifiably wrong and would be
     permanent in the pin lineage; nothing remote references `17ad490`, and
     the only local reference is the *uncommitted* gitlink, which this plan
     re-points.
   - **Trade-offs:** SHA churn; mitigated by a liveness/HEAD gate immediately
     before the amend.
   - **Alternatives considered:** keep the SHA (permanent wrong provenance);
     recreate the commit from scratch (identical outcome, more steps).
3. **Decision:** persistent fork branch `pin/faber2026` (user-approved).
   - **Rationale:** closes the dangling-object fragility REPRODUCE.md warns
     about; additive and non-destructive.
   - **Trade-offs:** the branch must be advanced on every future pin bump —
     REPRODUCE.md edit documents this as part of the bump procedure.
   - **Alternatives considered:** status quo dangling SHAs (fragile); tags
     (equally durable but pin bumps are a moving line, a branch matches).

**Patterns to follow:**
- Evidence-PR structure: Faber2026 PR #71 body (ancestry proof, scoped
  diffstat, parity byte-identity) — `gh pr view 71 --repo jakobtfaber/Faber2026`.
- Repro-doc sync: commit `fd7a1ee` (REPRODUCE.md + repro_manifest.csv to pin).
- Journal ride-along: `docs/rse/journal-protocol.md` "Commit policy".

## Implementation Phases

This is a git-orchestration plan: the "failing test → pass" loop maps to
**gate command → mutate → verify command**, with every gate shown. Steps
marked **[ONE-WAY]** are outward-facing (push/PR/merge) — covered by the
standing authorization, mechanically gated by `oneway-guard`.

Shell variables carried across steps (captured, never guessed):
`$FLITS_PR` (Phase 1 PR number), `$PIN2` (Phase 2 amended SHA).

### Phase 0: Freshness and liveness gates (read-only)

**Objective:** prove the ground hasn't moved since research; abort if it has.

**Tasks:**
- [x] **Gate: pipeline HEAD and cleanliness**

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline
  test "$(git rev-parse HEAD)" = "17ad490bd41d6d44fec8577b229448b98fe3d548" || { echo ABORT: HEAD moved; exit 1; }
  git status --porcelain | grep -q . && { echo ABORT: pipeline dirty; exit 1; } || echo clean
  ```

- [x] **Gate: guards still absent from fork main; lineage facts hold**

  ```bash
  git fetch origin main --quiet
  git cat-file -e origin/main:scintillation/scint_analysis/chime_artifact_guards.py 2>/dev/null \
    && { echo ABORT: guards already on main; exit 1; } || echo absent-as-expected
  git merge-base --is-ancestor 334cc74 origin/main && echo ancestry-ok
  git ls-remote origin | grep -E '79eaf7e|334cc74|17ad490' && { echo ABORT: pin SHAs now in a ref — replan; exit 1; } || echo dangling-as-expected
  ```

- [x] **Gate: no competing FLITS PR**

  ```bash
  gh pr list --repo jakobtfaber/dsa110-FLITS --state open --json number,title \
    --jq 'map(select(.title|test("guard|scint";"i")))' | grep -q '\[\]' || echo "REVIEW open PRs before continuing"
  ```

- [x] **Gate: super-repo separate lane inventory unchanged**

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
  git status --short --branch   # expect: gitlink pipeline modified, assessment doc + twoscreen untracked, sections/bib/journal modified — nothing new
  git worktree list --porcelain
  ```

**Verification:**
- [x] All four gates print their expected line; any ABORT halts the plan
      (mid-run failure policy: halt, report, re-plan — no partial mutation has
      happened yet in this phase).

### Phase 1: Land the guards on `jakobtfaber/dsa110-FLITS` `main`

**Objective:** guards merged to fork `main` via PR with CI green.

**Tasks:**
- [x] **Create an isolated worktree at fork main** (never disturb the pinned
      checkout the super-repo references)

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline
  git worktree add /private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/54fbfb21-8517-4f85-bf13-b0cf07a5bc6a/scratchpad/flits-guards-main \
    -b feat/chime-artifact-guards origin/main
  cd /private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/54fbfb21-8517-4f85-bf13-b0cf07a5bc6a/scratchpad/flits-guards-main
  ```

- [x] **Cherry-pick, watch it apply cleanly** (pre-verified: all touched
      pre-existing files byte-identical between `79eaf7e` and `origin/main`)

  ```bash
  git cherry-pick 17ad490bd41d6d44fec8577b229448b98fe3d548
  # expect: clean apply. On ANY conflict: git cherry-pick --abort && halt — the
  # byte-identity premise failed; re-diff and re-plan. Do not hand-resolve.
  ```

- [x] **Reword the picked commit's wrong PR reference** (subject only; body kept)

  ```bash
  git log -1 --format=%B | sed '1s/ (#149)$//' | git commit --amend -F -
  git log -1 --format=%s   # expect: "feat(scint): add CHIME artifact-control guards to Lorentzian driver"
  ```

- [x] **Run the new tests at main's tree, watch them pass** (the "failing
      test" already exists — 21 tests that cannot run on main today because
      the files are absent; this run proves they pass post-pick)

  ```bash
  env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
    /opt/anaconda3/bin/conda run -n py312 python -m pytest \
    scintillation/scint_analysis/tests/test_chime_artifact_guards.py \
    "analysis/scintillation-dsa-lorentzian-2026-07-07/test_driver_guards.py" -q
  # expect: 21 passed
  ```

- [x] **[ONE-WAY] Push the branch and open the PR**

  ```bash
  git push origin feat/chime-artifact-guards
  gh pr create --repo jakobtfaber/dsa110-FLITS --base main \
    --title "feat(scint): CHIME artifact-control guards for the Lorentzian driver" \
    --body "Cherry-pick of the 2026-07-09 guard work (local pin-lineage commit 17ad490) onto main. New module scintillation/scint_analysis/chime_artifact_guards.py + driver wiring: first-class harmonic mask, fail-closed CHIME provenance gate (diagnostic_only demotion), off-pulse ACF null, low-lag excision stability, harmonic-mask systematic. 16 unit + 5 driver integration tests. DSA path proven numerically unchanged. Companion pin bump lands in Faber2026 (mirrors the zach #149 -> pin flow)."
  FLITS_PR=$(gh pr list --repo jakobtfaber/dsa110-FLITS --head feat/chime-artifact-guards --json number --jq '.[0].number')
  echo "FLITS_PR=$FLITS_PR"
  ```

- [x] **Wait for CI (`Tests` workflow, `uvx nox -s tests`), then [ONE-WAY] merge**

  ```bash
  gh pr checks "$FLITS_PR" --repo jakobtfaber/dsa110-FLITS --watch
  # expect: all green. If tests fail in the uv env (e.g. a dep missing from
  # uv.lock that conda py312 has): halt and fix within this PR before merging.
  gh pr merge "$FLITS_PR" --repo jakobtfaber/dsa110-FLITS --squash --admin --delete-branch
  ```

**Dependencies:** Phase 0 gates passed.

**Verification:**
- [x] `git fetch origin main --quiet && git cat-file -e origin/main:scintillation/scint_analysis/chime_artifact_guards.py && echo on-main` → `on-main`
- [x] `git worktree remove /private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/54fbfb21-8517-4f85-bf13-b0cf07a5bc6a/scratchpad/flits-guards-main` succeeds (worktree clean).

### Phase 2: Reword the pin commit and publish `pin/faber2026`

**Objective:** pin lineage carries a correctly-attributed guard commit
`<PIN2>` and is reachable via a persistent fork branch.

**Tasks:**
- [x] **Gate: re-verify HEAD immediately before amending** (shared-tree
      protocol — another writer may have moved it during Phase 1)

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline
  test "$(git rev-parse HEAD)" = "17ad490bd41d6d44fec8577b229448b98fe3d548" || { echo ABORT: HEAD moved; exit 1; }
  git status --porcelain | grep -q . && { echo ABORT: dirty; exit 1; } || echo clean
  ```

- [x] **Amend the subject to reference the real PR** (content unchanged)

  ```bash
  git log -1 --format=%B \
    | sed "1s/.*/Promote CHIME artifact-control guards onto pin 79eaf7e (FLITS #$FLITS_PR)/" \
    | git commit --amend -F -
  PIN2=$(git rev-parse HEAD)
  echo "PIN2=$PIN2"
  ```

- [x] **Prove the amend changed nothing but the message**

  ```bash
  git diff --stat 17ad490bd41d6d44fec8577b229448b98fe3d548 "$PIN2" | grep -q . \
    && { echo ABORT: tree changed; exit 1; } || echo tree-identical
  git merge-base --is-ancestor 79eaf7eecfedcecae2c5bb46d2bf664a109d3ca4 "$PIN2" && echo ancestry-ok
  ```

- [x] **[ONE-WAY] Publish the pin lineage on the persistent branch**

  ```bash
  git push origin "$PIN2:refs/heads/pin/faber2026"
  git ls-remote origin pin/faber2026   # expect: $PIN2
  ```

**Dependencies:** Phase 1 (needs `$FLITS_PR`).

**Verification:**
- [x] `git ls-remote origin pin/faber2026 | grep -c "$PIN2"` → `1`
- [x] `gh api repos/jakobtfaber/dsa110-FLITS/commits/$PIN2 --jq .sha` succeeds (no 422).

### Phase 3: Faber2026 sync PR (gitlink bump + assessment doc + repro-doc sync)

**Objective:** Faber2026 `main` gets the pin bump with #71-grade evidence,
the assessment doc, the journal lines, and REPRODUCE.md/repro_manifest.csv
synced to `<PIN2>` (including the stale-paragraph fix).

**Tasks:**
- [x] **Branch off up-to-date main; carry ONLY this lane's paths**

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
  git fetch origin main --quiet
  git switch -c agent/bump-pipeline-chime-guards origin/main
  # gitlink: the submodule checkout already sits at $PIN2 after Phase 2's amend
  git -C pipeline rev-parse HEAD   # expect $PIN2
  git add pipeline docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md docs/rse/specs/plan/plan-sync-chime-guards-to-origin-main.md docs/rse/journal.jsonl
  # NEVER: git add -A / git add . — the manuscript lane must not be swept in.
  git status --short   # expect exactly: M pipeline, A assessment doc, A this plan, M journal — plus the UNSTAGED manuscript lane
  ```

- [x] **Edit `REPRODUCE.md:27-34`** — replace the stale paragraph

  Old text (verbatim, starts "One wrinkle worth knowing"):
  > The `.gitmodules` URL above is what a fresh `git submodule update --init` clones, and it does resolve the pinned SHA. But **pipeline development happens on the `jakobtfaber/dsa110-FLITS` fork**, and the pinned commit is *not* an ancestor of either repo's `main` — it sits 310 commits along a divergent line, on the branch `fix/budget-table-data-post-igm-lognormal`. A pipeline fix is therefore PR'd against that branch, not against `main` (see FLITS #146, #147, #148). Check `git merge-base --is-ancestor` before ever bumping the pin.

  New text:
  > The `.gitmodules` URL above is what a fresh `git submodule update --init` clones, and it resolves the pinned SHA. **Pipeline development happens on the `jakobtfaber/dsa110-FLITS` fork.** Since FLITS #151 merged the old divergent line into the fork's `main`, the pin base is an ancestor of fork `main`; the pin itself sits 1–2 replayed commits off it. The full pin lineage is published on the fork branch **`pin/faber2026`** (since 2026-07-09), so pinned SHAs are reachable by ref, not just as fork-network dangling objects. A pipeline fix is PR'd against fork `main`, then replayed onto the pin (see FLITS #149 → Faber2026 #71 for the pattern); advance `pin/faber2026` on every bump, and check `git merge-base --is-ancestor` before ever bumping the pin.

- [x] **Edit `REPRODUCE.md:150-158`** — extend the pin history sentence.
  After "…`334cc74 → 79eaf7e` as Faber2026 #71, a single commit promoting the
  `zach` C2D4 beta fit." insert:
  > Then `79eaf7e → <PIN2-short>` as Faber2026 #<this-PR>, a single commit promoting the CHIME artifact-control guards (FLITS #$FLITS_PR; scintillation lane only).
  and update both "currently pinned submodule (`79eaf7e`)" mentions
  (lines 150, 152–155) to `<PIN2-short>`, keeping the "no `*_table_data.json`
  and neither table emitter is touched" claim — re-proven by the parity gate
  below. (`<PIN2-short>` = `git rev-parse --short=7 $PIN2`; the PR number is
  known after `gh pr create`, so this edit is finalized in the same commit
  via `--amend` right after the PR number is assigned, or the PR number is
  referenced as "this PR" — match `fd7a1ee`'s wording.)

- [x] **Edit `repro_manifest.csv`** — append to the `notes` field of each of
  the 4 rows matching `79eaf7e` (rows 5, 8, 9, 13):

  ```
   UPDATE 2026-07-09 (pin now <PIN2-short>, Faber2026 #<this-PR>): one-commit descendant of 79eaf7e promoting the CHIME scintillation artifact-control guards (FLITS #$FLITS_PR); touches only scintillation/ and analysis/scintillation-dsa-lorentzian-2026-07-07/ — no galaxies/, no emitters, no *_table_data.json — so every claim verified at 79eaf7e carries unchanged.
  ```

  Apply with a small python snippet (CSV-safe; do not sed a quoted CSV):

  ```bash
  python3 - "$PIN2" <<'EOF'
  import csv, sys
  short = sys.argv[1][:7]
  upd = (" UPDATE 2026-07-09 (pin now %s): one-commit descendant of 79eaf7e "
         "promoting the CHIME scintillation artifact-control guards; touches only "
         "scintillation/ and analysis/scintillation-dsa-lorentzian-2026-07-07/ -- "
         "no galaxies/, no emitters, no *_table_data.json -- so every claim "
         "verified at 79eaf7e carries unchanged." % short)
  rows = list(csv.reader(open("repro_manifest.csv")))
  n = 0
  for r in rows[1:]:
      if any("79eaf7e" in c for c in r):
          r[-1] += upd; n += 1
  assert n == 4, f"expected 4 rows, hit {n}"
  csv.writer(open("repro_manifest.csv", "w", newline="")).writerows(rows)
  print("updated", n, "rows")
  EOF
  ```

- [x] **Gate: parity byte-identity across the bump** (the #71 evidence check;
  the `parity` CI check re-proves it on the PR)

  ```bash
  git -C pipeline diff --stat 79eaf7eecfedcecae2c5bb46d2bf664a109d3ca4 "$PIN2" -- galaxies/ exports/ | grep -q . \
    && { echo ABORT: parity-read files changed; exit 1; } || echo parity-clean
  git -C pipeline rev-list --left-right --count "79eaf7eecfedcecae2c5bb46d2bf664a109d3ca4...$PIN2"   # expect: 0 1
  ```

- [x] **Append a journal entry, commit, [ONE-WAY] push + PR**

  ```bash
  bash scripts/journal-append.sh claude-main scint-guards working \
    "Landing guard sync: FLITS #$FLITS_PR merged to fork main; pin/faber2026 published at ${PIN2:0:7}; opening Faber2026 pin-bump PR (gitlink 79eaf7e -> ${PIN2:0:7} + assessment doc + repro-doc sync)."
  git add REPRODUCE.md repro_manifest.csv docs/rse/journal.jsonl
  git commit -m "Bump pipeline pin 79eaf7e -> ${PIN2:0:7} (CHIME artifact-control guards)" \
    -m "Promotes the 2026-07-09 guard work (FLITS #$FLITS_PR) onto the pin without switching lineage. Adds the session assessment doc, this plan, journal entries, and syncs REPRODUCE.md + repro_manifest.csv to the new pin (incl. correcting the stale divergent-branch paragraph; pin lineage now published on fork branch pin/faber2026)." \
    -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    -- pipeline docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md docs/rse/specs/plan/plan-sync-chime-guards-to-origin-main.md docs/rse/journal.jsonl REPRODUCE.md repro_manifest.csv
  git push origin agent/bump-pipeline-chime-guards
  gh pr create --repo jakobtfaber/Faber2026 --base main \
    --title "Bump pipeline pin 79eaf7e -> ${PIN2:0:7} (CHIME artifact-control guards)" \
    --body "$(printf '## Bump pipeline pin `79eaf7e` -> `%s` — CHIME artifact-control guards\n\nMakes the 2026-07-09 guard work (FLITS #%s) available to Faber2026 **without switching lineage**; pin lineage now published on fork branch `pin/faber2026`.\n\n### Evidence\n1. **Ancestry (fast-forward):** `git merge-base --is-ancestor 79eaf7e %s` passes — compare is ahead 1, behind 0.\n2. **Submodule diff is guards-only:** 8 files under `scintillation/` + `analysis/scintillation-dsa-lorentzian-2026-07-07/`. No `galaxies/`, no `exports/`, no `*_table_data.json`.\n3. **Parity invariant:** every file the `table-parity` check reads is byte-identical between `79eaf7e` and `%s` (diff --stat empty).\n4. **Tests:** 21 new guard tests pass at the pin (16 unit + 5 driver integration); full scint suite 149 passed / 2 skipped in-session.\n5. **Reachability:** `%s` is fetchable via `pin/faber2026` (ls-remote verified), closing the dangling-SHA hazard REPRODUCE.md documented.\n6. Assessment doc + repro-doc sync included (precedent: fd7a1ee).\n' "${PIN2:0:7}" "$FLITS_PR" "${PIN2:0:7}" "${PIN2:0:7}" "${PIN2:0:7}")"
  ```

- [x] **Wait for the required `parity` check, then [ONE-WAY] merge**

  ```bash
  gh pr checks --repo jakobtfaber/Faber2026 --watch   # expect: parity green
  gh pr merge --repo jakobtfaber/Faber2026 --squash --admin --delete-branch
  ```

**Dependencies:** Phase 2 (`$PIN2` published; submodule HEAD at `$PIN2`).

**Verification:**
- [x] `git fetch origin main --quiet && git ls-tree origin/main pipeline` shows `$PIN2`.
- [x] `git show origin/main:docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md | head -1` → `# Assessment: ChatGPT review of the scintillation "de-combing" code`.

### Phase 4: Post-merge verification, local reconciliation, Overleaf pull

**Objective:** prove a fresh consumer resolves the new pin; leave the local
tree clean; hand Overleaf a pullable `main`.

**Tasks:**
- [x] **Reconcile local main** (manuscript lane rides untouched)

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
  git switch main && git pull --ff-only origin main
  git status --short   # expect ONLY the manuscript lane (sections/, bib/, twoscreen) — pipeline gitlink clean, docs clean
  ```

- [x] **Fresh-clone reproducibility test (the real gate the old convention
  failed silently)**

  ```bash
  cd /private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/54fbfb21-8517-4f85-bf13-b0cf07a5bc6a/scratchpad
  git clone --filter=blob:none https://github.com/jakobtfaber/Faber2026.git fresh-clone-verify
  cd fresh-clone-verify && git submodule update --init pipeline
  git -C pipeline rev-parse HEAD   # expect $PIN2
  ```

- [x] **Journal the closeout**

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
  bash scripts/journal-append.sh claude-main scint-guards done \
    "Guard sync landed: FLITS #$FLITS_PR on fork main; pin/faber2026 at ${PIN2:0:7}; Faber2026 pin-bump PR merged; fresh-clone submodule update resolves ${PIN2:0:7}. Manuscript twoscreen lane untouched (live, separate owner)."
  ```

  (This re-dirties `journal.jsonl` by one line — expected; it rides with the
  next doc commit per protocol.)

- [ ] **Overleaf pull (manual, user)** — in the Overleaf project for
  Faber2026: Menu → GitHub → *Pull GitHub changes into Overleaf*, then
  recompile. Expected: pull succeeds, **PDF unchanged** (no compiled `.tex`
  changed in this sync). The `overleaf` skill / `olcli` can drive this if the
  user prefers agent-side execution.

**Dependencies:** Phase 3 merged.

**Verification:** listed inline (fresh-clone SHA check is the phase's own
gate).

## Success Criteria

### Automated Verification

- [x] `gh pr view $FLITS_PR --repo jakobtfaber/dsa110-FLITS --json state --jq .state` → `MERGED`
- [x] `git -C pipeline ls-remote origin pin/faber2026` → `$PIN2`
- [x] `git -C pipeline cat-file -e origin/main:scintillation/scint_analysis/chime_artifact_guards.py` → exit 0
- [x] `git ls-tree origin/main pipeline` (Faber2026) → `$PIN2`
- [ ] Fresh clone + `git submodule update --init pipeline` → HEAD `$PIN2`, no fetch error
- [x] Faber2026 required `parity` check green on the merged PR
- [x] 21 guard tests pass at `$PIN2`:
      `conda run -n py312 python -m pytest scintillation/scint_analysis/tests/test_chime_artifact_guards.py "analysis/scintillation-dsa-lorentzian-2026-07-07/test_driver_guards.py" -q`
- [x] `git -C pipeline diff --stat 17ad490 $PIN2` → empty (amend was message-only)
- [x] Super-repo `git status --short` shows no `pipeline` modification and no
      untracked assessment doc after Phase 4 pull

### Manual Verification

- [ ] Overleaf pull of Faber2026 `main` succeeds; recompile completes; PDF
      diff is empty (expected — no compiled `.tex` in this sync)
- [ ] Spot-read the merged REPRODUCE.md paragraph: pin-lineage description
      matches live remote state (branch `pin/faber2026` visible on GitHub UI)
- [ ] The manuscript lane (sections/, bib/, twoscreen) is still intact and
      uncommitted after all phases (its owner decides its landing)

### Reproducibility & Correctness (research code)

- [x] No numerical outputs change: `git -C pipeline diff 79eaf7e..$PIN2 -- '*.json' '*.tex'` touches only
      `freya_chime_guards_demo.json`-class analysis-dir artifacts, no
      manuscript-embedded tables/figures (parity gate proves the embedded set)
- [x] The guard commit's in-session verification stands: DSA widths
      bit-identical pre/post guards; CHIME freya demotes to `diagnostic_only`
      (documented in `CHANGES-artifact-controls.md` at the pin)

## Testing Strategy

**Unit (in-phase):** the 21 existing guard tests run at three points — the
pin (already verified), the cherry-picked main tree (Phase 1), and FLITS CI
(`uvx nox -s tests`, Phase 1 merge gate).

**Integration:** Faber2026 `parity` required check on the PR (Phase 3);
fresh-clone submodule resolution (Phase 4) — this is the test the old
dangling-SHA convention had no coverage for.

**Manual:** Overleaf pull + recompile (Phase 4).

**Test data:** none needed beyond the repos; the fresh clone uses
`--filter=blob:none` to stay light.

## Migration Strategy

**Rollback plan:**
- Phase 1: revert the squash-merge commit on fork main (`git revert -m` not
  needed — squash produces a single commit; `gh pr create` a revert PR).
- Phase 2: `git push origin :refs/heads/pin/faber2026` removes the branch
  (pin lineage returns to prior dangling state — non-destructive to history).
- Phase 3: revert the squash commit on Faber2026 main (gitlink returns to
  `79eaf7e`; docs revert with it).
- Local: `git -C pipeline reset --hard 17ad490` restores the pre-amend SHA if
  needed before any push (after push, no reset — additive reverts only).

**Backward compatibility:** old pin SHAs (`6c87890`, `334cc74`, `79eaf7e`)
remain resolvable exactly as before; `pin/faber2026` additionally makes
`79eaf7e` (ancestor of `$PIN2`) reachable by ref.

## Risk Assessment

1. **Risk:** FLITS CI (`uvx nox -s tests`) fails on the guard tests in the uv
   env (deps differ from conda py312; `uv.lock` is known to lack `healpy`).
   - **Likelihood:** Low-Medium | **Impact:** Medium
   - **Mitigation:** fix inside the Phase 1 PR (mark tests needing missing
     deps with the repo's existing skip conventions, or add the dep to the
     lock in the same PR). Merge only on green. Nothing downstream starts
     until this lands.
2. **Risk:** another writer moves the pipeline checkout or gitlink mid-plan
   (repo lane-liveness is `live`).
   - **Likelihood:** Medium | **Impact:** High (amend on wrong HEAD)
   - **Mitigation:** Phase 0 and Phase 2 HEAD gates re-verify immediately
     before mutation; any mismatch aborts with no partial state (amend is the
     first local mutation and is itself gated).
3. **Risk:** cherry-pick conflicts despite byte-identity checks (e.g. context
   drift in an untouched hunk).
   - **Likelihood:** Low | **Impact:** Low
   - **Mitigation:** abort-on-conflict policy (no hand-resolution inside the
     plan); re-diff and re-plan.
4. **Risk:** Faber2026 `parity` check red for reasons unrelated to this bump
   (strict up-to-date protection + concurrent merges).
   - **Likelihood:** Low | **Impact:** Medium
   - **Mitigation:** branch from fresh `origin/main` (Phase 3 step 1);
     `--admin` merge only after `parity` is green on the current head.
5. **Risk:** sweep-in of the live manuscript lane.
   - **Likelihood:** Low | **Impact:** High (another session's work)
   - **Mitigation:** pathspec-only `git add`/`git commit --` throughout;
     `git status --short` gate before commit enumerates the expected file set.

## Edge Cases and Error Handling

1. **Case:** `$FLITS_PR` CI is green but merge rejected (protection change).
   - **Expected:** halt; surface the protection diff; do not bypass beyond
     `--admin` (which precedent establishes).
2. **Case:** fresh-clone test fails to fetch `$PIN2` (Phase 4).
   - **Expected:** halt before telling the user to pull Overleaf; check
     `pin/faber2026` exists on the fork and that GitHub replicated it; re-run.
3. **Case:** journal hook auto-appends during the plan (protocol's staleness
   hook).
   - **Expected:** benign — journal is append-only; `git add docs/rse/journal.jsonl`
     picks up whatever is there at commit time.

## Documentation Updates

- [ ] `REPRODUCE.md` — stale divergent-branch paragraph corrected; pin history
      extended; `pin/faber2026` convention documented (Phase 3).
- [ ] `repro_manifest.csv` — 4 pin-referencing rows get UPDATE notes (Phase 3).
- [ ] `docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md` — committed
      as-is (Phase 3).
- [ ] `docs/rse/journal.jsonl` — working + done entries (Phases 3–4).
- [ ] This plan file — committed in the Phase 3 PR.

## Timeline Estimate

- Phase 0: minutes. Phase 1: ~15–30 min (CI-bound). Phase 2: minutes.
- Phase 3: ~20–30 min (doc edits + parity CI). Phase 4: ~10 min + user's
  Overleaf pull.

## Open Questions

*(none — scope and pin-branch decisions resolved with the user 2026-07-09)*

---

## References

**Research/context documents:**
- [assessment-chatgpt-scint-decombing-review.md](../assessment/assessment-chatgpt-scint-decombing-review.md)
- [experiment-freya-chime-instrumental-origin.md](../experiment/experiment-freya-chime-instrumental-origin.md)
- `../journal-protocol.md` (commit policy)
- `../../../REPRODUCE.md` (pin hazards; lines 25–36, 145–158)

**Files analyzed:** `pipeline` @ `17ad490` (diffstat, ancestry, remote refs),
`.gitmodules`, `REPRODUCE.md`, `repro_manifest.csv`,
`.github/workflows/table-parity.yml` (required check `parity`),
`pipeline/.github/workflows/tests.yml`, Faber2026 PR #71 / FLITS PR #149
(precedent), FLITS PR list #144–155, branch protection API for
`jakobtfaber/Faber2026@main`.

**Precedent commits:** `fd7a1ee` (repro-doc sync), `12df554`/PR #71 (pin bump
evidence pattern).

---

## Review History

### Version 1.0 — 2026-07-09
- Initial plan. Scope (guards-only; twoscreen lane excluded) and pin-branch
  decision (`pin/faber2026`) confirmed with the user.- [x]plementation Plan: Sync CHIME artifact-control guards to origin/main (Faber2026 + dsa110-FLITS)

---
**Date:** 2026-07-09
**Author:** AI Assistant (Claude, session 54fbfb21)
**Status:** Complete (manual verification pending: Overleaf pull)
**Related Documents:**
- [Assessment: ChatGPT scint de-combing review](../assessment/assessment-chatgpt-scint-decombing-review.md) *(untracked; committed by this plan)*
- [Experiment: freya CHIME instrumental origin](../experiment/experiment-freya-chime-instrumental-origin.md)

---

## Overview

The 2026-07-09 Claude Science session (a1d05406) implemented CHIME
artifact-control guards for the scintillation Lorentzian driver and committed
them **only locally**, as pipeline commit `17ad490` on top of the current pin
`79eaf7e`. Nothing has reached GitHub: the commit is in no remote ref, there is
no PR, the Faber2026 `pipeline` gitlink is dirty (uncommitted bump
`79eaf7e 17ad490`), and the session's assessment doc is untracked. The work
itself is verified (21/21 new tests pass locally; auditor findings confined to
chat prose).

This plan lands that work on `origin/main` of **both** repos — the guards on
`jakobtfaber/dsa110-FLITS` `main` via cherry-pick PR (mirroring the zach
FLITS #149 → pin-replay 79eaf7e → Faber2026 #71 precedent), and the pin bump +
assessment doc + repro-doc sync on `jakobtfaber/Faber2026` `main` via a
`#71`-style evidence PR — then verifies a fresh clone resolves the new pin, so
the user can pull `main` into Overleaf and recompile.

It also fixes the documented pin-reachability fragility: pin commits currently
exist on GitHub only as dangling fork-network objects (verified:
`git ls-remote origin` lists 143 refs; none contain `334cc74`/`79eaf7e`). Per
user decision (2026-07-09), the pin lineage gets a **persistent branch**
`pin/faber2026` on the `jakobtfaber/dsa110-FLITS` fork.

**Goal:** `origin/main` of both repos carries the guard work; the Faber2026
pin points at a reachable, correctly-messaged pin commit; a fresh
`git clone && git submodule update --init` succeeds; Overleaf pulls `main`
cleanly.

**Motivation:** Un-strand a $25/2.2 h verified work product; close the
reproducibility hazard before it bites a fresh clone; give Overleaf a clean
`main` to sync from.

## Current State Analysis

**Pipeline submodule (`pipeline/`, fork `jakobtfaber/dsa110-FLITS`):**
- HEAD detached at `17ad490` ("feat(scint): add CHIME artifact-control guards
  to Lorentzian driver (#149)"), parent `79eaf7e`, working tree clean.
- The `(#149)` subject reference is **wrong** — FLITS #149 is the zach C2D4
  beta promotion (merged 12:08Z), not the guards. The guards have no PR.
- `17ad490` diffstat (8 files, +1151/−4): new
  `scintillation/scint_analysis/chime_artifact_guards.py` (417 lines), new
  `scintillation/scint_analysis/tests/test_chime_artifact_guards.py` (210),
  new `analysis/scintillation-dsa-lorentzian-2026-07-07/test_driver_guards.py`
  (129), new `analysis/scintillation-dsa-lorentzian-2026-07-07/CHANGES-artifact-controls.md`,
  edits to `analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py`
  (+258), `.../README.md` (+38), `scintillation/scint_analysis/analysis.py`
  (+6), `scintillation/scint_analysis/pipeline.py` (+8).
- `17ad490` is **not** on GitHub (API 422); `79eaf7e`/`334cc74` are dangling
  fork-network objects in no ref.
- `334cc74` **is** an ancestor of fork `origin/main` (verified
  `merge-base --is-ancestor`); `79eaf7e...origin/main` is ahead 1 / behind 29.
  Every guard-touched pre-existing file is **byte-identical** between
  `79eaf7e` and `origin/main` (verified per-file `git diff --stat` empty), so
  the cherry-pick onto main is expected clean.
- FLITS CI: `.github/workflows/tests.yml` runs `uvx nox -s tests` (py3.12) on
  PRs and main pushes.

**Faber2026 super-repo:**
- `pipeline` gitlink dirty: `79eaf7e → 17ad490` (uncommitted).
- `docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md` untracked
  (content verified accurate against the session).
- `docs/rse/journal.jsonl` +5 uncommitted append-only lines (4 from the
  completed `repro-spine` lane, 1 from this session's review). Journal
  protocol (`docs/rse/journal-protocol.md`, "Commit policy") says the journal
  rides along with any doc/code commit.
- `REPRODUCE.md:27-34` is **stale** (confirmed): claims the pin sits "310
  commits along a divergent line, on the branch
  `fix/budget-table-data-post-igm-lognormal`" and that fixes are PR'd against
  that branch. That branch was merged into fork main (FLITS #151) and deleted;
  the pin base `334cc74` is now an ancestor of fork main, and no such branch
  exists on the remote.
- `REPRODUCE.md:150-158` documents the pin history ending at `79eaf7e`
  (Faber2026 #68, #71); `repro_manifest.csv` rows 5, 8, 9, 13 carry
  "pin now 79eaf7e" UPDATE notes (grep `79eaf7e` → 4 rows). Precedent
  `fd7a1ee` ("docs(repro): sync REPRODUCE.md + repro_manifest.csv to the
  current pin") requires the same sync for this bump.
- Branch protection on `main`: required check `parity`
  (`.github/workflows/table-parity.yml`), strict (branch must be up to date),
  1 review required — precedent PRs #71/#149 were owner-merged
  (`mergedBy: jakobtfaber`) without an approving review, i.e. admin merge.
- **Separate live lane (out of scope):** manuscript edits
  `sections/{results,discussion,appendix}.tex`, `bib/refs.bib` (+46), and
  untracked `sections/twoscreen_formalism.tex` (`\input` at
  `sections/appendix.tex:198`). `lane-liveness` verdict: **live**. Preserved
  untouched per user decision.

**Standing authorization:** repo `CLAUDE.md` grants cross-session push/PR/merge
without per-action approval; the `oneway-guard` hook may still surface one
Allow dialog (sticky window).

## Desired End State

**New behavior / state:**
- `jakobtfaber/dsa110-FLITS` `main` contains the guard commit (via merged PR).
- Fork branch `pin/faber2026` exists, pointing at the reworded pin commit
  `<PIN2>` (history: fork-main ancestry → `334cc74` → `79eaf7e` → `<PIN2>`).
- `jakobtfaber/Faber2026` `main` contains: gitlink → `<PIN2>`, the assessment
  doc, the journal lines, and REPRODUCE.md/repro_manifest.csv synced to
  `<PIN2>` (including the corrected stale paragraph).
- Local working tree: super-repo clean on `main` (except the preserved
  manuscript lane), submodule checked out at `<PIN2>`.

**Success looks like:**
- Fresh clone + `git submodule update --init pipeline` checks out `<PIN2>`
  without fetch errors.
- Overleaf pulls Faber2026 `main` and recompiles; PDF is **unchanged** (this
  sync touches no compiled `.tex` — the twoscreen lane, which does change the
  PDF, lands separately).
- `git status` in the super-repo no longer shows `pipeline` modified or the
  assessment doc untracked.

## What We're NOT Doing

- [ ] **Not** touching the live twoscreen manuscript lane
  (`sections/*.tex`, `bib/refs.bib`, `sections/twoscreen_formalism.tex`) —
  another session's in-flight work; it lands separately when its owner
  finishes.
- [ ] **Not** switching the pin to FLITS `main` (would drag 29 unrelated
  commits — V1 keystone, DM provenance, scattering manifest — into the pin;
  #71 precedent explicitly stays on-lineage).
- [ ] **Not** changing `.gitmodules` (URL stays `https://github.com/dsa110/dsa110-FLITS.git`;
  fork-network object sharing plus the new branch make the pin resolvable).
- [ ] **Not** fixing the casey CHIME configs' missing
  `grid_regularization`/`bandpass_normalization` blocks (13/14 configs demote
  to `diagnostic_only` by design; separate science decision).
- [ ] **Not** deleting or force-updating any existing remote branch; all
  steps are additive (new branches, new commits, revert-able merges).

**Rationale:** the user asked for a sync of the guard work; everything else is
either another lane's property or a separately-reviewed science decision.

## Implementation Approach

**Technical strategy:** mirror the zach precedent exactly — (1) guards land on
fork `main` via their own PR; (2) the pin lineage gets the same content as a
replay commit (already exists as `17ad490`; only the message is wrong, so
amend the subject → `<PIN2>`); (3) publish the pin lineage on a persistent
branch; (4) bump the Faber2026 gitlink via an evidence PR that replicates
#71's checks (ancestry, diff scope, parity byte-identity) and syncs the repro
docs, per `fd7a1ee` precedent.

**Key architectural decisions:**
1. **Decision:** cherry-pick `17ad490` onto fork `main` rather than merge the
   pin lineage into main.
   - **Rationale:** guard-touched files are byte-identical between `79eaf7e`
     and `origin/main`, so the pick is clean; merging the lineage would drag
     the replayed zach commit into main's history a second time.
   - **Trade-offs:** guards exist as two SHAs (main + pin), same as zach.
   - **Alternatives considered:** pin→main merge (history noise); rebasing the
     pin onto main (rewrites the pin lineage — forbidden).
2. **Decision:** amend `17ad490`'s subject (content unchanged) before
   publishing, producing `<PIN2>`.
   - **Rationale:** the `(#149)` reference is verifiably wrong and would be
     permanent in the pin lineage; nothing remote references `17ad490`, and
     the only local reference is the *uncommitted* gitlink, which this plan
     re-points.
   - **Trade-offs:** SHA churn; mitigated by a liveness/HEAD gate immediately
     before the amend.
   - **Alternatives considered:** keep the SHA (permanent wrong provenance);
     recreate the commit from scratch (identical outcome, more steps).
3. **Decision:** persistent fork branch `pin/faber2026` (user-approved).
   - **Rationale:** closes the dangling-object fragility REPRODUCE.md warns
     about; additive and non-destructive.
   - **Trade-offs:** the branch must be advanced on every future pin bump —
     REPRODUCE.md edit documents this as part of the bump procedure.
   - **Alternatives considered:** status quo dangling SHAs (fragile); tags
     (equally durable but pin bumps are a moving line, a branch matches).

**Patterns to follow:**
- Evidence-PR structure: Faber2026 PR #71 body (ancestry proof, scoped
  diffstat, parity byte-identity) — `gh pr view 71 --repo jakobtfaber/Faber2026`.
- Repro-doc sync: commit `fd7a1ee` (REPRODUCE.md + repro_manifest.csv to pin).
- Journal ride-along: `docs/rse/journal-protocol.md` "Commit policy".

## Implementation Phases

This is a git-orchestration plan: the "failing test → pass" loop maps to
**gate command → mutate → verify command**, with every gate shown. Steps
marked **[ONE-WAY]** are outward-facing (push/PR/merge) — covered by the
standing authorization, mechanically gated by `oneway-guard`.

Shell variables carried across steps (captured, never guessed):
`$FLITS_PR` (Phase 1 PR number), `$PIN2` (Phase 2 amended SHA).

### Phase 0: Freshness and liveness gates (read-only)

**Objective:** prove the ground hasn't moved since research; abort if it has.

**Tasks:**
- [x] **Gate: pipeline HEAD and cleanliness**

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline
  test "$(git rev-parse HEAD)" = "17ad490bd41d6d44fec8577b229448b98fe3d548" || { echo ABORT: HEAD moved; exit 1; }
  git status --porcelain | grep -q . && { echo ABORT: pipeline dirty; exit 1; } || echo clean
  ```

- [x] **Gate: guards still absent from fork main; lineage facts hold**

  ```bash
  git fetch origin main --quiet
  git cat-file -e origin/main:scintillation/scint_analysis/chime_artifact_guards.py 2>/dev/null \
    && { echo ABORT: guards already on main; exit 1; } || echo absent-as-expected
  git merge-base --is-ancestor 334cc74 origin/main && echo ancestry-ok
  git ls-remote origin | grep -E '79eaf7e|334cc74|17ad490' && { echo ABORT: pin SHAs now in a ref — replan; exit 1; } || echo dangling-as-expected
  ```

- [x] **Gate: no competing FLITS PR**

  ```bash
  gh pr list --repo jakobtfaber/dsa110-FLITS --state open --json number,title \
    --jq 'map(select(.title|test("guard|scint";"i")))' | grep -q '\[\]' || echo "REVIEW open PRs before continuing"
  ```

- [x] **Gate: super-repo separate lane inventory unchanged**

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
  git status --short --branch   # expect: gitlink pipeline modified, assessment doc + twoscreen untracked, sections/bib/journal modified — nothing new
  git worktree list --porcelain
  ```

**Verification:**
- [x] All four gates print their expected line; any ABORT halts the plan
      (mid-run failure policy: halt, report, re-plan — no partial mutation has
      happened yet in this phase).

### Phase 1: Land the guards on `jakobtfaber/dsa110-FLITS` `main`

**Objective:** guards merged to fork `main` via PR with CI green.

**Tasks:**
- [x] **Create an isolated worktree at fork main** (never disturb the pinned
      checkout the super-repo references)

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline
  git worktree add /private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/54fbfb21-8517-4f85-bf13-b0cf07a5bc6a/scratchpad/flits-guards-main \
    -b feat/chime-artifact-guards origin/main
  cd /private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/54fbfb21-8517-4f85-bf13-b0cf07a5bc6a/scratchpad/flits-guards-main
  ```

- [x] **Cherry-pick, watch it apply cleanly** (pre-verified: all touched
      pre-existing files byte-identical between `79eaf7e` and `origin/main`)

  ```bash
  git cherry-pick 17ad490bd41d6d44fec8577b229448b98fe3d548
  # expect: clean apply. On ANY conflict: git cherry-pick --abort && halt — the
  # byte-identity premise failed; re-diff and re-plan. Do not hand-resolve.
  ```

- [x] **Reword the picked commit's wrong PR reference** (subject only; body kept)

  ```bash
  git log -1 --format=%B | sed '1s/ (#149)$//' | git commit --amend -F -
  git log -1 --format=%s   # expect: "feat(scint): add CHIME artifact-control guards to Lorentzian driver"
  ```

- [x] **Run the new tests at main's tree, watch them pass** (the "failing
      test" already exists — 21 tests that cannot run on main today because
      the files are absent; this run proves they pass post-pick)

  ```bash
  env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
    /opt/anaconda3/bin/conda run -n py312 python -m pytest \
    scintillation/scint_analysis/tests/test_chime_artifact_guards.py \
    "analysis/scintillation-dsa-lorentzian-2026-07-07/test_driver_guards.py" -q
  # expect: 21 passed
  ```

- [x] **[ONE-WAY] Push the branch and open the PR**

  ```bash
  git push origin feat/chime-artifact-guards
  gh pr create --repo jakobtfaber/dsa110-FLITS --base main \
    --title "feat(scint): CHIME artifact-control guards for the Lorentzian driver" \
    --body "Cherry-pick of the 2026-07-09 guard work (local pin-lineage commit 17ad490) onto main. New module scintillation/scint_analysis/chime_artifact_guards.py + driver wiring: first-class harmonic mask, fail-closed CHIME provenance gate (diagnostic_only demotion), off-pulse ACF null, low-lag excision stability, harmonic-mask systematic. 16 unit + 5 driver integration tests. DSA path proven numerically unchanged. Companion pin bump lands in Faber2026 (mirrors the zach #149 -> pin flow)."
  FLITS_PR=$(gh pr list --repo jakobtfaber/dsa110-FLITS --head feat/chime-artifact-guards --json number --jq '.[0].number')
  echo "FLITS_PR=$FLITS_PR"
  ```

- [x] **Wait for CI (`Tests` workflow, `uvx nox -s tests`), then [ONE-WAY] merge**

  ```bash
  gh pr checks "$FLITS_PR" --repo jakobtfaber/dsa110-FLITS --watch
  # expect: all green. If tests fail in the uv env (e.g. a dep missing from
  # uv.lock that conda py312 has): halt and fix within this PR before merging.
  gh pr merge "$FLITS_PR" --repo jakobtfaber/dsa110-FLITS --squash --admin --delete-branch
  ```

**Dependencies:** Phase 0 gates passed.

**Verification:**
- [x] `git fetch origin main --quiet && git cat-file -e origin/main:scintillation/scint_analysis/chime_artifact_guards.py && echo on-main` → `on-main`
- [x] `git worktree remove /private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/54fbfb21-8517-4f85-bf13-b0cf07a5bc6a/scratchpad/flits-guards-main` succeeds (worktree clean).

### Phase 2: Reword the pin commit and publish `pin/faber2026`

**Objective:** pin lineage carries a correctly-attributed guard commit
`<PIN2>` and is reachable via a persistent fork branch.

**Tasks:**
- [x] **Gate: re-verify HEAD immediately before amending** (shared-tree
      protocol — another writer may have moved it during Phase 1)

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline
  test "$(git rev-parse HEAD)" = "17ad490bd41d6d44fec8577b229448b98fe3d548" || { echo ABORT: HEAD moved; exit 1; }
  git status --porcelain | grep -q . && { echo ABORT: dirty; exit 1; } || echo clean
  ```

- [x] **Amend the subject to reference the real PR** (content unchanged)

  ```bash
  git log -1 --format=%B \
    | sed "1s/.*/Promote CHIME artifact-control guards onto pin 79eaf7e (FLITS #$FLITS_PR)/" \
    | git commit --amend -F -
  PIN2=$(git rev-parse HEAD)
  echo "PIN2=$PIN2"
  ```

- [x] **Prove the amend changed nothing but the message**

  ```bash
  git diff --stat 17ad490bd41d6d44fec8577b229448b98fe3d548 "$PIN2" | grep -q . \
    && { echo ABORT: tree changed; exit 1; } || echo tree-identical
  git merge-base --is-ancestor 79eaf7eecfedcecae2c5bb46d2bf664a109d3ca4 "$PIN2" && echo ancestry-ok
  ```

- [x] **[ONE-WAY] Publish the pin lineage on the persistent branch**

  ```bash
  git push origin "$PIN2:refs/heads/pin/faber2026"
  git ls-remote origin pin/faber2026   # expect: $PIN2
  ```

**Dependencies:** Phase 1 (needs `$FLITS_PR`).

**Verification:**
- [x] `git ls-remote origin pin/faber2026 | grep -c "$PIN2"` → `1`
- [x] `gh api repos/jakobtfaber/dsa110-FLITS/commits/$PIN2 --jq .sha` succeeds (no 422).

### Phase 3: Faber2026 sync PR (gitlink bump + assessment doc + repro-doc sync)

**Objective:** Faber2026 `main` gets the pin bump with #71-grade evidence,
the assessment doc, the journal lines, and REPRODUCE.md/repro_manifest.csv
synced to `<PIN2>` (including the stale-paragraph fix).

**Tasks:**
- [x] **Branch off up-to-date main; carry ONLY this lane's paths**

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
  git fetch origin main --quiet
  git switch -c agent/bump-pipeline-chime-guards origin/main
  # gitlink: the submodule checkout already sits at $PIN2 after Phase 2's amend
  git -C pipeline rev-parse HEAD   # expect $PIN2
  git add pipeline docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md docs/rse/specs/plan/plan-sync-chime-guards-to-origin-main.md docs/rse/journal.jsonl
  # NEVER: git add -A / git add . — the manuscript lane must not be swept in.
  git status --short   # expect exactly: M pipeline, A assessment doc, A this plan, M journal — plus the UNSTAGED manuscript lane
  ```

- [x] **Edit `REPRODUCE.md:27-34`** — replace the stale paragraph

  Old text (verbatim, starts "One wrinkle worth knowing"):
  > The `.gitmodules` URL above is what a fresh `git submodule update --init` clones, and it does resolve the pinned SHA. But **pipeline development happens on the `jakobtfaber/dsa110-FLITS` fork**, and the pinned commit is *not* an ancestor of either repo's `main` — it sits 310 commits along a divergent line, on the branch `fix/budget-table-data-post-igm-lognormal`. A pipeline fix is therefore PR'd against that branch, not against `main` (see FLITS #146, #147, #148). Check `git merge-base --is-ancestor` before ever bumping the pin.

  New text:
  > The `.gitmodules` URL above is what a fresh `git submodule update --init` clones, and it resolves the pinned SHA. **Pipeline development happens on the `jakobtfaber/dsa110-FLITS` fork.** Since FLITS #151 merged the old divergent line into the fork's `main`, the pin base is an ancestor of fork `main`; the pin itself sits 1–2 replayed commits off it. The full pin lineage is published on the fork branch **`pin/faber2026`** (since 2026-07-09), so pinned SHAs are reachable by ref, not just as fork-network dangling objects. A pipeline fix is PR'd against fork `main`, then replayed onto the pin (see FLITS #149 → Faber2026 #71 for the pattern); advance `pin/faber2026` on every bump, and check `git merge-base --is-ancestor` before ever bumping the pin.

- [x] **Edit `REPRODUCE.md:150-158`** — extend the pin history sentence.
  After "…`334cc74 → 79eaf7e` as Faber2026 #71, a single commit promoting the
  `zach` C2D4 beta fit." insert:
  > Then `79eaf7e → <PIN2-short>` as Faber2026 #<this-PR>, a single commit promoting the CHIME artifact-control guards (FLITS #$FLITS_PR; scintillation lane only).
  and update both "currently pinned submodule (`79eaf7e`)" mentions
  (lines 150, 152–155) to `<PIN2-short>`, keeping the "no `*_table_data.json`
  and neither table emitter is touched" claim — re-proven by the parity gate
  below. (`<PIN2-short>` = `git rev-parse --short=7 $PIN2`; the PR number is
  known after `gh pr create`, so this edit is finalized in the same commit
  via `--amend` right after the PR number is assigned, or the PR number is
  referenced as "this PR" — match `fd7a1ee`'s wording.)

- [x] **Edit `repro_manifest.csv`** — append to the `notes` field of each of
  the 4 rows matching `79eaf7e` (rows 5, 8, 9, 13):

  ```
   UPDATE 2026-07-09 (pin now <PIN2-short>, Faber2026 #<this-PR>): one-commit descendant of 79eaf7e promoting the CHIME scintillation artifact-control guards (FLITS #$FLITS_PR); touches only scintillation/ and analysis/scintillation-dsa-lorentzian-2026-07-07/ — no galaxies/, no emitters, no *_table_data.json — so every claim verified at 79eaf7e carries unchanged.
  ```

  Apply with a small python snippet (CSV-safe; do not sed a quoted CSV):

  ```bash
  python3 - "$PIN2" <<'EOF'
  import csv, sys
  short = sys.argv[1][:7]
  upd = (" UPDATE 2026-07-09 (pin now %s): one-commit descendant of 79eaf7e "
         "promoting the CHIME scintillation artifact-control guards; touches only "
         "scintillation/ and analysis/scintillation-dsa-lorentzian-2026-07-07/ -- "
         "no galaxies/, no emitters, no *_table_data.json -- so every claim "
         "verified at 79eaf7e carries unchanged." % short)
  rows = list(csv.reader(open("repro_manifest.csv")))
  n = 0
  for r in rows[1:]:
      if any("79eaf7e" in c for c in r):
          r[-1] += upd; n += 1
  assert n == 4, f"expected 4 rows, hit {n}"
  csv.writer(open("repro_manifest.csv", "w", newline="")).writerows(rows)
  print("updated", n, "rows")
  EOF
  ```

- [x] **Gate: parity byte-identity across the bump** (the #71 evidence check;
  the `parity` CI check re-proves it on the PR)

  ```bash
  git -C pipeline diff --stat 79eaf7eecfedcecae2c5bb46d2bf664a109d3ca4 "$PIN2" -- galaxies/ exports/ | grep -q . \
    && { echo ABORT: parity-read files changed; exit 1; } || echo parity-clean
  git -C pipeline rev-list --left-right --count "79eaf7eecfedcecae2c5bb46d2bf664a109d3ca4...$PIN2"   # expect: 0 1
  ```

- [x] **Append a journal entry, commit, [ONE-WAY] push + PR**

  ```bash
  bash scripts/journal-append.sh claude-main scint-guards working \
    "Landing guard sync: FLITS #$FLITS_PR merged to fork main; pin/faber2026 published at ${PIN2:0:7}; opening Faber2026 pin-bump PR (gitlink 79eaf7e -> ${PIN2:0:7} + assessment doc + repro-doc sync)."
  git add REPRODUCE.md repro_manifest.csv docs/rse/journal.jsonl
  git commit -m "Bump pipeline pin 79eaf7e -> ${PIN2:0:7} (CHIME artifact-control guards)" \
    -m "Promotes the 2026-07-09 guard work (FLITS #$FLITS_PR) onto the pin without switching lineage. Adds the session assessment doc, this plan, journal entries, and syncs REPRODUCE.md + repro_manifest.csv to the new pin (incl. correcting the stale divergent-branch paragraph; pin lineage now published on fork branch pin/faber2026)." \
    -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    -- pipeline docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md docs/rse/specs/plan/plan-sync-chime-guards-to-origin-main.md docs/rse/journal.jsonl REPRODUCE.md repro_manifest.csv
  git push origin agent/bump-pipeline-chime-guards
  gh pr create --repo jakobtfaber/Faber2026 --base main \
    --title "Bump pipeline pin 79eaf7e -> ${PIN2:0:7} (CHIME artifact-control guards)" \
    --body "$(printf '## Bump pipeline pin `79eaf7e` -> `%s` — CHIME artifact-control guards\n\nMakes the 2026-07-09 guard work (FLITS #%s) available to Faber2026 **without switching lineage**; pin lineage now published on fork branch `pin/faber2026`.\n\n### Evidence\n1. **Ancestry (fast-forward):** `git merge-base --is-ancestor 79eaf7e %s` passes — compare is ahead 1, behind 0.\n2. **Submodule diff is guards-only:** 8 files under `scintillation/` + `analysis/scintillation-dsa-lorentzian-2026-07-07/`. No `galaxies/`, no `exports/`, no `*_table_data.json`.\n3. **Parity invariant:** every file the `table-parity` check reads is byte-identical between `79eaf7e` and `%s` (diff --stat empty).\n4. **Tests:** 21 new guard tests pass at the pin (16 unit + 5 driver integration); full scint suite 149 passed / 2 skipped in-session.\n5. **Reachability:** `%s` is fetchable via `pin/faber2026` (ls-remote verified), closing the dangling-SHA hazard REPRODUCE.md documented.\n6. Assessment doc + repro-doc sync included (precedent: fd7a1ee).\n' "${PIN2:0:7}" "$FLITS_PR" "${PIN2:0:7}" "${PIN2:0:7}" "${PIN2:0:7}")"
  ```

- [x] **Wait for the required `parity` check, then [ONE-WAY] merge**

  ```bash
  gh pr checks --repo jakobtfaber/Faber2026 --watch   # expect: parity green
  gh pr merge --repo jakobtfaber/Faber2026 --squash --admin --delete-branch
  ```

**Dependencies:** Phase 2 (`$PIN2` published; submodule HEAD at `$PIN2`).

**Verification:**
- [x] `git fetch origin main --quiet && git ls-tree origin/main pipeline` shows `$PIN2`.
- [x] `git show origin/main:docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md | head -1` → `# Assessment: ChatGPT review of the scintillation "de-combing" code`.

### Phase 4: Post-merge verification, local reconciliation, Overleaf pull

**Objective:** prove a fresh consumer resolves the new pin; leave the local
tree clean; hand Overleaf a pullable `main`.

**Tasks:**
- [x] **Reconcile local main** (manuscript lane rides untouched)

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
  git switch main && git pull --ff-only origin main
  git status --short   # expect ONLY the manuscript lane (sections/, bib/, twoscreen) — pipeline gitlink clean, docs clean
  ```

- [x] **Fresh-clone reproducibility test (the real gate the old convention
  failed silently)**

  ```bash
  cd /private/tmp/claude-501/-Users-jakobfaber-Developer-repos-github-com-jakobtfaber-Faber2026/54fbfb21-8517-4f85-bf13-b0cf07a5bc6a/scratchpad
  git clone --filter=blob:none https://github.com/jakobtfaber/Faber2026.git fresh-clone-verify
  cd fresh-clone-verify && git submodule update --init pipeline
  git -C pipeline rev-parse HEAD   # expect $PIN2
  ```

- [x] **Journal the closeout**

  ```bash
  cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
  bash scripts/journal-append.sh claude-main scint-guards done \
    "Guard sync landed: FLITS #$FLITS_PR on fork main; pin/faber2026 at ${PIN2:0:7}; Faber2026 pin-bump PR merged; fresh-clone submodule update resolves ${PIN2:0:7}. Manuscript twoscreen lane untouched (live, separate owner)."
  ```

  (This re-dirties `journal.jsonl` by one line — expected; it rides with the
  next doc commit per protocol.)

- [ ] **Overleaf pull (manual, user)** — in the Overleaf project for
  Faber2026: Menu → GitHub → *Pull GitHub changes into Overleaf*, then
  recompile. Expected: pull succeeds, **PDF unchanged** (no compiled `.tex`
  changed in this sync). The `overleaf` skill / `olcli` can drive this if the
  user prefers agent-side execution.

**Dependencies:** Phase 3 merged.

**Verification:** listed inline (fresh-clone SHA check is the phase's own
gate).

## Success Criteria

### Automated Verification

- [x] `gh pr view $FLITS_PR --repo jakobtfaber/dsa110-FLITS --json state --jq .state` → `MERGED`
- [x] `git -C pipeline ls-remote origin pin/faber2026` → `$PIN2`
- [x] `git -C pipeline cat-file -e origin/main:scintillation/scint_analysis/chime_artifact_guards.py` → exit 0
- [x] `git ls-tree origin/main pipeline` (Faber2026) → `$PIN2`
- [ ] Fresh clone + `git submodule update --init pipeline` → HEAD `$PIN2`, no fetch error
- [ ] Faber2026 required `parity` check green on the merged PR
- [ ] 21 guard tests pass at `$PIN2`:
      `conda run -n py312 python -m pytest scintillation/scint_analysis/tests/test_chime_artifact_guards.py "analysis/scintillation-dsa-lorentzian-2026-07-07/test_driver_guards.py" -q`
- [ ] `git -C pipeline diff --stat 17ad490 $PIN2` → empty (amend was message-only)
- [ ] Super-repo `git status --short` shows no `pipeline` modification and no
      untracked assessment doc after Phase 4 pull

### Manual Verification

- [ ] Overleaf pull of Faber2026 `main` succeeds; recompile completes; PDF
      diff is empty (expected — no compiled `.tex` in this sync)
- [ ] Spot-read the merged REPRODUCE.md paragraph: pin-lineage description
      matches live remote state (branch `pin/faber2026` visible on GitHub UI)
- [ ] The manuscript lane (sections/, bib/, twoscreen) is still intact and
      uncommitted after all phases (its owner decides its landing)

### Reproducibility & Correctness (research code)

- [ ] No numerical outputs change: `git -C pipeline diff 79eaf7e..$PIN2 -- '*.json' '*.tex'` touches only
      `freya_chime_guards_demo.json`-class analysis-dir artifacts, no
      manuscript-embedded tables/figures (parity gate proves the embedded set)
- [ ] The guard commit's in-session verification stands: DSA widths
      bit-identical pre/post guards; CHIME freya demotes to `diagnostic_only`
      (documented in `CHANGES-artifact-controls.md` at the pin)

## Testing Strategy

**Unit (in-phase):** the 21 existing guard tests run at three points — the
pin (already verified), the cherry-picked main tree (Phase 1), and FLITS CI
(`uvx nox -s tests`, Phase 1 merge gate).

**Integration:** Faber2026 `parity` required check on the PR (Phase 3);
fresh-clone submodule resolution (Phase 4) — this is the test the old
dangling-SHA convention had no coverage for.

**Manual:** Overleaf pull + recompile (Phase 4).

**Test data:** none needed beyond the repos; the fresh clone uses
`--filter=blob:none` to stay light.

## Migration Strategy

**Rollback plan:**
- Phase 1: revert the squash-merge commit on fork main (`git revert -m` not
  needed — squash produces a single commit; `gh pr create` a revert PR).
- Phase 2: `git push origin :refs/heads/pin/faber2026` removes the branch
  (pin lineage returns to prior dangling state — non-destructive to history).
- Phase 3: revert the squash commit on Faber2026 main (gitlink returns to
  `79eaf7e`; docs revert with it).
- Local: `git -C pipeline reset --hard 17ad490` restores the pre-amend SHA if
  needed before any push (after push, no reset — additive reverts only).

**Backward compatibility:** old pin SHAs (`6c87890`, `334cc74`, `79eaf7e`)
remain resolvable exactly as before; `pin/faber2026` additionally makes
`79eaf7e` (ancestor of `$PIN2`) reachable by ref.

## Risk Assessment

1. **Risk:** FLITS CI (`uvx nox -s tests`) fails on the guard tests in the uv
   env (deps differ from conda py312; `uv.lock` is known to lack `healpy`).
   - **Likelihood:** Low-Medium | **Impact:** Medium
   - **Mitigation:** fix inside the Phase 1 PR (mark tests needing missing
     deps with the repo's existing skip conventions, or add the dep to the
     lock in the same PR). Merge only on green. Nothing downstream starts
     until this lands.
2. **Risk:** another writer moves the pipeline checkout or gitlink mid-plan
   (repo lane-liveness is `live`).
   - **Likelihood:** Medium | **Impact:** High (amend on wrong HEAD)
   - **Mitigation:** Phase 0 and Phase 2 HEAD gates re-verify immediately
     before mutation; any mismatch aborts with no partial state (amend is the
     first local mutation and is itself gated).
3. **Risk:** cherry-pick conflicts despite byte-identity checks (e.g. context
   drift in an untouched hunk).
   - **Likelihood:** Low | **Impact:** Low
   - **Mitigation:** abort-on-conflict policy (no hand-resolution inside the
     plan); re-diff and re-plan.
4. **Risk:** Faber2026 `parity` check red for reasons unrelated to this bump
   (strict up-to-date protection + concurrent merges).
   - **Likelihood:** Low | **Impact:** Medium
   - **Mitigation:** branch from fresh `origin/main` (Phase 3 step 1);
     `--admin` merge only after `parity` is green on the current head.
5. **Risk:** sweep-in of the live manuscript lane.
   - **Likelihood:** Low | **Impact:** High (another session's work)
   - **Mitigation:** pathspec-only `git add`/`git commit --` throughout;
     `git status --short` gate before commit enumerates the expected file set.

## Edge Cases and Error Handling

1. **Case:** `$FLITS_PR` CI is green but merge rejected (protection change).
   - **Expected:** halt; surface the protection diff; do not bypass beyond
     `--admin` (which precedent establishes).
2. **Case:** fresh-clone test fails to fetch `$PIN2` (Phase 4).
   - **Expected:** halt before telling the user to pull Overleaf; check
     `pin/faber2026` exists on the fork and that GitHub replicated it; re-run.
3. **Case:** journal hook auto-appends during the plan (protocol's staleness
   hook).
   - **Expected:** benign — journal is append-only; `git add docs/rse/journal.jsonl`
     picks up whatever is there at commit time.

## Documentation Updates

- [ ] `REPRODUCE.md` — stale divergent-branch paragraph corrected; pin history
      extended; `pin/faber2026` convention documented (Phase 3).
- [ ] `repro_manifest.csv` — 4 pin-referencing rows get UPDATE notes (Phase 3).
- [ ] `docs/rse/specs/assessment/assessment-chatgpt-scint-decombing-review.md` — committed
      as-is (Phase 3).
- [ ] `docs/rse/journal.jsonl` — working + done entries (Phases 3–4).
- [ ] This plan file — committed in the Phase 3 PR.

## Timeline Estimate

- Phase 0: minutes. Phase 1: ~15–30 min (CI-bound). Phase 2: minutes.
- Phase 3: ~20–30 min (doc edits + parity CI). Phase 4: ~10 min + user's
  Overleaf pull.

## Open Questions

*(none — scope and pin-branch decisions resolved with the user 2026-07-09)*

---

## References

**Research/context documents:**
- [assessment-chatgpt-scint-decombing-review.md](../assessment/assessment-chatgpt-scint-decombing-review.md)
- [experiment-freya-chime-instrumental-origin.md](../experiment/experiment-freya-chime-instrumental-origin.md)
- `../journal-protocol.md` (commit policy)
- `../../../REPRODUCE.md` (pin hazards; lines 25–36, 145–158)

**Files analyzed:** `pipeline` @ `17ad490` (diffstat, ancestry, remote refs),
`.gitmodules`, `REPRODUCE.md`, `repro_manifest.csv`,
`.github/workflows/table-parity.yml` (required check `parity`),
`pipeline/.github/workflows/tests.yml`, Faber2026 PR #71 / FLITS PR #149
(precedent), FLITS PR list #144–155, branch protection API for
`jakobtfaber/Faber2026@main`.

**Precedent commits:** `fd7a1ee` (repro-doc sync), `12df554`/PR #71 (pin bump
evidence pattern).

---

## Review History

### Version 1.0 — 2026-07-09
- Initial plan. Scope (guards-only; twoscreen lane excluded) and pin-branch
  decision (`pin/faber2026`) confirmed with the user.
