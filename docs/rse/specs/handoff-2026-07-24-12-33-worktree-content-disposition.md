# Handoff: finish Mac worktree retirement and SSD relocation

**Captured:** 2026-07-24 12:34 PDT / 2026-07-24T19:34:30Z  
**Parent map:** [Faber2026 #229](https://github.com/jakobtfaber/Faber2026/issues/229)  
**Preservation route:** [Faber2026 #233](https://github.com/jakobtfaber/Faber2026/issues/233)  
**Owner:** `jakobtfaber`  
**Next agent:** fresh session, outside the session that produced this handoff  
**Handoff branch:** `docs/handoff-worktree-disposition-20260724`  
**Handoff worktree:** `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-worktrees/handoff-worktree-disposition-20260724`

## Executive state

The original retirement estate is handled. The remaining work is a **new
10-worktree delta created after the sealed estate**:

- Eight clean worktrees contain merged or patch-equivalent content. They can be
  retired after a fresh, target-scoped owner/operation check. Estimated internal
  recovery: **2.97 GiB**.
- Two clean worktrees retain unmatched commits. Move them to
  `ArtifexBackupDrive`; do not delete them. Estimated internal recovery:
  **2.35 GiB**.
- No one is currently using any of these ten paths according to process,
  open-file, terminal, Repowire peer, and Repowire job checks.

Do not restart the estate-wide analysis. Work from the ten-row table below.

## Non-negotiable safety rules

1. **Issue #227 is already retired. Do not recreate, rerun, move, or remove it.**
   Protected path:
   `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-untrack-agent-briefs`.
   It must remain absent and unregistered.
2. Never blanket-prune or force-remove a worktree.
3. Before each action, refresh exact path, HEAD, branch, status, ignored and
   untracked payload, registration stanza, active owner, and relevant refs.
4. Treat operation markers in the **target Git directory** or shared common
   state as blockers. Sibling-worktree markers may be recorded as evidence-only
   only after proving they have no open handle/process and the target has no
   marker. Do not delete another worktree's marker.
5. For an external linked worktree, lock its registration:

   ```bash
   git --git-dir=<common> worktree lock \
     --reason "Preserved on removable ArtifexBackupDrive; unlock only while volume is mounted" \
     <external-path>
   ```

6. The `pipeline/` submodule pointer is deliberate. Do not change canonical
   parent or submodule refs as a side effect.

## Start here

```bash
cd /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026
python3 analysis/scripts/kb search "worktree retirement external relocation content disposition"
test -d /Volumes/ArtifexBackupDrive
df -h /System/Volumes/Data /Volumes/ArtifexBackupDrive
gh issue view 229 --repo jakobtfaber/Faber2026
gh issue view 233 --repo jakobtfaber/Faber2026
```

The five authority common directories are:

```text
/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/.git
/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/.git/modules/analysis
/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/.git/modules/pipeline
/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis/.git
/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/dsa110-FLITS/.git
```

At the final live check their worktree counts were `33 / 40 / 13 / 23 / 7`,
total `116`. This includes four linked worktrees now registered on the SSD and
this isolated handoff worktree. The handoff worktree was created after the
ten-row audit; it is active infrastructure for this document, not an eleventh
retirement candidate.

## Final new-worktree delta

Live main refs at audit time:

- Analysis: `759ad238b427`
- Parent: `1dfb5c2ae552`

All ten targets were clean in tracked and untracked state. None had a
target-specific operation marker or active owner.

| Path | Size | Evidence | Next action |
| --- | ---: | --- | --- |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis-worktrees/crossmatch-contract-20260724` | 446 MiB | HEAD `de1e0331fc15`; zero unique commits; merged pull request 91; no ignored payload | Retire |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis-worktrees/raw-chime-definition-20260724` | 446 MiB | HEAD `d76269e208fb`; `git cherry -`; merged pull request 92 | Retire |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis-worktrees/technical-review-20260724` | 446 MiB | HEAD `875765c64070`; `git cherry -`; merged pull request 93; 180 KiB disposable cache | Manifest cache, then retire |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis-worktrees/trust-docs-20260724` | 446 MiB | HEAD `2afbd06ec28c`; `git cherry -`; merged pull request 91; 176 KiB disposable cache | Manifest cache, then retire |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-worktrees/overleaf-research-20260724` | 169 MiB | HEAD `804b0d5ea678`; `git cherry -`; merged pull request 240; submodules uninitialized | Retire |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-worktrees/repository-map-followup` | 717 MiB | HEAD `94058a3da622`; `git cherry -`; merged pull request 246; both submodules initialized | Retire after exact nested-status receipt |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-worktrees/results-library-audit-20260724` | 186 MiB | HEAD `86d8c9f1a6c1`; zero unique commits; merged pull request 236; submodules uninitialized | Retire |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-worktrees/rfi-archive-20260724` | 186 MiB | HEAD `c34276da28e2`; `git cherry -`; merged pull request 236; submodules uninitialized | Retire |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-worktrees/repository-map-publish` | 1.1 GiB | HEAD `46aa13165c07`; two unmatched commits; clean; both submodules initialized | Move to SSD, repair nested links, lock |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-repository-map` | 1.2 GiB | HEAD `3d50b72197a7`; one unmatched commit; no remote branch; clean; both submodules initialized | Move to SSD, repair nested links, lock |

### Current unrelated marker noise

These markers had no open handle or matching process, but belong to other
worktrees. Do not remove them casually:

```text
.../Faber2026/.git/modules/analysis/worktrees/Faber2026-analysis-apj-finalize/AUTO_MERGE
.../Faber2026/.git/modules/analysis/worktrees/Faber2026-analysis-converge-rfi01a-20260722/sequencer
.../Faber2026/.git/modules/analysis/worktrees/review-rfi-preservation-limits/AUTO_MERGE
.../Faber2026/.git/modules/analysis/worktrees/Faber2026-analysis-wf09.jMR2S4/AUTO_MERGE
.../Faber2026/.git/worktrees/Faber2026-expanded-foreground-phase-two/index.lock
```

The final `index.lock` is zero bytes and dated 2026-07-23 23:01. It is a
sibling-worktree lock, not one of the ten targets. Recheck ownership; do not
delete it merely to make the common directory look clean.

The read-only final-delta auditor classified all ten actions as blocked while
any marker remained anywhere in the shared common directory. Later execution
work treated proven-unowned sibling markers as evidence-only, while still
failing closed on target-specific or shared-root/reference locks. This policy
disagreement was not durably resolved. The next agent must explicitly
re-adjudicate it from live marker ownership before mutation; do not silently
inherit either interpretation.

## What this session completed

### Receipt-retired linked worktrees

- `Faber2026-analysis-close-02-20260722`
  - Final receipt:
    `834be5bfc41d230abbcf0bc1bc079bac358358e52317610c80b73829b62d8b8b`
- `Faber2026-analysis-close-03-20260722`
  - Final receipt:
    `0894195fa29b019270582b73b8ce19550a6599fb36db837f75fde43477262fe6`
- `Faber2026-analysis-apj-closure`
  - Final receipt:
    `ee14e6300250b269ebe5f702d4bbfc693d0da83094a48cc68da98cc1c6c1a333`
- `Faber2026-analysis-count-audit`
  - Final receipt:
    `5a6ee43d6eca7c1aad85b7faee93a11e3df9c43e839158df2f5cff97fa80d706`
- `Faber2026-wayfinder18`
  - Concurrent safe-retirement receipt:
    `/Users/jakobfaber/Developer/scratch/receipts/Faber2026/worktree-retirement/content-cache-wayfinder18-20260724T185517Z/receipt.json`
  - Receipt SHA-256:
    `67d23c8568aeba4c9f67b969069504af8a930f91a54014370c70ea8a675defd8`
  - Branch remains at `9ea975de`; commit is reachable from `origin/main`.

Issues [#235](https://github.com/jakobtfaber/Faber2026/issues/235) and
[#237](https://github.com/jakobtfaber/Faber2026/issues/237) are closed.

### External linked worktrees

These are registered against canonical internal Git common directories and
therefore require both the internal repository and the mounted SSD:

```text
/Volumes/ArtifexBackupDrive/Faber2026-worktrees/analysis/set-expanded-independent-validation
/Volumes/ArtifexBackupDrive/Faber2026-worktrees/parent/.codex-expanded-foreground-map-closure-20260722
/Volumes/ArtifexBackupDrive/Faber2026-worktrees/parent/Faber2026-foreground-redshift-verdicts
/Volumes/ArtifexBackupDrive/Faber2026-worktrees/parent/Faber2026-rfi-route-validation
```

All are Git-locked against pruning while the drive is absent.

Important caveats:

- `set-expanded-independent-validation` preserves three local commits and review
  evidence. It is **not approved to land**. Baseline packet:
  `959ac4cc02b19fcb55bef884049f43886709f5a610f3485d5d43af414a984744`.
- `Faber2026-foreground-redshift-verdicts` preserves a local-only parent commit
  and an ignored Entire log. It is not protected by a GitHub branch.
- `Faber2026-rfi-route-validation` preserves 165 Python bytecode caches with old
  absolute paths. Regenerate caches before using it.

Issues [#238](https://github.com/jakobtfaber/Faber2026/issues/238) and
[#239](https://github.com/jakobtfaber/Faber2026/issues/239) are closed.

### External standalone clone archives

All nine orphan full-clone common directories from the estate are off internal
storage: three were earlier receipt-retired under
[#234](https://github.com/jakobtfaber/Faber2026/issues/234); six were preserved
on the SSD:

```text
/Volumes/ArtifexBackupDrive/Faber2026-preserved-checkouts/Faber2026-jointtf-preserve.YrLfOn
/Volumes/ArtifexBackupDrive/Faber2026-preserved-checkouts/Faber2026-jointtf-pin.r6tIac
/Volumes/ArtifexBackupDrive/Faber2026-preserved-checkouts/Faber2026-analysis-expanded-foreground-tickets-02-03
/Volumes/ArtifexBackupDrive/Faber2026-preserved-checkouts/.tmp-faber2026-final-pin.pk7WwE
/Volumes/ArtifexBackupDrive/Faber2026-preserved-checkouts/.tmp-faber2026-pr174.Lj4gff
/Volumes/ArtifexBackupDrive/Faber2026-preserved-checkouts/Faber2026-analysis-wayfinder18
/Volumes/ArtifexBackupDrive/Faber2026-preserved-checkouts/Faber2026-analysis-protected-corpus-15
```

The last two paths share one full-clone common directory, so the list contains
seven paths but six orphan common roots.

Preservation caveats recorded on #233:

- Both joint-fit archives include copied virtual environments whose shebangs,
  activation scripts, and editable-install metadata refer to deleted internal
  paths. Recreate `.venv` before use.
- `Faber2026-jointtf-preserve.YrLfOn` is an intentional `blob:none` partial
  clone. It lacks 4,008 promised historical objects. Current HEAD is complete;
  fetch promised objects before relying on it as an offline-complete history.
- `Faber2026-analysis-expanded-foreground-tickets-02-03` preserves nested
  analysis commit `dc265bc`, which was not found in current canonical or GitHub
  history. Do not remove that SSD archive.
- The PR174 wrapper contains three repaired worktrees. Its external linked
  worktrees are locked.

## Cross-volume relocation method

Native `git worktree move` was tested and failed cleanly with:

```text
fatal: ... Cross-device link
```

Do not use raw `mv` for a registered linked worktree. The successful method was:

1. Capture target and authority refs/worktree lists.
2. Copy with `ditto --rsrc --extattr --acl`.
3. Compare wrapper inventory, Git HEAD/branch/status including ignored files,
   and ref digests. Run repository connectivity checks.
4. Repair the parent linked-worktree path with `git worktree repair`.
5. For every initialized submodule, repair both the copied `.git` pointer and
   the internal nested Git directory's worktree path.
6. Lock the external worktree.
7. Rebaseline any exact concurrent sibling move/ref change.
8. Remove only the verified internal source.
9. Verify external Git state again.

Avoid recursive `lsof +D`, full byte hashing, or full directory `diff` on
multi-gigabyte trees. They consumed minutes without improving the decision.
Use exact process-path checks plus Git state, refs, object connectivity, and
path/size inventories.

`ArtifexBackupDrive` is journaled HFS+ with ownership disabled. Content and Git
state were preserved, but tar metadata hashes can differ because ownership
metadata differs.

## Disk truth

At capture:

```text
Internal APFS: 926 GiB total, 880 GiB used, 12 GiB available, 99% full
ArtifexBackupDrive: 931 GiB total, 112 GiB used, 819 GiB available
```

Substantial internal data was deleted or moved, but local Time Machine snapshots
held deleted blocks and made `df` lag. Three local snapshots remained:

```text
com.apple.TimeMachine.2026-07-24-101918.local
com.apple.TimeMachine.2026-07-24-111829.local
com.apple.TimeMachine.2026-07-24-121826.local
```

No snapshot was manually deleted. Snapshot thinning is a separate destructive
action and needs explicit owner approval. macOS already purged six older
snapshots automatically during the wave.

## Known unrelated repository state

- The parent checkout was already dirty. Do not stage or commit unrelated
  `AGENTS.md`, `README.md`, submodule pointer, science, figure, or generated
  changes.
- The canonical analysis checkout is on `codex/repository-archive-audit` and
  already has three untracked worktree planning documents. This handoff was
  deliberately moved out of that dirty checkout into the isolated handoff
  branch named above.
- Parent pull request
  [#204](https://github.com/jakobtfaber/Faber2026/pull/204) and analysis pull
  request
  [#56](https://github.com/jakobtfaber/Faber2026-analysis/pull/56) remain open
  drafts. The owner rejected host dispersion-measure trust promotion. Do not
  merge them as accepted science.
- The external radio-frequency-interference relocation receipt under
  `/Volumes/ArtifexBackupDrive/Faber2026-worktrees/receipts/20260724T190204Z-rfi-route-validation/`
  has a faulty `source_entries=1` count and lacks
  `delta/verification-summary.txt`. Independent manifests and an `rsync`
  checksum showed zero content delta apart from repaired `.git` links, but the
  three relocation final manifests still need a final SHA-256 seal. Treat this
  as receipt hygiene, not a reason to move or delete that worktree again.
- Standalone `dsa110-FLITS` has a pre-existing commit-graph integrity error.
  Multiple checks reproduced the same 776-line error. Do not repair it as part
  of worktree cleanup.
- Parent and analysis refs advanced during the relocation wave because other
  agents were landing repository-map work. Rebaseline before every mutation;
  do not compare against old main OIDs as if they were immutable.

## Definition of done for the next session

1. Eight merged delta worktrees are receipt-retired.
2. Two unmatched-commit delta worktrees are copied, repaired, verified, and
   locked on `ArtifexBackupDrive`; internal sources are absent.
3. A fresh five-common census shows no other post-estate internal worktree
   delta.
4. #229 records the final delta and closes.
5. #233 records final archive caveats and closes only if the owner accepts the
   partial-clone and stale-environment limitations.
6. #227 remains absent and unregistered.
7. Report physical internal paths removed separately from APFS free-space
   reporting; do not claim snapshot-held bytes as immediately reclaimed.
