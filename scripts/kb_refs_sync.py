#!/usr/bin/env python3
"""Sync the cited-references library from the local Zotero desktop API.

Matches every entry in bib/refs.bib against the running Zotero library
(DOI first, then normalised title) and writes bib/references_library.json
with abstracts and Zotero item keys. The kb refs adapter merges this file
into the index, so reference search gets full abstracts.

Requires Zotero desktop running (local API on 127.0.0.1:23119). Stdlib only.

Usage: python3 scripts/kb_refs_sync.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb.adapters import _bib_entries  # noqa: E402
from kb import config  # noqa: E402

ZOTERO = "http://127.0.0.1:23119/api/users/0/items"
OUT = config.REFS_CSL_JSON


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", t.lower())


def norm_doi(d: str) -> str:
    return d.lower().strip().removeprefix("https://doi.org/").removeprefix("doi:")


def fetch_library() -> list[dict]:
    items, start = [], 0
    while True:
        url = f"{ZOTERO}?format=json&limit=100&start={start}"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                page = json.loads(r.read())
        except OSError as e:
            sys.exit(f"kb_refs_sync: cannot reach Zotero local API ({e}). "
                     "Is Zotero desktop running?")
        if not page:
            return items
        items.extend(page)
        start += 100


def main() -> None:
    by_doi: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    for it in fetch_library():
        d = it.get("data", {})
        if d.get("itemType") in ("attachment", "note", "annotation"):
            continue
        if d.get("DOI"):
            by_doi[norm_doi(d["DOI"])] = d
        if d.get("title"):
            by_title[norm_title(d["title"])] = d

    out, unmatched = [], []
    bib_text = (config.REPO_ROOT / config.BIB_FILES[0]).read_text(errors="replace")
    for _etype, key, f in _bib_entries(bib_text):
        hit, how = None, None
        if f.get("doi") and norm_doi(f["doi"]) in by_doi:
            hit, how = by_doi[norm_doi(f["doi"])], "doi"
        elif f.get("title") and norm_title(f["title"]) in by_title:
            hit, how = by_title[norm_title(f["title"])], "title"
        if hit is None:
            unmatched.append(key)
            continue
        out.append({
            "id": key,
            "zotero_key": hit.get("key"),
            "DOI": hit.get("DOI") or f.get("doi"),
            "title": hit.get("title") or f.get("title"),
            "abstract": hit.get("abstractNote") or "",
            "matched_by": how,
        })

    OUT.write_text(json.dumps(out, indent=1))
    print(f"kb_refs_sync: matched {len(out)} / {len(out) + len(unmatched)} "
          f"bib entries -> {OUT.relative_to(config.REPO_ROOT)}")
    if unmatched:
        print("unmatched (not in Zotero, or DOI/title mismatch):")
        for k in unmatched:
            print(f"  - {k}")


if __name__ == "__main__":
    main()
