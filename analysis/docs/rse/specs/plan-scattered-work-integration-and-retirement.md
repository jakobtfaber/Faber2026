# Plan: Scattered-Work Integration and Retirement

---
**Date:** 2026-07-25
**Author:** AI Assistant (structure approved by owner 2026-07-25; revised after
independent adversarial review, 15 findings addressed)
**Status:** Approved structure; ready for `ai-research-workflows:implementing-plans`
**Source handoff:** `docs/rse/specs/handoff-2026-07-25-19-03-scattered-work-rescue-and-consolidation.md`
---

## 1. Overview

Capture of all scattered Faber2026 / Faber2026-analysis / dsa110-FLITS work
completed 2026-07-25 (rescue v2 on the backup drive; preservation bundles in
scratch). This plan covers the next two phases: **integration** (getting
captured work onto development branches and repointing stale path references)
and **retirement** (evidence-gated removal of redundant copies). End state:
`~/Developer/repos/github.com/jakobtfaber/` plus `~/Data/Faber2026` are the
only locations holding project material.

Science-authority reconciliation (the ten uncertainties in the parent-root
`worktree-reconciliation.md`) is **out of scope**; where this plan and that
document interact, that document governs. Consequence made explicit:
**Track A of Phase 5 (retiring repository checkouts) cannot run until the
reconciliation has assigned an authority status to the relevant analysis
family** — that is Tier 2 gate item 1, and this plan does not manufacture it.
Phases 1–4 and Phase 5 Track B (non-checkout artifacts) do not depend on it.

## 2. Current State Analysis

- **Cherry-pick resolution safe.** Standalone `Faber2026-analysis` at
  `6c0e9b3640061ba95df54cc457898fb24824a3e2`, clean, pushed 2026-07-25 to
  `origin/codex/nine-sightline-cherrypick-resolution-20260725` (verified by
  `ls-remote`). Local branch `codex/nine-sightline-search-contract` is
  5 ahead / 4 behind its origin counterpart. Divergence unresolved.
- **Rescue handoff and worktree records landed** — `Faber2026-analysis`
  PR #94, squash-merged to `main` 2026-07-26T02:14Z.
- **Overleaf path references: 62 live matches** (34 Faber2026 incl.
  submodule working copies / 20 Faber2026-analysis / 8 dsa110-FLITS) for
  pattern `Developer/overleaf/Faber2026`. Counts drift; the enumeration
  command in Phase 2 is authoritative, not this figure. Matches split into
  *functional* references (rewrite) and *historical records* (leave
  verbatim) — classification below.
- **Four backup-drive side-checkouts**, live state verified 2026-07-25:

  | Path (under `/Volumes/ArtifexBackupDrive/Faber2026-worktrees/`) | Branch | HEAD | Dirty |
  |---|---|---|---|
  | `parent/.codex-expanded-foreground-map-closure-20260722` | `codex/expanded-foreground-map-closure` | `9ea975de` | 2 (submodule pointer moves) |
  | `parent/Faber2026-foreground-redshift-verdicts` | `research/foreground-redshift-verdicts` | `6e6a986b` | 0 (locked worktree) |
  | `parent/Faber2026-rfi-route-validation` | **detached** | `94052932` | 1 (`analysis` submodule pointer move) |
  | `analysis/set-expanded-independent-validation` | `codex/auto-set-expanded-independent-validation` | `9ef214f` | 2 |

  Owner approved (2026-07-25) creating `research/rfi-route-validation` for
  the detached checkout; branch not yet created. The detached checkout's
  single dirty entry is a **submodule pointer move, not a content file** —
  it is never committed (deliberate-pin rule); both pointer states go to
  the receipt.
- **Preservation artifacts without terminal disposition:** ~29 GB under
  `/Volumes/ArtifexBackupDrive/Faber2026-*` (rescue v2, preserved-bundles
  incl. 10 empty slots with a recovery map, preserved-bags,
  preserved-checkouts, drive worktrees) and 1.6 GB under
  `~/Developer/scratch/preservation/` (FLITS unreferenced 679 MB bundle,
  Overleaf 197 MB bundle, plus **unexamined** 780 MB
  `Faber2026-science-gates-20260722`). Both locations are staging under the
  owner's rule, not storage.
