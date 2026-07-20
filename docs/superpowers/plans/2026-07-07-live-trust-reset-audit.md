# Live Trust-Reset Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the live manuscript and pipeline provenance state back into alignment with the trust-reset rules verified on 2026-07-07.

**Architecture:** Treat manuscript text and pipeline provenance as separate lanes. First remove or withhold any still-active unvalidated manuscript claims in the compiled chain, then document the current submodule pin provenance without bumping the pin. Keep the existing dirty V6/spec artifacts out of this plan unless the owner explicitly assigns that lane.

**Tech Stack:** LaTeX manuscript rooted at `main.tex`, pinned Git submodule at `pipeline/`, RTK-wrapped shell commands, `latexmk` through `rtk make`, repo journal via `scripts/journal-append.sh`, closeout via `mskill tool agent-closeout-check`.

---

## File Structure

- Modify: `sections/observations.tex`
  - Responsibility: compiled Observations prose. This is the only currently verified active `\includegraphics` surface in the included manuscript chain.
- Create: `docs/rse/specs/pipeline-submodule-provenance-2026-07-07.md`
  - Responsibility: record the current submodule pin, fork/upstream reachability, and the decision not to bump the pin before C3.
- Modify: `docs/rse/journal.jsonl`
  - Responsibility: append-only work attribution through `scripts/journal-append.sh`; never edit by hand.
- No change: `pipeline/`
  - Responsibility: pinned submodule worktree. Inspect only in this plan; do not checkout branches or update the parent gitlink.
- No change: untracked `docs/rse/specs/dm/dm-power-*` and `docs/rse/specs/v6/v6-*` artifacts
  - Responsibility: pre-existing V6/spec lane artifacts. Leave untouched unless the owner assigns that lane.

### Task 1: Reconfirm Live Manuscript Surfaces

**Files:**
- Inspect: `main.tex`
- Inspect: `sections/observations.tex`
- Inspect: `sections/toa.tex`
- Inspect: `CONTEXT.md`
- Inspect: `docs/rse/specs/plan/plan-circulation-readiness.md`

- [ ] **Step 1: Journal the start**

Run:

```bash
bash scripts/journal-append.sh "codex-gpt-5.5/exec-2026-07-07" "ms" "working" "Starting live trust-reset manuscript surface audit."
```

Expected: prints `journaled:` and appends one JSONL record to `docs/rse/journal.jsonl`.

- [ ] **Step 2: Verify the included manuscript chain**

Run:

```bash
rtk rg -n '\\input\{|\\includegraphics|\\begin\{abstract\}|\\end\{abstract\}' main.tex sections
```

Expected: `main.tex` includes `sections/observations.tex`; `sections/observations.tex` contains the only active `\includegraphics` line in the included chain; the abstract in `main.tex` is already conservative.

- [ ] **Step 3: Verify trust-reset constraints before editing**

Run:

```bash
rtk rg -n "Avoid|withheld|re-validation|DM-derived|fit-|foreground|citable|trust" CONTEXT.md docs/rse/specs/plan/plan-circulation-readiness.md
```

Expected: the output identifies the current rules for withholding fit-derived, census-derived, budget-derived, association-derived, DM-derived, scintillation, and energy products until their validation gates pass.

- [ ] **Step 4: Confirm no TOA table remains active**

Run:

```bash
rtk rg -n "tab:toa|mean 2\\.42|r=0\\.14|p=0\\.67|P_\\{cc\\}|Residuals and systematics" sections/toa.tex
```

Expected: only the withholding language and method definitions remain; no active table or revoked statistics are present.

### Task 2: Withhold the Active NE2025 Figure and Numeric Claims

**Files:**
- Modify: `sections/observations.tex`

- [ ] **Step 1: Replace the active NE2025 result prose and figure block**

In `sections/observations.tex`, replace the current `\subsection{Milky Way foreground}` block with:

```tex
\subsection{Milky Way foreground}
\label{sec:obs-mw}

The Milky Way foreground characterization is withheld in this circulation
draft. Restoring this subsection requires the foreground and dispersion-budget
re-validation gates to document the NE2025 query inputs, sightline coordinates,
frequency scaling assumptions, cached grid products, and event-level values
used by the manuscript. Until that pass is complete, this section records the
analysis slot but quotes no Galactic dispersion, pulse-broadening, or
scintillation-bandwidth values as citable results.

% Removed figure candidate:
% - Artifact: figures/ne2025_mw_characterization.pdf
% - Generator: pipeline-side NE2025 characterization workflow; exact script and
%   pinned inputs must be recorded before re-addition.
% - Inputs: twelve co-detection sightlines, NE2025 Milky Way model query, and
%   frequency-scaling assumptions.
% - Reason withheld: Galactic foreground model products are not citable until
%   the foreground and dispersion-budget re-validation gates pass.
```

Expected: there is no active `figure*` environment and no active `\includegraphics` in this subsection.

- [ ] **Step 2: Verify no active figures remain in the included chain**

Run:

```bash
rtk rg -n '\\includegraphics|\\begin\{figure' main.tex sections
```

Expected: no active uncommented figure or includegraphics lines remain in the files included by `main.tex`.

- [ ] **Step 3: Compile the manuscript**

Run:

```bash
rtk make
```

Expected: `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` exits 0. If `rtk make` reports only that the PDF is current, run:

```bash
latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex
```

Expected: forced rebuild exits 0 with no new warnings introduced by this edit.

- [ ] **Step 4: Commit the manuscript-only change if cleanly scoped**

Run:

```bash
rtk git diff -- sections/observations.tex
rtk git add sections/observations.tex docs/rse/journal.jsonl
rtk git commit -m "ms: withhold unvalidated NE2025 foreground figure"
```

Expected: commit includes only `sections/observations.tex` and journal entries from this lane. Do not stage `pipeline` or pre-existing untracked V6/spec artifacts.

### Task 3: Document Current Pipeline Submodule Provenance

**Files:**
- Create: `docs/rse/specs/pipeline-submodule-provenance-2026-07-07.md`
- Modify: `docs/rse/journal.jsonl`
- Inspect only: `.gitmodules`
- Inspect only: `pipeline/`

- [ ] **Step 1: Journal the provenance lane**

Run:

```bash
bash scripts/journal-append.sh "codex-gpt-5.5/exec-2026-07-07" "C3" "working" "Documenting current pipeline submodule provenance without bumping the pin."
```

Expected: prints `journaled:`.

- [ ] **Step 2: Reconfirm parent gitlink and submodule remotes**

Run:

```bash
rtk git ls-tree HEAD pipeline
rtk git config -f .gitmodules --get-regexp '^submodule\\.pipeline\\.'
rtk git -C pipeline remote -v
rtk git -C pipeline branch -r --contains 2d62ac89811f0aa3f7da917e40788eadea5af697
```

Expected: parent gitlink is `2d62ac89811f0aa3f7da917e40788eadea5af697`; `.gitmodules` points at `https://github.com/dsa110/dsa110-FLITS.git`; the containing remote branch is fork-side or agent-side, not a validated upstream org release branch.

- [ ] **Step 3: Create the provenance note**

Create `docs/rse/specs/pipeline-submodule-provenance-2026-07-07.md` with:

```markdown
# Pipeline Submodule Provenance Note — 2026-07-07

The parent manuscript repo currently pins `pipeline/` at
`2d62ac89811f0aa3f7da917e40788eadea5af697`.

`.gitmodules` declares the canonical URL:

```text
https://github.com/dsa110/dsa110-FLITS.git
```

Local inspection found the checked-out commit reachable through the fork/agent
development branch used for V6/DM-power work, not through a validated upstream
org release branch. This means the manuscript can currently reproduce from the
local checkout and fork remotes, but the declared submodule URL and the actual
development provenance are not yet aligned.

Decision for this circulation draft: do not bump the submodule pin as part of
the manuscript trust-reset cleanup. C3 remains downstream of the V/A/B
re-validation gates. The next C3 action is to either land the relevant FLITS
work into `dsa110/dsa110-FLITS` through a reviewed PR, or explicitly document
and accept a fork-backed submodule provenance policy before changing the parent
gitlink.
```

Expected: the note names the live pin `2d62ac8`, not stale pin `7e77437`.

- [ ] **Step 4: Commit the provenance note separately**

Run:

```bash
rtk git diff -- docs/rse/specs/pipeline-submodule-provenance-2026-07-07.md docs/rse/journal.jsonl
rtk git add docs/rse/specs/pipeline-submodule-provenance-2026-07-07.md docs/rse/journal.jsonl
rtk git commit -m "docs: record pipeline submodule provenance gap"
```

Expected: commit includes only the provenance note and journal entries from this lane. Do not stage the `pipeline` gitlink unless C3 is explicitly unblocked.

### Task 4: Final Verification and Closeout

**Files:**
- Inspect: git status
- Inspect: build output
- Create outside repo if needed: `/tmp/faber2026-live-trust-reset-closeout-20260707.json`

- [ ] **Step 1: Run final status**

Run:

```bash
rtk git status --porcelain=v1
```

Expected: only known pre-existing dirty paths remain, or the task-scoped commits have removed all task-scoped dirt.

- [ ] **Step 2: Build once after all manuscript edits**

Run:

```bash
rtk make
```

Expected: exits 0. If the output says no work was needed and a forced proof is required, run:

```bash
latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex
```

Expected: exits 0.

- [ ] **Step 3: Run closeout gate**

Run:

```bash
mskill tool agent-closeout-check \
  --repo /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026 \
  --touched sections/observations.tex \
  --touched docs/rse/specs/pipeline-submodule-provenance-2026-07-07.md \
  --touched docs/rse/journal.jsonl
```

Expected: if the repo is still dirty from pre-existing artifacts, the checker asks for a dirty-state packet.

- [ ] **Step 4: Provide dirty-state packet if required**

Create `/tmp/faber2026-live-trust-reset-closeout-20260707.json` with all dirty paths classified under `dirtyState`. Use `taskScoped` only for paths edited and validated by this plan. Put the existing V6/spec artifacts and any unassigned submodule checkout state in `preExistingUnrelated` or `generatedOrCache` with `residualActions`.

Run:

```bash
mskill tool agent-closeout-check \
  --repo /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026 \
  --touched sections/observations.tex \
  --touched docs/rse/specs/pipeline-submodule-provenance-2026-07-07.md \
  --touched docs/rse/journal.jsonl \
  --packet /tmp/faber2026-live-trust-reset-closeout-20260707.json \
  --json
```

Expected: `"ok": true`.

## Self-Review

- Spec coverage: The plan covers the live manuscript contradiction found after the stale audit note, records the current pipeline provenance gap, avoids submodule pin changes before C3, and preserves dirty-state discipline.
- Placeholder scan: The plan uses exact paths, exact replacement text, and exact commands. No task depends on unstated future content.
- Type consistency: The closeout packet name and touched paths match the files changed by the tasks.
