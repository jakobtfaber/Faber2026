#!/usr/bin/env python3
"""Running Notes → headless Claude Code CLI bridge (ADHD manuscript pulse).

Append-only inbox + localhost UI. Submit invokes:

  claude --model claude-opus-4-8 --effort xhigh -p '…' < /dev/null

Not a Cursor agent. Stdlib only.

Usage:
  python3 scripts/running_notes.py serve [--port 8765]
  python3 scripts/running_notes.py submit "note text…"
  python3 scripts/running_notes.py status
  python3 scripts/running_notes.py dry-run "note text…"
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "docs/rse/ops/running-notes"
INBOX = OPS / "inbox"
NOTES_JSONL = INBOX / "notes.jsonl"
DISPOSITIONS = OPS / "dispositions"
STATUS_PATH = OPS / "status.json"
HTML_PATH = OPS / "index.html"
PULSE_PATH = OPS / "pulse.json"
BOARD = ROOT / "docs/rse/control/BOARD.md"
MAP = ROOT / "docs/rse/wayfinder/map-apj-submission.md"

# 8765 is often taken by Claude Code local helpers on this machine.
DEFAULT_PORT = 18765
CLAUDE_MODEL = "claude-opus-4-8"
CLAUDE_EFFORT = "xhigh"
_job_lock = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dirs() -> None:
    INBOX.mkdir(parents=True, exist_ok=True)
    DISPOSITIONS.mkdir(parents=True, exist_ok=True)


def write_status(payload: dict) -> None:
    ensure_dirs()
    STATUS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_status() -> dict:
    if not STATUS_PATH.exists():
        return {"state": "idle", "plain_english": "No notes submitted yet."}
    return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


def append_note(text: str) -> dict:
    ensure_dirs()
    note = {
        "id": uuid.uuid4().hex[:12],
        "ts": utc_now(),
        "text": text.strip(),
    }
    with NOTES_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(note, ensure_ascii=False) + "\n")
    return note


def find_claude() -> Path | None:
    env = os.environ.get("CLAUDE_BIN")
    if env:
        p = Path(env)
        return p if p.is_file() else None
    which = shutil.which("claude")
    if which:
        return Path(which)
    for candidate in (
        Path.home() / ".local/bin/claude",
        Path("/opt/homebrew/bin/claude"),
        Path("/usr/local/bin/claude"),
    ):
        if candidate.is_file():
            return candidate
    return None


def auth_hint() -> str:
    return (
        "Claude Code CLI not ready. Run: claude auth status "
        "(expect authMethod claude.ai, subscriptionType max). "
        "Do not use --bare. Then retry submit."
    )


def check_claude_auth(claude: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [str(claude), "auth", "status"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(ROOT),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"Could not run claude auth status: {exc}"
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return False, auth_hint() + f"\n\n{out.strip()}"
    compact = out.lower().replace(" ", "")
    if '"loggedin":true' in compact:
        return True, out.strip()
    if "not logged" in out.lower() or "unauthenticated" in out.lower():
        return False, auth_hint() + f"\n\n{out.strip()}"
    return True, out.strip()


def build_prompt(note: dict, disposition_path: Path) -> str:
    resume_excerpt = ""
    if MAP.exists():
        text = MAP.read_text(encoding="utf-8")
        marker = "## Resume pointer"
        idx = text.find(marker)
        resume_excerpt = text[idx : idx + 1800] if idx >= 0 else text[:1200]
    board_head = BOARD.read_text(encoding="utf-8")[:2000] if BOARD.exists() else "(missing)"

    return f"""You are sorting an ADHD "Running Note" into the Faber2026 manuscript plan.

REPO ROOT: {ROOT}

AUTHORITY (read these files with your tools; do not invent science claims):
- Wayfinder map + resume pointer: docs/rse/wayfinder/map-apj-submission.md
- Manuscript board: docs/rse/control/BOARD.md
- Verification / data chain: docs/rse/protocols/verification-protocol.md
  (plain vocabulary: Raw Data → Input Data Products → Measurements and Fits
   → Analyses and Interpretations → In-Manuscript Claims)
- Trust / context: CONTEXT.md

CURRENT RESUME POINTER EXCERPT (may be stale — prefer live map file):
---
{resume_excerpt}
---

BOARD HEAD EXCERPT:
---
{board_head}
---

NOTE id={note["id"]} ts={note["ts"]}:
---
{note["text"]}
---

TASK:
1. Interpret the note in plain English (what the author meant).
2. Sort it onto the roadmap: which wayfinder ticket(s), BOARD section(s),
   and data-chain layer it belongs to. Prefer existing tickets/sections.
