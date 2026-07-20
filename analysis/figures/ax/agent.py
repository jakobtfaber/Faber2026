#!/usr/bin/env python3
"""Ax agent front door for figure_flow (optional; needs ``pip install axllm``).

Deterministic work still runs via ``scripts/figure_flow.py``. This module only
exposes typed tools so an AxAgent can list / regen / status without opening
plot scripts. CI and ``make figures`` do not import axllm.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLOW = ROOT / "scripts" / "figure_flow.py"
SKILL_PATH = Path(__file__).resolve().parent / "SKILL.md"


def _run_flow(*args: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(FLOW), *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(out.strip() or f"figure_flow exit {proc.returncode}")
    return out.strip()


def list_figures() -> str:
    """List catalog figures (id, tex label, flags)."""
    return _run_flow("list")


def figure_status() -> str:
    """Report stale / missing-input status for manuscript figures."""
    try:
        return _run_flow("stale")
    except RuntimeError as exc:
        # stale returns 1 when anything is stale — still useful text
        return str(exc)


def regen_figure(figure_id: str = "", manuscript: bool = False, clone_ok: bool = False) -> str:
    """Regenerate one figure id, or the manuscript / clone-ok selection."""
    args = ["regen"]
    if figure_id:
        args.extend(["--id", figure_id])
    if manuscript:
        args.append("--manuscript")
    if clone_ok:
        args.append("--clone-ok")
    if not figure_id and not manuscript:
        raise ValueError("pass figure_id and/or manuscript=True")
    return _run_flow(*args)


def load_skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _as_ax_functions():
    """Adapt callables to whatever the installed axllm expects."""
    try:
        from axllm import fn  # type: ignore

        built = []
        for func in (list_figures, figure_status, regen_figure):
            try:
                built.append(fn(func))
            except TypeError:
                # Fluent builder ports: fn("name").handler(...).build()
                built.append(
                    fn(func.__name__)
                    .description(func.__doc__ or func.__name__)
                    .handler(func)
                    .build()
                )
        return built
    except Exception:
        return [
            {"name": "list_figures", "description": list_figures.__doc__, "func": list_figures},
            {"name": "figure_status", "description": figure_status.__doc__, "func": figure_status},
            {"name": "regen_figure", "description": regen_figure.__doc__, "func": regen_figure},
        ]


def build_agent():
    """Build an AxAgent with tools bound to figure_flow.

    Requires ``pip install axllm``. Returns the agent object; caller supplies
    an ``ai(...)`` client and calls ``forward``.
    """
    try:
        from axllm import agent
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "axllm not installed. Install with: pip install axllm\n"
            "Or use the deterministic CLI: python3 scripts/figure_flow.py --help"
        ) from exc

    skill_body = load_skill_text()
    config = {
        "agentIdentity": {
            "name": "manuscriptFigureFlow",
            "description": (
                "Regenerate Faber2026 manuscript figures via the catalog. "
                "Never open producer source unless figure_flow fails."
            ),
        },
        "functions": _as_ax_functions(),
        "skills": [
            {
                "name": "manuscript-figure-regen",
                "content": skill_body,
            }
        ],
    }
    return agent(
        'request:string -> action:class "list, regen, status, explain", '
        "figure_ids:string[], notes:string",
        config,
    )


# Mermaid DAG for human/agent readability (execution uses figure_flow, not this).
MANUSCRIPT_FLOW_MERMAID = """
flowchart TD
  %%ax load: path:string -> nodes:json
  %%ax sort: nodes:json -> order:string[]
  %%ax run: order:string[], dry_run:boolean -> receipts:json

  load[Load catalog.yaml] --> sort[Topo-sort deps]
  sort --> run[Run producers + write receipts]
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-skill",
        action="store_true",
        help="print SKILL.md and exit",
    )
    parser.add_argument(
        "--print-mermaid",
        action="store_true",
        help="print the documentary AxFlow mermaid and exit",
    )
    parser.add_argument(
        "--check-tools",
        action="store_true",
        help="run list_figures via tools (no axllm required)",
    )
    parser.add_argument(
        "--build-agent",
        action="store_true",
        help="construct AxAgent (requires axllm); does not call an LLM",
    )
    args = parser.parse_args(argv)

    if args.print_skill:
        print(load_skill_text())
        return 0
    if args.print_mermaid:
        print(MANUSCRIPT_FLOW_MERMAID.strip())
        return 0
    if args.check_tools:
        print(list_figures())
        return 0
    if args.build_agent:
        ag = build_agent()
        print(f"built agent: {type(ag).__name__}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
