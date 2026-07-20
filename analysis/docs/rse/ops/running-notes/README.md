# Manuscript pulse + Running Notes

One page: ADHD map (NOW / data chain / READY·IN-DRAFT) + jot box.
Submit → headless **Claude Code CLI** sorts into the Faber2026 roadmap.
Not a Cursor agent. Not a Cursor canvas.

## URLs

| URL | Role |
|-----|------|
| https://faber2026.jakobtfaber.com | Public (Cloudflare Tunnel `orchestrator-tunnel` → `:18765`) |
| http://127.0.0.1:18765/ | Local origin |

Tunnel ingress: `~/.cloudflared/config.yml` (template in
`maistro/config/cloudflared-config.yml`). DNS: CNAME → tunnel UUID.

**Auth:** Cloudflare Access on the hostname (OTP / allow-listed emails —
same pattern as Hermes). No app-level Submit token. Localhost has no Access
gate (loopback only).

## Start

```bash
# from repo root
python3 scripts/running_notes.py serve
# open http://127.0.0.1:18765/  or  https://faber2026.jakobtfaber.com
```

Persistent origin (optional):

```bash
cp docs/rse/ops/running-notes/com.jakobfaber.faber2026-notes.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jakobfaber.faber2026-notes.plist
```

Or CLI:

```bash
python3 scripts/running_notes.py submit "casey DM strip — pick before asking"
python3 scripts/running_notes.py status
python3 scripts/running_notes.py dry-run "test"   # argv only; no Claude
```

Make aliases: `make notes-serve` · `make notes MSG='…'`

## Edit the map

Author snapshot lives in `pulse.json` (served as `/api/pulse`). Change NOW,
chain “you are here”, or section READY/IN-DRAFT there; reload the page.

## What happens on Submit

1. Append raw note → `inbox/notes.jsonl` (gitignored).
2. Invoke:
   `claude --model claude-opus-4-8 --effort xhigh -p '…' < /dev/null`
3. Claude reads BOARD + wayfinder resume pointer + data-chain vocabulary,
   writes a short disposition under `dispositions/<id>.json` (tracked when
   you choose to commit them).
4. UI status: **queued → Claude sorting → done** (or error with auth hint).

## Auth

Subscription only. Check: `claude auth status` (expect `claude.ai` / Max).
Never `--bare`. If submit fails auth, the bridge surfaces that hint and
keeps the note in the inbox.

## Rules Claude must follow

- Sort onto existing tickets / BOARD sections / data-chain layers.
- Plain English disposition for the status panel.
- **Do not invent science claims** (no new DMs, TOAs, energies, …).
- Write only under `docs/rse/ops/running-notes/dispositions/`.

## Paths

| Path | Role |
|------|------|
| `pulse.json` | Author map snapshot (NOW / chain / sections) |
| `index.html` | Unified pulse + notes UI |
| `inbox/notes.jsonl` | Append-only raw notes (gitignored) |
| `inbox/<id>.claude.log` | Claude stdout/stderr for that job (gitignored) |
| `dispositions/<id>.json` | Structured sort result |
| `status.json` | Live UI state (gitignored) |
