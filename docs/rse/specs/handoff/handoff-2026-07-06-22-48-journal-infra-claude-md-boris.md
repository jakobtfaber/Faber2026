# Handoff: Multi-harness journal cadence verified end-to-end; global CLAUDE.md /boris pass shipped

---
**Date:** 2026-07-06 22:48
**Author:** AI Assistant (claude-fable-5/session-9f491a6c)
**Status:** Handoff
**Branch:** main
**Commit:** 1dec28c (this session's last; main tip now 7f93b10 from concurrent sessions)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Journal cadence — Claude hooks (UserPromptSubmit staleness + PostToolUse mid-turn trigger) | ✅ Complete | Live-verified in this session (hooks fire, model complies) |
| Journal cadence — Codex hooks | ✅ Complete, **verified end-to-end** | Two live `codex exec` canaries: gpt-5.5 quoted both injected reminders verbatim. Two blockers found+fixed (see Learnings) |
| Journal cadence — Cursor hooks (`.cursor/hooks.json`) | ✅ Built, ⚠ untested in live Cursor | postToolUse cadence reminder + afterFileEdit self-journaling fallback; smoke-tested only. Cursor will prompt to approve project hooks on next open |
| Journal cadence — launchd watchdog (all-harness backstop) | ✅ Complete | `com.jakobfaber.faber2026-journal-watchdog`, every 5 min, detection-only |
| AGENTS.md honesty pass | ✅ Complete | Owner correction: instruction files have no clock — demoted to advisory in `AGENTS.md` + protocol doc |
| Global `~/.claude/CLAUDE.md` /boris critique + improve | ✅ Complete, **merged** | dotfiles PR #209 squash-merged (`b5fa6ad`); `chezmoi verify` green; local main reset to origin |
| Collateral stale-doc fixes (`~/GEMINI.md` glossary rule, dead insight-hook ref) | ✅ Complete | Both verified stale before fixing |
| A1 two-screen design discussion | 🔄 Open thread | Owner asked to open it; six elements presented; trigger-calibration question (elements 1/2) is the live one |
| Trust-reset §V execution | 🔄 In progress by OTHER sessions | P0.1/P2.1/P2.2 closed (their handoff below); Codex session live on P2.3 at time of writing |

**Current Workflow Phase:** Implement (infrastructure lane complete; research lanes V·P2–P6 in flight across sessions)

## Workflow Artifacts

- [plan-trust-reset-revalidation.md](../plan/plan-trust-reset-revalidation.md) — the seven-phase §V re-validation plan (V1–V6); governs all research lanes
- [research-trust-reset-revalidation.md](../research/research-trust-reset-revalidation.md) — explorer inventories backing the plan
- [plan-circulation-readiness.md](../plan/plan-circulation-readiness.md) — master lane ledger (A/B/C/D/E/F/G + V), decisions ledger (all re-opened as working choices)
- [handoff-2026-07-06-22-30-provenance-p0-p2-machine-verification.md](../handoff/handoff-2026-07-06-22-30-provenance-p0-p2-machine-verification.md) — the concurrent provenance session's handoff (P0.1/P2.1/P2.2 closed) — read for research-lane state
- [machine-inventory-verification-2026-07-06.md](../misc/machine-inventory-verification-2026-07-06.md) — live-verified machine inventory
- [implement-route-a-crosscheck.md](../implement/implement-route-a-crosscheck.md) — in-flight Codex P2.3 work (cube integrity crosscheck)

## Critical References

- `docs/rse/journal-protocol.md` — the journal contract every agent in this repo must follow (cadence, agent tags, enforcement matrix incl. Codex trust-gate + JSON-output constraints)
- `docs/rse/journal.jsonl` — live activity log; **read the tail before doing anything** — it is the coordination ground truth for concurrent writers
- `docs/rse/board/readiness.html` — task board (artifact URL in journal-protocol.md §2); lanes, trust state, journal panel

## Recent Changes (this session)

- `scripts/journal-*.sh` (5 scripts) + `scripts/render_journal_panel.py`, `scripts/launchd/com.jakobfaber.faber2026-journal-watchdog.plist` — full cadence system (commits `cdc7bf2`→`1dec28c`)
- `.claude/settings.json`, `.codex/hooks.json`, `.cursor/hooks.json`, `AGENTS.md` — per-harness enforcement surfaces
- `scripts/journal-staleness-hook.sh:10-15` — output switched to `hookSpecificOutput` JSON (Codex rejects plain stdout starting with `[`)
- Off-repo: dotfiles `home/dot_claude/private_CLAUDE.md` (PR #209, merged `b5fa6ad`); `~/GEMINI.md:13`; `~/.codex/config.toml` `[hooks.state]` — trust entries for both repo journal hooks (machine-local)

## Verification State / Known-Broken

- **Codex hook layer:** VERIFIED (canary transcripts in session scratchpad). Constraint: trust entries live in `~/.codex/config.toml`, machine-local — **any change to a hook command string in `.codex/hooks.json` silently disables that hook until re-trusted** (script-content edits are safe).
- **Cursor hook layer:** NOT yet exercised by a live Cursor session — gating + JSON parsing smoke-tested only.
- **Unpushed:** Faber2026 main is **11 commits ahead of origin** (push gated — Overleaf pulls main; owner go required).
- **Dirty working tree:** `CLAUDE.md` (repo) — owner's own uncommitted preamble edit, separate lane, do not sweep. `docs/rse/journal.jsonl` accumulates live entries between commits by design.
- **P2.3 (other session):** cube-integrity detector failing on 4/12 CHIME cubes (no >5σ detection under pre-registered statistic), 7 lag-table triage rows — per its own journal entries; not this session's claim to verify.

## Learnings

- **Codex hooks engine is Claude-compatible by construction** (`ClaudeHooksEngine` in openai/codex source) — same events, same `hookSpecificOutput` wire format. Two real gotchas: (1) per-hook `trusted_hash` gate in `~/.codex/config.toml` (hash = sha256 of key-sorted canonical JSON of `{event_name, matcher-group}` — reproduced and validated against known hashes); (2) UserPromptSubmit stdout beginning `[`/`{` that isn't valid wire JSON is dropped as Failed.
- **Instruction files cannot enforce time-based protocols** (no clock). Enforcement hierarchy: hooks (mechanical) > watchdog (wall-clock detection only) > AGENTS.md (advisory). Cursor's `afterFileEdit` hook can self-journal without model cooperation — strongest pattern for uncooperative harnesses.
- **The journal is working as designed across harnesses:** the provenance session (claude-sonnet-5) and a live Codex session (codex-gpt-5) are both self-reporting with lane tags; the pre-journal "unattributed-writer" era is closed.
- Global CLAUDE.md carried three verified-stale references (dead script, GEMINI.md contradiction, live-state "currently present" claim) — config files rot like docs; verify tool-path claims before relying.

## Action Items & Next Steps

1. [ ] **Resume the A1 design discussion** with the owner — the trigger-calibration question (escalation thresholds for the second broadening component) is the open item that changes fitting behavior. Context: CONTEXT.md "Scint→scattering coupling" + board A1 card.
2. [ ] **Owner decision: push Faber2026 main** (11 commits) — Overleaf pulls main; gated.
3. [ ] Open Cursor once in this repo to approve the project hooks (first live exercise of the Cursor layer).
4. [ ] Research lanes: follow the provenance handoff (P2 remainder, then P3–P6 per plan-trust-reset-revalidation.md); coordinate via journal tail — a Codex session may still hold P2.3.
5. [ ] Deferred: repo CLAUDE.md pointer to journal-protocol.md (owner's editor holds the file); my-skillset extraction of the separate-lane protocol into `dirty-git-state` skill (recommended in the /boris critique).

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` (against `plan-trust-reset-revalidation.md`, next open phase) — or none if resuming the A1 discussion, which is conversational.

## Other Notes

- Journal protocol applies to the receiving session immediately: append on start (`scripts/journal-append.sh "<agent>" "<lane>" working "<note>"`), every ≤10 min while active, rebake + redeploy board at boundaries.
- `382aa39 "Remove remaining manuscript figures"` (22:20, journaled) removed appendix figures — consistent with trust reset; check journal.jsonl for its attribution before touching appendix.tex.
- Dotfiles has an untracked separate-active lane: `home/dot_codex/publish-policy.toml` (being authored ~22:42, not this session's) — preserved, decision pending with its owner.

---

**Handoff created by AI Assistant on 2026-07-06**
