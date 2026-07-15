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
import csv
import fnmatch
import re
import subprocess
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
FIGURE_RE = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}")

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}

# Full-sample claims that must agree with the canonical roster.  These are
# deliberately anchored to sentences that describe the complete sample, not
# subset statements such as the eight DM-conditioned associations or nine
# redshift-constrained sightlines.
SAMPLE_COUNT_EXPECTATIONS = {
    "main.tex": [
        ("abstract sample", re.compile(
            r"(?:We present|Here we analyze)\s+(?P<count>\w+)\s+"
            r"(?:fast radio bursts|FRBs)\s+co-detected",
            re.IGNORECASE)),
        ("abstract association census", re.compile(
            r"All\s+(?P<count>\w+)\s+pass timing", re.IGNORECASE)),
        ("abstract DM census", re.compile(
            r"all\s+(?P<count>\w+)\s+events", re.IGNORECASE)),
        ("abstract foreground census", re.compile(
            r"all\s+(?P<count>\w+)\s+sightlines", re.IGNORECASE)),
    ],
    "sections/observations.tex": [
        ("sample-table introduction", re.compile(
            r"The\s+(?P<count>\w+)\s+bursts, their TNS designations",
            re.IGNORECASE)),
        ("paired spectra", re.compile(
            r"\((?P<count>\d+)\s+spectra in total", re.IGNORECASE), 2),
    ],
    "sections/results.tex": [
        ("association result", re.compile(
            r"All\s+(?P<count>\w+)\s+candidate pairs pass",
            re.IGNORECASE)),
        ("scintillation census", re.compile(
            r"Across the\s+(?P<count>\w+)\s+co-detections",
            re.IGNORECASE)),
    ],
    "sections/toa.tex": [
        ("TOA sample", re.compile(
            r"the\s+(?P<count>\w+)\s+events are genuine co-detections",
            re.IGNORECASE)),
        ("TOA residual census", re.compile(
            r"All\s+(?P<count>\w+)\s+residuals", re.IGNORECASE)),
    ],
    "sections/conclusions.tex": [
        ("conclusion sample", re.compile(
            r"the\s+(?P<count>\w+)-burst sample", re.IGNORECASE)),
    ],
}

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


def parse_count(token: str) -> int | None:
    token = token.lower()
    if token.isdigit():
        return int(token)
    return NUMBER_WORDS.get(token)


def table_roster(path: Path) -> set[str]:
    """Return the FRB designations in a manuscript table's data rows."""
    text = strip_comments(read_text(path))
    match = re.search(r"\\startdata(?P<body>.*?)\\enddata", text, re.DOTALL)
    if not match:
        return set()
    return set(re.findall(r"(?m)^\s*(FRB\s+\d{8}[A-Z])\b", match.group("body")))


def check_sample_counts(files: Iterable[Path], findings: list[str]) -> None:
    """Check complete-sample claims and generated-table rosters."""
    canonical_path = ROOT / "sample_table.tex"
    canonical = table_roster(canonical_path)
    if not canonical:
        findings.append("sample_table.tex: canonical sample roster not found")
        return
    expected = len(canonical)

    for table_name in ("dm_measurements_table.tex", "budget_table.tex"):
        roster = table_roster(ROOT / table_name)
        if roster != canonical:
            missing = ", ".join(sorted(canonical - roster)) or "none"
            extra = ", ".join(sorted(roster - canonical)) or "none"
            findings.append(
                f"{table_name}: roster differs from sample_table.tex "
                f"(missing: {missing}; extra: {extra})")

    by_relpath = {str(path.relative_to(ROOT)): path for path in files}
    for relpath, expectations in SAMPLE_COUNT_EXPECTATIONS.items():
        path = by_relpath.get(relpath)
        if path is None:
            findings.append(f"{relpath}: required full-sample section not reachable")
            continue
        text = strip_comments(read_text(path))
        for item in expectations:
            description, pattern, *multiplier = item
            match = pattern.search(text)
            if not match:
                findings.append(
                    f"{relpath}: missing audited full-sample claim ({description})")
                continue
            observed = parse_count(match.group("count"))
            wanted = expected * (multiplier[0] if multiplier else 1)
            if observed != wanted:
                findings.append(
                    f"{relpath}: {description} count is {match.group('count')}; "
                    f"expected {wanted} from the {expected}-burst canonical roster")


