"""Faber2026 repo knowledge base.

Hybrid (FTS5 BM25 + embedding) retrieval over manuscript docs, wayfinder
tickets, git history, pipeline code, cited references, and (optionally) an
Obsidian vault — Cerebras-style "extract in place" at single-repo scale.

Usage: python3 scripts/kb --help
"""
