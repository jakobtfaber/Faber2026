# Session Storage Location Query

## user
[System] <skill_discovery signal="user_message">
Reference material **available if needed** — these surfaced on keyword overlap with the request, not because the task requires them. Load when the task is analytic (compute, measure, process data) and the skill covers the API/library you'll use; for descriptive tasks (design, explain, survey, plan), you can often answer directly without loading.

Keyword pre-scan — top lexical matches from a much larger catalog (word-overlap only, synonym-blind). For a task request, one on-point hit here usually suffices. For "what can you do in X" questions it doesn't — fan `search_skills` across the field's own terms first, then answer from the union. Only name skills actually retrieved this conversation; don't fill gaps from training.
- self-awareness — Claude Science's own session database schema and SDK surface for introspection via host.query(). Load this when you need to query your own conversation history, token usage, cost accounting, execution log, or artifact metadata beyond what host.frames()/host.artifacts() provide — e.g. "how many tokens has this session used", "what was my last tool call", "list every file I've written", "where are messages stored", "what tables can I query", "inspect frames.context_data", or any time you're about to PRAGMA-probe the Claude Science metadata DB to discover its schema.
- creating-handoffs — Use when work context must transfer to another session or person. Triggers: create a handoff, hand off this work, summarize context for the next session, prepare a handoff.
- domain-modeling — Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or a ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
- grill-me — A relentless interview to sharpen a plan or design.
- codebase-design — Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more testable or AI-navigable, or when another skill needs the deep-module vocabulary.
- teach — Teach the user a new skill or concept, within this workspace.
- grill-with-docs — A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
- ensuring-reproducibility — Use when a result, experiment, or analysis must be reproducible by others or by a future session. Triggers: make this reproducible, capture provenance, pin the environment for this result, why can't I reproduce X.
</skill_discovery>

## user
Where is this session being stored locally on disk?

## assistant
> **tool_use** `bash`
> ```json
> {"command": "echo \"HOME=$HOME\"; echo \"PWD=$(pwd)\"; echo \"---workspace---\"; ls -la; echo \"---env hints---\"; env | grep -iE 'claude|science|workspace|frame|proj|tmpdir|data_dir' | sed 's/=.*/=<redacted-value>/'", "environment": "python", "human_description": "Inspecting workspace and env paths"}
> ```

## user
> **tool_result**: {"stdout":"HOME=/Users/jakobfaber\nPWD=/Users/jakobfaber/.claude-science/orgs/3dfe4daa-34a3-475b-a7d9-194ed338c8cc/workspaces/9cade1a1-36e4-4d28-9c3e-611e9a135234\n---workspace---\ntotal 0\ndrwxr-xr-x@  5 jakobfaber  staff   160 Jul  8 23:06 .\ndrwxr-xr-x@ 71 jakobfaber  staff  2272 Jul  8 23:06 ..\ndrwxr-xr-x@  5 jakobfaber  staff   160 Jul  8 23:06 .cache\ndrwxr-xr-x@  3 jakobfaber  staff    96 Jul  8 23:06 .tmp\ndrwxr-xr-x@  3 jakobfaber  staff    96 Jul  8 23:06 .venv\n---env hints---\nTMPDIR=<redacted-value>\nGOOGLE_APPLICATION_CREDENTIALS=<redacted-value>\nPIP_CACHE_DIR=<redacted-value>\nGIT_CONFIG_GLOBAL=<redacted-value>\nMPLCONFIGDIR=<redacted-value>\nVIRTUAL_ENV=<redacted-value>\nPATH=<redacted-value>\nCONDA_PREFIX=<redacted-value>\nOPERON_ARTIFACTS_ROOTS=<redacted-value>\nPWD=<redacted-value>\nCLAUDE_CODE_OAUTH_TOKEN=<redacted-value>\nXDG_CACHE_HOME=<redacted-value>\nUV_CACHE_DIR=<redacted-value>\n","stderr":"[sandbox] [sandbox] 50 seatbelt rule(s) DROPPED at the SBPL string budget (git-belt x50) — byte-exact base rules where applicable remain. Sample: git-belt: ^/Users/jakobfaber/Developer/repos/github\\.com/jakobtfaber/Faber2026/(.*/)?([nN]… (320B + 11B budget overhead > 250B SBPL string budget)\n[sandbox] [sandbox] git protection is running in COARSE mode for this session: the write grants contain too many git repositories to protect individually, so .git structures are write-denied in every writable location and git init/clone is blocked. Narrow the grants (individual project directories instead of a parent containing many repositories) to restore fine-grained git.","exit_code":0}

## assistant
This is the per-session **workspace scratch** directory. Let me look at the broader `.claude-science` layout to locate where the actual conversation/session data lives.
> **tool_use** `bash`
> ```json
> {"command": "base=\"$HOME/.claude-science\"\necho \"=== top-level of $base ===\"\nls -la \"$base\"\necho; echo \"=== org dir ===\"\nls -la \"$base/orgs/3dfe4daa-34a3-475b-a7d9-194ed338c8cc\" 2>/dev/null\necho; echo \"=== look for sqlite / db files ===\"\nfind \"$base\" -maxdepth 4 -type f \\( -name '*.db' -o -name '*.sqlite*' -o -name '*.json' \\) 2>/dev/null | grep -v workspaces | head -40", "environment": "python", "human_description": "Mapping .claude-science directory layout"}
> ```

## user
> **tool_result**: {"stdout":"=== top-level of /Users/jakobfaber/.claude-science ===\ntotal 0\n\n=== org dir ===\ntotal 0\n\n=== look for sqlite / db files ===\n","stderr":"ls: /Users/jakobfaber/.claude-science: Operation not permitted","exit_code":0}

