# Comprehensive Git Worktree Inventory (2026-07-22)

> **HISTORICAL SNAPSHOT — superseded as of 2026-07-25. Do not read the counts
> below as current state.** A retirement pass ran between 2026-07-22 and
> 2026-07-24. `~/Developer/scratch/worktrees/` no longer exists, and every local
> scratch worktree listed here is gone. Verified live registration on
> 2026-07-25 is **7 worktrees total**:
>
> - `Faber2026`: repo root (`codex/scintillation-notebook-wayfinder`) + 3 **locked**
>   on `/Volumes/ArtifexBackupDrive/Faber2026-worktrees/parent/`
>   (`codex/expanded-foreground-map-closure`, `research/foreground-redshift-verdicts`,
>   and one detached-HEAD RFI route-validation checkout).
> - `analysis`: submodule root (`codex/repository-archive-audit`) + 1 **locked** at
>   `/Volumes/ArtifexBackupDrive/Faber2026-worktrees/analysis/set-expanded-independent-validation`.
> - `pipeline`: submodule root (`codex/repository-archive-audit`) only.
>
> Four of those seven live on `ArtifexBackupDrive`; they are invisible and
> `git worktree prune` will deregister them while that volume is unmounted.
>
> The retired checkouts were mostly preserved — **51 numbered slots** under
> `/Volumes/ArtifexBackupDrive/Faber2026-preserved-bundles/`
> (`wave3-20260724T204828Z`, 41; `wave3b-detached-20260724T205254Z`, 10), plus
> `Faber2026-preserved-bags/` and `Faber2026-preserved-checkouts/`. **Preservation
> is not complete.** Audited slot-by-slot 2026-07-25:
>
> | Slot state | Count |
> |---|---|
> | has `unique.bundle` | 35 |
> | diff / untracked-tarball only (no unique commits to bundle — expected) | 6 |
> | **completely empty — preservation failed** | **10** |
>
> Do **not** cite `all_manifest_artifacts_present: true` from
> `~/Developer/scratch/faber2026-retirement-qualification-20260722.6Bd2Wy/validation.json`
> as coverage proof for these bundles: it was captured `2026-07-22T22:54Z`, and
> the wave3 bundles were written `2026-07-24 13:51`. It validated an earlier,
> different artifact set.
>
> The 10 empty slots, and where their content actually survives (checked
> 2026-07-25):
>
> | Empty slot | Recoverable from |
> |---|---|
> | `wave3/17-Faber2026-analysis-host-dm-repair-v2`, `wave3/27-Faber2026-host-dm-repair-v2` | branch `codex/host-dm-repair-v2`, present locally **and** on `origin` in both repos |
> | `wave3/03-Faber2026-analysis-host-dm-ac58513` | commit object `ac58513` still present in `analysis` ("docs: hand off completed host-DM aperture repair", 2026-07-23) |
> | `wave3/05-Faber2026-analysis-trust-5292337` | commit `5292337` present (merge of `origin/main` into trust lane, 2026-07-22) |
> | `wave3/06-Faber2026-analysis-trust-a9ac20c-diff` | commit `a9ac20c` present ("docs: resolve trust assessment registry", 2026-07-22) |
> | `wave3/07-Faber2026-analysis-trust-ef3211b-diff` | commit `ef3211b` present ("fix: enforce fail-closed trust registry coverage", 2026-07-22) |
> | `wave3/39-dsa110-FLITS-pr72-source.v2ifuj` | `jakobtfaber/dsa110-FLITS` PR **#72, MERGED** ("D3: h17 arc archive hash-map audit and iacobus copy") |
> | `wave3/02-.codex-analysis-review-pr36`, `wave3b/01-.codex-analysis-review-pr36` | **UNRESOLVED** — no surviving local ref; `gh pr view 36 --repo jakobtfaber/Faber2026-analysis` lookup failed. Needs a decision before those commit objects are ever garbage-collected. |
>
> The four bare commit objects are unreferenced — they survive only until a `gc`
> prunes them. If any of that trust-registry or host-DM work still matters,
> anchor it with a real ref now.
>
> This file is retained as the pre-retirement census — it is the only record of
> what the 132 checkouts *were*, which is what the preserved bundles need to be
> read against. Retirement rules going forward: see
> `plan-worktree-consolidation-2026-07-22.md` (idle clock cancelled 2026-07-25).

