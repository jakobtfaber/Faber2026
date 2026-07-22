"""Optional embedding backend (fastembed / ONNX, fully local).

If fastembed or numpy is missing the KB degrades to FTS-only search; nothing
else changes. Install with:  pip install fastembed numpy
"""

from __future__ import annotations

import sqlite3
import sys

from . import config

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


def available() -> bool:
    if np is None:
        return False
    try:
        import fastembed  # noqa: F401
    except ImportError:
        return False
    return True


def _model():
    from fastembed import TextEmbedding

    return TextEmbedding(config.EMBED_MODEL)


def embed_pending(con: sqlite3.Connection, batch: int = 128) -> int:
    """Embed all chunks with NULL embedding. Returns count embedded."""
    rows = con.execute(
        "SELECT id, heading, text FROM chunks WHERE embedding IS NULL"
    ).fetchall()
    if not rows:
        return 0
    model = _model()
    done = 0
    for i in range(0, len(rows), batch):
        chunk_rows = rows[i: i + batch]
        texts = [
            (f"{h}\n{t}" if h else t)[:4000] for _, h, t in chunk_rows
        ]
        embed_fn = getattr(model, "passage_embed", model.embed)
        for (cid, _, _), vec in zip(chunk_rows, embed_fn(texts)):
            v = np.asarray(vec, dtype=np.float32)
            v /= (np.linalg.norm(v) or 1.0)
            con.execute(
                "UPDATE chunks SET embedding=? WHERE id=?", (v.tobytes(), cid)
            )
        done += len(chunk_rows)
        con.commit()
        print(f"kb: embedded {done}/{len(rows)}", file=sys.stderr)
    return done


def embed_query(text: str):
    model = _model()
    embed_fn = getattr(model, "query_embed", model.embed)
    v = np.asarray(next(iter(embed_fn([text]))), dtype=np.float32)
    return v / (np.linalg.norm(v) or 1.0)
