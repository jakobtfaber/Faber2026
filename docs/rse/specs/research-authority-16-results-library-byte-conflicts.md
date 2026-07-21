# Research: authority-16 results-library byte conflicts

**Date:** 2026-07-21  
**Scope:** Read-only review artifact for
[`authority-16`](../wayfinder/tickets/authority-16-adjudicate-results-library-byte-conflicts.md).
No bytes moved, linked, replaced, deleted, or trusted.  
**Parent state:** `33cf9fe1c10acccaa44c59a59e645c06776ebf3d`
(`origin/main`, clean).  
**Pipeline state:** `c6111390ce9c159483a844417f5fd9d187e13f5b`
(`pipeline` gitlink, clean detached submodule).  
**Observed library root:** `/Users/jakobfaber/Data/Faber2026/results-library`.

## Question

For `scintillation.dsa-lorentzian-2026-07-07` and
`dispersion.pipeline-results-root`, both catalog source and library destination
are real directories. Establish exact manifests, byte differences, producing
commits, consumers, trust states, recovery evidence, and a non-overwriting
disposition with rollback packet.

## Method

Read-only commands only:

```bash
python3 scripts/kb search "results-library byte conflicts scintillation dsa lorentzian dispersion pipeline results root authority"
python3 scripts/materialize_results_library.py --dry-run \
  --only scintillation.dsa-lorentzian-2026-07-07 \
  --only dispersion.pipeline-results-root
find <tree> -type f -print0 | sort -z | while ... shasum -a 256 ...
git -C pipeline log --name-status -- <source>
git -C pipeline archive 221f26a^ ... | tar -x -C "$tmp"
diff -qr "$tmp/<historical-source>" "<library-slot>"
```

The knowledge-base command returned no ranked hit for this exact conflict.

## Gate Reproduction

`materialize_results_library.py --dry-run --only ...` returned:

```text
scintillation.dsa-lorentzian-2026-07-07  analysis/scintillation-dsa-lorentzian-2026-07-07/results  ->  would-conflict-both-real
dispersion.pipeline-results-root         results  ->  would-conflict-both-real
2 conflict(s); resolve manually
```

This independently reproduces the ticket's fail-closed gate. No write command
was run.

## Exact Tree Manifests

The exact per-file manifest format was:

```text
<sha256>  <size_bytes>  <relative_path>
```

Aggregate fingerprints below are SHA-256 hashes of the sorted manifest text,
not data-file hashes.

| Slot | Tree | Files | Disk | Manifest hash |
|---|---:|---:|---:|---|
| `scintillation.dsa-lorentzian-2026-07-07` | `pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/results` | 4 | 868 KiB | `026a5d1f5a1c3c7fe329ea1736f94468fc51ac91060c6af9fc1f3a2ddbce9e08` |
| `scintillation.dsa-lorentzian-2026-07-07` | `/Users/jakobfaber/Data/Faber2026/results-library/scintillation/2026-07-07_dsa-lorentzian` | 45 | 12,584 KiB | `684c7d5294f4a09b47585446188ebd570026e4145ac8f62fc61bc8595644a360` |
| `dispersion.pipeline-results-root` | `pipeline/results` | 2 | 8 KiB | `0d3578df5f4d6720bcf6fc6c1bb255021a41a01bb220c71060f2e5d0859196b6` |
| `dispersion.pipeline-results-root` | `/Users/jakobfaber/Data/Faber2026/results-library/dispersion/pipeline-results-root` | 75 | 26,708 KiB | `f0ab01b2f79498fd917ca3a5c087854b904c5c9ec8d69f0c522a94e774bd8719` |

Directory identity at observation:

| Tree | Type/mode | Inode | Directory mtime |
|---|---|---:|---|
| repo scintillation source | `Directory drwxr-xr-x` | `327357401` | `2026-07-20T23:06:08-0700` |
| library scintillation slot | `Directory drwxr-xr-x` | `321971526` | `2026-07-15T19:23:20-0700` |
| repo dispersion source | `Directory drwxr-xr-x` | `327357798` | `2026-07-20T23:06:08-0700` |
| library dispersion slot | `Directory drwxr-xr-x` | `321971932` | `2026-07-15T19:23:21-0700` |

### Current Scintillation Source Manifest

```text
3ef5465827a59c1f97cf001cb99bd92e7b846b45234be59b1630bf9172b6a4e1  747  oran_qualified/figures.review.json
efaae17332939497198b83b07674aaa766d0619d2936c4436a42c693fd83fdd6  110140  oran_qualified/figures/oran_dsa_calibrated_measurement.png
b1a95b8eddbf9ab4137d054efa688d60a959b373730903699e4398b29f5bbe0b  2063  oran_qualified/MEASUREMENT.md
e0c455e1c73e1a9bd24bbc833029cd5506d1d710fe18585251094b48d11e89f9  766666  oran_qualified/validation.json
```

### Current Dispersion Source Manifest

