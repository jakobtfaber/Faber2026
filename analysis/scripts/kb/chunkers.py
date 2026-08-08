"""Heading-aware chunkers for markdown, LaTeX, and python source."""

from __future__ import annotations

import ast
import re

from . import config

Chunk = tuple  # (heading | None, text)

_MD_HEADING = re.compile(r"^(#{1,4})\s+(.*)$", re.M)
_TEX_SECTION = re.compile(r"\\(sub){0,2}section\*?\{([^}]*)\}")


def _pack(sections: list[tuple[str | None, str]]) -> list[Chunk]:
    """Merge tiny sections into neighbours; split oversized ones on blank lines."""
    out: list[Chunk] = []
    for heading, body in sections:
        body = body.strip()
        if not body:
            continue
        while len(body) > 2 * config.CHUNK_TARGET:
            cut = body.rfind("\n\n", config.CHUNK_MIN, config.CHUNK_TARGET)
            if cut == -1:
                cut = config.CHUNK_TARGET
            out.append((heading, body[:cut].strip()))
            body = body[cut:].strip()
        if out and len(body) < config.CHUNK_MIN and out[-1][0] == heading:
            out[-1] = (heading, out[-1][1] + "\n\n" + body)
        else:
            out.append((heading, body))
    return out


def chunk_markdown(text: str) -> list[Chunk]:
    matches = list(_MD_HEADING.finditer(text))
    if not matches:
        return _pack([(None, text)])
    sections: list[tuple[str | None, str]] = []
    if matches[0].start() > 0:
        sections.append((None, text[: matches[0].start()]))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((m.group(2).strip(), text[m.end():end]))
    return _pack(sections)


def chunk_latex(text: str) -> list[Chunk]:
    # Strip comments (keeps line structure).
    text = re.sub(r"(?<!\\)%.*", "", text)
    matches = list(_TEX_SECTION.finditer(text))
    if not matches:
        return _pack([(None, text)])
    sections: list[tuple[str | None, str]] = []
    if matches[0].start() > 0:
        sections.append((None, text[: matches[0].start()]))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((m.group(2).strip(), text[m.end():end]))
    return _pack(sections)


def chunk_python(text: str, max_chunk: int = 2000) -> list[Chunk]:
    """Module docstring + one chunk per top-level function/class.

    Falls back to plain-text chunking on syntax errors (Cerebras chunks
    class -> method; at this corpus size top-level granularity suffices).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _pack([(None, text)])
    lines = text.splitlines()
    chunks: list[Chunk] = []
    mod_doc = ast.get_docstring(tree)
    if mod_doc:
        chunks.append(("module docstring", mod_doc))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min(
                [node.lineno] + [d.lineno for d in node.decorator_list]
            ) - 1
            src = "\n".join(lines[start: node.end_lineno])
            if len(src) > max_chunk:
                src = src[:max_chunk] + "\n# ... truncated ..."
            chunks.append((node.name, src))
    if not chunks:
        return _pack([(None, text)])
    return chunks
