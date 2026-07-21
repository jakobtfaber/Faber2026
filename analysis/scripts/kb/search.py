"""Hybrid retrieval: FTS5 BM25 + embedding cosine, fused with RRF.

score(chunk) = sum over signals of 1 / (RRF_K + rank)   (Cerebras: k = 60)
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from . import config, embed


@dataclass
class Hit:
    score: float
    source: str
    ref: str
    title: str | None
    heading: str | None
    text: str
    updated_at: str | None
    signals: str  # "fts", "vec", or "fts+vec"


def _fts_query(query: str) -> str:
    """Quote each token so user text can't break FTS5 syntax."""
    tokens = re.findall(r"\w+", query)
    return " ".join(f'"{t}"' for t in tokens) if tokens else '""'


def _fts_ranks(con: sqlite3.Connection, query: str,
               sources: list[str] | None) -> list[int]:
    sql = (
        "SELECT f.rowid FROM chunks_fts f"
        " JOIN chunks c ON c.id = f.rowid"
        " JOIN documents d ON d.id = c.doc_id"
        " WHERE chunks_fts MATCH ?"
    )
    args: list = [_fts_query(query)]
    if sources:
        sql += f" AND d.source IN ({','.join('?' * len(sources))})"
        args += sources
    sql += " ORDER BY bm25(chunks_fts) LIMIT ?"
    args.append(config.CANDIDATES)
    return [r[0] for r in con.execute(sql, args)]


def _vec_ranks(con: sqlite3.Connection, query: str,
               sources: list[str] | None) -> list[int]:
    import numpy as np

    sql = (
        "SELECT c.id, c.embedding FROM chunks c"
        " JOIN documents d ON d.id = c.doc_id"
        " WHERE c.embedding IS NOT NULL"
    )
    args: list = []
    if sources:
        sql += f" AND d.source IN ({','.join('?' * len(sources))})"
        args += sources
    rows = con.execute(sql, args).fetchall()
    if not rows:
        return []
    ids = np.array([r[0] for r in rows])
    mat = np.frombuffer(b"".join(r[1] for r in rows), dtype=np.float32)
    mat = mat.reshape(len(rows), config.EMBED_DIM)
    q = embed.embed_query(query)
    sims = mat @ q  # rows are L2-normalised at index time
    top = np.argsort(-sims)[: config.CANDIDATES]
    return [int(ids[i]) for i in top]


def search(
    con: sqlite3.Connection,
    query: str,
    k: int = 10,
    sources: list[str] | None = None,
    fts_only: bool = False,
) -> list[Hit]:
    ranklists: dict[str, list[int]] = {"fts": _fts_ranks(con, query, sources)}
    if not fts_only and embed.available():
        ranklists["vec"] = _vec_ranks(con, query, sources)

    scores: dict[int, float] = {}
    tags: dict[int, set[str]] = {}
    for signal, ranks in ranklists.items():
        for rank, cid in enumerate(ranks):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (config.RRF_K + rank + 1)
            tags.setdefault(cid, set()).add(signal)

    hits: list[Hit] = []
    for cid, score in sorted(scores.items(), key=lambda x: -x[1])[:k]:
        row = con.execute(
            "SELECT d.source, d.ref, d.title, c.heading, c.text, d.updated_at"
            " FROM chunks c JOIN documents d ON d.id = c.doc_id WHERE c.id=?",
            (cid,),
        ).fetchone()
        if row is None:
            continue
        hits.append(Hit(round(score, 5), row[0], row[1], row[2], row[3],
                        row[4], row[5], "+".join(sorted(tags[cid]))))
    return hits