- **Registered worktrees: 7**, four on the backup drive (three locked
  parent-side, one analysis-side). `git worktree prune` while the drive is
  unmounted deregisters them — never run detached.
- **Leftover clutter** in the canonical directory:
  `Faber2026-worktrees/` (786 MB, one old checkout `special-refs-20260724`),
  `Faber2026-analysis-worktrees/` (empty), `Faber2026-analysis-jointtf.qjhnHz`
  (4 KB). Captured in rescue v2 folder `04-`; disposition in Phase 5 Track B.

## 3. Desired End State

- The `codex/nine-sightline-search-contract` divergence has one recorded
  owner decision, executed and verified against pinned commit hashes.
- Zero *functional* references to `Developer/overleaf/Faber2026` on `main`
  of the two standalone repos and on the tip of the FLITS default branch;
  the parent repo's working copies carry the same edits via its submodule
  checkouts, with the parent-`main` criterion **deferred to the next
  deliberate submodule pin bump** (out of this plan; see Phase 2 note).
- All four side-checkouts' branches exist on their origin remotes,
  including new `research/rfi-route-validation` at `94052932`.
- Preservation artifacts have one owner-decided terminal home; the 780 MB
  science-gates directory is examined and classified.
- Every retired path removed only after passing the applicable gate
  (Track A: Tier 2 four-part gate + stash/ref/liveness extensions;
  Track B: artifact provenance gate) with an owner approval naming that
  exact path.

## 4. What We're NOT Doing

- No science-authority decisions; no manuscript promotion; no Overleaf sync.
- No rewriting of historical records (handoffs, claude-science frames,
  dated specs, receipts) even where they contain the retired path.
- No `pipeline/` or `analysis/` submodule-pointer commits anywhere, in any
  repo or worktree, for any reason within this plan.
- No branch or tag deletion; no force-push; no `git worktree prune`; no
  reflog expiry or `git gc` anywhere.
- No deletion of the canonical three clones or `~/Data/Faber2026` under any
  argument, including "it is backed up".
- No blanket retirement of the 25+ analysis ticket worktrees — each is its
  own Track A review, out of this plan's scope unless the owner queues it.

## 5. Implementation Approach

Five sequential phases, each ending at a verified checkpoint. Phases 1–3
are mechanical and reversible (branch pushes, focused PRs) under the
standing 2026-07-08 authorization. Phases 4–5 contain one-way doors: every
destructive step is preceded by an explicit owner approval naming exact
paths. One writer per repo at a time; staleness proven by `range-diff` or
content comparison — never `git cherry` (repos rebase/squash-merge). All
remote verifications use `git -C <the-worktree-in-question> ls-remote
--exit-code origin <ref>` and compare the **full 40-character hash** against
the expected value; `--exit-code` makes an absent ref fail loudly.

## 6. Implementation Phases

### Phase 1 — Divergence decision packet (Faber2026-analysis)

**Objective:** one owner decision on the 5-ahead / 4-behind split of
`codex/nine-sightline-search-contract`.

1. Build the packet (no working-tree mutation; note `git fetch` does update
   remote-tracking refs and `FETCH_HEAD` — record the fetched origin tip
   hash in the packet as the evidence snapshot):

   ```bash
   cd ~/Developer/repos/github.com/jakobtfaber/Faber2026-analysis
   git fetch origin
   BASE=$(git merge-base codex/nine-sightline-search-contract origin/codex/nine-sightline-search-contract)
   LOCAL=$(git rev-parse codex/nine-sightline-search-contract)
   REMOTE=$(git rev-parse origin/codex/nine-sightline-search-contract)
   echo "base=$BASE local=$LOCAL remote=$REMOTE"   # pin all three in the packet
   git range-diff "$BASE..$REMOTE" "$BASE..$LOCAL"
   git log --oneline --left-right "$LOCAL...$REMOTE"
   git diff "$LOCAL" "$REMOTE" --stat
   ```

