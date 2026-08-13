"""The changed-files lint gate must honour the lint scope pyproject declares.

`lint_changed.py` names every changed file on ruff's command line, and ruff
ignores `extend-exclude` for paths named that way unless `--force-exclude` is
passed. Without the flag, the gate lints trees `[tool.ruff] extend-exclude`
declares out of scope (`*/studies/*`, `.archive`) as soon as a commit touches
one — so a one-line import repair under `scattering/studies/joint-refits/`
arrived carrying 215 pre-existing style findings it did not introduce.

Both facts below have to hold together: the flag has to be passed, and the
configured scope has to be the thing that flag defers to.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lint_changed  # noqa: E402


class _Result:
    returncode = 0
    stdout = ""


def _recording_run(recorded: list[list[str]]):
    """A `subprocess.run` stub: record every call, answer ruff, pass on the rest.

    Recording every call rather than only ruff's is what lets a test assert
    that git was reached; recording ruff alone cannot tell "the fall-through
    ran" from "nothing took that branch".

    `real_run` is read here, before the caller's `monkeypatch.setattr` replaces
    the attribute. `lint_changed` and this module hold the same `subprocess`
    module object, so a fall-through that re-read `subprocess.run` at call time
    would find this stub and recurse until `RecursionError` rather than reach
    git. Call this before installing the patch, never after.
    """
    real_run = subprocess.run

    def fake_run(argv, *args, **kwargs):
        recorded.append(list(argv))
        if argv and argv[0] == "ruff":
            return _Result()
        return real_run(argv, *args, **kwargs)

    return fake_run


def _calls_to(recorded: list[list[str]], program: str) -> list[list[str]]:
    return [argv for argv in recorded if argv and argv[0] == program]


def test_the_gate_passes_force_exclude_to_ruff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the real code path rather than grepping its source."""
    recorded: list[list[str]] = []

    monkeypatch.setattr(lint_changed.subprocess, "run", _recording_run(recorded))
    monkeypatch.setattr(lint_changed, "_changed_python_files", lambda base: ["scripts/lint_changed.py"])
    monkeypatch.delenv("LINT_BASE_INTERSECT", raising=False)
    monkeypatch.setenv("BASE_SHA", "HEAD")

    assert lint_changed.main() == 0
    ruff_calls = _calls_to(recorded, "ruff")
    assert ruff_calls, "the gate never invoked ruff"
    assert ruff_calls[0][:3] == ["ruff", "check", "--force-exclude"], ruff_calls[0]


def test_the_stub_falls_through_to_real_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """The non-ruff branch has to reach git rather than re-enter the stub.

    `_changed_python_files` is deliberately left unstubbed, so `main()` drives
    real git plumbing through that branch. `BASE_SHA=HEAD` makes the diff empty,
    so the gate returns 0 without reaching ruff.

    Returning rather than raising `RecursionError` is the property this was
    written for, but returning is not enough on its own: the test would pass
    just as quietly if `_changed_python_files` stopped routing through
    `subprocess`, leaving the guard exercising nothing. Asserting a `git` call
    was recorded pins the fall-through itself.
    """
    recorded: list[list[str]] = []

    monkeypatch.setattr(lint_changed.subprocess, "run", _recording_run(recorded))
    monkeypatch.delenv("LINT_BASE_INTERSECT", raising=False)
    monkeypatch.setenv("BASE_SHA", "HEAD")

    assert lint_changed.main() == 0
    assert _calls_to(recorded, "git"), f"the fall-through never reached git: {recorded}"
    assert not _calls_to(recorded, "ruff"), "an empty diff should never reach ruff"


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff is a test-group dependency")
def test_force_exclude_defers_to_the_configured_exclusions() -> None:
    """Named files inside an excluded tree must produce no findings."""
    excluded = sorted((ROOT / "scattering" / "studies").rglob("*.py"))[:40]
    if not excluded:
        pytest.skip("no files under the excluded studies tree")

    named = [str(path.relative_to(ROOT)) for path in excluded]
    result = subprocess.run(
        ["ruff", "check", "--force-exclude", "--output-format", "concise", *named],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "ruff reported findings in a tree pyproject excludes:\n" + result.stdout
    )
