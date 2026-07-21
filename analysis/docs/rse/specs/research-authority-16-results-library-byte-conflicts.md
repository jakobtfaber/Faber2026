# Research: results-library real-byte conflicts

**Observed:** 2026-07-20 PDT / 2026-07-21 UTC  
**Scope:** Read-only adjudication for
[`Adjudicate the results-library real-byte conflicts`](../wayfinder/tickets/authority-16-adjudicate-results-library-byte-conflicts.md).  
**Parent authority:** `origin/main` at
`ef32cbb0113a50aa77f1c1fcf4c9b1f1f5ede82b`.
**Pipeline authority pin:**
`7d26b1f7d3747afebb0ed7064d3058d25fb33396`.
**Library root:** `/Users/jakobfaber/Data/Faber2026/results-library`.  
**Mutation:** none. No bytes were moved, linked, replaced, deleted, or trusted.

Concurrent Wayfinder work advanced `origin/main` after the first observation.
The result was rechecked after the adjudication merge at parent
`ef32cbb0113a50aa77f1c1fcf4c9b1f1f5ede82b`, which pins pipeline
`7d26b1f7d3747afebb0ed7064d3058d25fb33396`. The relevant tracked trees and
their clean manifests are unchanged from `ded8d195`.

## Verdict

Neither collision is a same-result overwrite problem.

- Both library directories are exact byte replicas of the two pre-relocation
  Git trees at pipeline commit
  `af78543d4747d339b9f13283b4b8528c91a71cb3`.
- The corresponding clean-checkout source directories contain only the
  post-relocation tracked control files.
- The canonical Mac checkout also contains later ignored working outputs:
  13 PDFs in the scintillation source and 289 files in `pipeline/results`.
  Those ignored trees have no complete independent byte replica or run receipt.
- Therefore the library trees are **historical snapshot replicas**; the
  canonical source trees are **mixed working/control surfaces**. Neither is a
  result authority. Scientific trust remains `provisional` and `mixed`.

Keep all four directories unchanged. The broad `materialize` instructions are
semantically wrong for these composite sources and must remain fail-closed.

## Reproduced gate

The focused dry-run still returns exactly two conflicts:

```text
scintillation.dsa-lorentzian-2026-07-07  -> would-conflict-both-real
dispersion.pipeline-results-root         -> would-conflict-both-real
2 conflict(s); resolve manually
```

Command:

```bash
python3 scripts/materialize_results_library.py --dry-run \
  --only scintillation.dsa-lorentzian-2026-07-07 \
  --only dispersion.pipeline-results-root
```

The guard is implemented in
[`materialize_results_library.py`](../../scripts/materialize_results_library.py)
and regression-tested in
[`test_results_library_repair.py`](../../tests/test_results_library_repair.py).

## Exact identities and manifests

The authoritative aggregate algorithm is `tree_manifest()` in
[`build_results_library_inventory.py`](../../scripts/build_results_library_inventory.py).
It hashes each regular file's relative path, size, and SHA-256 in deterministic
relative-path order. The four canonical live hashes were frozen before the
repair in
[`action-packet.json`](../certificates/results-library-repair-2026-07-20/action-packet.json)
and reproduced after the repair.

| Surface | Files | Bytes | Tree SHA-256 |
|---|---:|---:|---|
| canonical scintillation source | 17 | 1,686,569 | `721e5942f358086cc55b8f8d53eaf8c838a8870214455a75afdbef5f62e5d006` |
| scintillation library destination | 45 | 12,791,899 | `16823666dcc5f1e2e700e3c62026ab01b28e6487d1a50db884375cacdb9e86fb` |
| canonical dispersion source | 291 | 115,972,920 | `1f2b75ece0c028c5c208104e150a6294ca93231484178b99168c40cc0f113d06` |
| dispersion library destination | 75 | 27,177,361 | `09867d25a1047d97fc540db22446e75d16eaa103593ca75d52550c1e3d9a5c5e` |

Directory identity at observation:

| Surface | Inode | Mode | Directory mtime |
|---|---:|---|---|
| canonical scintillation source | `311786997` | `drwxr-xr-x` | `2026-07-17T00:53:51-0700` |
| scintillation library destination | `321971526` | `drwxr-xr-x` | `2026-07-15T19:23:20-0700` |
| canonical dispersion source | `310224232` | `drwxr-xr-x` | `2026-07-20T13:27:20-0700` |
| dispersion library destination | `321971932` | `drwxr-xr-x` | `2026-07-15T19:23:21-0700` |

### Clean-checkout baseline

An isolated clean checkout at the same pipeline pin has no ignored working
outputs. Its source manifests are:

| Clean source | Files | Bytes | Tree SHA-256 |
|---|---:|---:|---|
| scintillation | 4 | 879,616 | `116e3bbc18b037c4e11f54187f006598b4f1e1d30f1e901e65b78e05c7bc0e14` |
| dispersion | 2 | 3,256 | `7ed404992f01a4454f71a44d4a147bc91178dbc0883fe0f022a1369a8ecc9abe` |