**Scope**: `Faber2026` main repository, `./analysis/` (`Faber2026-analysis`), `./pipeline/` (`dsa110-FLITS`), standalone workspace/tmp/Overleaf worktrees, and `h17` remote worktrees.  
**Total Worktrees Cataloged**: 132 *(as of 2026-07-22; 7 remain live — see banner)*

## Summary by Category
- **`Faber2026` Main Repo (Manuscript)**: 23 registered worktrees
- **`analysis/` Submodule (`Faber2026-analysis`)**: 41 registered worktrees
- **`pipeline/` Submodule (`dsa110-FLITS`)**: 9 registered worktrees
- **Standalone Workspace / Scratch / Overleaf Checkouts**: 44 worktrees
- **`h17` Remote Worktrees**: 15 worktrees

### 1. Main Repository (`Faber2026`) Registered Worktrees

| Location / Path | Branch |
| :--- | :--- |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026` | `codex/scintillation-notebook-wayfinder` |
| `/Users/jakobfaber/.windsurf/worktrees/Faber2026/Faber2026-pewter-maxwell` | `pewter-maxwell` |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/.codex-expanded-foreground-map-closure-20260722` | `codex/expanded-foreground-map-closure` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-chime-rfi-successor` | `codex/chime-rfi-preservation-gates-successor-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-expanded-foreground-phase-two` | `codex/expanded-foreground-phase-two` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-foreground-redshift-verdicts` | `research/foreground-redshift-verdicts` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-host-dm-repair` | `codex/host-dm-repair` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-joint-scattering-controlled-20260722` | `codex/joint-scattering-controlled-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-joint-scattering-repro` | `codex/joint-scattering-repro-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-jointtf-grok-revalidation` | `rse/jointtf-grok-harvest-revalidation` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-morphology-nine-review` | `codex/morphology-nine-review-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-nine-sightline-search-contract` | `codex/nine-sightline-search-contract` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-nine-sightline-successor` | `codex/nine-sightline-search-contract-successor-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-overleaf-native-git-contract` | `research/overleaf-native-git-contract` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-quarantine-20260717` | `ms/quarantine-outdated-science-20260717` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-rfi-preservation-prototype` | `codex/prototype-chime-rfi-preservation-gates` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-rfi-route-validation` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-scint-2l` | `ms/scint-joint-candidate-20260717` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-ticket14-roster` | `codex/repair-ticket14-roster` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-visual-science-review` | `codex/visual-science-review` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-wayfinder-auto/audit-results-library-conflicts` | `codex/auto-audit-results-library-conflicts` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-wayfinder07` | `codex/wayfinder-07-pin-host-redshift-evidence` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-wayfinder18` | `codex/wayfinder-18-law-host-redshifts` |


### 2. Submodule `analysis/` (`Faber2026-analysis`) Registered Worktrees

| Location / Path | Branch |
| :--- | :--- |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/.git/modules/analysis` | `codex/repository-archive-audit` |
| `/private/tmp/faber2026-analysis-rfi01a.qjYxMq` | `codex/rfi-validation-01a-review` |
| `/private/tmp/faber2026-phineas-analysis.2Lpoj0` | `codex/phineas-probabilistic-crossing` |
| `/private/tmp/ticket14-review.8DUSiy` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/.codex-analysis-main-post41` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/.codex-analysis-review-pr36` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/.codex-analysis-wayfinder18-publish` | `codex/wayfinder-18-law-host-redshifts-v2` |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis-ticket14-lfs-publish` | `codex/freeze-anonymous-catalog-corpus-lfs` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-apj-closure` | `codex/apj-wayfinder-closure` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-apj-finalize` | `codex/apj-wayfinder-finalize` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-apj-integrate` | `codex/apj-wayfinder-integrate` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-checkout-inventory` | `ms/checkout-advisory-triage` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-close-02-20260722` | `codex/close-crossmatch-contract-02` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-close-03-20260722` | `codex/close-physics-authority-03` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-controller-hardening` | `codex/controller-queue-hardening` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-controller-queue` | `codex/controller-queue-repair` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-converge-coauthor11-20260722` | `codex/converge-coauthor11-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-converge-host-redshift18-20260722` | `codex/converge-host-redshift18-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-converge-rfi01a-20260722` | `codex/converge-rfi01a-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-convergence-20260722` | `codex/convergence-wave-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-count-audit` | `codex/review-count-audit` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-dm-board-20260722` | `codex/wayfinder-default-recommendation-approval` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-foreground-source-verify-09` | `codex/verify-foreground-sources-09` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-free-alpha` | `codex/resolve-free-alpha-reporting` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-freeze-anonymous-catalog-corpus` | `codex/freeze-anonymous-catalog-corpus-complete` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-host-redshifts` | `codex/auto-host-redshifts` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-joint-scattering-controlled-20260722` | `codex/joint-scattering-controlled-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-pr33-audit` | `codex/host-dm-trust-ratification` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-rfi-preservation` | `codex/auto-rfi-preservation` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-ticket-10` | `codex/review-ticket-10` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-ticket14` | `codex/repair-ticket14-authoritative-roster` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-trust` | `codex/resolve-trust-assessment` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-auto/resolve-expanded-crossmatch-contract` | `codex/auto-resolve-expanded-crossmatch-contract` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-auto/review-coauthor-candidates` | `codex/auto-review-coauthor-candidates` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-auto/review-count-audit` | `codex/auto-review-count-audit` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-auto/review-rfi-preservation-limits` | `codex/auto-review-rfi-preservation-limits` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-auto/review-technical-robustness-dispositions` | `codex/auto-review-technical-robustness-dispositions` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-auto/review-trust-ledger` | `codex/auto-review-trust-ledger` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-controller-runtime` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-unblock` | `codex/unblock-wayfinder-tickets` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wf09.jMR2S4` | `codex/resolve-dsa-denominator` |


