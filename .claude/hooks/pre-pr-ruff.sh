#!/usr/bin/env bash
# PreToolUse hook — runs Ruff check before any `gh pr create` command.
#
# Claude Code passes the full tool context on stdin as JSON:
#   { "tool_name": "Bash", "tool_input": { "command": "..." }, ... }
#
# Exit 0  → allow the tool call to proceed.
# Exit 2  → block the tool call (Claude treats this as a blocking error).
# stdout  → shown to the user.

set -euo pipefail

INPUT=$(cat)

# Extract the bash command being run.
COMMAND=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    cmd = d.get('tool_input', d).get('command', '')
    print(cmd)
except Exception:
    pass
" 2>/dev/null || true)

# Only act on gh pr create calls.
if ! printf '%s' "$COMMAND" | grep -qE 'gh[[:space:]]+pr[[:space:]]+create'; then
  exit 0
fi

# ── Locate Ruff ──────────────────────────────────────────────────────────────
RUFF=""
if [[ -x "backend/.venv/bin/ruff" ]]; then
  RUFF="backend/.venv/bin/ruff"
elif command -v ruff &>/dev/null; then
  RUFF="ruff"
else
  echo "⚠  ruff not found — skipping lint check before PR creation."
  exit 0
fi

# ── Run Ruff ─────────────────────────────────────────────────────────────────
echo "Running Ruff before creating PR..."
echo ""

if "$RUFF" check backend/app/ backend/tests/; then
  echo ""
  echo "✓ Ruff passed — proceeding with PR creation."
  exit 0
else
  echo ""
  echo "✗ Ruff check failed. Fix the errors above before creating the PR."
  exit 2
fi