2. Record the packet as
   `docs/rse/specs/decision-nine-sightline-divergence-2026-07.md` in
   Faber2026-analysis: the three pinned hashes, both commit lists, the
   range-diff verdict on which local commits are patch-equivalent upstream,
   the file-level conflicts, and 2–3 concrete resolution options (rebase
   local onto origin tip; merge; or adopt the local line and open a PR
   superseding the remote 4).
3. Present to the owner as a queue item (wayfinder ticket or PR comment on
   the pushed `codex/nine-sightline-cherrypick-resolution-20260725`
   branch); record the decision in the packet file.
4. Execute the decided resolution on a focused branch + PR. **Verify:**
   with `$BASE` and `$LOCAL` from the packet and `TIP` = the surviving
   branch head:

   ```bash
   git range-diff "$BASE..$LOCAL" "$BASE..$TIP"
   ```

   Every packet commit the owner accepted must appear as `=` (unchanged) or
   with a documented modification; any `<` -only (dropped) row is a failure.
   If the resolution was squash-merged, instead assert content coverage:
   `git diff $TIP $LOCAL -- <accepted paths>` must be empty for every path
   the accepted commits touched.

**Depends on:** nothing. **Blocks:** nothing downstream mechanically.

### Phase 2 — Repoint functional Overleaf references

**Objective:** zero functional references to the retired
`~/Developer/overleaf/Faber2026` checkout on the standalone repos' default
branches; historical records untouched.

**Submodule scoping (explicit):** edits to files inside the parent repo's
`analysis/` and `pipeline/` working copies are committed and PR'd **in the
standalone repos** (`Faber2026-analysis`, `dsa110-FLITS`). The parent's
pinned gitlinks continue to reference pre-edit commits until the next
deliberate pin bump, which is a separately scoped step outside this plan.
Therefore the Phase 2 success criterion applies to the standalone repos'
default branches and to the parent's own tracked files (`AGENTS.md`) only —
**not** to parent `main` as instantiated through its pins.

Authoritative enumeration (run fresh at each repo root; `rg` prints paths
relative to the root without a `./` prefix when given no path argument):

```bash
rg -l --hidden -g '!.git' 'Developer/overleaf/Faber2026'
```

Classification filter — a match is **historical** (excluded) if under
`docs/rse/specs/`, `docs/rse/claude-science/`, `docs/superpowers/plans/`,
`.agents/`, `.claude-science/`, or is a log/receipt (`*.jsonl`,
`execution-log*`). The working check, per repo root:

```bash
rg -l --hidden -g '!.git' 'Developer/overleaf/Faber2026' \
  | rg -v '(^|/)(docs/rse/specs/|docs/rse/claude-science/|docs/superpowers/plans/|\.agents/|\.claude-science/)' \
  | rg -v '\.jsonl$|execution-log'
# expect: the functional file list now; EMPTY after the edits land
```

Functional set as of 2026-07-25 (re-derive with the command above before
editing; the list below is the expected result, not the authority):

- `AGENTS.md` (Faber2026 root; Faber2026-analysis root) — replace the
  Overleaf path with the canonical repo path in the workspace-layout prose.
- `REPRODUCE.md` + `repro_manifest.csv` (Faber2026-analysis) — repoint
  artifact paths to `~/Developer/repos/github.com/jakobtfaber/Faber2026/…`.
- `scripts/manuscript/regenerate_budget_figures.sh`,
  `tools/sync_figures.py` (dsa110-FLITS) — replace the hardcoded Overleaf
  root with the parent-repo root; keep relative sub-paths unchanged.
- `analysis/scattering-refit-2026-06/local_runs/configs/freya_{chime,dsa}_run.yaml`
  (dsa110-FLITS) — repoint output/figure directories.
- `docs/rse/specs/runbook-overleaf-propagation-2026-07-08.md`
  (Faber2026-analysis) — special case: it *documents* the old route and is
  inside the historical-exclusion directory, so the emptiness check never
  covers it. Its verification is its own explicit assertion (step 4 below):
  prepend a dated banner stating the checkout is retired and Overleaf now
  pulls from GitHub in the browser; do not rewrite its steps.

