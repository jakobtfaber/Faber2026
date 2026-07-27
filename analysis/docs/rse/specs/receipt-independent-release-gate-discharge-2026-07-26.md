# Receipt: independent Figure 3 release-gate blocker discharge

- Date: 2026-07-26
- Objective: independently discharge the seven adversarial-review blockers on
  the Figure 3 expanded-foreground release gate, and bring the gate to a
  landable state bound to the current parent commit and pipeline pin.
- Phase: verification. No repair, promotion, retirement, or pin change was
  performed.
- Status: **VERIFIED** for the verification work. The gate itself remains
  **failed / fail_closed** on four substantive blockers.

## Source snapshot

| Item | Value |
|---|---|
| Manuscript parent (`Faber2026`) | `ac004ece8f22bce3b117099a2f23e05b5abe6528`, branch `main`, clean |
| Parent `pipeline` gitlink | `78b448f05946923ef1c0acc19068fed313911ec6` |
| Parent `analysis` gitlink | `65a771492e23e1f9b045cfc851d1808569893194` |
| Analysis branch | `codex/auto-set-expanded-independent-validation`, merged with `origin/main` at `a30b516`, merge commit `d41629aca240f85eb0dc8f53ba64086cadb5ad35` |
| Pipeline checkout used | Local `--shared` clone of `dsa110-FLITS`, detached at `78b448f0`, clean working tree |
| Verification time | 2026-07-26 |

The `dsa110-FLITS` and `Faber2026` repositories were used read-only. No
worktree was added, removed, or pruned in either. No submodule pin was changed.

## Commands

Source replay, run at three commit bindings through a driver that calls
`scripts/verify_foreground_registry_sources.py:verify` directly:

```
verify(analysis_repo, pipeline_repo,
       analysis_commit=<A>, pipeline_commit=<P>)
```

| Binding (analysis / pipeline) | rows | source_verified | discrepancies | gate_pass |
|---|---:|---:|---:|---|
| `fe73689c` / `c913175e` (previous gate) | 52 | 52 | 0 | false — worktree differs from pinned blobs |
| `fe73689c` / `78b448f0` (**current pin**) | 52 | **46** | **6** | false |
| `d41629ac` / `f5c1d1f3` (pipeline main) | 52 | 52 | 0 | **true** |

Registry replay, re-executed rather than read:

```
python3 scripts/replay_frozen_nine_sightline_corpora.py \
  --pipeline-dir <pinned pipeline checkout> --output <report>
```

Release gate:

```
python3 scripts/validate_expanded_foreground_independent_release_gate.py \
  --pipeline-repo <pinned pipeline checkout> \
  --manuscript-repo <Faber2026>
```

## Outputs and checksums

Recomputed from bytes; eleven of twelve pinned artifacts matched.

| Artifact | Pinned before | Recomputed |
|---|---|---|
| `…/nine-sightline-registry-replay-2026-07-23/replay.json` | `a3ebd607…` | `f6b5d7bf…` (**drift**; gate updated) |
| `…/foreground-source-verification-2026-07-22/replay.json` | `ef3c5e01…` | matches |
| `…/decision-2026-07-23-figure-approval-inventory.md` | `b12443b4…` | matches |
| `…/candidates/fig3-halo-grid.pdf` | `45017274…` | matches |
| seven `…/provenance/*` evidence files | as pinned | all match |

New evidence receipt, added by this work:

| Path | SHA-256 |
|---|---|
| `docs/rse/specs/evidence/foreground-source-verification-pinned-pipeline-2026-07-26/replay.json` | `6a5c3df4a808fdc8ff855432ff42e5df53976513846e4c8e353f5542dee66f2d` |

Registry snapshots, computed from pipeline blobs:

| Pipeline commit | `intervening_census_registry.csv` SHA-256 |
|---|---|
| `f3c8d22a` (Figure 3 build input) | `f35dd8beb733b08dbb38894e5df6fc04af13fc731fd57c3f61dfc8441afd6fbc` |
| `78b448f0` (**current pin**) | `96bfd32302b00df943ba998ba3bf6557f3d8c06d882079cad1a5c9846d47d06a` |
| `c913175e`, `f5c1d1f3` | `96bfd323…` (identical to the pin) |

Figure 3 promotion state:

| Artifact | SHA-256 |
|---|---|
| Installed `Faber2026/figures/sightline_halo_grid.pdf` | `cd719ef203b5f17709db1a9229d7f8fa74b26ee693090bb252632846a29edc00` |
| Staged candidate `fig3-halo-grid.pdf` | `45017274a7e3d60cf6918d72c3e89558c0e9d50e27427d39a216547c4999fa6c` |

They differ, and `figure_review/approval_receipts/fig3-halo-grid.json` does not
exist. No promotion occurred.

## Verification method and evidence

1. **Independent reproduction.** Both replays were re-executed from a clean
   pinned checkout, not read from their reports. The registry replay
   reproduced every published field exactly: 52 rows, 49 finite-host rows, 7
   duplicate checks passed, empty verdict and budget mismatch arrays, and all
   four input hashes.
2. **Comparison against the producing artifact.** The Figure 3 build record's
   `registry_sha256` was compared against the registry blob at the pinned
   pipeline commit, which is what exposed the stale snapshot.
