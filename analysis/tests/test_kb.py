"""Knowledge-base regression tests (FTS path only — no embedding deps)."""

import sys
from types import ModuleType
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from kb import adapters, config, db, embed, search  # noqa: E402
from kb.chunkers import chunk_markdown, chunk_python  # noqa: E402
from kb.adapters import _bib_entries  # noqa: E402
from workspace import manuscript_root  # noqa: E402


def _mkdb(tmp_path):
    con = db.connect(tmp_path / "kb.sqlite3")
    db.upsert_document(
        con, source="docs", ref="a.md", title="scattering notes",
        updated_at="2026-07-01",
        chunks=[("Two-screen", "The two-screen scattering model constrains "
                               "screen distances via the frequency lever arm.")],
    )
    db.upsert_document(
        con, source="tickets", ref="t1.md", title="ticket one",
        updated_at="2026-07-02",
        chunks=[(None, "Ratify the DM budget priors before circulation.")],
    )
    con.commit()
    return con


def test_fts_search_hits(tmp_path):
    con = _mkdb(tmp_path)
    hits = search.search(con, "two-screen scattering", fts_only=True)
    assert hits and hits[0].ref == "a.md"
    assert hits[0].signals == "fts"


def test_source_filter(tmp_path):
    con = _mkdb(tmp_path)
    hits = search.search(con, "priors", sources=["tickets"], fts_only=True)
    assert hits and all(h.source == "tickets" for h in hits)


def test_incremental_upsert_skips_unchanged(tmp_path):
    con = _mkdb(tmp_path)
    changed = db.upsert_document(
        con, source="docs", ref="a.md", title="scattering notes",
        updated_at="2026-07-01",
        chunks=[("Two-screen", "The two-screen scattering model constrains "
                               "screen distances via the frequency lever arm.")],
    )
    assert changed is False


def test_prune_missing(tmp_path):
    con = _mkdb(tmp_path)
    assert db.prune_missing(con, "docs", set()) == 1
    assert search.search(con, "two-screen", fts_only=True) == []


def test_query_escaping_no_crash(tmp_path):
    con = _mkdb(tmp_path)
    search.search(con, 'AND OR "unbalanced ( NEAR', fts_only=True)


def test_embedding_model_uses_persistent_repo_cache(monkeypatch):
    calls = {}
    fake_fastembed = ModuleType("fastembed")

    def fake_text_embedding(model_name, **kwargs):
        calls["model_name"] = model_name
        calls.update(kwargs)
        return object()

    fake_fastembed.TextEmbedding = fake_text_embedding
    monkeypatch.setitem(sys.modules, "fastembed", fake_fastembed)

    embed._model()

    assert calls == {
        "model_name": config.EMBED_MODEL,
        "cache_dir": str(REPO / ".kb" / "fastembed_cache"),
    }


def test_chunk_markdown_headings():
    chunks = chunk_markdown("# A\n\n" + "x" * 300 + "\n\n## B\n\n" + "y" * 300)
    assert [h for h, _ in chunks] == ["A", "B"]


def test_chunk_python_functions():
    src = '"""mod doc"""\n\ndef f():\n    return 1\n\nclass C:\n    pass\n'
    names = [h for h, _ in chunk_python(src)]
    assert names == ["module docstring", "f", "C"]


def test_bib_parser_roundtrip():
    bib = manuscript_root() / "bib" / "refs.bib"
    entries = list(_bib_entries(bib.read_text(errors="replace")))
    assert len(entries) >= 60
    keys = {k for _, k, _ in entries}
    assert "Macquart2020" in keys
    for _, _, fields in entries:
        assert "title" in fields or "author" in fields


def test_sources_span_analysis_and_manuscript():
    assert config.ANALYSIS_ROOT == REPO
    assert config.MANUSCRIPT_ROOT == manuscript_root()
    assert any(doc[1] == "main.tex" for doc in adapters.iter_docs())
    assert any(doc[1].startswith("analysis/docs/") for doc in adapters.iter_docs())
    assert next(adapters.iter_config())[1].startswith("analysis/")
    assert any(doc[1] == "Macquart2020" for doc in adapters.iter_refs())