```text
cb3fbc4182d662e7c8b572a0ce2eb67301ff122472d8ce286fa1f956df292f46  399  joint_fit_summary.md
1daea1a0ef1d4e7487c9ca16daa58a5ffc70c5633065bdb110348abf30d48448  2857  README.md
```

### Library-only Payloads

The scintillation library slot has 41 files not present in the current source:
the campaign catalog files, `DSA_LORENTZIAN_FITS.md`,
`dsa_lorentzian_components.csv`, `dsa_lorentzian_fits.json`, per-burst
`*_dsa_lorentzian_fits.json`, and 24 PNG/SVG figure files under `figures/`.
The current source has no repo-only file; all 4 repo-side files are also in the
library with identical hashes.

The dispersion library slot has 73 files not present in the current source:
DM phase products, smoke metrics, per-burst galaxy CSVs, mass-profile PNGs,
sightline PNGs, figure manifests/reviews, budget files, and survey coverage.
`README.md` is identical on both sides. `joint_fit_summary.md` exists on both
sides but differs:

| Path | Repo hash/size | Library hash/size | Meaning |
|---|---|---|---|
| `joint_fit_summary.md` | `cb3fbc4182d662e7c8b572a0ce2eb67301ff122472d8ce286fa1f956df292f46` / 399 bytes | `41122c7b56b13a1535b47daf2f537515472f3c65d8c0de0fa0a9f2986ce034e5` / 2,656 bytes | Current repo file is a quarantine tombstone; library file is the pre-relocation bulk summary. |

## Producing Commits

`pipeline` commit
`221f26a2aca10ad264b081acf3501ec6f85977cf` (`2026-07-15T20:10:31-07:00`,
`chore(results): relocate campaign products to results library (#189)`) deleted
the bulk files from both source trees.

