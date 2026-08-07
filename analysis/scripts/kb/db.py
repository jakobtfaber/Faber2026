"""SQLite storage: unified document/chunk schema + FTS5 index.

Every source (doc section, ticket, commit, function, reference, note) lands in
the same two tables, so one query interface covers everything — the Cerebras
"unified data model" principle.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    ref TEXT NOT NULL,
    title TEXT,
    updated_at TEXT,
    content_hash TEXT NOT NULL,
    meta TEXT,
    UNIQUE (source, ref)
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    ord INTEGER NOT NULL,
    heading TEXT,
    text TEXT NOT NULL,
    embedding BLOB
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
    USING fts5(text, heading, title, tokenize='porter unicode61');
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def upsert_document(
    con: sqlite3.Connection,
    *,
    source: str,
    ref: str,
    title: str | None,
    updated_at: str | None,
    chunks: list[tuple[str | None, str]],  # (heading, text)
    meta: dict | None = None,
) -> bool:
    """Insert or refresh one document. Returns True if (re)written.

    Unchanged documents (same content hash) are skipped, so embeddings for
    their chunks survive and only changed content is re-embedded.
    """
    full_text = "\n\x1e\n".join(t for _, t in chunks)
    h = content_hash(full_text)
    row = con.execute(
        "SELECT id, content_hash FROM documents WHERE source=? AND ref=?",
        (source, ref),
    ).fetchone()
    if row and row[1] == h:
        return False
    if row:
        delete_document(con, row[0])
    cur = con.execute(
        "INSERT INTO documents (source, ref, title, updated_at, content_hash, meta)"
        " VALUES (?,?,?,?,?,?)",
        (source, ref, title, updated_at, h, json.dumps(meta) if meta else None),
    )
    doc_id = cur.lastrowid
    for ord_, (heading, text) in enumerate(chunks):
        ccur = con.execute(
            "INSERT INTO chunks (doc_id, ord, heading, text) VALUES (?,?,?,?)",
            (doc_id, ord_, heading, text),
        )
        con.execute(
            "INSERT INTO chunks_fts (rowid, text, heading, title) VALUES (?,?,?,?)",
            (ccur.lastrowid, text, heading or "", title or ""),
        )
    return True


def delete_document(con: sqlite3.Connection, doc_id: int) -> None:
    for (cid,) in con.execute("SELECT id FROM chunks WHERE doc_id=?", (doc_id,)):
        con.execute("DELETE FROM chunks_fts WHERE rowid=?", (cid,))
    con.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
    con.execute("DELETE FROM documents WHERE id=?", (doc_id,))


def prune_missing(con: sqlite3.Connection, source: str, seen_refs: set[str]) -> int:
    """Drop documents of `source` whose ref was not seen this indexing pass."""
    gone = [
        (doc_id, ref)
        for doc_id, ref in con.execute(
            "SELECT id, ref FROM documents WHERE source=?", (source,)
        )
        if ref not in seen_refs
    ]
    for doc_id, _ in gone:
        delete_document(con, doc_id)
    return len(gone)


def stats(con: sqlite3.Connection) -> list[tuple[str, int, int, int]]:
    """(source, docs, chunks, embedded_chunks) per source."""
    return con.execute(
        """
        SELECT d.source, COUNT(DISTINCT d.id), COUNT(c.id),
               SUM(c.embedding IS NOT NULL)
        FROM documents d LEFT JOIN chunks c ON c.doc_id = d.id
        GROUP BY d.source ORDER BY d.source
        """
    ).fetchall()