Execution, per repo (three focused branches, three PRs):

1. Run the classification filter; record its output (the failing state).
2. Edit only the functional files; one commit per repo,
   `docs: repoint retired Overleaf checkout paths to canonical repos`.
3. Per-file validation, matched to file type:

   ```bash
   bash -n scripts/manuscript/regenerate_budget_figures.sh
   python3 -c "import ast; ast.parse(open('tools/sync_figures.py').read())"
   python3 -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]" \
     analysis/scattering-refit-2026-06/local_runs/configs/freya_chime_run.yaml \
     analysis/scattering-refit-2026-06/local_runs/configs/freya_dsa_run.yaml
   python3 -c "import csv,sys; rows=list(csv.reader(open('repro_manifest.csv'))); \
     assert len({len(r) for r in rows})==1, 'ragged csv'"
   # every newly written absolute path must exist:
   rg -o '/Users/jakobfaber/Developer/repos/github\.com/jakobtfaber/[^"'\'' )]*' \
     <edited files> | sort -u | while read -r p; do [ -e "$p" ] || echo "MISSING $p"; done
   ```

   A full figure-regeneration run of `regenerate_budget_figures.sh` is
   **deferred** to the next manuscript-figure task; the PR body must say so.
4. Assert the runbook banner:

   ```bash
   rg -c 'RETIRED.*2026-07' docs/rse/specs/runbook-overleaf-propagation-2026-07-08.md
   # expect: 1
   ```

5. Re-run the classification filter; must return empty. Record remaining
   historical matches in the PR body as the accepted exception list.
6. Open the three PRs; merge under standing authorization once checks pass.

**Verify:** classification filter empty at each standalone repo root on the
default branch; runbook banner assertion passes. This unblocks (but does
not execute) Overleaf-directory retirement in Phase 5.

### Phase 3 — Integrate side-checkout work

**Objective:** every side-checkout's unique committed work exists on an
origin branch of the correct repo. Submodule pointer moves are recorded,
never committed. Dirty-state disposition for each checkout is decided here
so Phase 5 Track A is not left with an illegal dead end.

Order (one writer at a time). All verifications:
`git -C $W ls-remote --exit-code origin <ref>` with full-hash comparison.

1. `parent/Faber2026-foreground-redshift-verdicts` (clean, locked):

   ```bash
   W=/Volumes/ArtifexBackupDrive/Faber2026-worktrees/parent/Faber2026-foreground-redshift-verdicts
   git -C $W push origin research/foreground-redshift-verdicts
   git -C $W ls-remote --exit-code origin refs/heads/research/foreground-redshift-verdicts
   # expect full hash matching: git -C $W rev-parse research/foreground-redshift-verdicts
   ```

2. `parent/Faber2026-rfi-route-validation` (detached `94052932`; the 1
   dirty entry is the `analysis` submodule pointer — not committed):

   ```bash
   W=/Volumes/ArtifexBackupDrive/Faber2026-worktrees/parent/Faber2026-rfi-route-validation
   git -C $W status --porcelain                       # receipt: record pointer state
   git -C $W diff --submodule=short                   # receipt: both SHAs
   git -C $W branch research/rfi-route-validation 94052932
   git -C $W push origin research/rfi-route-validation
   git -C $W ls-remote --exit-code origin refs/heads/research/rfi-route-validation
   # expect: 94052932… full hash
   ```

   No commit is made, so no branch switch is needed; the checkout stays
   detached and its pointer move stays uncommitted, receipted.
3. `parent/.codex-expanded-foreground-map-closure-20260722`
   (`codex/expanded-foreground-map-closure` @ `9ea975de`, 2 dirty =
   submodule pointer moves): push the branch as-is; record both pointer
   SHAs (`git diff --submodule=short`) in the receipt. No commits.
4. `analysis/set-expanded-independent-validation`
   (`codex/auto-set-expanded-independent-validation` @ `9ef214f`, 2 dirty):
   inspect with `git -C $W status --porcelain` and `git -C $W diff`. If a
   dirty file is source/docs: commit it on the checkout's own branch
   (already checked out, no detached-HEAD hazard), push, verify pushed tip
   hash. If generated: copy to rescue folder
   `/Volumes/ArtifexBackupDrive/Faber2026-rescue-20260725-v2/05-backupdrive-sidecheckouts/`
   with a note in that folder's manifest, and record in the receipt.

