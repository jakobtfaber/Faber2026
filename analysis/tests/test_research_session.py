"""Unit tests for scripts/research_session.py (no agents, no long-running work)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANALYSIS_ROOT / "scripts"))

import research_session  # noqa: E402

SLUG_SAFE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")

EMPTY_CONTRACT = """Scientific phase: exploration

Objective:

May change:

Must not change:

Done when:

Verification command:
"""


@pytest.fixture
def workbench(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "workbench"
    root.mkdir()
    monkeypatch.setenv("FABER2026_WORKBENCH", str(root))
    return root.resolve()


def _start(*extra: str) -> int:
    return research_session.main(
        ["start", "--issue", "205", "--phase", "exploration", "--event", "zach", *extra]
    )


def _record(workbench: Path) -> dict:
    path = workbench / "issue-205-zach" / "session.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_workbench_root_follows_the_environment_override(workbench: Path):
    assert research_session.workbench_root() == workbench
    assert research_session.require_workbench_root() == workbench
    assert research_session.workbench_root_source() == "FABER2026_WORKBENCH"


def test_missing_workbench_root_reports_an_actionable_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    absent = tmp_path / "nowhere"
    monkeypatch.setenv("FABER2026_WORKBENCH", str(absent))
    with pytest.raises(FileNotFoundError) as exc:
        research_session.require_workbench_root()
    message = str(exc.value)
    assert str(absent) in message
    assert "FABER2026_WORKBENCH" in message


def test_dry_run_writes_nothing(workbench: Path, capsys: pytest.CaptureFixture[str]):
    assert _start("--dry-run") == 0
    assert list(workbench.iterdir()) == []
    assert "DRY RUN" in capsys.readouterr().out.upper()


def test_start_creates_the_session_tree_and_records_commits(workbench: Path):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    assert (session_dir / "scratch").is_dir()
    assert (session_dir / "exports").is_dir()

    record = _record(workbench)
    assert record["slug"] == "issue-205-zach"
    assert record["issue"] == "205"
    assert record["event"] == "zach"
    assert record["state"] == "created"
    assert record["created_at"]
    assert record["workbench"]["root"] == str(workbench)
    assert record["workbench"]["root_source"] == "FABER2026_WORKBENCH"
    assert record["interpreter"] == str(ANALYSIS_ROOT / ".venv" / "bin" / "python")
    assert record["repositories"]["analysis"] == str(research_session.ANALYSIS_ROOT)

    analysis = record["git"]["analysis"]
    assert SHA1.match(analysis["head"]), analysis
    assert analysis["dirty"]["untracked"] >= 0
    assert "gitlink" in record["git"]["manuscript"]


def test_task_contract_is_written_empty_for_the_human(workbench: Path):
    assert _start() == 0
    task_file = workbench / "issue-205-zach" / "TASK.md"
    assert task_file.read_text(encoding="utf-8") == EMPTY_CONTRACT
    assert _record(workbench)["workbench"]["task_file"] == str(task_file)


def test_phase_lives_in_the_contract_not_in_the_machine_record(workbench: Path):
    assert _start() == 0
    assert "phase" not in _record(workbench)
    contract = (workbench / "issue-205-zach" / "TASK.md").read_text(encoding="utf-8")
    assert contract.startswith("Scientific phase: exploration")


def test_check_arguments_reach_both_files(workbench: Path):
    assert _start("--check", "make test", "--check", "pytest tests/test_x.py -q") == 0
    assert _record(workbench)["checks"] == ["make test", "pytest tests/test_x.py -q"]
    contract = (workbench / "issue-205-zach" / "TASK.md").read_text(encoding="utf-8")
    assert contract.endswith(
        "Verification command:\n  make test\n  pytest tests/test_x.py -q\n"
    )


def test_no_focused_test_is_invented(workbench: Path):
    assert _start() == 0
    printed = "\n".join(research_session.next_commands(_record(workbench)))
    assert "-m pytest" not in printed
    assert "pytest tests" not in printed
    assert "-k " not in printed


def test_start_writes_nothing_inside_either_checkout(workbench: Path):
    assert _start() == 0
    assert not (research_session.ANALYSIS_ROOT / "session.json").exists()
    assert not (research_session.ANALYSIS_ROOT / "TASK.md").exists()
    assert not (research_session.ANALYSIS_ROOT / "workbench").exists()


def test_dirty_summary_reads_the_porcelain_status_columns(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run = ["git", "-c", "user.email=t@e.st", "-c", "user.name=t"]
    subprocess.run([*run, "init", "-q", "-b", "main", "."], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("one\n", encoding="utf-8")
    (repo / "staged.txt").write_text("one\n", encoding="utf-8")
    subprocess.run([*run, "add", "tracked.txt", "staged.txt"], cwd=repo, check=True)
    subprocess.run([*run, "commit", "-qm", "init"], cwd=repo, check=True)

    assert research_session.dirty_summary(repo) == {
        "clean": True,
        "staged": 0,
        "unstaged": 0,
        "untracked": 0,
    }

    (repo / "tracked.txt").write_text("two\n", encoding="utf-8")  # unstaged: " M"
    (repo / "staged.txt").write_text("two\n", encoding="utf-8")
    subprocess.run([*run, "add", "staged.txt"], cwd=repo, check=True)  # staged: "M "
    (repo / "new.txt").write_text("three\n", encoding="utf-8")  # untracked: "??"

    assert research_session.dirty_summary(repo) == {
        "clean": False,
        "staged": 1,
        "unstaged": 1,
        "untracked": 1,
    }


def test_slug_is_deterministic_and_filesystem_safe():
    assert research_session.session_slug("205", "zach") == "issue-205-zach"
    assert research_session.session_slug("205", "zach") == research_session.session_slug(
        "205", "zach"
    )
    assert research_session.session_slug("205", None) == "issue-205"
    messy = research_session.session_slug("#205 ", "Zach / Two")
    assert SLUG_SAFE.match(messy), messy
    assert messy == "issue-205-zach-two"
    with pytest.raises(research_session.SessionError):
        research_session.session_slug("///", None)


def test_existing_session_fails_without_resume_or_force(
    workbench: Path, capsys: pytest.CaptureFixture[str]
):
    assert _start() == 0
    capsys.readouterr()
    assert _start() == 2
    err = capsys.readouterr().err
    assert "SESSION_EXISTS" in err
    assert "--resume" in err and "--force" in err


def test_resume_reopens_without_touching_scratch_or_exports(workbench: Path):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    sentinel = session_dir / "scratch" / "notebook.ipynb"
    sentinel.write_text("{}", encoding="utf-8")
    export = session_dir / "exports" / "figure.pdf"
    export.write_text("pdf", encoding="utf-8")

    first = _record(workbench)
    first["owner_note"] = "keep me"
    (session_dir / "session.json").write_text(
        json.dumps(first, indent=2) + "\n", encoding="utf-8"
    )

    assert _start("--resume") == 0
    second = _record(workbench)
    assert second["state"] == "resumed"
    assert second["owner_note"] == "keep me"
    assert second["created_at"] == first["created_at"]
    assert sentinel.read_text(encoding="utf-8") == "{}"
    assert export.read_text(encoding="utf-8") == "pdf"
    assert [path.name for path in sorted(workbench.iterdir())] == ["issue-205-zach"]


def test_resume_warns_loudly_when_repository_identity_moved(
    workbench: Path, capsys: pytest.CaptureFixture[str]
):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = _record(workbench)
    record["repositories"]["analysis"] = "/somewhere/else/analysis"
    session_file.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    capsys.readouterr()

    assert _start("--resume") == 0
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "analysis repository moved" in err
    assert any("moved" in warning for warning in _record(workbench)["warnings"])


def test_resume_without_an_existing_session_fails(
    workbench: Path, capsys: pytest.CaptureFixture[str]
):
    assert _start("--resume") == 2
    assert "NO_SESSION" in capsys.readouterr().err


def test_force_overwrites_and_keeps_the_human_contract(workbench: Path):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    contract = session_dir / "TASK.md"
    contract.write_text("Scientific phase: exploration\n\nObjective: mine\n", encoding="utf-8")
    first = _record(workbench)
    first["owner_note"] = "discard me"
    (session_dir / "session.json").write_text(
        json.dumps(first, indent=2) + "\n", encoding="utf-8"
    )

    assert _start("--force") == 0
    second = _record(workbench)
    assert second["state"] == "created"
    assert "owner_note" not in second
    assert contract.read_text(encoding="utf-8") == (
        "Scientific phase: exploration\n\nObjective: mine\n"
    )


def test_resume_and_force_are_mutually_exclusive(workbench: Path):
    with pytest.raises(SystemExit) as exc:
        _start("--resume", "--force")
    assert exc.value.code != 0


def test_unknown_phase_exits_non_zero(workbench: Path):
    with pytest.raises(SystemExit) as exc:
        research_session.main(["start", "--issue", "205", "--phase", "bogus"])
    assert exc.value.code != 0


def test_json_output_parses(workbench: Path, capsys: pytest.CaptureFixture[str]):
    assert _start("--json") == 0
    record = json.loads(capsys.readouterr().out)
    assert record["slug"] == "issue-205-zach"
    assert record["state"] == "created"


def test_origin_main_comparison_never_fetches(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    seen: list[list[str]] = []
    real_run = research_session.subprocess.run

    def _spy(argv, *args, **kwargs):
        seen.append(list(argv))
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(research_session.subprocess, "run", _spy)
    assert _start() == 0
    assert not any("fetch" in argv for argv in seen), seen

    origin = _record(workbench)["git"]["analysis"]["origin_main"]
    assert set(origin) == {"local_ref", "ahead", "behind", "comparison_basis"}
    assert "no fetch performed" in origin["comparison_basis"]
    if origin["local_ref"] is not None:
        assert SHA1.match(origin["local_ref"])
        assert isinstance(origin["ahead"], int)
        assert isinstance(origin["behind"], int)


def test_fetch_is_opt_in(workbench: Path, monkeypatch: pytest.MonkeyPatch):
    calls: list[Path] = []

    def _spy(repo: Path) -> None:
        calls.append(repo)
        return None

    monkeypatch.setattr(research_session, "fetch_origin_main", _spy)
    assert _start() == 0
    assert calls == []

    assert _start("--force", "--fetch") == 0
    assert calls == [research_session.ANALYSIS_ROOT]
    origin = _record(workbench)["git"]["analysis"]["origin_main"]
    if origin["local_ref"] is not None:
        assert origin["comparison_basis"] == research_session.FETCHED_BASIS


def test_fetch_origin_main_updates_the_local_ref(tmp_path: Path):
    run = ["git", "-c", "user.email=t@e.st", "-c", "user.name=t"]
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    seed.mkdir()
    subprocess.run([*run, "init", "-q", "-b", "main", "."], cwd=seed, check=True)
    (seed / "a.txt").write_text("a\n", encoding="utf-8")
    subprocess.run([*run, "add", "a.txt"], cwd=seed, check=True)
    subprocess.run([*run, "commit", "-qm", "a"], cwd=seed, check=True)
    subprocess.run([*run, "clone", "-q", "--bare", str(seed), str(origin)], check=True)

    clone = tmp_path / "clone"
    subprocess.run([*run, "clone", "-q", str(origin), str(clone)], check=True)
    assert research_session.origin_main_state(clone)["behind"] == 0

    # Advance the remote by fetching into it; a push would hit the global gate.
    (seed / "b.txt").write_text("b\n", encoding="utf-8")
    subprocess.run([*run, "add", "b.txt"], cwd=seed, check=True)
    subprocess.run([*run, "commit", "-qm", "b"], cwd=seed, check=True)
    subprocess.run(
        [*run, "-C", str(origin), "fetch", "-q", str(seed), "main:main"], check=True
    )

    assert research_session.origin_main_state(clone)["behind"] == 0  # stale local ref
    assert research_session.fetch_origin_main(clone) is None
    after = research_session.origin_main_state(clone, fetched=True)
    assert after["behind"] == 1
    assert after["comparison_basis"] == research_session.FETCHED_BASIS


def test_worktree_is_opt_in_and_only_printed_by_default(
    workbench: Path, capsys: pytest.CaptureFixture[str]
):
    assert _start() == 0
    out = capsys.readouterr().out
    assert "worktree: not created" in out
    assert "--resume --worktree" in out
    assert "git worktree add" not in out
    assert not (workbench / "issue-205-zach" / "worktree").exists()
    assert _record(workbench)["worktree"]["created"] is False


def test_unresolved_manuscript_is_recorded_not_fatal(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    def _raise() -> Path:
        raise RuntimeError("set FABER2026_ROOT=/path/to/Faber2026")

    monkeypatch.setattr(research_session, "manuscript_root", _raise)
    assert _start() == 0
    record = _record(workbench)
    assert record["repositories"]["manuscript"] is None
    assert "FABER2026_ROOT" in record["git"]["manuscript"]["error"]
    assert "FABER2026_ROOT" in capsys.readouterr().out


def test_next_commands_are_copy_pasteable(workbench: Path, capsys: pytest.CaptureFixture[str]):
    assert _start() == 0
    out = capsys.readouterr().out
    assert ".venv/bin/python" in out
    assert "ipykernel" in out
    assert "origin/main" in out
    assert "TASK.md" in out


def test_empty_workbench_override_is_treated_as_unset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FABER2026_WORKBENCH", "")
    assert research_session.workbench_root() == research_session.DEFAULT_WORKBENCH.resolve()
    assert research_session.workbench_root_source() == "default"


def test_workbench_inside_the_analysis_checkout_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
):
    inside = research_session.ANALYSIS_ROOT / "tmp-workbench-test"
    inside.mkdir(exist_ok=True)
    monkeypatch.setenv("FABER2026_WORKBENCH", str(inside))
    try:
        with pytest.raises(research_session.SessionError) as excinfo:
            research_session.require_workbench_root()
        assert excinfo.value.code == "WORKBENCH_INSIDE_CHECKOUT"
    finally:
        inside.rmdir()


def test_resume_refuses_to_overwrite_a_malformed_record(workbench: Path, capsys):
    session_dir = workbench / "issue-205-zach"
    session_dir.mkdir()
    session_file = session_dir / "session.json"
    session_file.write_text("{truncated", encoding="utf-8")
    assert _start("--resume") == 2
    assert session_file.read_text(encoding="utf-8") == "{truncated"
    assert "MALFORMED_SESSION" in capsys.readouterr().err


def test_resume_preserves_recorded_checks(workbench: Path):
    assert _start("--check", "make test") == 0
    assert _start("--resume") == 0
    assert _record(workbench)["checks"] == ["make test"]


def test_resume_rejects_a_slug_collision_with_different_identifiers(
    workbench: Path, capsys
):
    assert _start() == 0
    code = research_session.main(
        ["start", "--issue", "205", "--phase", "exploration", "--event", "Zach.", "--resume"]
    )
    assert code == 2
    assert "IDENTITY_MISMATCH" in capsys.readouterr().err
    assert _record(workbench)["event"] == "zach"


def test_validation_phase_writes_the_documented_header(workbench: Path):
    assert (
        research_session.main(["start", "--issue", "205", "--phase", "validation"]) == 0
    )
    task = (workbench / "issue-205" / "TASK.md").read_text(encoding="utf-8")
    assert task.startswith("Scientific phase: scientific validation\n")


def test_worktree_requires_a_filled_contract(workbench: Path, capsys):
    assert _start() == 0
    assert _start("--resume", "--worktree") == 2
    assert "CONTRACT_INCOMPLETE" in capsys.readouterr().err
    assert not (workbench / "issue-205-zach" / "worktree").exists()


def test_worktree_session_records_the_worktree_interpreter(workbench: Path):
    assert _start("--worktree", "--dry-run") == 0
    assert _start() == 0
    record_plain = _record(workbench)
    assert record_plain["project"] == str(research_session.ANALYSIS_ROOT)


def test_existing_plain_directory_is_not_reported_as_a_worktree():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "worktree"
        fake.mkdir()
        created, failure = research_session.add_worktree(fake, "test-slug")
        assert created is False
        assert failure is not None and "not a registered git worktree" in failure


def test_resume_rejects_replacement_checks(workbench: Path, capsys):
    assert _start("--check", "make test") == 0
    assert _start("--resume", "--check", "make lint") == 2
    assert "CHECKS_ON_RESUME" in capsys.readouterr().err
    assert _record(workbench)["checks"] == ["make test"]


def test_resume_rejects_an_unsupported_schema_version(workbench: Path, capsys):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["schema_version"] = 99
    session_file.write_text(json.dumps(record), encoding="utf-8")
    assert _start("--resume") == 2
    assert "SCHEMA_MISMATCH" in capsys.readouterr().err


def test_resume_rejects_a_phase_mismatch(workbench: Path, capsys):
    assert _start() == 0
    code = research_session.main(
        ["start", "--issue", "205", "--phase", "publication", "--event", "zach", "--resume"]
    )
    assert code == 2
    assert "PHASE_MISMATCH" in capsys.readouterr().err


def test_contract_gate_requires_all_five_fields(tmp_path: Path):
    task = tmp_path / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective:\n  measure\n\nMay change:\n\n"
        "Must not change:\n\nDone when:\n  done\n\nVerification command:\n  make test\n",
        encoding="utf-8",
    )
    assert research_session.contract_incomplete(task) == "'May change'"


def test_registered_worktree_on_the_wrong_branch_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    fake = tmp_path / "wt"
    fake.mkdir()
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(research_session, "_branch", lambda _p: "main")
    created, failure = research_session.add_worktree(fake, "test-slug")
    assert created is False
    assert failure is not None and "session/test-slug" in failure


def test_git_state_can_describe_a_worktree_checkout(tmp_path: Path):
    state, _ = research_session.collect_git_state(analysis_checkout=tmp_path)
    assert state["analysis"]["checkout"] == str(tmp_path)


def test_contract_gate_accepts_the_inline_form(tmp_path: Path):
    task = tmp_path / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: measure x\n\n"
        "May change: notebooks\n\nMust not change: configs\n\n"
        "Done when: figure exported\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    assert research_session.contract_incomplete(task) is None


def test_contract_gate_requires_the_phase_line(tmp_path: Path):
    task = tmp_path / "TASK.md"
    task.write_text(
        "Objective: x\n\nMay change: y\n\nMust not change: z\n\n"
        "Done when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    assert research_session.contract_incomplete(task) == "'Scientific phase'"


def test_resume_rejects_a_contract_without_a_phase_line(workbench: Path, capsys):
    assert _start() == 0
    task = workbench / "issue-205-zach" / "TASK.md"
    task.write_text(
        task.read_text(encoding="utf-8").replace("Scientific phase: exploration\n", ""),
        encoding="utf-8",
    )
    assert _start("--resume") == 2
    assert "PHASE_MISSING" in capsys.readouterr().err


def test_resume_rejects_a_switched_worktree_branch(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    (workbench / "issue-205-zach" / "worktree").mkdir()
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(research_session, "_branch", lambda _p: "main")
    assert _start("--resume") == 2
    assert "WORKTREE_BRANCH_MISMATCH" in capsys.readouterr().err


def test_next_commands_quote_paths_with_spaces(workbench: Path):
    record = {
        "project": "/tmp/a space/worktree",
        "repositories": {"analysis": "/tmp/a space/worktree"},
        "interpreter": "/tmp/a space/worktree/.venv/bin/python",
        "workbench": {"task_file": "/tmp/a space/TASK.md"},
        "slug": "s",
    }
    printed = "\n".join(research_session.next_commands(record))
    assert "'/tmp/a space/worktree'" in printed
    assert "'/tmp/a space/TASK.md'" in printed


def test_report_prints_no_manual_worktree_command(workbench: Path, capsys):
    assert _start() == 0
    out = capsys.readouterr().out
    assert "git worktree add" not in out
    assert "--resume --worktree" in out


def test_failed_worktree_creation_cleans_up_branch_and_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    # Since round thirty-two, branch deletion is proven-own only: the branch
    # must have been absent at the in-lock check AND its post-failure tip must
    # equal the base this add would have created it from.
    target = tmp_path / "worktree"
    cleaned: dict = {}
    verify_states = iter([None, None, "our-base"])

    def fake_run(argv, **kwargs):
        target.mkdir()
        (target / ".git").write_text("gitdir: partial", encoding="utf-8")
        class Proc:
            returncode = 1
            stderr = "smudge filter failed"
            stdout = ""
        return Proc()

    def fake_git(args, cwd, *, strip=True):
        if args[:2] == ["rev-parse", "--verify"]:
            return next(verify_states, "our-base")
        if args == ["rev-parse", "HEAD"]:
            # Partial checkout: HEAD resolves only in the ANALYSIS repo (the
            # base lookup), never inside the partial worktree itself.
            return "our-base" if cwd == research_session.ANALYSIS_ROOT else None
        cleaned.setdefault("git_calls", []).append(args)
        return ""

    monkeypatch.setattr(research_session.subprocess, "run", fake_run)
    monkeypatch.setattr(research_session, "_git", fake_git)
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: False)
    created, failure = research_session.add_worktree(target, "test-slug")
    assert created is False and "smudge" in failure
    assert not target.exists()
    assert ["worktree", "prune"] in cleaned["git_calls"]
    assert [
        "update-ref", "-d", "refs/heads/session/test-slug", "our-base"
    ] in cleaned["git_calls"]


def test_resume_rejects_a_vanished_worktree(workbench: Path, capsys):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    session_file.write_text(json.dumps(record), encoding="utf-8")
    assert _start("--resume") == 2
    assert "WORKTREE_MISSING" in capsys.readouterr().err


def test_resume_syncs_checks_from_the_edited_contract(workbench: Path):
    assert _start() == 0
    task = workbench / "issue-205-zach" / "TASK.md"
    task.write_text(
        task.read_text(encoding="utf-8").replace(
            "Verification command:", "Verification command:\n  make test-notebook"
        ),
        encoding="utf-8",
    )
    assert _start("--resume") == 0
    assert _record(workbench)["checks"] == ["make test-notebook"]


def test_cleanup_force_removes_a_registered_partial_worktree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    target = tmp_path / "worktree"
    target.mkdir()
    (target / ".git").write_text("gitdir: partial", encoding="utf-8")
    calls: list = []
    states = iter([True, False])

    monkeypatch.setattr(
        research_session, "registered_worktree", lambda _p: next(states)
    )
    monkeypatch.setattr(research_session, "_head", lambda _p: None)
    monkeypatch.setattr(
        research_session, "_git", lambda args, cwd, **k: calls.append(args) or ""
    )
    research_session._cleanup_failed_worktree(
        target, "test-slug", False, expected_branch_tip="our-base"
    )
    assert ["worktree", "remove", "--force", str(target)] in calls
    assert ["worktree", "prune"] in calls
    assert [
        "update-ref", "-d", "refs/heads/session/test-slug", "our-base"
    ] in calls
    assert not target.exists()


def test_next_commands_put_the_contract_first(workbench: Path):
    assert _start() == 0
    lines = research_session.next_commands(_record(workbench))
    assert lines[0].startswith("1) fill in the contract")


def test_workbench_inside_a_registered_worktree_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    wt = tmp_path / "some-worktree"
    (wt / "sub").mkdir(parents=True)
    monkeypatch.setenv("FABER2026_WORKBENCH", str(wt / "sub"))
    monkeypatch.setattr(
        research_session, "analysis_worktree_paths", lambda: [wt]
    )
    with pytest.raises(research_session.SessionError) as excinfo:
        research_session.require_workbench_root()
    assert excinfo.value.code == "WORKBENCH_INSIDE_CHECKOUT"


def test_worktree_recovery_reuses_a_preserved_session_branch():
    fresh = research_session.worktree_argv(Path("/tmp/wt"), "s", branch_exists=False)
    assert fresh[-2:] == ["-b", "session/s"]
    recovery = research_session.worktree_argv(Path("/tmp/wt"), "s", branch_exists=True)
    assert recovery[-1] == "session/s"
    assert "-b" not in recovery


def test_next_commands_use_the_admitted_frozen_rebuild(workbench: Path):
    assert _start() == 0
    printed = "\n".join(research_session.next_commands(_record(workbench)))
    assert "env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT" in printed
    assert "uv sync --frozen --group notebook" in printed
    assert "--locked" not in printed


def test_workbench_inside_a_manuscript_worktree_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    wt = tmp_path / "ms-worktree"
    (wt / "sub").mkdir(parents=True)
    monkeypatch.setenv("FABER2026_WORKBENCH", str(wt / "sub"))
    monkeypatch.setattr(research_session, "analysis_worktree_paths", lambda: [])
    monkeypatch.setattr(
        research_session, "worktree_paths", lambda repo: [wt] if repo else []
    )
    monkeypatch.setattr(
        research_session, "resolve_manuscript", lambda: (tmp_path / "ms", None)
    )
    with pytest.raises(research_session.SessionError) as excinfo:
        research_session.require_workbench_root()
    assert excinfo.value.code == "WORKBENCH_INSIDE_CHECKOUT"


def test_branch_recreation_bases_on_the_recorded_commit():
    argv = research_session.worktree_argv(
        Path("/tmp/wt"), "s", branch_exists=False, base_commit="abc123"
    )
    assert argv[-3:] == ["-b", "session/s", "abc123"]


def test_dry_run_resume_reports_a_registered_worktree(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    (workbench / "issue-205-zach" / "worktree").mkdir()
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    session_file.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda p: "session/issue-205-zach"
    )
    capsys.readouterr()
    assert _start("--resume", "--dry-run") == 0
    assert "worktree: not created" not in capsys.readouterr().out


def test_resume_clears_checks_when_the_contract_clears_them(workbench: Path):
    assert _start("--check", "make test") == 0
    task = workbench / "issue-205-zach" / "TASK.md"
    task.write_text(
        task.read_text(encoding="utf-8").replace("\n  make test", ""),
        encoding="utf-8",
    )
    assert _start("--resume") == 0
    assert _record(workbench)["checks"] == []


def test_force_rejects_checks_and_phase_conflicts_with_a_preserved_contract(
    workbench: Path, capsys
):
    assert _start() == 0
    assert _start("--force", "--check", "make test") == 2
    assert "CHECKS_ON_FORCE" in capsys.readouterr().err
    code = research_session.main(
        ["start", "--issue", "205", "--phase", "publication", "--event", "zach", "--force"]
    )
    assert code == 2
    assert "PHASE_MISMATCH" in capsys.readouterr().err


def test_resume_rejects_a_record_without_a_worktree_field(workbench: Path, capsys):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    del record["worktree"]
    session_file.write_text(json.dumps(record), encoding="utf-8")
    assert _start("--resume") == 2
    assert "MALFORMED_SESSION" in capsys.readouterr().err


def test_symlinked_session_directory_is_rejected(
    workbench: Path, tmp_path: Path, capsys
):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (workbench / "issue-205-zach").symlink_to(outside)
    assert _start() == 2
    assert "SESSION_DIR_NOT_PLAIN" in capsys.readouterr().err
    assert not (outside / "TASK.md").exists()


def test_next_commands_clear_both_uv_environment_variables(workbench: Path):
    assert _start() == 0
    printed = "\n".join(research_session.next_commands(_record(workbench)))
    assert "-u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT" in printed


def test_contract_gate_matches_the_documented_five_line_header(tmp_path: Path):
    task = tmp_path / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: measure x\n\n"
        "May change: notebooks\n\nMust not change: configs\n\n"
        "Done when: figure exported\n",
        encoding="utf-8",
    )
    assert research_session.contract_incomplete(task) is None


def test_force_adopts_the_preserved_contract_checks(workbench: Path):
    assert _start("--check", "make test") == 0
    assert _start("--force") == 0
    assert _record(workbench)["checks"] == ["make test"]


def test_concurrent_slug_claim_is_exclusive(workbench: Path):
    session_dir = workbench / "issue-205-zach"
    session_dir.mkdir()
    research_session.claim_session_file(session_dir / "session.json")
    with pytest.raises(research_session.SessionError) as excinfo:
        research_session.claim_session_file(session_dir / "session.json")
    assert excinfo.value.code == "SESSION_EXISTS"


def test_contract_gate_rejection_leaves_a_resumable_record(workbench: Path, capsys):
    assert _start("--worktree") == 2
    assert "CONTRACT_INCOMPLETE" in capsys.readouterr().err
    record = _record(workbench)
    assert record["slug"] == "issue-205-zach"
    assert _start("--resume") == 0


def test_stale_worktree_registration_is_pruned_on_start(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    # Since round twenty-seven a FRESH start refuses a stale registration
    # outright (recovery would otherwise be stranded); the repair still
    # happens only in add_worktree under the session lock, on resume.
    states = [True]
    pruned: list = []
    real_git = research_session._git

    def fake_git(args, cwd, **kwargs):
        if args[:2] == ["worktree", "prune"]:
            pruned.append(args)
            return ""
        return real_git(args, cwd, **kwargs)

    monkeypatch.setattr(
        research_session,
        "registered_worktree",
        lambda _p: states.pop() if states else False,
    )
    monkeypatch.setattr(research_session, "_git", fake_git)
    assert _start() == 2
    assert not pruned
    assert "STALE_WORKTREE_REGISTRATION" in capsys.readouterr().err


def test_fresh_start_rejects_a_leftover_contract(workbench: Path, capsys):
    session_dir = workbench / "issue-205-zach"
    session_dir.mkdir()
    (session_dir / "TASK.md").write_text(EMPTY_CONTRACT, encoding="utf-8")
    assert _start() == 2
    assert "STALE_CONTRACT" in capsys.readouterr().err


def test_new_session_rejects_a_stale_session_branch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    target = tmp_path / "worktree"
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: "deadbeef" if args[:2] == ["rev-parse", "--verify"] else "",
    )
    created, failure = research_session.add_worktree(target, "old-slug")
    assert created is False
    assert "never worktree-backed" in failure
    created, failure = research_session.add_worktree(
        target, "old-slug", allow_branch_reuse=True
    )
    assert failure is None or "never worktree-backed" not in failure


def test_dry_run_does_not_prune_stale_registrations(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    calls: list = []
    real_git = research_session._git

    def fake_git(args, cwd, **kwargs):
        calls.append(args)
        return real_git(args, cwd, **kwargs)

    states = [True]
    monkeypatch.setattr(
        research_session,
        "registered_worktree",
        lambda _p: states.pop() if states else False,
    )
    monkeypatch.setattr(research_session, "_git", fake_git)
    assert _start("--dry-run") == 2
    assert ["worktree", "prune"] not in calls
    assert "STALE_WORKTREE_REGISTRATION" in capsys.readouterr().err


def test_locked_stale_registration_is_unlocked_and_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # The unlock/prune/remove sequence now lives in add_worktree, under the
    # per-session creation lock.
    target = tmp_path / "worktree"
    git_calls: list = []
    reg = iter([True, True, True, False])

    def fake_git(args, cwd, **kwargs):
        git_calls.append(args)
        if args[:2] == ["rev-parse", "--verify"]:
            return None
        return ""

    def ok_run(argv, **kwargs):
        class Proc:
            returncode = 0
            stderr = ""
            stdout = ""
        return Proc()

    monkeypatch.setattr(
        research_session, "registered_worktree", lambda _p: next(reg, False)
    )
    monkeypatch.setattr(research_session, "_git", fake_git)
    monkeypatch.setattr(research_session.subprocess, "run", ok_run)
    created, failure = research_session.add_worktree(target, "s")
    assert failure is None and created is True
    assert any(a[:2] == ["worktree", "unlock"] for a in git_calls)
    assert ["worktree", "prune"] in git_calls


def test_worktree_creation_is_lock_serialized(tmp_path: Path, monkeypatch):
    target = tmp_path / "worktree"
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: None if args[:2] == ["rev-parse", "--verify"] else "",
    )
    lock = tmp_path / ".worktree.creating"
    lock.touch()
    created, failure = research_session.add_worktree(target, "s")
    assert created is False and "another invocation" in failure
    lock.unlink()

    def fail_run(argv, **kwargs):
        assert (tmp_path / ".worktree.creating").exists()
        class Proc:
            returncode = 1
            stderr = "boom"
            stdout = ""
        return Proc()

    monkeypatch.setattr(research_session.subprocess, "run", fail_run)
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: False)
    created, failure = research_session.add_worktree(target, "s")
    assert created is False and "boom" in failure
    assert not (tmp_path / ".worktree.creating").exists()


def test_session_dir_that_is_a_registered_checkout_is_rejected(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    session_dir = workbench / "issue-205-zach"
    session_dir.mkdir()
    monkeypatch.setattr(
        research_session, "worktree_paths", lambda repo: [session_dir]
    )
    assert _start() == 2
    assert "SESSION_DIR_IS_CHECKOUT" in capsys.readouterr().err


def test_worktree_recreation_requires_the_recorded_commit(workbench: Path, capsys):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    record = _record(workbench)
    record["worktree"]["created"] = True
    del record["git"]["analysis"]["head"]
    (session_dir / "session.json").write_text(json.dumps(record), encoding="utf-8")
    assert _start("--resume", "--worktree") == 2
    assert "RECORD_INCOMPLETE" in capsys.readouterr().err


def test_resume_rejects_a_record_without_identity_fields(workbench: Path, capsys):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    del record["event"]
    session_file.write_text(json.dumps(record), encoding="utf-8")
    assert _start("--resume") == 2
    assert "RECORD_INCOMPLETE" in capsys.readouterr().err


def test_late_registered_worktree_rebuilds_dependent_fields(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    worktree_dir = workbench / "issue-205-zach" / "worktree"
    worktree_dir.mkdir()
    # Planning sees no worktree; the final recheck sees a concurrent winner's.
    calls = {"n": 0}

    def registered(_p):
        calls["n"] += 1
        return calls["n"] >= 2

    monkeypatch.setattr(research_session, "registered_worktree", registered)
    monkeypatch.setattr(
        research_session, "_branch", lambda p: "session/issue-205-zach"
    )
    recorded_head = _record(workbench)["git"]["analysis"]["head"]
    monkeypatch.setattr(research_session, "_head", lambda _p: recorded_head)
    real_git = research_session._git
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: ""
        if args[:2] == ["merge-base", "--is-ancestor"]
        else real_git(args, cwd, **k),
    )
    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: {"worktree": {"pending": "other-invocation"}},
    )
    assert _start("--resume") == 0
    record = _record(workbench)
    assert record["worktree"]["created"] is True
    assert record["project"] == str(worktree_dir)
    assert record["interpreter"] == str(worktree_dir / ".venv" / "bin" / "python")


def test_losing_concurrent_worktree_creation_rebuilds_provenance(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    worktree_dir = workbench / "issue-205-zach" / "worktree"
    worktree_dir.mkdir()
    task = workbench / "issue-205-zach" / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    calls = {"n": 0}

    def registered(_p):
        calls["n"] += 1
        return calls["n"] >= 2  # planning misses it; the winner registers it

    monkeypatch.setattr(research_session, "registered_worktree", registered)
    monkeypatch.setattr(
        research_session, "_branch", lambda p: "session/issue-205-zach"
    )
    monkeypatch.setattr(
        research_session,
        "add_worktree",
        lambda *a, **k: (False, None),  # loser: worktree already exists, no error
    )
    recorded_head = _record(workbench)["git"]["analysis"]["head"]
    monkeypatch.setattr(research_session, "_head", lambda _p: recorded_head)
    real_git = research_session._git
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: ""
        if args[:2] == ["merge-base", "--is-ancestor"]
        else real_git(args, cwd, **k),
    )
    assert _start("--resume", "--worktree") == 0
    record = _record(workbench)
    assert record["worktree"]["created"] is True
    assert record["git"]["analysis"]["checkout"] == str(worktree_dir)


def test_redirected_scratch_symlink_is_rejected(workbench: Path, tmp_path: Path, capsys):
    session_dir = workbench / "issue-205-zach"
    session_dir.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (session_dir / "scratch").symlink_to(outside)
    assert _start() == 2
    assert "SESSION_CHILD_REDIRECTED" in capsys.readouterr().err


def test_stale_registration_repair_happens_under_the_creation_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"
    git_calls: list = []
    reg_states = iter([True, False])  # stale-check under lock, post-prune

    def fake_git(args, cwd, **kwargs):
        if args[0] == "worktree" or args[:2] == ["rev-parse", "--verify"]:
            git_calls.append(args)
            if args[:2] == ["rev-parse", "--verify"]:
                return None
            assert (tmp_path / ".worktree.creating").exists(), (
                "stale repair must run under the lock"
            )
            return ""
        return ""

    def fake_run(argv, **kwargs):
        class Proc:
            returncode = 0
            stderr = ""
            stdout = ""
        return Proc()

    monkeypatch.setattr(
        research_session,
        "registered_worktree",
        lambda _p: next(reg_states, False),
    )
    monkeypatch.setattr(research_session, "_git", fake_git)
    monkeypatch.setattr(research_session.subprocess, "run", fake_run)
    created, failure = research_session.add_worktree(target, "s")
    assert failure is None and created is True
    assert ["worktree", "prune"] in git_calls


def test_lock_recheck_adopts_a_concurrently_created_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"

    def registered(_p):
        # Pre-lock check: absent; post-lock recheck: the winner registered it.
        return target.exists()

    monkeypatch.setattr(research_session, "registered_worktree", registered)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/s"
    )
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: None if args[:2] == ["rev-parse", "--verify"] else "",
    )
    real_open = research_session.os.open

    def open_and_create(path, flags, *a):
        fd = real_open(path, flags, *a)
        target.mkdir()  # the concurrent winner finishes between check and lock
        return fd

    monkeypatch.setattr(research_session.os, "open", open_and_create)
    created, failure = research_session.add_worktree(target, "s")
    assert created is False and failure is None
    assert target.exists(), "the winner's worktree must never be torn down"


def test_resume_validates_children_and_contract_redirection(
    workbench: Path, tmp_path: Path, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    outside = tmp_path / "outside"
    outside.mkdir()
    scratch = session_dir / "scratch"
    import shutil as _sh

    _sh.rmtree(scratch)
    scratch.symlink_to(outside)
    assert _start("--resume") == 2
    assert "SESSION_CHILD_REDIRECTED" in capsys.readouterr().err
    scratch.unlink()
    scratch.mkdir()

    task = session_dir / "TASK.md"
    moved = tmp_path / "TASK.md"
    task.rename(moved)
    task.symlink_to(moved)
    assert _start("--resume") == 2
    assert "CONTRACT_REDIRECTED" in capsys.readouterr().err


def test_resume_rejects_an_unrecorded_registered_worktree(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    (workbench / "issue-205-zach" / "worktree").mkdir()
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    assert _start("--resume") == 2
    assert "WORKTREE_UNRECORDED" in capsys.readouterr().err


def test_task_contract_as_directory_is_rejected(workbench: Path, capsys):
    session_dir = workbench / "issue-205-zach"
    (session_dir / "TASK.md").mkdir(parents=True)
    assert _start() == 2
    assert "CONTRACT_REDIRECTED" in capsys.readouterr().err


def test_managed_child_as_regular_file_is_rejected(workbench: Path, capsys):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    import shutil as _sh

    _sh.rmtree(session_dir / "scratch")
    (session_dir / "scratch").write_text("not a directory", encoding="utf-8")
    assert _start("--resume") == 2
    assert "SESSION_CHILD_REDIRECTED" in capsys.readouterr().err


def test_session_path_as_regular_file_is_rejected(workbench: Path, capsys):
    (workbench / "issue-205-zach").write_text("not a directory", encoding="utf-8")
    assert _start() == 2
    assert "SESSION_DIR_NOT_PLAIN" in capsys.readouterr().err


def test_workbench_inside_a_reserved_data_tree_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    reserved = tmp_path / "dsa110"
    (reserved / "sub").mkdir(parents=True)
    monkeypatch.setattr(research_session, "RESERVED_DATA_TREES", (reserved,))
    monkeypatch.setenv("FABER2026_WORKBENCH", str(reserved / "sub"))
    with pytest.raises(research_session.SessionError) as excinfo:
        research_session.require_workbench_root()
    assert excinfo.value.code == "WORKBENCH_IN_DATA_TREE"


def test_symlinked_worktree_path_is_never_registered(tmp_path: Path, monkeypatch):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "worktree"
    link.symlink_to(real)
    monkeypatch.setattr(
        research_session, "analysis_worktree_paths", lambda: [real]
    )
    assert research_session.registered_worktree(link) is False
    assert research_session.registered_worktree(real) is True


def test_interrupted_worktree_creation_stays_recoverable(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )

    def interrupt(*a, **k):
        raise KeyboardInterrupt

    monkeypatch.setattr(research_session, "add_worktree", interrupt)
    with pytest.raises(KeyboardInterrupt):
        _start("--resume", "--worktree")
    record = _record(workbench)
    assert record["worktree"]["pending"]

    # The interrupted creation registered the worktree; a plain resume must
    # accept it (pending counts as recorded ownership), not raise UNRECORDED.
    (session_dir / "worktree").mkdir()
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    monkeypatch.setattr(
        research_session, "add_worktree", lambda *a, **k: (False, None)
    )
    recorded_head = record["git"]["analysis"]["head"]
    monkeypatch.setattr(research_session, "_head", lambda _p: recorded_head)
    real_git = research_session._git
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: ""
        if args[:2] == ["merge-base", "--is-ancestor"]
        else real_git(args, cwd, **k),
    )
    assert _start("--resume") == 0


def test_branch_reuse_requires_the_recorded_base_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"

    def fake_git(args, cwd, **kwargs):
        if args[:2] == ["rev-parse", "--verify"]:
            return "deadbeef"  # branch exists
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return None  # recorded base NOT in the branch lineage
        return ""

    monkeypatch.setattr(research_session, "_git", fake_git)
    created, failure = research_session.add_worktree(
        target, "s", "a" * 40, allow_branch_reuse=True
    )
    assert created is False
    assert "another lineage" in failure


def test_reserved_tree_symlink_alias_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    real = tmp_path / "real-dsa110"
    (real / "sub").mkdir(parents=True)
    alias = tmp_path / "alias"
    alias.symlink_to(real)
    monkeypatch.setattr(research_session, "RESERVED_DATA_TREES", (alias,))
    monkeypatch.setenv("FABER2026_WORKBENCH", str(real / "sub"))
    with pytest.raises(research_session.SessionError) as excinfo:
        research_session.require_workbench_root()
    assert excinfo.value.code == "WORKBENCH_IN_DATA_TREE"


def test_fresh_start_rejects_a_preregistered_worktree(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    (workbench / "issue-205-zach" / "worktree").mkdir(parents=True)
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    assert _start() == 2
    assert "WORKTREE_UNRECORDED" in capsys.readouterr().err


def test_pending_recovery_requires_lineage_of_the_registered_checkout(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["pending"] = True
    session_file.write_text(json.dumps(record), encoding="utf-8")
    (workbench / "issue-205-zach" / "worktree").mkdir()
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    real_git = research_session._git

    def fake_git(args, cwd, **kwargs):
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return None  # unrelated lineage
        return real_git(args, cwd, **kwargs)

    monkeypatch.setattr(research_session, "_git", fake_git)
    assert _start("--resume") == 2
    assert "WORKTREE_LINEAGE_MISMATCH" in capsys.readouterr().err


def test_plain_resume_preserves_a_concurrent_pending_marker(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"

    # A concurrent --resume --worktree persisted pending after this
    # invocation read the record; the merge read must carry it forward.
    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: {"worktree": {"pending": True}},
    )
    assert _start("--resume") == 0
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["pending"] is True


def test_managed_child_that_is_a_registered_checkout_is_rejected(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    scratch = workbench / "issue-205-zach" / "scratch"
    monkeypatch.setattr(
        research_session, "worktree_paths", lambda repo: [scratch]
    )
    assert _start("--resume") == 2
    assert "SESSION_CHILD_REDIRECTED" in capsys.readouterr().err


def test_final_write_rechecks_registration_under_the_write_lock(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    # Plain resume of a not-yet-worktree-backed record races a creator that
    # finishes between planning and the final locked write: the locked
    # recheck must record created=true instead of clobbering with false.
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"

    calls = {"n": 0}

    def registered(_p):
        calls["n"] += 1
        return calls["n"] >= 2

    monkeypatch.setattr(research_session, "registered_worktree", registered)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    recorded_head = _record(workbench)["git"]["analysis"]["head"]
    monkeypatch.setattr(research_session, "_head", lambda _p: recorded_head)
    real_git = research_session._git
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: ""
        if args[:2] == ["merge-base", "--is-ancestor"]
        else real_git(args, cwd, **k),
    )
    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: {"worktree": {"pending": "creator-invocation"}},
    )
    assert _start("--resume") == 0
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is True
    assert final["project"] == str(session_dir / "worktree")
    assert not (session_dir / "session.json.writing").exists()


def test_final_write_times_out_on_a_held_lock(workbench: Path, monkeypatch, capsys):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "session.json.writing").touch()
    monkeypatch.setattr(research_session.time, "sleep", lambda _s: None)
    assert _start("--resume") == 2
    assert "RECORD_LOCKED" in capsys.readouterr().err


def test_fetch_origin_main_uses_a_destination_refspec(monkeypatch, tmp_path: Path):
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        class Proc:
            returncode = 0
            stderr = ""
            stdout = ""
        return Proc()

    monkeypatch.setattr(research_session.subprocess, "run", fake_run)
    tmp_path.mkdir(exist_ok=True)
    assert research_session.fetch_origin_main(tmp_path) is None
    assert seen["argv"][-1] == "+refs/heads/main:refs/remotes/origin/main"


def test_stale_session_dir_registration_blocks_fresh_start(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    session_dir = workbench / "issue-205-zach"  # does NOT exist on disk
    monkeypatch.setattr(
        research_session, "worktree_paths", lambda repo: [session_dir]
    )
    assert _start() == 2
    assert "SESSION_DIR_IS_CHECKOUT" in capsys.readouterr().err


def test_failed_worktree_write_preserves_concurrent_ownership(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    session_file = session_dir / "session.json"

    def losing_add(*a, **k):
        # The winner persisted pending (and could still be mid-creation)
        # while this invocation lost the .creating lock.
        latest = json.loads(session_file.read_text(encoding="utf-8"))
        latest["worktree"]["pending"] = True
        session_file.write_text(json.dumps(latest), encoding="utf-8")
        return False, "another invocation is creating the worktree"

    monkeypatch.setattr(research_session, "add_worktree", losing_add)
    assert _start("--resume", "--worktree") == 1
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["pending"] is True


def test_unowned_late_registration_is_not_adopted(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    (workbench / "issue-205-zach" / "worktree").mkdir()
    calls = {"n": 0}

    def registered(_p):
        calls["n"] += 1
        return calls["n"] >= 2  # appears only at the final recheck, unowned

    monkeypatch.setattr(research_session, "registered_worktree", registered)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    assert _start("--resume") == 0
    err = capsys.readouterr().err
    assert "unrecorded party" in err
    assert _record(workbench)["worktree"]["created"] is False


def test_force_rejects_a_phase_less_preserved_contract(workbench: Path, capsys):
    assert _start() == 0
    task = workbench / "issue-205-zach" / "TASK.md"
    task.write_text(
        task.read_text(encoding="utf-8").replace("Scientific phase: exploration\n", ""),
        encoding="utf-8",
    )
    assert _start("--force") == 2
    assert "PHASE_MISSING" in capsys.readouterr().err


def test_pending_write_preserves_a_foreign_token(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["pending"] = "foreign-token"
    session_file.write_text(json.dumps(record), encoding="utf-8")

    seen = {}

    def failing_add(*a, **k):
        seen["pending"] = json.loads(session_file.read_text(encoding="utf-8"))[
            "worktree"
        ].get("pending")
        return False, "lost the creation lock"

    monkeypatch.setattr(research_session, "add_worktree", failing_add)
    monkeypatch.setattr(research_session, "_head", lambda _p: "a" * 40)
    real_git = research_session._git
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: ""
        if args[:2] == ["merge-base", "--is-ancestor"]
        else real_git(args, cwd, **k),
    )
    assert _start("--resume", "--worktree") == 1
    assert seen["pending"] == "foreign-token"
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["pending"] == "foreign-token"


def test_failed_recovery_of_an_owned_worktree_stays_retryable(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    session_file.write_text(json.dumps(record), encoding="utf-8")

    monkeypatch.setattr(
        research_session, "add_worktree", lambda *a, **k: (False, "transient")
    )
    assert _start("--resume", "--worktree") == 1
    final = json.loads(session_file.read_text(encoding="utf-8"))
    # Prior ownership survives the failed recovery: pending (ours) retained.
    assert final["worktree"]["pending"]


def test_session_record_symlink_is_rejected(workbench: Path, tmp_path: Path, capsys):
    session_dir = workbench / "issue-205-zach"
    session_dir.mkdir()
    external = tmp_path / "external.json"
    external.write_text("{}", encoding="utf-8")
    (session_dir / "session.json").symlink_to(external)
    assert _start("--resume") == 2
    assert "RECORD_REDIRECTED" in capsys.readouterr().err


def test_fresh_start_rejects_a_stale_worktree_registration(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    # Registered per git, but the directory is gone: fresh start must refuse.
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    assert _start() == 2
    assert "STALE_WORKTREE_REGISTRATION" in capsys.readouterr().err


def test_force_initialization_preserves_concurrent_ownership(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    # Since round thirty a live creation marker REJECTS --force outright
    # (CREATION_IN_FLIGHT) instead of merely preserving the marker.
    assert _start() == 0
    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: {"worktree": {"pending": "creator-token"}},
    )
    assert _start("--force") == 2
    assert "CREATION_IN_FLIGHT" in capsys.readouterr().err


def test_broken_symlink_in_managed_child_is_rejected(workbench: Path, capsys):
    session_dir = workbench / "issue-205-zach"
    session_dir.mkdir()
    (session_dir / "scratch").symlink_to(session_dir / "nowhere")
    assert _start() == 2
    assert "SESSION_CHILD_REDIRECTED" in capsys.readouterr().err


def test_stale_child_registration_is_rejected_without_directory(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    scratch = workbench / "issue-205-zach" / "scratch"  # never created on disk
    monkeypatch.setattr(
        research_session, "worktree_paths", lambda repo: [scratch]
    )
    assert _start() == 2
    assert "SESSION_CHILD_REDIRECTED" in capsys.readouterr().err


def test_malformed_git_state_yields_actionable_error_not_traceback(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["pending"] = "tok"
    record["git"]["analysis"] = "not-an-object"
    session_file.write_text(json.dumps(record), encoding="utf-8")
    (workbench / "issue-205-zach" / "worktree").mkdir()
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    assert _start("--resume") == 2
    err = capsys.readouterr().err
    assert "WORKTREE_LINEAGE_MISMATCH" in err


def test_late_disappearance_retains_ownership(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    session_file.write_text(json.dumps(record), encoding="utf-8")

    calls = {"n": 0}

    def registered(_p):
        calls["n"] += 1
        return calls["n"] == 1  # present at planning, gone at the final recheck

    monkeypatch.setattr(research_session, "registered_worktree", registered)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    assert _start("--resume") == 0
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False
    assert final["worktree"]["pending"]
    assert "ownership retained" in capsys.readouterr().err


def test_failure_cleanup_rebuilds_winner_provenance(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    # Since round forty-one the loser carries the WINNER'S validated fields
    # from its final write instead of sampling the checkout afresh.
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    session_file = session_dir / "session.json"

    def losing_add(*a, **k):
        latest = json.loads(session_file.read_text(encoding="utf-8"))
        latest["worktree"]["created"] = True
        latest["git"]["analysis"]["checkout"] = str(session_dir / "worktree")
        latest["project"] = str(session_dir / "worktree")
        latest["interpreter"] = str(
            session_dir / "worktree" / ".venv" / "bin" / "python"
        )
        session_file.write_text(json.dumps(latest), encoding="utf-8")
        return False, "lost the creation lock"

    monkeypatch.setattr(research_session, "add_worktree", losing_add)
    assert _start("--resume", "--worktree") == 1
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is True
    assert final["project"] == str(session_dir / "worktree")
    assert final["git"]["analysis"]["checkout"] == str(session_dir / "worktree")


def test_dangling_session_dir_symlink_is_rejected(workbench: Path, capsys):
    (workbench / "issue-205-zach").symlink_to(workbench / "nowhere")
    assert _start() == 2
    assert "SESSION_DIR_NOT_PLAIN" in capsys.readouterr().err


def test_dangling_worktree_symlink_is_rejected(tmp_path: Path, monkeypatch):
    target = tmp_path / "worktree"
    target.symlink_to(tmp_path / "nowhere")
    created, failure = research_session.add_worktree(target, "s")
    assert created is False
    assert "symlink" in failure


def test_resume_rejects_a_concurrently_replaced_record(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0

    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: {"created_at": "2099-01-01T00:00:00+00:00", "worktree": {}},
    )
    assert _start("--resume") == 2
    assert "RECORD_REPLACED" in capsys.readouterr().err


def test_fresh_dry_run_recommends_a_real_start_first(workbench: Path, capsys):
    assert _start("--dry-run") == 0
    out = capsys.readouterr().out
    assert "run the start for real" in out
    assert "(the printed environment commands refresh" not in out


def test_force_is_rejected_while_creation_is_in_flight(workbench: Path, capsys):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["pending"] = "creator-token"
    session_file.write_text(json.dumps(record), encoding="utf-8")
    assert _start("--force") == 2
    assert "CREATION_IN_FLIGHT" in capsys.readouterr().err


def test_second_force_revalidates_the_surviving_contract(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    task = workbench / "issue-205-zach" / "TASK.md"
    task.unlink()

    def racing_contract(task_file, phase, checks):
        # The first --force writes an exploration contract just before us.
        task_file.write_text(
            "Scientific phase: exploration\n\nObjective:\n\nMay change:\n\n"
            "Must not change:\n\nDone when:\n\nVerification command:\n",
            encoding="utf-8",
        )
        return False  # we observed it as already existing

    monkeypatch.setattr(research_session, "write_task_contract", racing_contract)
    code = research_session.main(
        ["start", "--issue", "205", "--phase", "publication", "--event", "zach", "--force"]
    )
    assert code == 2
    assert "PHASE_MISMATCH" in capsys.readouterr().err


def test_failure_cleanup_keeps_marker_while_creation_lock_is_held(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    session_file = session_dir / "session.json"
    (session_dir / ".worktree.creating").touch()  # an active creator holds it

    def losing_add(*a, **k):
        return False, "another invocation is creating the worktree"

    monkeypatch.setattr(research_session, "add_worktree", losing_add)
    assert _start("--resume", "--worktree") == 1
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["pending"]


def test_branch_created_concurrently_is_never_deleted_by_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"
    git_calls: list = []
    # Branch absent at the pre-lock check, present at the in-lock recheck.
    branch_states = iter([None, "deadbeef"])

    def fake_git(args, cwd, **kwargs):
        git_calls.append(args)
        if args[:2] == ["rev-parse", "--verify"]:
            return next(branch_states, "deadbeef")
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return ""
        return ""

    def fail_run(argv, **kwargs):
        class Proc:
            returncode = 1
            stderr = "branch already exists"
            stdout = ""
        return Proc()

    monkeypatch.setattr(research_session, "_git", fake_git)
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: False)
    monkeypatch.setattr(research_session.subprocess, "run", fail_run)
    created, failure = research_session.add_worktree(
        target, "s", allow_branch_reuse=True
    )
    assert created is False
    assert ["branch", "-D", "session/s"] not in git_calls


def test_appeared_checkout_requires_lineage_before_adoption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"

    def registered(_p):
        return target.exists()

    monkeypatch.setattr(research_session, "registered_worktree", registered)
    monkeypatch.setattr(research_session, "_branch", lambda _p: "session/s")
    monkeypatch.setattr(research_session, "_head", lambda _p: "f" * 40)
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: None
        if args[:2] in (["rev-parse", "--verify"], ["merge-base", "--is-ancestor"])
        else "",
    )
    real_open = research_session.os.open

    def open_and_create(path, flags, *a):
        fd = real_open(path, flags, *a)
        target.mkdir()  # a checkout appears after the lock is taken
        return fd

    monkeypatch.setattr(research_session.os, "open", open_and_create)
    created, failure = research_session.add_worktree(target, "s", "a" * 40)
    assert created is False
    assert "refusing to adopt" in failure


def test_force_rechecks_pending_under_the_init_lock(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    (workbench / "issue-205-zach" / "TASK.md").unlink()
    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: {"worktree": {"pending": "creator-token"}},
    )
    assert _start("--force") == 2
    assert "CREATION_IN_FLIGHT" in capsys.readouterr().err


def test_fresh_claimant_revalidates_a_concurrent_contract(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    def racing_contract(task_file, phase, checks):
        task_file.write_text(
            "Scientific phase: publication\n\nObjective:\n\nMay change:\n\n"
            "Must not change:\n\nDone when:\n\nVerification command:\n",
            encoding="utf-8",
        )
        return False

    monkeypatch.setattr(research_session, "write_task_contract", racing_contract)
    assert _start() == 2
    assert "PHASE_MISMATCH" in capsys.readouterr().err


def test_loser_keeps_marker_while_winner_is_uncommitted(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    session_file = session_dir / "session.json"
    (session_dir / "worktree").mkdir()

    # Winner registered the checkout (registered=True) but has not yet
    # recorded created=true; the loser must keep the marker.
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    monkeypatch.setattr(
        research_session,
        "add_worktree",
        lambda *a, **k: (False, "another invocation is creating the worktree"),
    )
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True  # ownership so resume passes gates
    session_file.write_text(json.dumps(record), encoding="utf-8")
    real_git = research_session._git
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: ""
        if args[:2] == ["merge-base", "--is-ancestor"]
        else real_git(args, cwd, **k),
    )
    monkeypatch.setattr(research_session, "_head", lambda _p: "a" * 40)
    assert _start("--resume", "--worktree") == 1
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["pending"] or final["worktree"]["created"]


def test_cleanup_deletes_only_a_provably_own_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"
    git_calls: list = []
    # Pre-lock: absent. In-lock: absent. Post-failure: a CONCURRENT writer's
    # branch exists at a tip different from our base.
    verify_states = iter([None, None, "concurrent-tip"])

    def fake_git(args, cwd, **kwargs):
        git_calls.append(args)
        if args[:2] == ["rev-parse", "--verify"]:
            return next(verify_states, "concurrent-tip")
        if args == ["rev-parse", "HEAD"]:
            return "our-base"
        return ""

    def fail_run(argv, **kwargs):
        class Proc:
            returncode = 1
            stderr = "branch already exists"
            stdout = ""
        return Proc()

    monkeypatch.setattr(research_session, "_git", fake_git)
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: False)
    monkeypatch.setattr(research_session.subprocess, "run", fail_run)
    created, failure = research_session.add_worktree(target, "s")
    assert created is False
    assert ["branch", "-D", "session/s"] not in git_calls


def test_branch_appearing_in_lock_is_not_reused_without_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"
    # Pre-lock: absent; in-lock: present; lineage unverifiable.
    verify_states = iter([None, "appeared-tip"])

    def fake_git(args, cwd, **kwargs):
        if args[:2] == ["rev-parse", "--verify"]:
            return next(verify_states, "appeared-tip")
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return None
        return ""

    monkeypatch.setattr(research_session, "_git", fake_git)
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: False)
    created, failure = research_session.add_worktree(target, "s")
    assert created is False
    assert "appeared concurrently" in failure


def test_switched_branch_is_not_recorded_at_final_write(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    session_file.write_text(json.dumps(record), encoding="utf-8")

    branches = iter(["session/issue-205-zach", "main"])  # switched mid-run
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: next(branches, "main")
    )
    assert _start("--resume") == 0
    err = capsys.readouterr().err
    assert "no longer on session/issue-205-zach" in err
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False


def test_unreadable_contract_yields_a_session_error(workbench: Path, capsys):
    assert _start() == 0
    task = workbench / "issue-205-zach" / "TASK.md"
    task.write_bytes(b"\xff\xfe invalid \xff utf8")
    assert _start("--resume") == 2
    assert "CONTRACT_UNREADABLE" in capsys.readouterr().err


def test_complete_concurrent_checkout_is_not_force_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    target = tmp_path / "worktree"
    target.mkdir()
    git_calls: list = []

    def fake_git(args, cwd, **kwargs):
        git_calls.append(args)
        return ""

    monkeypatch.setattr(research_session, "_git", fake_git)
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(research_session, "_head", lambda _p: "f" * 40)
    research_session._cleanup_failed_worktree(target, "s", True)
    assert not any(a[:2] == ["worktree", "remove"] for a in git_calls)
    assert "leaving it for its owner" in capsys.readouterr().err


def test_branch_deletion_is_atomic_compare_and_delete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"
    git_calls: list = []

    monkeypatch.setattr(
        research_session, "_git", lambda args, cwd, **k: git_calls.append(args) or ""
    )
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: False)
    research_session._cleanup_failed_worktree(
        target, "s", False, expected_branch_tip="a" * 40
    )
    assert ["update-ref", "-d", "refs/heads/session/s", "a" * 40] in git_calls
    assert not any(a[:2] == ["branch", "-D"] for a in git_calls)


def test_every_initializer_rechecks_record_generation(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: {"created_at": "2099-01-01T00:00:00+00:00", "worktree": {}},
    )
    assert _start() == 2  # fresh claimant, not resume
    assert "RECORD_REPLACED" in capsys.readouterr().err


def test_malformed_utf8_record_yields_session_error(workbench: Path, capsys):
    session_dir = workbench / "issue-205-zach"
    session_dir.mkdir()
    (session_dir / "session.json").write_bytes(b"\xff\xfe not json")
    assert _start("--resume") == 2
    assert "MALFORMED_SESSION" in capsys.readouterr().err


def test_live_checkout_appearing_during_stale_repair_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "worktree"
    # Registered throughout; the directory (a live checkout) appears after
    # the first prune.
    reg = iter([True, True, True, True])

    def fake_git(args, cwd, **kwargs):
        if args == ["worktree", "prune"]:
            target.mkdir(exist_ok=True)
            return ""
        if args[:2] == ["rev-parse", "--verify"]:
            return None
        return ""

    monkeypatch.setattr(
        research_session, "registered_worktree", lambda _p: next(reg, True)
    )
    monkeypatch.setattr(research_session, "_git", fake_git)
    monkeypatch.setattr(research_session, "_head", lambda _p: "f" * 40)
    created, failure = research_session.add_worktree(target, "s")
    assert created is False
    assert "became a live checkout" in failure


def test_worktree_target_registered_by_parent_is_rejected(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    target = workbench / "issue-205-zach" / "worktree"
    monkeypatch.setattr(
        research_session,
        "worktree_paths",
        lambda repo: [target] if repo != research_session.ANALYSIS_ROOT else [],
    )
    monkeypatch.setattr(
        research_session, "resolve_manuscript", lambda: (Path("/tmp/parent"), None)
    )
    assert _start() == 2
    assert "WORKTREE_TARGET_FOREIGN" in capsys.readouterr().err


def test_final_adopt_reproves_lineage(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    session_file.write_text(json.dumps(record), encoding="utf-8")

    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    monkeypatch.setattr(research_session, "_head", lambda _p: "b" * 40)
    real_git = research_session._git
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: None
        if args[:2] == ["merge-base", "--is-ancestor"]
        else real_git(args, cwd, **k),
    )
    assert _start("--resume") == 0
    err = capsys.readouterr().err
    assert "no longer contains the session's recorded base" in err
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False


def test_cleanup_leaves_a_foreign_or_complete_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    target = tmp_path / "worktree"
    (target / ".git").mkdir(parents=True)
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: False)
    monkeypatch.setattr(research_session, "_head", lambda _p: "f" * 40)
    monkeypatch.setattr(research_session, "_git", lambda a, c, **k: "")
    research_session._cleanup_failed_worktree(target, "s", True)
    assert target.exists()
    assert "leaving it rather than deleting" in capsys.readouterr().err


def test_final_adoption_requires_a_recorded_base(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    del record["git"]["analysis"]["head"]
    session_file.write_text(json.dumps(record), encoding="utf-8")

    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    assert _start("--resume") == 0
    assert "no valid git.analysis.head" in capsys.readouterr().err
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False


def test_resume_aborts_when_the_contract_phase_changes_mid_run(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0

    phases = iter(["exploration", "publication"])  # pre-lock ok, in-lock changed
    monkeypatch.setattr(
        research_session,
        "read_contract_phase",
        lambda _p: next(phases, "publication"),
    )
    assert _start("--resume") == 2
    assert "changed to 'publication'" in capsys.readouterr().err


def test_cleanup_leaves_a_plain_directory_from_another_producer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    target = tmp_path / "worktree"
    (target / "data").mkdir(parents=True)  # no .git entry at all
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: False)
    monkeypatch.setattr(research_session, "_git", lambda a, c, **k: "")
    research_session._cleanup_failed_worktree(target, "s", True)
    assert target.exists()
    assert "not attributable" in capsys.readouterr().err


def test_pending_write_aborts_on_a_replaced_record(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: {"created_at": "2099-01-01T00:00:00+00:00", "worktree": {}},
    )
    assert _start("--resume", "--worktree") == 2
    assert "RECORD_REPLACED" in capsys.readouterr().err


def test_rejected_owned_checkout_retains_ownership(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    session_file.write_text(json.dumps(record), encoding="utf-8")

    branches = iter(["session/issue-205-zach", "main"])  # switched mid-run
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: next(branches, "main")
    )
    assert _start("--resume") == 0
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False
    assert final["worktree"]["pending"]


def test_resume_rejects_a_record_without_repository_identities(
    workbench: Path, capsys
):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    del record["repositories"]
    session_file.write_text(json.dumps(record), encoding="utf-8")
    assert _start("--resume") == 2
    assert "RECORD_INCOMPLETE" in capsys.readouterr().err


def test_rejected_checkout_does_not_poison_recorded_provenance(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    trusted_head = record["git"]["analysis"]["head"]
    session_file.write_text(json.dumps(record), encoding="utf-8")

    branches = iter(["session/issue-205-zach", "main"])  # switched mid-run
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: next(branches, "main")
    )
    assert _start("--resume") == 0
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False
    assert final["worktree"]["pending"]
    assert final["git"]["analysis"]["head"] == trusted_head
    assert final["project"] == str(research_session.ANALYSIS_ROOT)


def test_contract_creation_is_exclusive_against_external_writers(tmp_path: Path):
    task = tmp_path / "TASK.md"
    task.write_text("human authored\n", encoding="utf-8")
    assert research_session.write_task_contract(task, "exploration", []) is False
    assert task.read_text(encoding="utf-8") == "human authored\n"


def test_init_write_aborts_when_generation_moved_after_validation(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    # --force validates against the current record, then a concurrent force
    # replaces it before the locked initialization write.
    generations = iter([
        {"created_at": "2026-01-01T00:00:00+00:00", "worktree": {}},
        {"created_at": "2099-01-01T00:00:00+00:00", "worktree": {}},
    ])
    monkeypatch.setattr(
        research_session,
        "read_existing_lenient",
        lambda _p: next(
            generations, {"created_at": "2099-01-01T00:00:00+00:00", "worktree": {}}
        ),
    )
    assert _start("--force") == 2
    assert "RECORD_REPLACED" in capsys.readouterr().err


def test_adoption_rejects_a_checkout_changed_during_sampling(
    workbench: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    trusted_head = record["git"]["analysis"]["head"]
    session_file.write_text(json.dumps(record), encoding="utf-8")

    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    monkeypatch.setattr(research_session, "_head", lambda _p: trusted_head)
    real_git = research_session._git
    monkeypatch.setattr(
        research_session,
        "_git",
        lambda args, cwd, **k: ""
        if args[:2] == ["merge-base", "--is-ancestor"]
        else real_git(args, cwd, **k),
    )
    real_collect = research_session.collect_git_state

    def poisoned_collect(*a, **k):
        state, parent = real_collect(*a, **k)
        if k.get("analysis_checkout") is not None:
            state["analysis"]["branch"] = "main"  # switched during sampling
        return state, parent

    monkeypatch.setattr(research_session, "collect_git_state", poisoned_collect)
    assert _start("--resume") == 0
    err = capsys.readouterr().err
    assert "changed between validation and provenance sampling" in err
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False
    assert final["worktree"]["pending"]


def test_resume_rejects_empty_repository_identities(workbench: Path, capsys):
    assert _start() == 0
    session_file = workbench / "issue-205-zach" / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["repositories"] = {}
    session_file.write_text(json.dumps(record), encoding="utf-8")
    assert _start("--resume") == 2
    assert "RECORD_INCOMPLETE" in capsys.readouterr().err


def test_rejected_checkout_routes_commands_to_canonical(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    record["project"] = str(session_dir / "worktree")
    record["interpreter"] = str(session_dir / "worktree" / ".venv" / "bin" / "python")
    session_file.write_text(json.dumps(record), encoding="utf-8")

    branches = iter(["session/issue-205-zach", "main"])
    monkeypatch.setattr(research_session, "registered_worktree", lambda _p: True)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: next(branches, "main")
    )
    assert _start("--resume") == 0
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False
    assert final["project"] == str(research_session.ANALYSIS_ROOT)
    assert final["interpreter"] == str(
        research_session.ANALYSIS_ROOT / ".venv" / "bin" / "python"
    )


def test_loser_adopts_winner_validated_fields_not_a_fresh_sample(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    task = session_dir / "TASK.md"
    task.write_text(
        "Scientific phase: exploration\n\nObjective: x\n\nMay change: y\n\n"
        "Must not change: z\n\nDone when: w\n\nVerification command: make test\n",
        encoding="utf-8",
    )
    session_file = session_dir / "session.json"

    def losing_add(*a, **k):
        latest = json.loads(session_file.read_text(encoding="utf-8"))
        latest["worktree"]["created"] = True
        latest["git"] = {"analysis": {"head": "w" * 40, "branch": "session/issue-205-zach", "checkout": str(session_dir / "worktree")}}
        latest["project"] = str(session_dir / "worktree")
        latest["interpreter"] = str(session_dir / "worktree" / ".venv" / "bin" / "python")
        session_file.write_text(json.dumps(latest), encoding="utf-8")
        return False, "lost the creation lock"

    monkeypatch.setattr(research_session, "add_worktree", losing_add)
    assert _start("--resume", "--worktree") == 1
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is True
    assert final["git"]["analysis"]["head"] == "w" * 40  # winner's, not sampled


def test_vanished_worktree_routes_commands_to_canonical(
    workbench: Path, monkeypatch: pytest.MonkeyPatch
):
    assert _start() == 0
    session_dir = workbench / "issue-205-zach"
    (session_dir / "worktree").mkdir()
    session_file = session_dir / "session.json"
    record = json.loads(session_file.read_text(encoding="utf-8"))
    record["worktree"]["created"] = True
    record["project"] = str(session_dir / "worktree")
    session_file.write_text(json.dumps(record), encoding="utf-8")

    calls = {"n": 0}

    def registered(_p):
        calls["n"] += 1
        return calls["n"] == 1  # present at planning, gone at the final check

    monkeypatch.setattr(research_session, "registered_worktree", registered)
    monkeypatch.setattr(
        research_session, "_branch", lambda _p: "session/issue-205-zach"
    )
    assert _start("--resume") == 0
    final = json.loads(session_file.read_text(encoding="utf-8"))
    assert final["worktree"]["created"] is False
    assert final["worktree"]["pending"]
    assert final["project"] == str(research_session.ANALYSIS_ROOT)
