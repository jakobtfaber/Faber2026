# Repo knowledge base (`scripts/kb`)

Hybrid-retrieval search over everything in this repo, modelled on the
[Cerebras internal knowledge base](https://www.cerebras.ai/blog/how-we-built-our-knowledge-base)
("extract in place, unified schema, hybrid retrieval") at single-repo scale.
No server, no API costs: one SQLite file at `.kb/kb.sqlite3` (gitignored).

## Quick start

```sh
pip install fastembed numpy      # optional but recommended (semantic search)
make kb-index                    # build/refresh the index (incremental)
python3 scripts/kb search "why did the DM budget priors change"
python3 scripts/kb search "screen distance constraint" --source refs -k 5
python3 scripts/kb stats
```

First `kb index` with fastembed downloads the embedding model (~130 MB,
BAAI/bge-small-en-v1.5, runs locally via ONNX) and embeds ~15k chunks —
a few minutes on Apple Silicon. Re-indexing is incremental: only changed
documents are re-chunked and re-embedded.

Without fastembed/numpy everything still works as BM25 full-text search
(`--fts-only` forces this). Tests (`tests/test_kb.py`) cover the FTS path
only, so CI needs no ML dependencies.

## Sources (unified schema: one `documents`/`chunks` table pair)

| source     | what                                                            | ref format        |
| ---------- | --------------------------------------------------------------- | ----------------- |
| `docs`     | root/docs/pipeline markdown, `sections/*.tex`, `main.tex`, `pipeline/exports/*.tex`, vendored READMEs | repo-relative path |
| `tickets`  | `docs/rse/wayfinder/tickets/*.md` (+Status/Assignee/Blocked-by) | repo-relative path |
| `git`      | commits: parent repo **and** `pipeline/` (FLITS) submodule; PRs via `gh` when installed | sha / `pipeline@sha` / `PR#n` |
| `code`     | function/class-level chunks, path-allowlisted (`kb/config.py`); incl. `pipeline/{notebooks,external}`, `.ipynb` at cell level (outputs skipped) | repo-relative path |
| `config`   | pipeline YAML (telescopes, sampler, bursts, manifests, envs)    | repo-relative path |
| `refs`     | `bib/refs.bib` + Zotero-enriched `bib/references_library.json`  | citekey           |
| `obsidian` | personal vault — off until `OBSIDIAN_VAULT` set in `kb/config.py` | vault-relative path |

Adding a source = one generator in `scripts/kb/adapters.py` + registry entry.

## Retrieval

Two rank lists per query — FTS5 BM25 (porter stemming) and cosine over
L2-normalised bge-small embeddings — fused by reciprocal rank fusion,
`score = Σ 1/(60 + rank)`, matching Cerebras' k=60. Each hit reports which
signals found it (`fts`, `vec`, or `fts+vec`). Paraphrase queries are the
reason embeddings earn their keep: "cosmic baryon census from dispersion
measures" finds Macquart2020/McQuinn2014 with zero keyword overlap.

Deliberately **not** built (single-owner corpus; add only if pain appears):
LLM distillation per document, per-thread bursting, age-decay ranking,
rerankers, planner/executor synthesis.

## Cited-references library

`scripts/kb_refs_sync.py` matches every `bib/refs.bib` entry against the
running Zotero desktop (local API, DOI-then-title matching) and writes
`bib/references_library.json` (committed) with abstracts + Zotero keys.
The Zotero collection **Faber2026-cited-references** mirrors the bib file
(all 63 entries as of 2026-07-19). After adding a citation:

```sh
make kb-refs-sync   # requires Zotero desktop running
```

If a new entry is missing from Zotero, import it there first (the sync
reports unmatched keys).