This distinction matters: a clean-clone manifest alone would omit the live
canonical working outputs that make replacement unsafe.

## Exact byte differences

### Scintillation

- Four `oran_qualified/` files occur on both sides and are byte-identical.
- The canonical source alone has 13 ignored PDFs totaling 806,953 bytes: one
  summary and twelve per-burst Lorentzian-fit figures.
- The library alone has 41 files: `DSA_LORENTZIAN_FITS.md`, aggregate and
  per-burst JSON, the component CSV, and PNG/SVG campaign figures.
- No common file differs.

The 13 source-only PDFs are not byte-identical to the similarly named tracked
parent-manuscript PDFs; one has no parent counterpart. No complete independent
byte copy was found. They are preserved working outputs, not a replica.

### Dispersion

- `README.md` is byte-identical.
- `joint_fit_summary.md` differs: the canonical source is a 399-byte quarantine
  tombstone with SHA-256
  `cb3fbc4182d662e7c8b572a0ce2eb67301ff122472d8ce286fa1f956df292f46`;
  the library holds the 2,656-byte pre-relocation summary with SHA-256
  `41122c7b56b13a1535b47daf2f537515472f3c65d8c0de0fa0a9f2986ce034e5`.
- The canonical source alone has 289 ignored files totaling 115,969,664 bytes:
  DM campaign panels, injection diagnostics, smoke/full-run products,
  DM-power figures, dynamic spectra, and host-DM posterior products.
- The library alone has 73 pre-relocation files: DM-phase products and metrics,
  sightline/galaxy outputs, budget artifacts, and review manifests.

No complete independent byte copy or unified production receipt was found for
the 289 source-only files. They remain an at-risk working tree.

## Production and recovery proof

Pipeline commit
`221f26a2aca10ad264b081acf3501ec6f85977cf` (`chore(results): relocate
campaign products to results library (#189)`) deleted the bulk tracked files
from both repository paths. Its immediate parent
`af78543d4747d339b9f13283b4b8528c91a71cb3` contains 45 scintillation files
and 75 dispersion files at those paths.

For every destination file, the on-disk Git blob identifier equals the blob
identifier in `af78543` and the relative-path sets are identical. Equivalently:

```bash
git -C pipeline archive af78543d4747d339b9f13283b4b8528c91a71cb3 \
  analysis/scintillation-dsa-lorentzian-2026-07-07/results results
diff -qr <archive>/analysis/scintillation-dsa-lorentzian-2026-07-07/results \
  /Users/jakobfaber/Data/Faber2026/results-library/scintillation/2026-07-07_dsa-lorentzian
diff -qr <archive>/results \
  /Users/jakobfaber/Data/Faber2026/results-library/dispersion/pipeline-results-root
```

Both comparisons are empty. Git history, including the GitHub remote, is an
independent exact recovery source for both library snapshots.

The `Faber2026-science-gates` preservation worktree supplies another local
copy: its 45-file scintillation tree has the same canonical hash, and its
dispersion tree contains the same 75-file snapshot plus one pointer document.
Git remains the stronger immutable recovery identity.

The current tracked leftovers are recoverable from pipeline commit `7d26b1f7`
(and identically from `ded8d195`).
The current ignored canonical outputs are not Git objects and cannot be
assigned a producing commit merely because their generating code is pinned.
Their complete recovery remains unproved.

## Consumers

The two catalog rows in
[`results_library_catalog.yaml`](../../scripts/results_library_catalog.yaml)
currently label the sources `materialize`, with trust `provisional` and
`mixed`. Their notes already distinguish bulk library products from CI-tracked
files, but the broad source paths erase that distinction.

Known consumers include:

- `pipeline/analysis/RESULTS_LIBRARY.md` and `pipeline/RESULTS_LIBRARY.md`,
  which describe the relocation;
- `scripts/build_provisional_propagation_tables.py`, which expects the
  scintillation component CSV through the repository path;
- `scripts/figure_review.py` and `figures/catalog.yaml`, which consume the
  Oran qualification and DSA summary evidence;
- dispersion figure/budget declarations under `figures/catalog.yaml`;
- pipeline tests that validate the quarantined historical joint summary rather
  than adopting the library summary.

These consumers need explicit snapshot or working-source selection. A broad
directory overlay would silently mix generations.

## Custody and trust classification

| Surface | Custody role | Scientific state |
|---|---|---|
| scintillation library directory | exact local replica of `af78543` historical snapshot | provisional; not manuscript-adopted by this decision |
| canonical scintillation source | mixed tracked control files plus unreceipted ignored working figures | unclassified working output; Oran sub-tree retains its separate qualification evidence |
| dispersion library directory | exact local replica of `af78543` historical snapshot | mixed; no claim promotion |
| canonical dispersion source | tracked README/tombstone plus unreceipted ignored working products | unclassified working output; not an authority or coherent replica |

