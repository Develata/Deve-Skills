#!/usr/bin/env bash
# codex_session_meta.sh — authoritative model/cli/effort lookup for a Codex MCP session
#
# Why this exists:
#   - Codex model self-report and `codex --version` both lose information
#     (observed 2026-04-27: dual artifact headers wrote `cli=0.125.0` while
#     the actual session JSONL records `cli_version=0.125.0-alpha.3`).
#   - Per .claude/skills/codex-orchestration/SKILL.md §1 "Model verification
#     oracle", the only authoritative source is the session JSONL written by
#     the codex runtime: `~/.codex{,-b}/sessions/YYYY/MM/DD/rollout-*-<threadId>.jsonl`.
#   - This script greps that JSONL and emits a stable key=value block so a
#     dual-review artifact can `<verbatim stdout>` it as a tamper-evident
#     header (any reviewer can re-run the same script against the same
#     threadId and reproduce the values byte-for-byte).
#
# Usage:
#   scripts/codex_session_meta.sh <threadId>
#
# Output (5 lines, key=value, stable order):
#   model=<slug>
#   cli_version=<ver>
#   effort=<low|medium|high|xhigh>
#   session_path=<absolute path to JSONL>
#   session_first_ts=<UTC ISO-8601 timestamp from filename>
#
# Exit codes:
#   0 = success
#   1 = bad usage
#   2 = no JSONL found for threadId in any codex home
#   3 = JSONL exists but model/cli_version not parseable

# NOTE: deliberately do NOT use `pipefail` here. grep | head -1 induces SIGPIPE
# on grep when head closes the pipe after the first line; with pipefail + set -e
# the script would exit silently. set -eu without pipefail is the right combo.
set -eu

if [[ $# -ne 1 ]]; then
  echo "usage: $(basename "$0") <threadId>" >&2
  echo "  e.g. $(basename "$0") 019dcab7-83ba-7781-9a89-e957ae771dfb" >&2
  exit 1
fi

threadId="$1"

# Auto-discover all codex homes (multi-account isolation per the
# codex-account-switching skill). Glob matches `~/.codex`, `~/.codex-b`,
# `~/.codex-personal`, `~/.codex-work`, etc. — any user-suffixed account
# layout. nullglob ensures the glob expands to nothing when no `.codex-*`
# accounts exist (avoids the literal string `~/.codex-*` being searched).
shopt -s nullglob
homes=("$HOME/.codex" "$HOME"/.codex-*)
shopt -u nullglob

jsonl=""
for home in "${homes[@]}"; do
  [[ -d "$home/sessions" ]] || continue
  match=$(find "$home/sessions" -type f -name "rollout-*-${threadId}.jsonl" 2>/dev/null | head -1)
  if [[ -n "$match" ]]; then
    jsonl="$match"
    break
  fi
done

if [[ -z "$jsonl" ]]; then
  echo "error: no rollout-*-${threadId}.jsonl found under any of: ${homes[*]/%//sessions}" >&2
  exit 2
fi

# Extract model + effort + cli_version. Model and effort are line-level greps;
# cli_version lives in the first line's payload JSON envelope.
model=$(grep -oE '"model":"[^"]*"' "$jsonl" | head -1 | sed 's/.*"model":"\([^"]*\)"/\1/')
effort=$(grep -oE '"effort":"[^"]*"' "$jsonl" | head -1 | sed 's/.*"effort":"\([^"]*\)"/\1/')
cli_version=$(head -1 "$jsonl" | python3 -c "import sys, json; d = json.loads(sys.stdin.read()); print(d.get('payload', {}).get('cli_version', ''))" 2>/dev/null || echo "")

if [[ -z "$model" || -z "$cli_version" ]]; then
  echo "error: JSONL $jsonl missing model or cli_version field" >&2
  exit 3
fi

# session_first_ts derived from filename: rollout-YYYY-MM-DDTHH-MM-SS-<threadId>.jsonl
# Convert dashes-in-time-component back to colons for ISO-8601.
fname=$(basename "$jsonl" .jsonl)
ts_part=$(echo "$fname" | sed -E 's/^rollout-([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}-[0-9]{2})-.*/\1/')
session_first_ts=$(echo "$ts_part" | sed -E 's/T([0-9]{2})-([0-9]{2})-([0-9]{2})/T\1:\2:\3Z/')

# Stable key=value output (do not reorder; downstream artifact templates may rely on order)
printf 'model=%s\n' "$model"
printf 'cli_version=%s\n' "$cli_version"
printf 'effort=%s\n' "${effort:-unknown}"
printf 'session_path=%s\n' "$jsonl"
printf 'session_first_ts=%s\n' "$session_first_ts"