**Dirty-state disposition (feeds Phase 5 Track A):** after the pushes,
each checkout carrying only *receipted submodule pointer moves* is
realigned by re-checking out the recorded gitlink
(`git -C $W submodule update --checkout -- <path>`), which restores the
pinned state and leaves the tree clean. This discards only the pointer
drift whose both-sides SHAs are already in the receipt; it is named in the
Phase 5 owner approval for that checkout before it is done. A checkout
whose dirty entries were committed or copied out is clean by construction.

No PRs are opened for these branches — landing into `main` is a
reconciliation activity (`worktree-reconciliation.md` Phase 4), not this
plan.

**Verify:** four `--exit-code` ls-remote outputs whose full hashes equal
the expected tips, written to the receipt.

### Phase 4 — Preservation-artifact termination

**Objective:** one owner-decided terminal home; nothing left parked on
staging.

1. Examine the unexamined directory (read-only):

   ```bash
   D=~/Developer/scratch/preservation/Faber2026-science-gates-20260722
   du -sh "$D"; find "$D" -maxdepth 2 | head -50
   git -C "$D" log --oneline -10 2>/dev/null; git -C "$D" status --porcelain 2>/dev/null
   ```

   Classify per the deletion-safety rules (opaque ⇒ UNVERIFIED, never
   junk); write findings to the receipt.
2. Re-verify **both** bundles from inside their source repositories:

   ```bash
   git -C ~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS bundle verify \
     ~/Developer/scratch/preservation/dsa110-FLITS-unreferenced-20260725/unreferenced-commits.bundle
   shasum -a 256 \
     ~/Developer/scratch/preservation/dsa110-FLITS-unreferenced-20260725/unreferenced-commits.bundle
   # expect 3933b486184b08675a20a7a3f7d1b5468c0953b8a5b1ee232b73ba979060a8a6

   git -C ~/Developer/overleaf/Faber2026 bundle verify \
     ~/Developer/scratch/preservation/Faber2026-overleaf-20260725/history/overleaf-comprehensive-preservation.bundle
   shasum -a 256 \
     ~/Developer/scratch/preservation/Faber2026-overleaf-20260725/history/overleaf-comprehensive-preservation.bundle
   # expected size 78,223,987 bytes; record the hash (no prior sha256 exists —
   # this run establishes it)
   ```

3. Present the owner one decision with a recommendation. Options:
   (a) `~/Data/Faber2026/preservation/` — **note the conflict**: the
   declared rule is `~/Data/Faber2026` holds *data products only*, and
   bundles/manifests are provenance material, so choosing (a) amends that
   rule and the amendment must be recorded in
   `faber2026-consolidation-target-layout` memory; (b) keep on the backup
   drive as designated cold storage — overturns the "drive = staging"
   rule, same recording requirement; (c) a new archive location, e.g.
   `~/Developer/repos/github.com/jakobtfaber/Faber2026/archive-provenance/`
   or a dedicated `~/Archives/Faber2026/` — no rule conflict but a new
   top-level location needs the owner's home-taxonomy sign-off.
   Recommendation: **(c) with `~/Data/Faber2026/provenance/`-style naming
   only if the owner prefers one root** — present all three, decide once,
   record where the owner says.
4. Execute the decided moves manifest-first, atomically:

   ```bash
   SRC=<source dir>; DST=<terminal home>/<name>; TMP=$DST.partial
   df -h "$(dirname "$DST")"                          # preflight: free space > du -sh $SRC
   (cd "$SRC" && find . -type f -exec shasum -a 256 {} + | sort -k2) > /tmp/src.manifest
   rsync -a "$SRC/" "$TMP/"
   (cd "$TMP" && find . -type f -exec shasum -a 256 {} + | sort -k2) > /tmp/dst.manifest
   diff /tmp/src.manifest /tmp/dst.manifest           # must be empty
   mv "$TMP" "$DST"                                   # atomic finalize
   # on any failure: rm -rf "$TMP" is the ONLY deletion allowed (partial copy,
   # named in the receipt), source untouched
   ```

   Originals are **not** deleted in this phase (that is Phase 5 through
   the gate). Symlinks inside the tree are preserved by `rsync -a`; the
   manifest covers regular files, and `find . -type l` output is recorded
   separately in the receipt for both sides.

