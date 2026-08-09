"""Every repository path the journal cadence scripts name must exist.

The cadence scripts (`analysis/scripts/journal-*.sh`) all open with
`[ -f "$J" ] || exit 0`, so a path that no longer resolves makes the script
exit quietly instead of failing. Nothing surfaces: no CI signal, no log line,
and the readiness board keeps showing a journal that simply stopped being
written. The 2026-08 monorepo consolidation moved the store to
`analysis/docs/rse/protocols/journal.jsonl` and left five scripts pointing at
the pre-move `docs/rse/journal.jsonl`, which is exactly that silent failure.

The check resolves each `"$VAR/..."` expression against the directory the
script assigns to `VAR`, so it also catches a future move of the store, the
append helper, or the readiness board. A script that inlines its base, or that
names a moved path only in a comment or a reminder string, exposes no such
expression to resolve; the substring checks cover that case.
"""

from __future__ import annotations

import plistlib
import re
from pathlib import Path

import pytest

ANALYSIS = Path(__file__).resolve().parents[1]
REPO = ANALYSIS.parent
SCRIPTS = ANALYSIS / "scripts"

CADENCE_SCRIPTS = [
    "journal-append.sh",
    "journal-cadence-cursor-hook.sh",
    "journal-cadence-posttool-hook.sh",
    "journal-cursor-afteredit-hook.sh",
    "journal-staleness-hook.sh",
    "journal-watchdog.sh",
]

# The watchdog prunes the git directory from its activity scan by glob; the
# directory is the claim, and its contents are not this test's business.
IGNORED_SUFFIXES = frozenset({"/.git/*"})

# Paths the 2026-08 monorepo consolidation moved. A script may name one in a
# comment or a reminder string rather than in a `"$VAR/..."` expression, where
# the resolution check below cannot see it — but an agent reading the comment
# still follows it to a file that is not there.
PRE_CONSOLIDATION_PATHS = (
    "docs/rse/journal.jsonl",
    "docs/rse/journal-protocol.md",
    "docs/rse/board/",
)

PATH_EXPR = re.compile(r"\$(ROOT|REPO|ANALYSIS)(/[A-Za-z0-9_./*-]+)")
ASSIGNMENT = re.compile(r"^(ROOT|REPO|ANALYSIS)=(.*)$", re.MULTILINE)

JOURNAL = ANALYSIS / "docs/rse/protocols/journal.jsonl"


def _bases(text: str) -> dict[str, Path]:
    """Map each base variable a script assigns to the directory it holds.

    A variable derived from the script's own location (`dirname "$0"/..`)
    resolves to the analysis directory; anything else — the git toplevel,
    Claude's project directory, a hard-coded checkout path — resolves to the
    checkout root.
    """
    return {
        var: ANALYSIS if 'dirname "$0"' in value else REPO
        for var, value in ASSIGNMENT.findall(text)
    }


def _named_paths(text: str) -> list[tuple[str, str]]:
    return [
        (var, suffix) for var, suffix in PATH_EXPR.findall(text) if suffix not in IGNORED_SUFFIXES
    ]


@pytest.mark.parametrize("name", CADENCE_SCRIPTS)
def test_cadence_script_paths_resolve(name: str) -> None:
    script = SCRIPTS / name
    assert script.is_file(), f"{name} is missing from analysis/scripts/"
    text = script.read_text()
    bases = _bases(text)
    missing = []
    for var, suffix in _named_paths(text):
        # A trailing `/*` is a find(1) prune glob; the directory is the claim.
        candidate = bases[var] / suffix.lstrip("/").removesuffix("/*")
        if not candidate.exists():
            missing.append(f"${var}{suffix}")
    assert not missing, f"{name} names paths that do not exist: {missing}"


@pytest.mark.parametrize(
    "name",
    [n for n in CADENCE_SCRIPTS if n != "journal-append.sh"],
)
def test_cadence_script_reads_the_current_journal(name: str) -> None:
    # journal-append.sh is excluded: it writes the store rather than guarding
    # on it, and tests/test_journal_append.sh already covers its behaviour.
    text = (SCRIPTS / name).read_text()
    assert JOURNAL.is_file()
    assert "docs/rse/protocols/journal.jsonl" in text, (
        f"{name} does not read {JOURNAL.relative_to(REPO)}; a stale path makes "
        'it exit silently at its `[ -f "$J" ]` guard'
    )


@pytest.mark.parametrize("name", CADENCE_SCRIPTS)
def test_cadence_script_names_no_pre_consolidation_path(name: str) -> None:
    text = (SCRIPTS / name).read_text()
    stale = [path for path in PRE_CONSOLIDATION_PATHS if path in text]
    assert not stale, (
        f"{name} still names pre-consolidation path(s) {stale}; the store is now "
        "analysis/docs/rse/protocols/, the board analysis/docs/rse/control/board/"
    )


def test_watchdog_plist_points_at_the_watchdog_script() -> None:
    plist = SCRIPTS / "launchd/com.jakobfaber.faber2026-journal-watchdog.plist"
    with plist.open("rb") as handle:
        arguments = plistlib.load(handle)["ProgramArguments"]
    # The plist carries an absolute path into the owner's checkout, so only the
    # in-repository tail is portable enough to assert on.
    script = next(argument for argument in arguments if argument.endswith(".sh"))
    _, _, tail = script.partition("/Faber2026/")
    assert tail, f"plist path is not inside a Faber2026 checkout: {script}"
    assert (REPO / tail).is_file(), f"plist points at a missing script: {tail}"