Per the ratified data/results policy, Git governs claims and Drive governs
receipted bulk bytes. The local results library is a navigation replica. Byte
identity proves recoverability, not scientific validity.

## Non-overwriting disposition

1. Keep all four current directories unchanged.
2. Record both existing library slots as immutable historical snapshots of
   pipeline commit `af78543`, with their expected tree hashes above.
3. Do not treat either live repository directory as the materialization source
   for those historical slots.
4. In a later implementation, replace these two broad `materialize` semantics
   with a non-mutating snapshot/inventory representation tied to commit,
   relative path, and tree hash. No existing library path is renamed or
   overwritten.
5. Before any relink or replacement could hide the canonical sources, preserve
   the 13 and 289 ignored files in a non-overwriting, receipt-bound hold and
   verify an independent copy. This adjudication does not authorize that copy.
6. Retire broad `pipeline/results` materialization; any later entry must name
   one coherent campaign or snapshot.
7. Give any later working-result publication a new identifier and an absent,
   versioned destination. Before copying it, require a complete manifest,
   producing-code/run receipt, independent recovery copy, and trust label.
8. Keep materialization fail-closed until that catalog change is implemented
   and tested. Do not add compatibility links.

This is a custody decision only. It does not authorize copying, movement,
relinking, deletion, trust promotion, or manuscript changes.

## Rollback and drift packet

No data rollback is needed for this adjudication because it performs no data
mutation. Any later implementation must freeze this preimage and stop on any
drift:

```yaml
parent_commit: ef32cbb0113a50aa77f1c1fcf4c9b1f1f5ede82b
pipeline_commit: 7d26b1f7d3747afebb0ed7064d3058d25fb33396
historical_recovery_commit: af78543d4747d339b9f13283b4b8528c91a71cb3
slots:
  scintillation.dsa-lorentzian-2026-07-07:
    canonical_source: {files: 17, bytes: 1686569, sha256: 721e5942f358086cc55b8f8d53eaf8c838a8870214455a75afdbef5f62e5d006}
    clean_source: {files: 4, bytes: 879616, sha256: 116e3bbc18b037c4e11f54187f006598b4f1e1d30f1e901e65b78e05c7bc0e14}
    library: {files: 45, bytes: 12791899, sha256: 16823666dcc5f1e2e700e3c62026ab01b28e6487d1a50db884375cacdb9e86fb}
  dispersion.pipeline-results-root:
    canonical_source: {files: 291, bytes: 115972920, sha256: 1f2b75ece0c028c5c208104e150a6294ca93231484178b99168c40cc0f113d06}
    clean_source: {files: 2, bytes: 3256, sha256: 7ed404992f01a4454f71a44d4a147bc91178dbc0883fe0f022a1369a8ecc9abe}
    library: {files: 75, bytes: 27177361, sha256: 09867d25a1047d97fc540db22446e75d16eaa103593ca75d52550c1e3d9a5c5e}
forbidden:
  - overwrite or merge either real directory
  - replace a real directory with a symlink
  - delete or move bytes
  - infer trust from byte identity
  - change manuscript claims
```

For a future repository-only catalog change, rollback is a scoped Git revert;
the four data-tree hashes must remain unchanged before and after. Any future
copy requires its own non-overwriting destination and receipt-driven rollback.

## Reproducibility

The minimal clean reproduction used the isolated Wayfinder worktree after
merging the adjudication into parent `ef32cbb0`, with its clean detached
pipeline submodule at `7d26b1f7`, macOS 27.0, and Python 3.12.13 from the
`py312` Conda environment.
No random process, accelerator, or numerical tolerance is involved.

Commands reproduced from that clean checkout:

```bash
/Users/jakobfaber/.conda/envs/py312/bin/python \
  scripts/materialize_results_library.py --dry-run \
  --only scintillation.dsa-lorentzian-2026-07-07 \
  --only dispersion.pipeline-results-root

/Users/jakobfaber/.conda/envs/py312/bin/python -m pytest -q \
  tests/test_results_library_repair.py

git -C pipeline ls-tree -r af78543d4747d339b9f13283b4b8528c91a71cb3 \
  analysis/scintillation-dsa-lorentzian-2026-07-07/results results
```

Results:

- focused dry-run: expected exit 1 with exactly the two
  `would-conflict-both-real` rows;
- focused tests: 6 passed;
- clean Git-blob comparison: all 45 scintillation and 75 dispersion library
  files exactly match `af78543` by path and blob identity;
- live canonical manifest reproduction: all four hashes match the frozen
  repair action packet;
- full science tests: 209 passed, 1 expected failure;
- `git diff --check`: passed.

The clean checkout intentionally reproduces the 4-file and 2-file tracked
baselines. The 17-file and 291-file manifests are live-state evidence from the
canonical working checkout, not claims that ignored files appear in a clone.