**Verify:** manifest diff empty at destination; receipt lists every
artifact, source, destination, hash.

### Phase 5 — Evidence-gated retirement

Two tracks with different gates. Both: one candidate at a time, no batch
verdicts, owner approval naming the exact path (and any lock release or
pointer realignment it covers), maximum five retirements per session
(reconciliation Phase 6 rule).

#### Track A — repository checkouts and registered worktrees

**Precondition: the reconciliation has assigned an authority status to the
checkout's analysis family.** Until then a Track A candidate stays queued.

Extended gate — all required:

```bash
# 1 authority status assigned (reconciliation record exists) — manual check
# 2 clean tree (after any receipted pointer realignment from Phase 3)
git -C <path> status --porcelain                       # expect empty
# 3 no parked changes
git -C <path> stash list                               # expect empty
# 4 all refs accounted for: every local ref is on origin, in a preservation
#   bundle, or explicitly receipted; fake remote namespaces named
git -C <path> for-each-ref --format='%(refname) %(objectname)'
# 5 no open PR
gh pr list --head <branch> --repo jakobtfaber/<repo>   # expect empty
# 6 no unmerged unique delta (range-diff or content comparison, never cherry)
git -C <repo> range-diff origin/main...<branch>
# 7 not the last copy of a preserved negative/superseded result the
#   reconciliation wants kept (plan-worktree-consolidation Tier 2, closing
#   requirement below the four-part list)
# 8 no live process using the path
lane-liveness <path>   # only 'quiescent' proceeds; plus lsof +D <path> | head
```

Mechanics after gate + approval — registered worktrees are **removed, not
trashed**: the checkout's unique state is provably zero by gate items 2–6,
and rescue v2 already holds its capture, so `_trash/` staging would
duplicate a verified capture. Sequence:

```bash
git -C <main-repo> worktree unlock <path>    # only if locked; named in approval
git -C <main-repo> worktree remove <path>    # refuses if dirty — that is the gate working
git -C <main-repo> worktree list --porcelain # confirm deregistration
```

Never `worktree remove --force`; a refusal means a gate item was wrong —
stop and re-run the gate. Non-registered standalone clones (e.g. the
Overleaf checkout, eligible only after Phase 2 merges and Phase 4 confirms
its 144 preserved refs + bundle at the terminal home, **including its two
figure stashes** — gate item 3 applies to it with the stashes proven
content-covered by the preservation bundle or explicitly exported first)
are moved to `~/Documents/_trash/<name>/` with a `PROVENANCE.md`, and
deleted only on the owner's separate explicit delete instruction.

#### Track B — non-checkout artifacts (no git gate applicable)

Candidates: `~/Developer/scratch/preservation/*` (after Phase 4 moves),
`~/Developer/scratch/faber2026-retirement-qualification-20260722.6Bd2Wy`,
scratch analysis outputs (~95 MB: `window_campaign_2L`, `campaign_r4/5/6`,
`perburst_figs`, `flits-local-runs` — owner may instead route these to
`~/Data/Faber2026` as data products), canonical-directory clutter
(`Faber2026-worktrees/`, `Faber2026-analysis-worktrees/` (empty),
`Faber2026-analysis-jointtf.qjhnHz`), and eventually the drive's rescue/
preserved trees once their contents reach the terminal home.

Artifact gate — all required:

1. **Provenance identified**: what produced it, per rescue manifests or
   Phase 4 examination; opaque ⇒ UNVERIFIED ⇒ not a candidate.
2. **Content coverage proven**: byte-identical copy exists at the terminal
   home (Phase 4 manifest diff) or the content is regenerable from a named
   live source recorded in the receipt.
