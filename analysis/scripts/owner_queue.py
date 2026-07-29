#!/usr/bin/env python3
"""Render validated owner decision cards from authoritative repository state."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scripts.wayfinder_state import Ticket, wayfinder_frontier
except ModuleNotFoundError:  # direct ``python scripts/owner_queue.py`` execution
    from wayfinder_state import Ticket, wayfinder_frontier


ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "docs/rse/wayfinder/tickets"
DEFAULT_OUTPUT = ROOT / "OWNER_QUEUE.md"
CARD_HEADING = "## Owner decision card"
CARD_RE = re.compile(
    rf"^{re.escape(CARD_HEADING)}\s*\n+\s*```json\s*\n"
    r"(?P<payload>.*?)\n```",
    re.MULTILINE | re.DOTALL,
)
ALLOWED_KINDS = {"scientific", "visual"}
ALLOWED_FIGURE_STATUSES = {"pending", "approved", "needs_revision"}


class QueueValidationError(ValueError):
    """Raised when an owner-facing source does not define a valid decision."""


@dataclass(frozen=True)
class DecisionChoice:
    id: str
    label: str


@dataclass(frozen=True)
class DecisionEvidence:
    label: str
    path: str
    sha256: str | None = None


@dataclass(frozen=True)
class DecisionRecommendation:
    choice: str
    reason: str


@dataclass(frozen=True)
class DecisionRecorder:
    path: str
    action: str


@dataclass(frozen=True)
class DecisionCard:
    id: str
    kind: str
    title: str
    decision: str
    recommended: DecisionRecommendation
    choices: tuple[DecisionChoice, ...]
    context: tuple[str, ...]
    evidence: tuple[DecisionEvidence, ...]
    effect: str
    recorder: DecisionRecorder
    priority: int
    source: str


def collect_wayfinder_frontier(
    tickets_root: Path = TICKETS, *, owner_facing_only: bool = False
) -> list[Ticket]:
    """Return the same pass-aware frontier consumed by owner-queue generation."""

    return wayfinder_frontier(tickets_root, owner_facing_only=owner_facing_only)


def _approved_receipt_matches(
    receipt_path: Path, candidate: dict[str, Any], *, batch_id: str
) -> bool:
    if not receipt_path.is_file():
        return False
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    reviewed_at = receipt.get("decision", {}).get("reviewed_at")
    try:
        datetime.fromisoformat(reviewed_at)
    except (TypeError, ValueError):
        return False
    return (
        receipt.get("schema_version") == 1
        and receipt.get("batch_id") == batch_id
        and receipt.get("candidate_id") == candidate.get("id")
        and receipt.get("candidate_sha256") == candidate.get("artifact_sha256")
        and receipt.get("promoted_sha256") == candidate.get("artifact_sha256")
        and receipt.get("promoted_target") == candidate.get("target")
        and receipt.get("decision", {}).get("status") == "approved"
        and receipt.get("decision", {}).get("reviewer_role") == "manuscript_owner"
        and bool(receipt.get("decision", {}).get("reviewer"))
        and bool(receipt.get("decision", {}).get("reviewed_at"))
    )


def _validate_figure_candidate(
    candidate: Any, *, manifest_path: Path, root: Path
) -> str:
    relative = manifest_path.relative_to(root)
    if not isinstance(candidate, dict):
        raise QueueValidationError(f"{relative}: figure candidate must be an object")
    required = {"id", "artifact", "artifact_sha256", "target", "decision"}
    if not required <= set(candidate):
        raise QueueValidationError(
            f"{relative}: figure candidate missing {sorted(required - set(candidate))}"
        )
    if (
        not isinstance(candidate["id"], str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", candidate["id"])
        or not isinstance(candidate["artifact"], str)
        or not candidate["artifact"].strip()
        or not isinstance(candidate["artifact_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", candidate["artifact_sha256"])
        or not isinstance(candidate["target"], str)
        or not candidate["target"].strip()
        or not isinstance(candidate["decision"], dict)
    ):
        raise QueueValidationError(f"{relative}: malformed figure candidate identity")
    artifact = (manifest_path.parent / candidate["artifact"]).resolve()
    if not artifact.is_relative_to(root.resolve()):
        raise QueueValidationError(
            f"{relative}: candidate artifact escapes repository: {candidate['artifact']}"
        )
    if not artifact.is_file():
        raise QueueValidationError(
            f"{relative}: candidate artifact is missing: {candidate['artifact']}"
        )
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != candidate["artifact_sha256"]:
        raise QueueValidationError(f"{relative}: candidate artifact SHA-256 drift")
    status = candidate["decision"].get("status")
    if status not in ALLOWED_FIGURE_STATUSES:
        raise QueueValidationError(
            f"{relative}: unknown candidate decision status {status!r}"
        )
    return status


def collect_undecided_figure_batches(root: Path = ROOT) -> list[Path]:
    receipts = root / "figure_review/decisions/approval_receipts"
    dispositions_path = root / "figure_review/decisions/batch_dispositions.json"
    dispositions: dict[str, dict[str, object]] = {}
    if dispositions_path.is_file():
        payload = json.loads(dispositions_path.read_text(encoding="utf-8"))
        dispositions = payload.get("batches", {})
    undecided: list[Path] = []
    for manifest_path in sorted(
        (root / "figure_review/artifacts/batches").glob("*/manifest.json")
    ):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        disposition = dispositions.get(manifest_path.parent.name, {})
        if disposition.get("owner_queue") is False:
            continue
        batch_id = manifest.get("batch_id", manifest_path.parent.name)
        for candidate in manifest.get("candidates", []):
            _validate_figure_candidate(
                candidate, manifest_path=manifest_path, root=root
            )
        if any(
            candidate["decision"]["status"] == "pending"
            and not _approved_receipt_matches(
                receipts / f"{candidate['id']}.json",
                candidate,
                batch_id=batch_id,
            )
            for candidate in manifest.get("candidates", [])
        ):
            undecided.append(manifest_path.parent)
    return undecided


def _require_card_shape(
    payload: Any, *, relative_source: str
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise QueueValidationError(f"{relative_source}: decision card must be an object")
    required = {
        "id",
        "kind",
        "title",
        "decision",
        "recommended",
        "choices",
        "context",
        "evidence",
        "effect",
        "recorder",
    }
    unknown = set(payload) - required - {"priority"}
    missing = required - set(payload)
    if missing or unknown:
        raise QueueValidationError(
            f"{relative_source}: decision-card keys missing={sorted(missing)} "
            f"unknown={sorted(unknown)}"
        )
    for key in ("id", "kind", "title", "decision", "effect"):
        if not isinstance(payload[key], str):
            raise QueueValidationError(
                f"{relative_source}: decision-card {key} must be text"
            )
    if not isinstance(payload.get("priority", 100), int) or isinstance(
        payload.get("priority", 100), bool
    ):
        raise QueueValidationError(
            f"{relative_source}: decision-card priority must be an integer"
        )
    recommended = payload["recommended"]
    if (
        not isinstance(recommended, dict)
        or set(recommended) != {"choice", "reason"}
        or not all(isinstance(recommended[key], str) for key in recommended)
    ):
        raise QueueValidationError(
            f"{relative_source}: recommended must contain text choice and reason"
        )
    choices = payload["choices"]
    if not isinstance(choices, list) or any(
        not isinstance(choice, dict)
        or set(choice) != {"id", "label"}
        or not all(isinstance(choice[key], str) for key in choice)
        for choice in choices
    ):
        raise QueueValidationError(
            f"{relative_source}: choices must contain text id and label"
        )
    context = payload["context"]
    if not isinstance(context, list) or any(
        not isinstance(item, str) for item in context
    ):
        raise QueueValidationError(
            f"{relative_source}: context must be a list of text facts"
        )
    evidence = payload["evidence"]
    if not isinstance(evidence, list) or any(
        not isinstance(item, dict)
        or not {"label", "path"} <= set(item)
        or set(item) - {"label", "path", "sha256"}
        or not isinstance(item["label"], str)
        or not isinstance(item["path"], str)
        or ("sha256" in item and not isinstance(item["sha256"], str))
        for item in evidence
    ):
        raise QueueValidationError(
            f"{relative_source}: evidence entries require text label, path, and optional SHA-256"
        )
    recorder = payload["recorder"]
    if (
        not isinstance(recorder, dict)
        or set(recorder) != {"path", "action"}
        or not all(isinstance(recorder[key], str) for key in recorder)
    ):
        raise QueueValidationError(
            f"{relative_source}: recorder must contain text path and action"
        )
    return payload


def _load_card(payload: Any, *, source: Path, root: Path) -> DecisionCard:
    relative_source = source.relative_to(root).as_posix()
    payload = _require_card_shape(payload, relative_source=relative_source)
    try:
        card = DecisionCard(
            id=payload["id"],
            kind=payload["kind"],
            title=payload["title"],
            decision=payload["decision"],
            recommended=DecisionRecommendation(**payload["recommended"]),
            choices=tuple(DecisionChoice(**choice) for choice in payload["choices"]),
            context=tuple(payload["context"]),
            evidence=tuple(
                DecisionEvidence(**item) for item in payload["evidence"]
            ),
            effect=payload["effect"],
            recorder=DecisionRecorder(**payload["recorder"]),
            priority=int(payload.get("priority", 100)),
            source=relative_source,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise QueueValidationError(
            f"{relative_source}: malformed decision card: {exc}"
        ) from exc
    _validate_card(card, root=root)
    return card


def _validate_card(card: DecisionCard, *, root: Path) -> None:
    prefix = f"{card.source}: decision {card.id!r}"
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", card.id):
        raise QueueValidationError(f"{prefix}: invalid stable id")
    if card.kind not in ALLOWED_KINDS:
        raise QueueValidationError(
            f"{prefix}: kind must be scientific or visual, not {card.kind!r}"
        )
    if not 1 <= len(card.title.split()) <= 8:
        raise QueueValidationError(f"{prefix}: title must contain 1-8 words")
    required_text = {
        "decision": card.decision,
        "recommendation reason": card.recommended.reason,
        "effect": card.effect,
        "recorder action": card.recorder.action,
    }
    for label, value in required_text.items():
        if not value.strip():
            raise QueueValidationError(f"{prefix}: {label} must not be empty")
    if len(card.choices) not in {2, 3}:
        raise QueueValidationError(f"{prefix}: exactly 2-3 choices are required")
    choice_ids = [choice.id for choice in card.choices]
    if len(choice_ids) != len(set(choice_ids)):
        raise QueueValidationError(f"{prefix}: choice ids must be unique")
    if any(
        not re.fullmatch(r"[a-z0-9][a-z0-9-]*", choice.id)
        or not choice.label.strip()
        for choice in card.choices
    ):
        raise QueueValidationError(
            f"{prefix}: every choice needs a stable id and non-empty label"
        )
    if card.recommended.choice not in choice_ids:
        raise QueueValidationError(
            f"{prefix}: recommended choice is not one of the declared choices"
        )
    if not 1 <= len(card.context) <= 3:
        raise QueueValidationError(f"{prefix}: context must contain 1-3 facts")
    if any(not fact.strip() for fact in card.context):
        raise QueueValidationError(f"{prefix}: context facts must not be empty")
    if not 1 <= len(card.evidence) <= 3:
        raise QueueValidationError(f"{prefix}: evidence must contain 1-3 links")
    for item in card.evidence:
        if not item.label.strip() or not item.path.strip():
            raise QueueValidationError(
                f"{prefix}: evidence labels and paths must not be empty"
            )
        if re.match(r"https?://", item.path):
            continue
        if not item.sha256:
            raise QueueValidationError(
                f"{prefix}: local evidence requires a SHA-256: {item.path}"
            )
        path = (root / item.path).resolve()
        if not path.is_relative_to(root.resolve()):
            raise QueueValidationError(
                f"{prefix}: evidence path escapes repository: {item.path}"
            )
        if not path.is_file():
            raise QueueValidationError(f"{prefix}: evidence is missing: {item.path}")
        if item.sha256:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != item.sha256:
                raise QueueValidationError(
                    f"{prefix}: evidence SHA-256 drift: {item.path}"
                )
    recorder = (root / card.recorder.path).resolve()
    if not recorder.is_relative_to(root.resolve()):
        raise QueueValidationError(
            f"{prefix}: recorder path escapes repository: {card.recorder.path}"
        )
    if not recorder.is_file():
        raise QueueValidationError(
            f"{prefix}: recorder path is not a file: {card.recorder.path}"
        )


def _ticket_card(ticket: Ticket, *, root: Path) -> DecisionCard:
    text = ticket.path.read_text(encoding="utf-8")
    match = CARD_RE.search(text)
    relative = ticket.path.relative_to(root)
    if not match:
        raise QueueValidationError(
            f"{relative}: open owner-facing ticket lacks {CARD_HEADING!r}"
        )
    try:
        payload = json.loads(match.group("payload"))
    except json.JSONDecodeError as exc:
        raise QueueValidationError(
            f"{relative}: invalid decision-card JSON: {exc}"
        ) from exc
    return _load_card(payload, source=ticket.path, root=root)


def collect_ticket_cards(root: Path = ROOT) -> list[DecisionCard]:
    tickets = collect_wayfinder_frontier(
        root / "docs/rse/wayfinder/tickets", owner_facing_only=True
    )
    return [_ticket_card(ticket, root=root) for ticket in tickets]


def collect_figure_cards(root: Path = ROOT) -> list[DecisionCard]:
    receipts = root / "figure_review/decisions/approval_receipts"
    cards: list[DecisionCard] = []
    for batch in collect_undecided_figure_batches(root):
        manifest_path = batch / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        batch_id = manifest.get("batch_id", batch.name)
        for candidate in manifest.get("candidates", []):
            if candidate["decision"]["status"] != "pending":
                continue
            if _approved_receipt_matches(
                receipts / f"{candidate['id']}.json",
                candidate,
                batch_id=batch_id,
            ):
                continue
            payload = candidate.get("owner_decision_card")
            if payload is None:
                raise QueueValidationError(
                    f"{manifest_path.relative_to(root)}: pending candidate "
                    f"{candidate['id']!r} lacks owner_decision_card"
                )
            cards.append(_load_card(payload, source=manifest_path, root=root))
    return cards


def collect_decision_cards(root: Path = ROOT) -> list[DecisionCard]:
    cards = collect_ticket_cards(root) + collect_figure_cards(root)
    seen: dict[str, str] = {}
    for card in cards:
        if card.id in seen:
            raise QueueValidationError(
                f"duplicate decision id {card.id!r}: {seen[card.id]} and {card.source}"
            )
        seen[card.id] = card.source
    return sorted(cards, key=lambda card: (card.priority, card.title.casefold(), card.id))


def _short_hash(value: str) -> str:
    return value[:8] + "…"


def render_owner_queue(root: Path = ROOT) -> str:
    cards = collect_decision_cards(root)
    lines = [
        "# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`",
        "",
        "_Only scientific and visual decisions. Silence leaves every item blocked._",
        "",
    ]
    if not cards:
        lines.extend(["No decisions queued.", ""])
        return "\n".join(lines)
    for index, card in enumerate(cards, start=1):
        lines.extend(
            [
                f"## {index}. {card.title}",
                "",
                f"**Decision:** {card.decision}",
                "",
                f"**Recommended:** `{card.recommended.choice}` — "
                f"{card.recommended.reason}",
                "",
                "**Choose:**",
                "",
            ]
        )
        for choice in card.choices:
            lines.append(f"- `{choice.id}` — {choice.label}")
        lines.extend(["", "**Context:**", ""])
        lines.extend(f"- {fact}" for fact in card.context)
        lines.extend(["", "**Evidence:**", ""])
        for item in card.evidence:
            suffix = f" — `{_short_hash(item.sha256)}`" if item.sha256 else ""
            lines.append(f"- [{item.label}]({item.path}){suffix}")
        lines.extend(
            [
                "",
                f"**Effect:** {card.effect}",
                "",
                f"**Record:** `{card.recorder.path}` — {card.recorder.action}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def validate_rendered_queue(
    root: Path = ROOT, output: Path = DEFAULT_OUTPUT
) -> list[DecisionCard]:
    cards = collect_decision_cards(root)
    if not output.is_file():
        raise QueueValidationError(f"generated queue is missing: {output}")
    if output.read_text(encoding="utf-8") != render_owner_queue(root):
        raise QueueValidationError(f"generated queue is stale: {output}")
    return cards


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--check",
        action="store_true",
        help="validate cards, evidence, hashes, and recorders without writing",
    )
    result.add_argument(
        "--json",
        action="store_true",
        help="print validated decision cards as JSON without writing",
    )
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        cards = (
            validate_rendered_queue(output=args.output.resolve())
            if args.check
            else collect_decision_cards()
        )
    except QueueValidationError as exc:
        print(f"owner queue invalid: {exc}")
        return 1
    if args.check:
        print(f"owner queue: {len(cards)} valid decisions")
        return 0
    if args.json:
        print(json.dumps([asdict(card) for card in cards], indent=2))
        return 0
    output = args.output.resolve()
    rendered = render_owner_queue()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
