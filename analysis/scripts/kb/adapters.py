"""Source adapters. Each yields documents in the unified schema:

    (source, ref, title, updated_at, chunks, meta)

Adding a source = adding one generator function here and registering it in
ADAPTERS (the Cerebras "connectors via pull request" model).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

from . import config
from .chunkers import chunk_latex, chunk_markdown, chunk_python

Doc = tuple  # (source, ref, title, updated_at, chunks, meta)


def _mtime(path: Path) -> str:
    return dt.date.fromtimestamp(path.stat().st_mtime).isoformat()


def _rel(path: Path) -> str:
    return str(path.relative_to(config.REPO_ROOT))


def _excluded(path: Path) -> bool:
    return bool(config.DOCS_EXCLUDE_PARTS.intersection(path.parts))


# ---------------------------------------------------------------------------
# docs
# ---------------------------------------------------------------------------

def iter_docs() -> Iterator[Doc]:
    seen: set[Path] = set()
    for pattern in config.DOCS_GLOBS:
        for path in sorted(config.REPO_ROOT.glob(pattern)):
            if path in seen or _excluded(path) or not path.is_file():
                continue
            if config.TICKETS_DIR in path.parents:
                continue  # tickets adapter owns these
            seen.add(path)
            text = path.read_text(errors="replace")
            if not text.strip():
                continue
            chunker = chunk_latex if path.suffix == ".tex" else chunk_markdown
            yield ("docs", _rel(path), path.name, _mtime(path), chunker(text), None)


# ---------------------------------------------------------------------------
# tickets (wayfinder markdown tracker)
# ---------------------------------------------------------------------------

_TICKET_HEADER = re.compile(
    r"^(Status|Assignee|Blocked by|Blocks)\s*:\s*(.+)$", re.I | re.M
)


def iter_tickets() -> Iterator[Doc]:
    if not config.TICKETS_DIR.is_dir():
        return
    for path in sorted(config.TICKETS_DIR.glob("*.md")):
        text = path.read_text(errors="replace")
        meta = {
            m.group(1).lower().replace(" ", "_"): m.group(2).strip()
            for m in _TICKET_HEADER.finditer(text[:2000])
        }
        title_m = re.search(r"^#\s+(.*)$", text, re.M)
        title = title_m.group(1).strip() if title_m else path.stem
        yield ("tickets", _rel(path), title, _mtime(path), chunk_markdown(text), meta)


# ---------------------------------------------------------------------------
# git (commits; PR titles/bodies folded in via `gh` when available)
# ---------------------------------------------------------------------------

def iter_git() -> Iterator[Doc]:
    out = subprocess.run(
        ["git", "log", f"-{config.GIT_MAX_COMMITS}", "--date=short",
         "--pretty=format:%H%x1f%ad%x1f%an%x1f%s%x1f%b%x1e"],
        cwd=config.REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    for record in out.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        sha, date, author, subject, body = (record.split("\x1f") + [""] * 5)[:5]
        text = subject + ("\n\n" + body.strip() if body.strip() else "")
        yield ("git", sha, subject[:120], date,
               [(None, text)], {"author": author})

    if shutil.which("gh"):
        try:
            prs = json.loads(subprocess.run(
                ["gh", "pr", "list", "--state", "all", "--limit", "500",
                 "--json", "number,title,body,mergedAt,updatedAt,author"],
                cwd=config.REPO_ROOT, capture_output=True, text=True, check=True,
            ).stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            print("kb: gh present but PR listing failed; skipping PRs",
                  file=sys.stderr)
            prs = []
        for pr in prs:
            date = (pr.get("mergedAt") or pr.get("updatedAt") or "")[:10]
            text = pr["title"] + ("\n\n" + pr["body"] if pr.get("body") else "")
            yield ("git", f"PR#{pr['number']}", pr["title"][:120], date or None,
                   [(None, text)],
                   {"author": (pr.get("author") or {}).get("login")})


# ---------------------------------------------------------------------------
# code
# ---------------------------------------------------------------------------

def iter_code() -> Iterator[Doc]:
    for dir_ in config.CODE_DIRS:
        base = config.REPO_ROOT / dir_
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if _excluded(path) or path.stat().st_size > config.CODE_MAX_FILE_BYTES:
                continue
            text = path.read_text(errors="replace")
            if not text.strip():
                continue
            yield ("code", _rel(path), path.name, _mtime(path),
                   chunk_python(text), None)


# ---------------------------------------------------------------------------
# refs (bib entries, optionally enriched by a Zotero CSL-JSON export)
# ---------------------------------------------------------------------------

_BIB_ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.M)
_BIB_FIELD = re.compile(r"(\w+)\s*=\s*(\{|\")")


def _bib_entries(text: str) -> Iterator[tuple[str, str, dict[str, str]]]:
    """Yield (entry_type, key, fields) with brace-balanced field values."""
    for m in _BIB_ENTRY.finditer(text):
        etype, key = m.group(1).lower(), m.group(2)
        if etype in ("comment", "preamble", "string"):
            continue
        # Scan the balanced body of this entry.
        depth, i = 1, m.end()
        start = i
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start: i - 1]
        fields: dict[str, str] = {}
        for fm in _BIB_FIELD.finditer(body):
            name = fm.group(1).lower()
            open_ch = fm.group(2)
            j = fm.end()
            if open_ch == "{":
                d = 1
                k = j
                while k < len(body) and d > 0:
                    if body[k] == "{":
                        d += 1
                    elif body[k] == "}":
                        d -= 1
                    k += 1
                val = body[j: k - 1]
            else:
                k = body.find('"', j)
                val = body[j: k if k != -1 else len(body)]
            fields[name] = re.sub(r"[{}]", "", " ".join(val.split()))
        yield etype, key, fields


def iter_refs() -> Iterator[Doc]:
    enrich: dict[str, dict] = {}
    if config.REFS_CSL_JSON.is_file():
        for item in json.loads(config.REFS_CSL_JSON.read_text()):
            for k in filter(None, [item.get("id"),
                                   (item.get("DOI") or "").lower()]):
                enrich[str(k)] = item
    for bib in config.BIB_FILES:
        path = config.REPO_ROOT / bib
        if not path.is_file():
            continue
        for etype, key, f in _bib_entries(path.read_text(errors="replace")):
            extra = enrich.get(key) or enrich.get((f.get("doi") or "").lower())
            abstract = f.get("abstract") or (extra or {}).get("abstract") or ""
            lines = [
                f.get("title", key),
                f.get("author", ""),
                " ".join(filter(None, [f.get("journal") or f.get("booktitle"),
                                       f.get("year"), f.get("volume")])),
                f"doi:{f['doi']}" if f.get("doi") else "",
                f"arXiv:{f['eprint']}" if f.get("eprint") else "",
                abstract,
            ]
            text = "\n".join(filter(None, lines))
            meta = {"type": etype, "year": f.get("year"), "doi": f.get("doi"),
                    "eprint": f.get("eprint")}
            yield ("refs", key, f.get("title", key)[:200], f.get("year"),
                   [(key, text)], meta)


# ---------------------------------------------------------------------------
# obsidian (optional personal vault)
# ---------------------------------------------------------------------------

def iter_obsidian() -> Iterator[Doc]:
    vault = config.OBSIDIAN_VAULT
    if vault is None:
        return
    if not vault.is_dir():
        print(f"kb: obsidian vault not found: {vault}", file=sys.stderr)
        return
    for path in sorted(vault.rglob("*.md")):
        if ".obsidian" in path.parts or ".trash" in path.parts:
            continue
        text = path.read_text(errors="replace")
        if not text.strip():
            continue
        yield ("obsidian", str(path.relative_to(vault)), path.stem,
               _mtime(path), chunk_markdown(text), None)


ADAPTERS = {
    "docs": iter_docs,
    "tickets": iter_tickets,
    "git": iter_git,
    "code": iter_code,
    "refs": iter_refs,
    "obsidian": iter_obsidian,
}