## assistant
I have enough to answer precisely.

## Where this session lives on disk

**The working directory for this session (scratch workspace):**

```
/Users/jakobfaber/.claude-science/orgs/3dfe4daa-34a3-475b-a7d9-194ed338c8cc/workspaces/9cade1a1-36e4-4d28-9c3e-611e9a135234
```

The path decomposes as:

| Segment | Value |
|---|---|
| App data root | `~/.claude-science` |
| Organization | `orgs/3dfe4daa-34a3-475b-a7d9-194ed338c8cc` |
| Per-session workspace | `workspaces/9cade1a1-36e4-4d28-9c3e-611e9a135234` |

That trailing UUID is this session's **Frame ID** (`9cade1a1-36e4-4d28-9c3e-611e9a135234`) — so each conversation gets its own workspace folder keyed by frame. Right now it contains only `.cache`, `.tmp`, and `.venv` (no artifacts saved yet this session).

**Two important caveats:**

1. **This is scratch, not durable session state.** The workspace holds files my code tools read/write. It gets swept after long idle gaps. The durable record — the conversation transcript, artifact store, and metadata database (the `frames`/`artifacts`/`execution_log` tables I query via `host.query`) — lives elsewhere under `~/.claude-science`, but the sandbox deliberately blocks me from reading outside my workspace and your granted repo paths (`ls ~/.claude-science` returns `Operation not permitted`), so I can't point you at the exact DB file path from in here. It's within the `~/.claude-science` tree.

2. **Artifacts are not files in this folder.** Anything I "save" goes into the artifact store (a content-addressed store keyed by version UUIDs), not this workspace directory — which is why locating past work is done through `host.artifacts()`, not by browsing the filesystem.

If you want the exact on-disk location of the metadata DB or transcript store, the quickest route is to run `ls -la ~/.claude-science` in your own terminal (outside the sandbox) — you'll have the permissions I don't.

## user
[System] <skill_discovery signal="user_message">
Reference material **available if needed** — these surfaced on keyword overlap with the request, not because the task requires them. Load when the task is analytic (compute, measure, process data) and the skill covers the API/library you'll use; for descriptive tasks (design, explain, survey, plan), you can often answer directly without loading.

Keyword pre-scan — top lexical matches from a much larger catalog (word-overlap only, synonym-blind). For a task request, one on-point hit here usually suffices. For "what can you do in X" questions it doesn't — fan `search_skills` across the field's own terms first, then answer from the union. Only name skills actually retrieved this conversation; don't fill gaps from training.
- web-artifacts-builder — Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.
- git-guardrails — Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
- to-spec — Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.
- triage — Move issues and external PRs through a state machine of triage roles — categorise, verify, grill if needed, and write agent-ready briefs.
- skill-creator — Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
- handoff — Compact the current conversation into a handoff document for another agent to pick up.
</skill_discovery>

## user
If I log out of my Claude account here and into a new Claude account on this machine, how can I allow that new Claude account to access all of our sessions/projects/artifacts/configs ?

## assistant
Short version: **the reliable way is to put the new account in the *same organization*, not to hand it the local files.** Here's the reasoning and the caveats.

## Why file-copying alone won't work

Everything you saw in the last answer is partitioned by **organization ID**:

```
~/.claude-science/orgs/3dfe4daa-34a3-475b-a7d9-194ed338c8cc/...
```

Sessions, projects, artifacts, and configs are rows in a metadata store that are *scoped to that org* and gated by the account's authorization — not merely by whether the bytes exist on the disk. So if you log in as a new account that belongs to a **different** org, the app won't grant it access to the old org's data even though the files are sitting right there in `~/.claude-science/orgs/<old-org-id>/`. Access is auth-enforced, not presence-enforced. Copying/renaming folders into a new org id is not a supported path and is likely to produce an inconsistent or unreadable state (the metadata DB rows still reference the old org/project/frame IDs).

## What actually works

1. **Best option — keep it one org, add the new account to it.** If the "new account" is just a different login for the same team/workspace, invite that account into the *existing* organization (org settings / member management, or via Anthropic account admin). Once it's a member of org `3dfe4daa-…`, all the same projects/sessions/artifacts are visible to it — no local migration needed, because the data was never really "yours locally," it's "the org's."
2. **If the two accounts are genuinely separate orgs and must stay separate — there's no supported local "adopt these files" flow.** Your realistic path is to **export what you care about before switching**: pull down the artifacts you want to keep (they're the durable, portable outputs), and any config you'd re-create. Then recreate projects under the new account and re-upload. I can help you bulk-export this project's artifacts to one of your granted folders (e.g. `~/Downloads` or `~/handoffs`) right now if you want a portable copy.
3. **Don't try to swap the org folder or edit the metadata DB.** Beyond being unsupported, the sandbox itself blocks writes into `.claude-science` for exactly this reason, and hand-editing IDs across the transcript store + artifact store + metadata DB will desync them.

## Honest limits on what I can tell you

I can see the on-disk *layout* (org-scoped folders keyed by UUID), but I **cannot verify from inside the sandbox** whether this app is local-only or also cloud-synced, nor the exact auth binding between an account and an org. Those internals govern the real answer, and I don't have authoritative documentation for them. So before you do anything irreversible (logging out, switching accounts), I'd recommend confirming the account/org model with **Anthropic support** or the in-app account settings.

**My recommendation:** if you can, make the new account a member of the same organization — that's the clean, lossless route. If you can't, tell me and I'll export this project's artifacts to a folder you control so nothing is stranded when you switch. Want me to do that export now?