3. **Content extraction.** Text extracted from the candidate and installed
   Figure 3 PDFs confirms both still print `FRB 20230913A` and `FRB 20240203A`.
4. **Adversarial self-check.** Two tests assert that neither flipping `status`
   to `passed` while retaining blockers, nor emptying the blocker list, can
   pass the gate.

## Findings

### 1. The previous gate was bound to an unreachable pipeline commit

`c913175e` is titled "foreground: freeze six missing source identities" but is
**not an ancestor of the pipeline main line**. It is a pre-landing form of the
change that landed as `f5c1d1f3` (pipeline #231). The previous gate's
52/52 source-verification evidence was produced against that commit, so it
described a lineage the manuscript does not pin.

### 2. Source verification is 46/52 at the commit the manuscript actually pins

At `78b448f0` the six identity-only rows have no frozen authoritative source
rows:

| Row | Discrepancy |
|---|---|
| `oran/halo/195393180643665627` | redshiftless PS1-STRM ledger semantics mismatch; payload row missing |
| `wilhelm/halo/194453151328186646` | same |
| `hamilton/halo/192943050854547067` | same |
| `chromatica/halo/196673126794497004` | same |
| `isha/halo/WISEA J044538.83+701843.3` | manual extension lacks frozen authoritative source rows |
| `oran/halo/WISEA J211150.32+724807.8` | same |

Verdict and budget replays are clean at every binding tested. The shortfall is
pin-lag, not a data defect: the same replay is 52/52 with zero discrepancies at
pipeline main `f5c1d1f3`.

### 3. Figure 3 was built from a superseded registry snapshot

The candidate's build record pins registry `f35dd8be…` at pipeline `f3c8d22a`
(pipeline #223). The pinned registry is `96bfd323…`. The two differ in exactly
one field across seven rows:

| Row | Figure 3 build | Current pin |
|---|---|---|
| `chromatica` (3 halo rows) | `FRB 20240203A` | `FRB 20240203D` |
| `freya` (2 halo rows) | `FRB 20230325A` | `FRB 20230325C` |
| `hamilton` (2 halo rows) | `FRB 20230913A` | `FRB 20230913G` |

No redshift, mass, radius, impact-parameter, verdict, or budget field differs.
The correction was adopted in pipeline #225, `6057501d`, "data: adopt Verdi
source-event identifiers" — which is also the `source_verification_base_commit`
recorded in the registry replay evidence.

The consequence is presentational but publication-relevant: both the candidate
and the **currently installed manuscript figure** print two superseded
transient identifiers.

## Changes made

- `scripts/verify_foreground_registry_sources.py`: added `--pipeline-commit`
  and `--analysis-commit`, defaulting to the previous constants.
- `scripts/validate_expanded_foreground_independent_release_gate.py`: replays
  at the commits the gate declares rather than the verifier's constants;
  verifies the manuscript checkout's `HEAD` and `pipeline` gitlink against the
  recorded commits; verifies the pinned registry blob at the pinned pipeline
  commit; rejects a Figure 3 candidate built from an unpinned registry
  snapshot; reports the replayed row and discrepancy counts explicitly.
- `docs/rse/specs/validation-expanded-foreground-independent-release-gate.json`:
  rebound to `ac004ece` / `78b448f0`; corrected the drifted registry-replay
  hash and pipeline commit; added the pinned-registry and Figure 3 build
  snapshot expectations; expanded the blocker list from two to four.
- `docs/rse/specs/evidence/foreground-source-verification-pinned-pipeline-2026-07-26/replay.json`:
  new receipt, the independent replay at the current pin.
- `tests/test_expanded_foreground_independent_release_gate.py`: four new tests;
  one existing integration assertion corrected from an untrue 52/52 claim.
- `ADVERSARIAL_REVIEW_BLOCKERS.md` and the wayfinder ticket: corrected, with
  evidence.

Nothing was promoted. The installed Figure 3 bytes, the pipeline gitlink, and
the expanded-catalog gate were not modified.

## Failures and retries

The neighbouring `tests/test_replay_frozen_nine_sightline_corpora.py` exceeds a
two-minute budget because it re-runs the full corpus replay; it was run
separately rather than alongside the fast suite.

## Preliminary, blocked, and stale findings

- **STALE, now corrected:** the ticket's "current source replay verifies 52/52
  rows" was true only for the unreachable `c913175e` binding.
- **STALE, unmodified:** the 2026-07-23 approval inventory describes the local
  Overleaf working copy, which was retired on 2026-07-25. The owner decision it
  records ("none approved") is unaffected, so the document was left as the
  owner wrote it.

## Owner approvals

None sought or granted during this work. This was verification only.

## Actions still prohibited

Promoting Figure 3, promoting scientific trust, saying `Verified`, changing the
pipeline pin, merging this pull request, and modifying the expanded-catalog
gate.

## Final disposition

The gate is landable as a corrected, honestly failing gate. Four blockers
stand, none dischargeable by verification:

1. `expanded-catalog-gate-not-passed` — needs the catalog repair lane.
2. `source-verification-incomplete` — needs a pipeline pin bump to `f5c1d1f3`
   or later. **Owner decision.**
3. `figure3-registry-snapshot-stale` — needs Figure 3 regenerated from the
   pinned registry. **Owner decision**, and it also implicates the figure
   already installed in the manuscript.
4. `figure3-owner-approval-missing` — needs an owner visual review.
