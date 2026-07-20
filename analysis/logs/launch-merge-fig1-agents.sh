#!/usr/bin/env bash
# Launch Codex + Claude design agents for merge-fig1-jointmodel brief.
set -euo pipefail
ROOT="/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026"
cd "$ROOT"
mkdir -p logs

PROMPT_FILE="$ROOT/logs/merge-fig1-jointmodel-prompt-short.txt"
cat > "$PROMPT_FILE" <<'EOF'
Read-only design pass. Do not edit files or run git writes.

1. Read logs/merge-fig1-jointmodel-brief.md and follow it exactly.
2. Inspect scripts/plot_codetection_gallery.py, pipeline/flits/batch/codetection_plots.py, sections/observations.tex, sections/jointmodel_pairs.tex, sections/results.tex (jointmodel refs), docs/rse/specs/plan/plan-unified-12burst-figure.md, docs/rse/specs/jointmodel/jointmodel-pair-fit-quality-flags.md, and trust-reset bits in CONTEXT.md.
3. Optionally view figures/codetection_gallery.png and one figures/jointmodel_pair/*_jointmodel_pair.png.
4. Return ONLY the structured proposal (brief sections 1-8).
EOF

PROMPT="$(cat "$PROMPT_FILE")"

# Kill any leftover design agents from prior attempts
pkill -f 'codex exec.*merge-fig1|codex exec.*Read-only design pass' 2>/dev/null || true
pkill -f 'claude --model claude-fable-5 --effort xhigh' 2>/dev/null || true
sleep 1

rm -f logs/codex-merge-fig1-jointmodel.md \
      logs/claude-merge-fig1-jointmodel.md \
      logs/claude-merge-fig1-jointmodel.stream.jsonl
: > logs/codex-merge-fig1-jointmodel.stdout.log
: > logs/codex-merge-fig1-jointmodel.stderr.log
: > logs/claude-merge-fig1-jointmodel.stderr.log

# Codex: argv prompt, stdin closed hard
(
  exec < /dev/null
  env -u OPENAI_API_KEY -u CODEX_API_KEY codex exec \
    --skip-git-repo-check \
    -C "$ROOT" \
    -m gpt-5.6-sol \
    -c 'model_reasoning_effort="medium"' \
    -s read-only \
    -o logs/codex-merge-fig1-jointmodel.md \
    "$PROMPT" \
    > logs/codex-merge-fig1-jointmodel.stdout.log \
    2> logs/codex-merge-fig1-jointmodel.stderr.log
) &
echo "codex_pid=$!"

# Claude: prompt via printf pipe (required for stream-json), effort xhigh
(
  printf '%s' "$PROMPT" | claude \
    --model claude-fable-5 \
    --effort xhigh \
    --permission-mode plan \
    -p \
    --verbose \
    --output-format stream-json \
    --include-partial-messages \
    > logs/claude-merge-fig1-jointmodel.stream.jsonl \
    2> logs/claude-merge-fig1-jointmodel.stderr.log
) &
echo "claude_pid=$!"

sleep 2
ps -p $(jobs -p) -o pid,etime,state,command 2>/dev/null | head -20 || true
pgrep -fl 'codex exec|claude --model claude-fable-5' | head -10