The immediate parent
`af78543d4747d339b9f13283b4b8528c91a71cb3` (`2026-07-15T13:23:36-07:00`,
merge of pull request #188) contains the full pre-relocation source trees:
120 files across the two paths.

The current `pipeline` pin
`c6111390ce9c159483a844417f5fd9d187e13f5b` retains only the repo-side leftovers:

- `analysis/scintillation-dsa-lorentzian-2026-07-07/results/oran_qualified/*`
  from `cc447f7` / `e462478`;
- `results/README.md`;
- `results/joint_fit_summary.md`, later changed by
  `23fbd295a25aaa80e352ecf0c08287ba4f60a885`
  (`chore(science): quarantine superseded result products (#202)`).

## Independent Recovery Evidence

The strongest recovery copy is `pipeline` git history, not the stale inventory:

```text
git -C pipeline archive 221f26a^ analysis/scintillation-dsa-lorentzian-2026-07-07/results results
diff -qr <archive>/analysis/scintillation-dsa-lorentzian-2026-07-07/results \
  /Users/jakobfaber/Data/Faber2026/results-library/scintillation/2026-07-07_dsa-lorentzian
diff -qr <archive>/results \
  /Users/jakobfaber/Data/Faber2026/results-library/dispersion/pipeline-results-root
```

Both `diff -qr` commands produced no output. Therefore the current library slots
are exact byte replicas of the pre-relocation source trees at `221f26a^`.

The stale external inventory is weaker evidence: it was generated
`2026-07-20T14:09:06Z` from deleted worktree
`/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-jointtf-grok-revalidation`,
but still records these two slots as tracked materializations with sizes
`868K` and `8.0K`.

Additional local scratch worktrees contain current `pipeline/results` checkouts,
but those are not independent bulk recovery copies; they mirror the post-
relocation repo leftovers.

## Consumers

### Scintillation Slot

Current consumers of repo-side or cataloged scintillation products:

- Catalog entry:
  `scripts/results_library_catalog.yaml:58-66` says mode `materialize`, trust
  `provisional`, source
  `analysis/scintillation-dsa-lorentzian-2026-07-07/results`, and notes that
  `oran_qualified/` stays git-tracked for figure approval.
- Results-library pointer:
  `pipeline/analysis/RESULTS_LIBRARY.md:3-13` says campaign result trees are
  materialized under `$FABER2026_RESULTS_LIBRARY` and maps this campaign to
  `scintillation/2026-07-07_dsa-lorentzian`.
- Parent figure catalog:
  `figures/catalog.yaml:190-212` consumes
  `oran_qualified/figures/oran_dsa_calibrated_measurement.png` as a pipeline
  qualification product, not a manuscript figure.
- Parent figure catalog:
  `figures/catalog.yaml:239-257` keeps `dsa_lorentzian_summary` discoverable but
  `manuscript: false`, `clone_ok: false`, and notes it was removed from the
  compiled manuscript on 2026-07-17.
- Provisional table builder:
  `scripts/build_provisional_propagation_tables.py:13-15,117-120` reads
  `dsa_lorentzian_components.csv` from the repo source path; this currently
  fails unless a later repair restores a link or adjusts the source.
- Figure-review provenance:
  `scripts/figure_review.py:168-170` names the component catalog, fit catalog,
  and Oran qualification files as evidence inputs.

### Dispersion Slot

Current consumers of repo-side or cataloged dispersion products:

- Catalog entry:
  `scripts/results_library_catalog.yaml:89-97` says mode `materialize`, trust
  `mixed`, source `results`, and notes bulk `dm_phase` content should live in
  the library while `joint_fit_summary.md` stays git-tracked.
- Results-library pointer:
  `pipeline/RESULTS_LIBRARY.md:1-18` says bulk products for `pipeline/results`
  live under `$FABER2026_RESULTS_LIBRARY/dispersion/pipeline-results-root/`.
- Parent figure catalog:
  `figures/catalog.yaml:75-114` expects
  `pipeline/results/sightline_dm_scattering_budget.csv` as an intermediate for
  budget figures; that file exists only in the library slot at this observation.
- Pipeline tests:
  `pipeline/tests/test_joint_summary_reproducible.py:1-25` now validates the
  quarantined legacy summary under `quarantine/2026-07-17-outdated-science/`,
  not the library summary.
- Pipeline README:
  `pipeline/results/README.md:1-18` still describes historical `results/bursts`
  layout and is not a current bulk manifest.

## Trust States

| Slot | Catalog trust | Evidence trust | Disposition trust |
|---|---|---|---|
| `scintillation.dsa-lorentzian-2026-07-07` | `provisional` | Byte identity to `221f26a^` proven; scientific adoption not proven. DSA-only summary is not a manuscript figure. | `replica of pre-relocation bulk result plus current repo-side qualification leftovers`; not authority; unresolved repair target. |
| `dispersion.pipeline-results-root` | `mixed` | Byte identity to `221f26a^` proven for library; current repo summary tombstone conflicts with the library summary. | `replica of pre-relocation bulk result plus current repo-side tombstone`; not authority; unresolved repair target. |

No owner gate, manuscript claim, Figure 3 state, redshift/budget choice, or
scientific trust state changes here.

## Disposition

Recommended non-overwriting disposition:

1. Keep both current source directories exactly as they are.
2. Keep both library directories exactly as they are.
3. Classify the library directories as recovered exact replicas of the
   `221f26a^` pre-relocation bulk source trees.
4. Classify the current repo directories as post-relocation control-plane
   leftovers:
   `oran_qualified/` for scintillation and a quarantine tombstone plus README
   for dispersion.
5. Do not re-run materialization for these slots until the later repair wave has
   an exact action packet that either uses a non-overwriting archive directory
   or turns the repo-side source into a symlink only after exact rollback proof.
6. Leave trust fail-closed: `provisional` and `mixed` are catalog labels, not
   claim-level acceptance.

## Rollback Packet For Later Repair

Before any future repair touches these paths, record this packet and stop on
drift:

```yaml
parent_commit: 33cf9fe1c10acccaa44c59a59e645c06776ebf3d
pipeline_commit: c6111390ce9c159483a844417f5fd9d187e13f5b
historical_recovery_commit: af78543d4747d339b9f13283b4b8528c91a71cb3
library_root: /Users/jakobfaber/Data/Faber2026/results-library
slots:
  scintillation.dsa-lorentzian-2026-07-07:
    source: pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/results
    destination: /Users/jakobfaber/Data/Faber2026/results-library/scintillation/2026-07-07_dsa-lorentzian
    source_manifest_hash: 026a5d1f5a1c3c7fe329ea1736f94468fc51ac91060c6af9fc1f3a2ddbce9e08
    destination_manifest_hash: 684c7d5294f4a09b47585446188ebd570026e4145ac8f62fc61bc8595644a360
    recovery: git archive 221f26a^ source equals destination by diff -qr
    rollback_rule: restore exact pre-action directory from non-overwriting archive or git archive; never overwrite without hash match
  dispersion.pipeline-results-root:
    source: pipeline/results
    destination: /Users/jakobfaber/Data/Faber2026/results-library/dispersion/pipeline-results-root
    source_manifest_hash: 0d3578df5f4d6720bcf6fc6c1bb255021a41a01bb220c71060f2e5d0859196b6
    destination_manifest_hash: f0ab01b2f79498fd917ca3a5c087854b904c5c9ec8d69f0c522a94e774bd8719
    recovery: git archive 221f26a^ source equals destination by diff -qr
    rollback_rule: restore exact pre-action directory from non-overwriting archive or git archive; never overwrite without hash match
forbidden:
  - delete bytes
  - replace directories in place
  - promote trust
  - change manuscript claims
  - change pipeline gitlink as a side effect
```

## Synthesis

The two conflicts are not evidence of lost bytes. They are expected collisions
between a post-relocation repo checkout and an external library that still holds
the exact pre-relocation bulk result trees. The correct near-term state is
`unresolved conflict, recovery proven, no mutation authorized`.