def normalize_figure_path(raw: str) -> str:
    """Normalize a TeX graphic path to the manifest's repo-relative form."""
    path = raw.replace("#1", "*")
    if not Path(path).suffix:
        path += ".pdf"
    # Most manuscript graphics live under figures/, but a small number of
    # pinned-submodule qualification artifacts are intentionally compiled from
    # pipeline/. Preserve either explicit repository-relative root.
    if not path.startswith(("figures/", "pipeline/")):
        path = "figures/" + path
    return path


def manifest_entries(kind: str | None = None) -> list[dict[str, str]]:
    with (ROOT / "repro_manifest.csv").open(newline="", encoding="utf-8") as fh:
        rows = csv.DictReader(fh)
        return [row for row in rows
                if row.get("embedded_in_manuscript", "").lower() == "yes"
                and (kind is None or row.get("type", "").lower() == kind)]


def patterns_overlap(a: str, b: str) -> bool:
    """Return true for equal paths or when either manifest/glob covers the other."""
    return a == b or fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a)


def pipeline_is_pinned() -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--stage", "pipeline"], cwd=ROOT,
        text=True, capture_output=True, check=False)
    return result.returncode == 0 and result.stdout.startswith("160000 ")


def figure_assets(pattern: str) -> list[Path]:
    return list(ROOT.glob(pattern))


def check_figures_and_provenance(
        files: Iterable[Path], findings: list[str]) -> None:
    """Require every compiled graphic to exist and have an embedded manifest row."""
    entries = manifest_entries("figure")
    included: list[tuple[Path, str]] = []
    needs_pipeline_pin = False
    for path in files:
        text = strip_comments(read_text(path))
        included.extend((path, normalize_figure_path(m.group(1)))
                        for m in FIGURE_RE.finditer(text))

    for source, figure in included:
        matches = [entry for entry in entries
                   if patterns_overlap(figure, entry["output"])]
        if not matches:
            findings.append(
                f"{source.relative_to(ROOT)}: compiled figure '{figure}' has no "
                "embedded figure row in repro_manifest.csv")
        else:
            needs_pipeline_pin |= any(
                entry.get("producer", "").startswith("pipeline/")
                for entry in matches)
        assets = figure_assets(figure)
        if not assets:
            findings.append(
                f"{source.relative_to(ROOT)}: compiled figure '{figure}' not found")
        elif "*" in figure:
            expected = len(table_roster(ROOT / "sample_table.tex"))
            if len(assets) != expected:
                findings.append(
                    f"{source.relative_to(ROOT)}: compiled figure family "
                    f"'{figure}' has {len(assets)} assets; expected {expected} "
                    "from the canonical sample roster")

    if needs_pipeline_pin and not pipeline_is_pinned():
        findings.append(
            "pipeline: expected a pinned gitlink for figure provenance")


def check_inputs_and_provenance(files: Iterable[Path], findings: list[str]) -> None:
    r"""Check that \input{} table/card files carry provenance comments."""
    generated_suffixes = ("_table.tex", "_cards.tex", "_data.tex")
    table_entries = manifest_entries("table")
    needs_pipeline_pin = False
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
            if target.name.endswith("_table.tex"):
                output = str(target.relative_to(ROOT))
                matches = [entry for entry in table_entries
                           if entry.get("output") == output]
                if not matches:
                    findings.append(
                        f"{output}: generated table has no embedded table row "
                        "in repro_manifest.csv")
                else:
                    needs_pipeline_pin |= any(
                        entry.get("producer", "").startswith("pipeline/")
                        for entry in matches)

    if needs_pipeline_pin and not pipeline_is_pinned():
        findings.append(
            "pipeline: expected a pinned gitlink for table provenance")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="F3 manuscript consistency audit")
    parser.add_argument("--write-report", type=Path, default=None,
                        help="Write findings to a markdown report file")
    parser.add_argument("--include-ok", action="store_true",
                        help="Print sections/files that passed checks")
    args = parser.parse_args(argv)

    files = tex_files()
    findings: list[str] = []

    check_sample_counts(files, findings)
    check_retired_language(files, findings)
    check_cross_refs(files, findings)
    check_inputs_and_provenance(files, findings)
    check_figures_and_provenance(files, findings)

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
