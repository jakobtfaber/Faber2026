from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _valid_card(root: Path, *, card_id: str = "test-decision") -> dict:
    evidence = root / "evidence.txt"
    evidence.write_text("evidence\n", encoding="utf-8")
    recorder = root / "record.json"
    recorder.write_text("{}\n", encoding="utf-8")
    return {
        "id": card_id,
        "kind": "scientific",
        "title": "Test decision",
        "decision": "Choose the scientifically valid interpretation?",
        "recommended": {"choice": "accept", "reason": "Evidence supports it."},
        "choices": [
            {"id": "accept", "label": "Accept the interpretation."},
            {"id": "reject", "label": "Reject it."},
        ],
        "context": ["The producing check passed."],
        "evidence": [
            {
                "label": "Evidence",
                "path": "evidence.txt",
                "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            }
        ],
        "effect": "Records the scientific disposition.",
        "recorder": {"path": "record.json", "action": "Record the choice."},
        "priority": 10,
    }


def _write_ticket(
    path: Path,
    *,
    title: str,
    status: str,
    assignee: str,
    card: dict | None = None,
) -> None:
    lines = [
        f"# {title}",
        "",
        "- Type: `wayfinder:task` (HITL)",
        f"- Status: {status}",
        f"- Assignee: {assignee}",
        "- Blocked by: none",
        "",
    ]
    if card is not None:
        lines.extend(
            [
                "## Owner decision card",
                "",
                "```json",
                json.dumps(card, indent=2),
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def test_owner_frontier_keeps_open_hitl_tickets_even_when_assigned(tmp_path):
    from scripts.owner_queue import collect_wayfinder_frontier

    tickets = tmp_path / "tickets"
    tickets.mkdir()
    _write_ticket(
        tickets / "open.md",
        title="Open owner decision",
        status="open",
        assignee="unassigned",
    )
    _write_ticket(
        tickets / "claimed.md",
        title="Claimed owner decision",
        status="open",
        assignee="Codex",
    )
    _write_ticket(
        tickets / "resolved.md",
        title="Resolved owner decision",
        status="resolved",
        assignee="unassigned",
    )
    titles = {
        ticket.title
        for ticket in collect_wayfinder_frontier(tickets, owner_facing_only=True)
    }
    assert titles == {"Open owner decision", "Claimed owner decision"}


def test_owner_queue_cli_regenerates_from_authoritative_frontier(tmp_path):
    output = tmp_path / "OWNER_QUEUE.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/owner_queue.py"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    rendered = output.read_text(encoding="utf-8")
    assert "**Decision:**" in rendered
    assert "**Recommended:**" in rendered
    assert "Obtain the authoritative host-redshift ledger" not in rendered


def test_owner_queue_canonical_render_is_date_independent():
    from scripts.owner_queue import render_owner_queue

    rendered = render_owner_queue(ROOT)
    assert "Silence leaves every item blocked" in rendered
    assert re.search(r"_Generated \d{4}-\d{2}-\d{2}", rendered) is None


def test_owner_queue_cli_defaults_to_repository_only(tmp_path):
    output = tmp_path / "OWNER_QUEUE.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/owner_queue.py"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Open PRs" not in output.read_text(encoding="utf-8")


def test_figure_batch_disposition_controls_owner_queue(tmp_path):
    from scripts.owner_queue import collect_undecided_figure_batches

    batches = tmp_path / "figure_review/artifacts/batches"
    receipts = tmp_path / "figure_review/decisions/approval_receipts"
    receipts.mkdir(parents=True)
    for name in ("stale", "current"):
        batch = batches / name
        batch.mkdir(parents=True)
        artifact = batch / "candidate.pdf"
        artifact.write_bytes(name.encode())
        (batch / "manifest.json").write_text(
            json.dumps(
                {
                    "candidates": [
                        {
                            "id": f"{name}-candidate",
                            "artifact": "candidate.pdf",
                            "artifact_sha256": hashlib.sha256(
                                artifact.read_bytes()
                            ).hexdigest(),
                            "target": f"figures/{name}.pdf",
                            "decision": {"status": "pending"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
    (tmp_path / "figure_review/decisions/batch_dispositions.json").write_text(
        json.dumps(
            {
                "batches": {
                    "stale": {
                        "owner_queue": False,
                        "status": "superseded",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    assert [path.name for path in collect_undecided_figure_batches(tmp_path)] == [
        "current"
    ]


def test_matching_approval_receipt_removes_only_exact_candidate(tmp_path):
    from scripts.owner_queue import collect_undecided_figure_batches

    batch = tmp_path / "figure_review/artifacts/batches/current"
    batch.mkdir(parents=True)
    artifact = batch / "candidate.pdf"
    artifact.write_bytes(b"candidate")
    artifact_sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    candidate = {
        "id": "figure",
        "artifact": "candidate.pdf",
        "artifact_sha256": artifact_sha256,
        "target": "figures/figure.pdf",
        "decision": {"status": "pending"},
    }
    (batch / "manifest.json").write_text(
        json.dumps({"batch_id": "current", "candidates": [candidate]}),
        encoding="utf-8",
    )
    receipts = tmp_path / "figure_review/decisions/approval_receipts"
    receipts.mkdir(parents=True)
    receipt = {
        "schema_version": 1,
        "batch_id": "current",
        "candidate_id": "figure",
        "candidate_sha256": "b" * 64,
        "promoted_sha256": "b" * 64,
        "promoted_target": "figures/figure.pdf",
        "decision": {
            "status": "approved",
            "reviewer_role": "manuscript_owner",
            "reviewer": "Owner",
            "reviewed_at": "2026-07-29T00:00:00Z",
        },
    }
    (receipts / "figure.json").write_text(json.dumps(receipt), encoding="utf-8")
    assert collect_undecided_figure_batches(tmp_path) == [batch]
    receipt["candidate_sha256"] = artifact_sha256
    receipt["promoted_sha256"] = artifact_sha256
    (receipts / "figure.json").write_text(json.dumps(receipt), encoding="utf-8")
    assert collect_undecided_figure_batches(tmp_path) == []
    invalid_receipts = []
    for key, value in (
        ("batch_id", "wrong"),
        ("candidate_id", "wrong"),
        ("promoted_target", "figures/wrong.pdf"),
        ("schema_version", 99),
    ):
        invalid = json.loads(json.dumps(receipt))
        invalid[key] = value
        invalid_receipts.append(invalid)
    invalid_role = json.loads(json.dumps(receipt))
    invalid_role["decision"]["reviewer_role"] = "agent"
    invalid_receipts.append(invalid_role)
    invalid_time = json.loads(json.dumps(receipt))
    invalid_time["decision"]["reviewed_at"] = "not-a-time"
    invalid_receipts.append(invalid_time)
    for invalid in invalid_receipts:
        (receipts / "figure.json").write_text(json.dumps(invalid), encoding="utf-8")
        assert collect_undecided_figure_batches(tmp_path) == [batch]


def test_cards_are_ordered_and_deduplicated(tmp_path):
    from scripts.owner_queue import QueueValidationError, collect_decision_cards

    tickets = tmp_path / "docs/rse/wayfinder/tickets"
    tickets.mkdir(parents=True)
    first = _valid_card(tmp_path, card_id="first")
    first["priority"] = 20
    second = _valid_card(tmp_path, card_id="second")
    second["priority"] = 10
    _write_ticket(
        tickets / "first.md",
        title="First",
        status="open",
        assignee="—",
        card=first,
    )
    _write_ticket(
        tickets / "second.md",
        title="Second",
        status="open",
        assignee="—",
        card=second,
    )
    assert [card.id for card in collect_decision_cards(tmp_path)] == [
        "second",
        "first",
    ]
    first["id"] = "second"
    _write_ticket(
        tickets / "first.md",
        title="First",
        status="open",
        assignee="—",
        card=first,
    )
    with pytest.raises(QueueValidationError, match="duplicate decision id"):
        collect_decision_cards(tmp_path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda card: card.update(kind="technical"),
            "kind must be scientific or visual",
        ),
        (lambda card: card.update(choices=card["choices"][:1]), "2-3 choices"),
        (
            lambda card: card["recommended"].update(choice="missing"),
            "recommended choice",
        ),
        (lambda card: card.update(context=[]), "context must contain"),
        (lambda card: card.update(evidence=[]), "evidence must contain"),
        (lambda card: card.update(decision={}), "decision-card decision must be text"),
        (
            lambda card: card["choices"][0].update(id=""),
            "every choice needs a stable id",
        ),
        (
            lambda card: card["recommended"].update(reason=""),
            "recommendation reason must not be empty",
        ),
        (
            lambda card: card["recorder"].update(path="."),
            "recorder path is not a file",
        ),
    ],
)
def test_invalid_cards_fail_closed(tmp_path, mutate, message):
    from scripts.owner_queue import QueueValidationError, collect_decision_cards

    tickets = tmp_path / "docs/rse/wayfinder/tickets"
    tickets.mkdir(parents=True)
    card = _valid_card(tmp_path)
    mutate(card)
    _write_ticket(
        tickets / "decision.md",
        title="Decision",
        status="open",
        assignee="—",
        card=card,
    )
    with pytest.raises(QueueValidationError, match=message):
        collect_decision_cards(tmp_path)


def test_evidence_hash_and_paths_are_validated(tmp_path):
    from scripts.owner_queue import QueueValidationError, collect_decision_cards

    tickets = tmp_path / "docs/rse/wayfinder/tickets"
    tickets.mkdir(parents=True)
    card = _valid_card(tmp_path)
    card["evidence"][0]["sha256"] = "0" * 64
    _write_ticket(
        tickets / "decision.md",
        title="Decision",
        status="open",
        assignee="—",
        card=card,
    )
    with pytest.raises(QueueValidationError, match="SHA-256 drift"):
        collect_decision_cards(tmp_path)
    card["evidence"][0] = {
        "label": "Missing",
        "path": "missing.txt",
        "sha256": "0" * 64,
    }
    _write_ticket(
        tickets / "decision.md",
        title="Decision",
        status="open",
        assignee="—",
        card=card,
    )
    with pytest.raises(QueueValidationError, match="evidence is missing"):
        collect_decision_cards(tmp_path)
    outside = tmp_path.parent / "outside-evidence.txt"
    outside.write_text("outside\n", encoding="utf-8")
    card["evidence"][0] = {
        "label": "Outside",
        "path": "../outside-evidence.txt",
        "sha256": "0" * 64,
    }
    _write_ticket(
        tickets / "decision.md",
        title="Decision",
        status="open",
        assignee="—",
        card=card,
    )
    with pytest.raises(QueueValidationError, match="escapes repository"):
        collect_decision_cards(tmp_path)


def test_resolving_ticket_removes_card(tmp_path):
    from scripts.owner_queue import collect_decision_cards

    tickets = tmp_path / "docs/rse/wayfinder/tickets"
    tickets.mkdir(parents=True)
    card = _valid_card(tmp_path)
    ticket = tickets / "decision.md"
    _write_ticket(
        ticket, title="Decision", status="open", assignee="Codex", card=card
    )
    assert [item.id for item in collect_decision_cards(tmp_path)] == [
        "test-decision"
    ]
    _write_ticket(
        ticket, title="Decision", status="resolved", assignee="Codex", card=card
    )
    assert collect_decision_cards(tmp_path) == []


def test_open_owner_ticket_without_card_fails_closed(tmp_path):
    from scripts.owner_queue import QueueValidationError, collect_decision_cards

    tickets = tmp_path / "docs/rse/wayfinder/tickets"
    tickets.mkdir(parents=True)
    _write_ticket(
        tickets / "decision.md",
        title="Decision",
        status="open",
        assignee="—",
    )
    with pytest.raises(QueueValidationError, match="lacks '## Owner decision card'"):
        collect_decision_cards(tmp_path)


def test_pending_figure_without_card_fails_closed(tmp_path):
    from scripts.owner_queue import QueueValidationError, collect_decision_cards

    batch = tmp_path / "figure_review/artifacts/batches/current"
    batch.mkdir(parents=True)
    artifact = batch / "candidate.pdf"
    artifact.write_bytes(b"candidate")
    (batch / "manifest.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "figure",
                        "artifact": "candidate.pdf",
                        "artifact_sha256": hashlib.sha256(
                            artifact.read_bytes()
                        ).hexdigest(),
                        "target": "figures/figure.pdf",
                        "decision": {"status": "pending"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(QueueValidationError, match="lacks owner_decision_card"):
        collect_decision_cards(tmp_path)


def test_unknown_figure_decision_status_fails_closed(tmp_path):
    from scripts.owner_queue import QueueValidationError, collect_decision_cards

    batch = tmp_path / "figure_review/artifacts/batches/current"
    batch.mkdir(parents=True)
    artifact = batch / "candidate.pdf"
    artifact.write_bytes(b"candidate")
    (batch / "manifest.json").write_text(
        json.dumps(
            {
                "batch_id": "current",
                "candidates": [
                    {
                        "id": "figure",
                        "artifact": "candidate.pdf",
                        "artifact_sha256": hashlib.sha256(
                            artifact.read_bytes()
                        ).hexdigest(),
                        "target": "figures/figure.pdf",
                        "decision": {"status": "pendng"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(QueueValidationError, match="unknown candidate decision status"):
        collect_decision_cards(tmp_path)


def test_json_and_check_modes_do_not_write_queue(tmp_path):
    from scripts.owner_queue import render_owner_queue

    output = tmp_path / "queue.md"
    output.write_text(render_owner_queue(ROOT), encoding="utf-8")
    check = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/owner_queue.py"),
            "--check",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    assert "valid decisions" in check.stdout
    assert output.is_file()
    payload = subprocess.run(
        [sys.executable, str(ROOT / "scripts/owner_queue.py"), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert payload.returncode == 0, payload.stdout + payload.stderr
    assert isinstance(json.loads(payload.stdout), list)


def test_check_mode_rejects_stale_generated_queue(tmp_path):
    output = tmp_path / "queue.md"
    output.write_text("stale\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/owner_queue.py"),
            "--check",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "generated queue is stale" in result.stdout
