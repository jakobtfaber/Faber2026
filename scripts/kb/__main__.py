"""CLI: python3 scripts/kb {index,search,stats}"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

if __package__ in (None, ""):
    # Invoked as `python3 scripts/kb` — re-run with proper package context so
    # relative imports work.
    import runpy

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    runpy.run_module("kb", run_name="__main__")
    sys.exit(0)

from . import adapters, config, db, embed, search as search_mod


def cmd_index(args: argparse.Namespace) -> None:
    con = db.connect(Path(args.db))
    names = args.source or list(adapters.ADAPTERS)
    for name in names:
        if name not in adapters.ADAPTERS:
            sys.exit(f"kb: unknown source '{name}' "
                     f"(known: {', '.join(adapters.ADAPTERS)})")
        seen: set[str] = set()
        written = 0
        for source, ref, title, updated, chunks, meta in adapters.ADAPTERS[name]():
            if not chunks:
                continue
            seen.add(ref)
            written += db.upsert_document(
                con, source=source, ref=ref, title=title,
                updated_at=updated, chunks=chunks, meta=meta,
            )
        pruned = db.prune_missing(con, name, seen)
        con.commit()
        print(f"kb: {name}: {len(seen)} docs ({written} new/updated,"
              f" {pruned} pruned)")
    if not args.no_embed:
        if embed.available():
            n = embed.embed_pending(con)
            print(f"kb: embedded {n} chunks")
        else:
            print("kb: fastembed/numpy not installed — FTS-only index "
                  "(pip install fastembed numpy)", file=sys.stderr)
    con.commit()


def cmd_search(args: argparse.Namespace) -> None:
    con = db.connect(Path(args.db))
    hits = search_mod.search(con, args.query, k=args.k,
                             sources=args.source or None,
                             fts_only=args.fts_only)
    if args.json:
        print(json.dumps([h.__dict__ for h in hits], indent=2))
        return
    if not hits:
        print("no results")
        return
    for i, h in enumerate(hits, 1):
        loc = h.ref + (f" § {h.heading}" if h.heading else "")
        date = f"  ({h.updated_at})" if h.updated_at else ""
        print(f"{i:2d}. [{h.source}] {loc}{date}  "
              f"[{h.signals}, {h.score}]")
        snippet = " ".join(h.text.split())[:400]
        print(textwrap.indent(textwrap.fill(snippet, 96), "    "))
        print()


def cmd_stats(args: argparse.Namespace) -> None:
    con = db.connect(Path(args.db))
    rows = db.stats(con)
    if not rows:
        print("empty index — run: python3 scripts/kb index")
        return
    print(f"{'source':<10} {'docs':>6} {'chunks':>7} {'embedded':>9}")
    for source, docs, chunks, emb in rows:
        print(f"{source:<10} {docs:>6} {chunks:>7} {emb or 0:>9}")


def main() -> None:
    p = argparse.ArgumentParser(
        prog="kb", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--db", default=str(config.DB_PATH))
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="(re)index sources incrementally")
    pi.add_argument("--source", action="append",
                    help="limit to one source (repeatable)")
    pi.add_argument("--no-embed", action="store_true",
                    help="skip the embedding pass")
    pi.set_defaults(fn=cmd_index)

    ps = sub.add_parser("search", help="hybrid search")
    ps.add_argument("query")
    ps.add_argument("-k", type=int, default=10)
    ps.add_argument("--source", action="append",
                    help="filter by source (repeatable)")
    ps.add_argument("--fts-only", action="store_true")
    ps.add_argument("--json", action="store_true")
    ps.set_defaults(fn=cmd_search)

    pt = sub.add_parser("stats", help="index contents per source")
    pt.set_defaults(fn=cmd_stats)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
