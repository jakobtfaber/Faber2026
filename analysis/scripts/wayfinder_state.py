#!/usr/bin/env python3
"""Parse Wayfinder Markdown tickets and compute their fail-closed frontier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


HEADER_RE = re.compile(r"^- (?P<key>[^:]+):\s*(?P<value>.*)$", re.MULTILINE)
LINK_RE = re.compile(r"\[[^]]+\]\((?P<target>[^)]+\.md)\)")
REQUIRED_OUTCOME_RE = re.compile(r"\(requires\s+`(?P<outcome>[^`]+)`\)")


@dataclass(frozen=True)
class Blocker:
    target: str | None
    required_outcome: str | None
    description: str


@dataclass(frozen=True)
class Ticket:
    path: Path
    title: str
    ticket_type: str
    status: str
    assignee: str
    resolution_gate: str
    gate_outcome: str
    blockers: tuple[Blocker, ...]

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def is_owner_facing(self) -> bool:
        return "(hitl)" in self.ticket_type.lower()

    @property
    def is_assigned(self) -> bool:
        return self.assignee.strip().lower() not in {
            "",
            "-",
            "—",
            "none",
            "unassigned",
        }


def _normalized_status(value: str) -> str:
    match = re.match(r"(?:\*\*)?([a-z_-]+)", value.strip(), re.IGNORECASE)
    return match.group(1).lower() if match else ""


def parse_ticket_text(text: str, path: Path = Path("<ticket>")) -> Ticket:
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    headers = {
        match.group("key").strip().lower(): match.group("value").strip()
        for match in HEADER_RE.finditer(text)
    }
    blocker_value = headers.get("blocked by", "")
    blockers: list[Blocker] = []
    links = list(LINK_RE.finditer(blocker_value))
    required = REQUIRED_OUTCOME_RE.search(blocker_value)
    required_outcome = required.group("outcome").lower() if required else None
    for link in links:
        blockers.append(
            Blocker(
                target=link.group("target"),
                required_outcome=required_outcome,
                description=blocker_value,
            )
        )
    if not links and blocker_value.strip().lower() not in {"", "-", "—", "none"}:
        blockers.append(Blocker(None, None, blocker_value))
    return Ticket(
        path=path,
        title=title_match.group(1).strip() if title_match else path.stem,
        ticket_type=headers.get("type", ""),
        status=_normalized_status(headers.get("status", "")),
        assignee=headers.get("assignee", ""),
        resolution_gate=headers.get("resolution gate", "").strip("`").lower(),
        gate_outcome=headers.get("gate outcome", "").strip("`").lower(),
        blockers=tuple(blockers),
    )


def parse_ticket(path: Path) -> Ticket:
    return parse_ticket_text(path.read_text(encoding="utf-8"), path)


def ticket_clears_dependency(
    ticket: Ticket, required_outcome: str | None = None
) -> bool:
    if ticket.status != "resolved":
        return False
    if ticket.resolution_gate == "pass-only" and ticket.gate_outcome != "pass":
        return False
    return required_outcome is None or ticket.gate_outcome == required_outcome


def ticket_is_unblocked(ticket: Ticket, tickets_root: Path) -> bool:
    for blocker in ticket.blockers:
        if blocker.target is None:
            return False
        blocker_path = (ticket.path.parent / blocker.target).resolve()
        if (
            not blocker_path.is_relative_to(tickets_root.resolve())
            or not blocker_path.is_file()
        ):
            return False
        if not ticket_clears_dependency(
            parse_ticket(blocker_path), blocker.required_outcome
        ):
            return False
    return True


def wayfinder_frontier(
    tickets_root: Path, *, owner_facing_only: bool = False
) -> list[Ticket]:
    tickets = [parse_ticket(path) for path in sorted(tickets_root.glob("*.md"))]
    return [
        ticket
        for ticket in tickets
        if ticket.is_open
        and not ticket.is_assigned
        and (not owner_facing_only or ticket.is_owner_facing)
        and ticket_is_unblocked(ticket, tickets_root)
    ]