3. If it is a new owner decision or execution item, say so — do NOT invent
   new science numbers, DMs, TOAs, or manuscript claims.
4. Write ONE disposition JSON file exactly to:
   {disposition_path}
   Schema:
   {{
     "id": "{note["id"]}",
     "note_id": "{note["id"]}",
     "sorted_at": "<ISO-8601 UTC>",
     "plain_english": "<2-5 sentences for the ADHD status UI>",
     "data_chain": "<one of: Raw Data | Input Data Products | Measurements and Fits | Analyses and Interpretations | In-Manuscript Claims | unclear>",
     "wayfinder_tickets": ["<nn or ticket filename stems>"],
     "board_sections": ["<section headings from BOARD>"],
     "suggested_next": "<one concrete next action, or empty string>",
     "invented_claims": false
   }}
5. Also print the same JSON object alone as your final message (no markdown fence).

Pathspec discipline: only write the disposition file under
docs/rse/ops/running-notes/dispositions/. Do not edit BOARD, wayfinder,
tex, pipeline pin, or unrelated dirty lanes.
"""


def claude_cmd(claude: Path, prompt: str) -> list[str]:
    return [
        str(claude),
        "--model",
        CLAUDE_MODEL,
        "--effort",
        CLAUDE_EFFORT,
        "-p",
        prompt,
    ]


def extract_json_object(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    start = text.rfind("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def fallback_disposition(note: dict, reason: str) -> dict:
    return {
        "id": note["id"],
        "note_id": note["id"],
        "sorted_at": utc_now(),
        "plain_english": reason,
        "data_chain": "unclear",
        "wayfinder_tickets": [],
        "board_sections": [],
        "suggested_next": "",
        "invented_claims": False,
        "error": True,
    }


def run_claude_sort(note: dict, *, dry_run: bool = False) -> dict:
    ensure_dirs()
    disposition_path = DISPOSITIONS / f"{note['id']}.json"
    prompt = build_prompt(note, disposition_path)
    claude = find_claude()
    if claude is None:
        disp = fallback_disposition(note, auth_hint())
        disposition_path.write_text(json.dumps(disp, indent=2) + "\n", encoding="utf-8")
        return disp

    cmd = claude_cmd(claude, prompt)
    if dry_run:
        return {
            "dry_run": True,
            "note": note,
            "argv_prefix": cmd[:6] + ["<prompt>"],
            "stdin": "/dev/null",
            "disposition_path": str(disposition_path.relative_to(ROOT)),
            "claude_bin": str(claude),
        }

    ok, auth_out = check_claude_auth(claude)
    if not ok:
        disp = fallback_disposition(note, auth_out)
        disposition_path.write_text(json.dumps(disp, indent=2) + "\n", encoding="utf-8")
        return disp

    log_path = INBOX / f"{note['id']}.claude.log"
    try:
        with log_path.open("w", encoding="utf-8") as log_fh:
            proc = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(ROOT),
                timeout=900,
            )
    except subprocess.TimeoutExpired:
        disp = fallback_disposition(
            note,
            "Claude sorting timed out after 15 minutes. Note is still in the inbox.",
        )
        disposition_path.write_text(json.dumps(disp, indent=2) + "\n", encoding="utf-8")
        return disp
    except OSError as exc:
        disp = fallback_disposition(note, f"Failed to launch Claude: {exc}")
        disposition_path.write_text(json.dumps(disp, indent=2) + "\n", encoding="utf-8")
        return disp

    if disposition_path.exists():
        try:
            disp = json.loads(disposition_path.read_text(encoding="utf-8"))
            if isinstance(disp, dict):
                disp.setdefault("note_id", note["id"])
                return disp
        except json.JSONDecodeError:
            pass

    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    parsed = extract_json_object(log_text)
    if parsed is not None:
        parsed.setdefault("id", note["id"])
        parsed.setdefault("note_id", note["id"])
        parsed.setdefault("sorted_at", utc_now())
        parsed.setdefault("invented_claims", False)
        disposition_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
        return parsed

    reason = (
        f"Claude exited {proc.returncode} without a disposition file. "
        f"See {log_path.relative_to(ROOT)}. Note remains in the inbox."
    )
    disp = fallback_disposition(note, reason)
    disposition_path.write_text(json.dumps(disp, indent=2) + "\n", encoding="utf-8")
    return disp


def submit(text: str, *, wait: bool = True, dry_run: bool = False) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("Note text is empty.")

    if dry_run:
        note = {
            "id": "dryrun000001",
            "ts": utc_now(),
            "text": text,
        }
        return run_claude_sort(note, dry_run=True)

    if not _job_lock.acquire(blocking=False):
        return {
            "state": "busy",
            "plain_english": "Another note is still being sorted. Wait, then retry.",
        }

    note = append_note(text)
    write_status(
        {
            "state": "queued",
            "note_id": note["id"],
            "submitted_at": note["ts"],
            "plain_english": "Queued. Claude will sort this into the roadmap.",
            "note_preview": text[:240],
        }
    )

    def worker() -> None:
        try:
            write_status(
                {
                    "state": "sorting",
                    "note_id": note["id"],
                    "submitted_at": note["ts"],
                    "plain_english": "Claude is sorting this note into the manuscript plan…",
                    "note_preview": text[:240],
                }
            )
            disp = run_claude_sort(note, dry_run=False)
            err = bool(disp.get("error"))
            write_status(
                {
                    "state": "error" if err else "done",
                    "note_id": note["id"],
                    "submitted_at": note["ts"],
                    "finished_at": utc_now(),
                    "plain_english": disp.get("plain_english")
                    or ("Sorted." if not err else "Sort failed."),
                    "disposition": disp,
                    "disposition_path": str(
                        (DISPOSITIONS / f"{note['id']}.json").relative_to(ROOT)
                    ),
                }
            )
        finally:
            _job_lock.release()

    if wait:
        try:
            worker()
        except Exception:
            _job_lock.release()
            raise
        return read_status()

    threading.Thread(target=worker, daemon=True).start()
    return read_status()


class NotesHandler(BaseHTTPRequestHandler):
    server_version = "RunningNotes/1.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self._send(code, data, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            if not HTML_PATH.exists():
                self._json(500, {"error": f"Missing UI at {HTML_PATH}"})
                return
            self._send(
                200,
                HTML_PATH.read_bytes(),
                "text/html; charset=utf-8",
            )
            return
        if path == "/api/status":
            self._json(200, read_status())
            return
        if path in ("/api/pulse", "/pulse.json"):
            if not PULSE_PATH.exists():
                self._json(500, {"error": f"Missing pulse at {PULSE_PATH}"})
                return
            try:
                payload = json.loads(PULSE_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self._json(500, {"error": f"Invalid pulse.json: {exc}"})
                return
            self._json(200, payload)
            return
        if path == "/api/health":
            claude = find_claude()
            self._json(
                200,
                {
                    "ok": True,
                    "repo": str(ROOT),
                    "claude_bin": str(claude) if claude else None,
                    "pulse": str(PULSE_PATH) if PULSE_PATH.exists() else None,
                },
            )
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/submit":
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid JSON"})
            return
        # Auth is Cloudflare Access on faber2026.jakobtfaber.com (edge).
        text = (payload.get("text") or "").strip()
        if not text:
            self._json(400, {"error": "empty note"})
            return
        try:
            result = submit(text, wait=False, dry_run=False)
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return
        self._json(202, result)


def cmd_serve(port: int) -> int:
    ensure_dirs()
    if not HTML_PATH.exists():
        print(f"Missing UI: {HTML_PATH}", file=sys.stderr)
        return 1
    claude = find_claude()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), NotesHandler)
    print(f"Running Notes bridge: http://127.0.0.1:{port}/", flush=True)
    print(f"Repo: {ROOT}", flush=True)
    print(f"Claude: {claude or 'NOT FOUND — submit will fail with auth hint'}", flush=True)
    print("Ctrl-C to stop.", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    return 0


def cmd_status() -> int:
    print(json.dumps(read_status(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_serve = sub.add_parser("serve", help="Localhost ADHD UI + submit API")
    p_serve.add_argument("--port", type=int, default=DEFAULT_PORT)

    p_submit = sub.add_parser("submit", help="Append note and run Claude sort")
    p_submit.add_argument("text", nargs="+", help="Note text")
    p_submit.add_argument(
        "--async",
        dest="async_",
        action="store_true",
        help="Return after queueing (do not wait for Claude)",
    )

    sub.add_parser("status", help="Print status.json")

    p_dry = sub.add_parser("dry-run", help="Show Claude argv; do not call Claude")
    p_dry.add_argument("text", nargs="+", help="Note text")

    args = parser.parse_args(argv)

    if args.cmd == "serve":
        return cmd_serve(args.port)
    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "dry-run":
        print(json.dumps(submit(" ".join(args.text), dry_run=True), indent=2))
        return 0
    if args.cmd == "submit":
        result = submit(" ".join(args.text), wait=not args.async_, dry_run=False)
        print(json.dumps(result, indent=2))
        return 0 if result.get("state") in {"done", "queued", "sorting"} else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