### 3. Submodule `pipeline/` (`dsa110-FLITS`) Registered Worktrees

| Location / Path | Branch |
| :--- | :--- |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/.git/modules/pipeline` | `codex/repository-archive-audit` |
| `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/dsa110-FLITS-ticket16-read` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/scratch/recovery/flits-window-tuning-ae67bdf` | `codex/chromatica-cross-band-scintillation` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dsa110-FLITS-count-audit` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dsa110-FLITS-joint-scattering-seeded-20260722` | `codex/joint-scattering-seeded-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dsa110-FLITS-registry-roster` | `codex/repair-production-registry-roster` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-pipeline-foreground-source-verify-09` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/scratch/worktrees/FLITS-quarantine-20260717` | `agent/quarantine-outdated-science-20260717` |
| `/Users/jakobfaber/Developer/scratch/worktrees/pipeline-archive-historical-diagnostics-20260720` | `codex/archive-historical-diagnostics-20260720` |


### 4. Standalone Workspace, Scratch, & Overleaf Worktrees

| Location / Path | Branch |
| :--- | :--- |
| `/private/tmp/faber2026-lfs-verify.pHnnuN` | `codex/freeze-anonymous-catalog-corpus-complete` |
| `/tmp/faber2026-lfs-verify.pHnnuN` | `codex/freeze-anonymous-catalog-corpus-complete` |
| `/tmp/ticket14-review.8DUSiy` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-expanded-foreground-tickets-02-03` | `codex/close-expanded-foreground-tickets-02-03` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dsa110-FLITS-law-lead` | `main` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-joint-scattering-repro` | `codex/joint-scattering-repro-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-phase6-runtime-release` | `codex/release-native-runtime` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-trust-publish` | `codex/resolve-trust-assessment` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-fix-skill-adoption-hook` | `codex/fix-skill-adoption-hook` |
| `/Users/jakobfaber/Developer/scratch/worktrees/flits-joint-tf-fits` | `joint/tf-fit-window-resolution` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-route-authority` | `codex/authoritative-pass-gates-published` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-free-alpha-publish` | `codex/resolve-free-alpha-reporting` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-visual-science-review` | `codex/visual-science-review-v2` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-publish` | `codex/unblock-wayfinder-tickets` |
| `/Users/jakobfaber/Developer/scratch/worktrees/flits-preserve-scintillation-methods-187` | `codex/preserve-scintillation-methods-187` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-tune-mcp-health` | `codex/fix-mcp-probe-limit` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-publish-policy-common-dir` | `fix/publish-policy-common-dir` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-trust-publish-v2` | `codex/resolve-trust-assessment-v2` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-runtime-admission` | `feat/mcp-status-health` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-wayfinder18` | `codex/wayfinder-18-law-host-redshifts` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-markedit-phase6` | `codex/cutover-markedit-runtime` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-rfi-route-failclosed` | `codex/fail-closed-rfi-route-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-live-cutover` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-markedit-node-cleanup` | `codex/fix-markedit-node-cleanup` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-fit-audit` | `codex/audit-fit-rails-pbf` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-host-dm-repair` | `codex/host-dm-repair` |
| `/Users/jakobfaber/Developer/scratch/worktrees/my-skillset-mattpocock-install` | `(detached HEAD)` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-skill-adoption` | `feat/skill-adoption-cutover` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-perplexity-watcher` | `fix/perplexity-watcher` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-component-counts` | `codex/audit-component-counts` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-final-runtime-teardown` | `codex/final-runtime-teardown` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-mcp-projector-safety` | `feat/mcp-projector-safety` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-protected-corpus-15` | `codex/protected-corpus-15` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-disable-census-mcp` | `codex/disable-census-mcp` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-robustness` | `codex/resolve-robustness-dispositions` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-deploy-source-root` | `codex/fix-deploy-source-root` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dsa110-FLITS-fit-audit` | `codex/audit-fit-rails-pbf` |
| `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-joint-scattering-owner-ci` | `codex/joint-scattering-owner-ci-20260722` |
| `/Users/jakobfaber/Developer/scratch/worktrees/dotfiles-disable-census-publish` | `codex/disable-census-mcp` |
| `/Users/jakobfaber/Developer/overleaf/Faber2026` | `main` |
| `/Users/jakobfaber/Developer/overleaf/olcli` | `main` |
| `/Users/jakobfaber/Developer/overleaf/Faber2024` | `main` |
| `/Users/jakobfaber/Developer/overleaf/Faber2024a-refrep` | `overleaf-2024-03-16-2255` |
| `/Users/jakobfaber/Developer/overleaf/branched-flow-projects` | `main` |


### 5. Remote `h17` Worktrees

| Location / Path | Branch |
| :--- | :--- |
| `/data/dsa110-continuum` | `agent/production-worktree-cutover` |
| `/data/dsa110-continuum-io-publish` | `codex/clarify-bright-source-label` |
| `/data/dsa110-continuum-worktrees/agent-monitor-recovery` | `agent/monitor-recovery` |
| `/data/dsa110-continuum-worktrees/agent-sault-weighted-coadd` | `agent/sault-weighted-coadd` |
| `/data/dsa110-continuum-worktrees/carta-public-readonly-159` | `research/carta-public-readonly-159` |
| `/data/dsa110-continuum-worktrees/continue-rejected-epochs` | `codex/continue-rejected-epochs` |
| `/data/dsa110-continuum-worktrees/epoch-gaincal-calibrator-selection` | `agent/epoch-gaincal-calibrator-selection` |
| `/data/dsa110-continuum-worktrees/epoch-gaincal-direct-first` | `agent/epoch-gaincal-direct-first` |
| `/data/dsa110-continuum-worktrees/epoch-gaincal-multifield-canary` | `codex/epoch-gaincal-multifield-canary` |
| `/data/dsa110-continuum-worktrees/phase-a` | `phase-c1-stage-events` |
| `/data/dsa110-continuum-worktrees/production-cutover` | `agent/production-worktree-cutover` |
| `/data/dsa110-continuum-worktrees/vlass-full-fallback` | `(detached HEAD)` |
| `/home/ubuntu/worktrees/t0audit-pr` | `ms/audit-standing-line-toa-note-20260719` |
| `/home/ubuntu/worktrees/flits-window-tuning` | `(detached HEAD)` |
| `/home/ubuntu/worktrees/joint-tf-fits` | `(detached HEAD)` |

