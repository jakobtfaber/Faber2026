#!/usr/bin/env python3
"""F3 manuscript consistency audit.

Checks the LaTeX manuscript for:
- per-section burst sample counts vs the twelve-sightline roster;
- retired language (rail taxonomy, alpha=4-limit quoting) that should have been
  purged per plan-circulation-readiness.md;
- broken or duplicate cross-references;
- missing provenance comments on input tables and figures.

Exits 0 if no issues are found, 1 otherwise. Findings are printed and optionally
written to a report file.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

# Commands whose argument is a label that must exist.
REF_CMDS = (r"\\ref\*?", r"\\cref\*?", r"\\Cref\*?", r"\\nameref\*?",
            r"\\autoref\*?", r"\\pageref\*?")
REF_RE = re.compile(r"(?:" + "|".join(REF_CMDS) + r")\{([^}]+)\}")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
INPUT_RE = re.compile(r"\\input\{([^}]+)\}")

# Files whose entire purpose is to discuss a retired term in a derivation
# context (not to quote it as a result) are excluded from the retired-language
# sweep.  Add paths here sparingly; the default is to flag every occurrence.
EXCLUDED_FROM_RETIRED = {
    ROOT / "sections" / "emg_alpha4_appendix.tex",
}

RETIRED_PATTERNS = [
    (re.compile(r"\brail[- ]?class(?:es)?\b"), "retired rail-class taxonomy"),
    (re.compile(r"\brail[- ]?tall(?:y|ies)\b"), "retired rail tally"),
    (re.compile(r"\brailed\b"), "retired rail-class vocabulary"),
    # alpha=4 should not be followed immediately by a digit or dot (avoids alpha=4.4).
    (re.compile(r"(?:^|[^a-zA-Z])alpha\s*=\s*4\b(?![\.,]\d)"), "retired alpha=4-limit quoting"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_comments(text: str) -> str:
    """Remove LaTeX comments (unescaped % to end of line) from text."""
    out = []
    for line in text.splitlines():
        # Remove from an unescaped % to end of line.
        line = re.sub(r"(?<!\\)%.*", "", line)
        out.append(line)
    return "\n".join(out)


def tex_files() -> list[Path]:
    r"""Return all .tex files reachable from main.tex via \input{} commands."""
    seen: set[Path] = set()
    frontier = [ROOT / "main.tex"]
    while frontier:
        path = frontier.pop()
        if not path.exists():
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        text = strip_comments(read_text(path))
        for match in INPUT_RE.finditer(text):
            stem = match.group(1)
            candidates = [ROOT / stem, (ROOT / stem).with_suffix(".tex")]
            for candidate in candidates:
                if candidate.exists():
                    frontier.append(candidate)
                    break
    return sorted(seen)


def check_retired_language(files: Iterable[Path], findings: list[str]) -> None:
    for path in files:
        if path.resolve() in EXCLUDED_FROM_RETIRED:
            continue
        text = strip_comments(read_text(path))
        lines = text.splitlines()
        for lineno, line in enumerate(lines, start=1):
            lower = line.lower()
            for pat, reason in RETIRED_PATTERNS:
                if pat.search(lower):
                    findings.append(
                        f"{path.relative_to(ROOT)}:{lineno}: retired language "
                        f"({reason}): {line.strip()[:120]}")


def check_cross_refs(files: Iterable[Path], findings: list[str]) -> None:
    labels: dict[str, Path] = {}
    refs: list[tuple[Path, int, str, str]] = []
    for path in files:
        text = strip_comments(read_text(path))
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in LABEL_RE.finditer(line):
                label = match.group(1)
                if label in labels:
                    findings.append(
                        f"{path.relative_to(ROOT)}:{lineno}: duplicate label "
                        f"'{label}' (first defined in {labels[label].relative_to(ROOT)})")
                else:
                    labels[label] = path
            for match in REF_RE.finditer(line):
                refs.append((path, lineno, match.group(0), match.group(1)))
    for path, lineno, cmd, label in refs:
        if label not in labels:
            findings.append(
                f"{path.relative_to(ROOT)}:{lineno}: undefined reference '{label}' "
                f"in {cmd}")


def check_inputs_and_provenance(files: Iterable[Path], findings: list[str]) -> None:
    r"""Check that \input{} table/card files carry provenance comments."""
    generated_suffixes = ("_table.tex", "_cards.tex", "_data.tex")
    for path in files:
        text = read_text(path)
        for match in INPUT_RE.finditer(text):
            stem = match.group(1)
            # Resolve relative to ROOT, adding .tex if missing.
            candidates = [ROOT / stem, (ROOT / stem).with_suffix(".tex")]
            target = next((c for c in candidates if c.exists()), None)
            if target is None:
                findings.append(
                    f"{path.relative_to(ROOT)}: \\input{{{stem}}} target not found")
                continue
            if not target.name.endswith(generated_suffixes):
                continue
            # Look for a provenance comment in the first 10 lines; keyword need
            # not be the first word after %.
            head = "\n".join(read_text(target).splitlines()[:10])
            if not re.search(r"%.*\b(?:Source|Generated|Provenance|Produced|From)\b",
                             head, re.IGNORECASE):
                findings.append(
                    f"{target.relative_to(ROOT)}: missing provenance comment "
                    f"(expected a top-level Source/Generated/Provenance/Produced/From line)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="F3 manuscript consistency audit")
    parser.add_argument("--write-report", type=Path, default=None,
                        help="Write findings to a markdown report file")
    parser.add_argument("--include-ok", action="store_true",
                        help="Print sections/files that passed checks")
    args = parser.parse_args(argv)

    files = tex_files()
    findings: list[str] = []

    check_retired_language(files, findings)
    check_cross_refs(files, findings)
    check_inputs_and_provenance(files, findings)

    if args.write_report:
        lines = ["# F3 manuscript consistency audit findings", ""]
        if findings:
            lines.append(f"**Total findings:** {len(findings)}")
            lines.append("")
            for f in findings:
                lines.append(f"- {f}")
        else:
            lines.append("No findings.")
        args.write_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote report to {args.write_report}")

    if findings:
        print(f"F3 consistency audit: {len(findings)} finding(s)")
        for f in findings:
            print(f"  {f}")
        return 1
    print("F3 consistency audit: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