3. **No live process** (`lane-liveness` quiescent, `lsof +D` empty).
4. **Owner approval naming the exact path.**

Then move to `~/Documents/_trash/<name>/` (or `_holding/` if any item is
uncertain) with `PROVENANCE.md`; `rm` only on separate explicit delete
instruction, per the deletion-safety rules.

**Verify (both tracks):** post-retirement `git worktree list --porcelain`
on all three repos shows only intended registrations; before/after
inventory diff in the receipt.

## 7. Success Criteria

**Automated:**

- Phase 2 classification filter (§6 Phase 2) returns empty at both
  standalone repo roots on their default branches; runbook banner
  assertion returns 1. (Parent-main-via-pins criterion explicitly deferred
  to the next pin bump.)
- `git -C <repo> ls-remote --exit-code origin <ref>` succeeds with
  expected full hashes for: `research/foreground-redshift-verdicts`
  (`6e6a986b…`), `research/rfi-route-validation` (`94052932…`),
  `codex/expanded-foreground-map-closure` (`9ea975de…`),
  `codex/auto-set-expanded-independent-validation` (`9ef214f…` or its
  committed child).
- `git bundle verify` passes for both preservation bundles at their
  terminal home; FLITS bundle sha256 =
  `3933b486184b08675a20a7a3f7d1b5468c0953b8a5b1ee232b73ba979060a8a6`;
  Overleaf bundle hash matches the value recorded in Phase 4 step 2.
- Phase 2 per-file validations pass (`bash -n`, `ast.parse`, YAML parse,
  CSV shape, path-existence sweep).
- Phase 4 manifest diffs empty.
- `git worktree list --porcelain` matches the intended post-retirement
  registration set on all three repos.

**Manual (owner):**

- Divergence decision recorded in the decision packet file.
- Terminal-home decision recorded, including which layout rule (if any)
  it amends.
- One named approval per retired path, covering any lock release and
  pointer realignment; `_trash/` staging inspected before any final
  delete instruction.
- Science-gates 780 MB classification reviewed.
- Authority-status precondition confirmed per Track A candidate.

## 8. Testing Strategy

Phase 2 touches prose (`AGENTS.md`, runbook banner), manifests
(`REPRODUCE.md`, `repro_manifest.csv`), two YAML run configs, and two
tools; each has a matched validation in Phase 2 step 3 (syntax parse, YAML
parse, CSV shape, absolute-path existence sweep, banner assertion). A full
figure-regeneration run is deferred and named in the PR. Integration
phases are verified by `--exit-code` remote assertions with full-hash
comparison and by `range-diff` against pinned hashes; preservation by
sorted sha256 manifest diffs with atomic finalize; retirement by
before/after worktree inventory diff. Each phase ends with a receipt
under `docs/rse/specs/` (or the established receipt location) before the
next begins.

## 9. References

- [Handoff 2026-07-25 (source)](handoff-2026-07-25-19-03-scattered-work-rescue-and-consolidation.md)
- [Worktree consolidation plan, amended](plan-worktree-consolidation-2026-07-22.md) — Tier 2 gate incl. the not-last-copy closing requirement
- [Worktree inventory, historical banner](worktree-inventory-2026-07-22.md) — recovery map for 10 empty slots
- [Reconciliation audit](worktree-reconciliation-audit-2026-07-22.md)
- `worktree-reconciliation.md` (parent repo root, owner-authored) — governs on any conflict
- Rescue captures: `/Volumes/ArtifexBackupDrive/Faber2026-rescue-20260725-v2/` folders `01-`–`06-`
- Adversarial review (Codex, 2026-07-25): 15 findings, all incorporated —
  scope precondition for Track A; submodule-pin scoping of the Phase 2
  criterion; detached-HEAD push semantics; dirty-worktree realignment
  path; `--exit-code`/full-hash remote checks; corrected classification
  filter; both-bundle verification; terminal-home rule conflict surfaced;
  remove-vs-trash mechanics split; Track B artifact gate; stash/ref/
  liveness/last-copy gate extensions; manifest-based copy verification;
  pinned-hash Phase 1 verification; fetch-mutation caveat; per-file-type
  validations.
