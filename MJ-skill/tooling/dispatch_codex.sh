#!/usr/bin/env bash
# dispatch_codex.sh — codex exec with stall-detection watchdog
#
# Why: codex exec can silently stall (stdin EOF block, network hang, etc).
# task tracker shows "running" but log file is frozen. Without a watchdog,
# this wastes hours before manual intervention.
#
# This wrapper:
#   - Forces stdin to /dev/null (defends against the known stdin EOF bug)
#   - Spawns a side watchdog that checks log size every 60s
#   - If log size is unchanged for STALL_MIN consecutive minutes, kill codex
#     and write a .stall marker file
#   - Returns codex's exit code, or 124 if killed by watchdog
#
# Usage:
#   bash scripts/dispatch_codex.sh <log_path> <stall_minutes> <prompt> [expected_output_path]
#
#   <log_path>           absolute path to log file (will be overwritten)
#   <stall_minutes>      watchdog tolerance — kill if log size unchanged for this many minutes (recommended 5-10)
#   <prompt>             the full PROMPT string to pass to codex exec
#   [expected_output_path]  OPTIONAL absolute path to the deliverable file codex is supposed to write
#                           (e.g., _CODEX_REPORT.md). If provided, after codex exits cleanly we check
#                           whether this file exists with size > 0. If NOT, append DISPATCH_STATUS=no_output
#                           to log and exit 125 — defends against "codex completed cleanly with exit 0
#                           but produced no deliverable" failure mode.
#
# Conventions:
#   - working directory: passed via `-C` defaults to current pwd at dispatch time
#   - sandbox: workspace-write
#   - model: gpt-5.5, reasoning: xhigh
#   - on stall: writes "${log_path%.log}.stall" with diagnostic detail
#   - on completion (with expected output present): appends DISPATCH_STATUS=completed (exit N) to log
#   - on completion (with expected output MISSING): appends DISPATCH_STATUS=no_output to log; exit 125
#   - on stall: appends DISPATCH_STATUS=stalled (killed by watchdog) to log; exit 124

set -u
set -o pipefail

# CWD robustness: cd to project root before doing anything else.
# Defends against caller's pwd having drifted into a subdir (a common source of
# `bash: scripts/dispatch_codex.sh: No such file or directory` exit-127 failures
# when relative paths in subsequent invocations don't resolve). The wrapper is
# always located at <REPO_ROOT>/scripts/dispatch_codex.sh, so we derive REPO_ROOT
# from this script's own location.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

LOG_PATH="${1:-}"
STALL_MIN="${2:-5}"
PROMPT="${3:-}"
EXPECTED_OUTPUT="${4:-}"

if [[ -z "$LOG_PATH" || -z "$PROMPT" ]]; then
  echo "usage: $0 <log_path> <stall_minutes> <prompt> [expected_output_path]" >&2
  exit 2
fi

if ! [[ "$STALL_MIN" =~ ^[0-9]+$ ]]; then
  echo "error: stall_minutes must be positive integer, got '$STALL_MIN'" >&2
  exit 2
fi

STALL_SEC=$(( STALL_MIN * 60 ))
STALL_MARKER="${LOG_PATH%.log}.stall"
CWD="$REPO_ROOT"

# --- Cowork BRIEF completeness gate (WARN-first) -----------------------------
# Moves a governance checklist from memory into the dispatch gate: if a cowork
# BRIEF lives in this dispatch's run dir, it MUST carry the two governance lines
# (DR check + DR ingest check) per docs/conventions/cowork_and_commits.md
# §DR-trigger / §DR-ingest. Missing => warn loudly to stderr (surfaces in the
# dispatch task output). WARN-only for now (dispatch still proceeds); escalate
# to block-with-override after a low-false-positive trial, per the
# forbidden_terms_guard escalation pattern. Override marker to silence on a
# legitimately brief-less dispatch: set COWORK_BRIEF_GATE_OK=1 in the env.
if [[ "${COWORK_BRIEF_GATE_OK:-0}" != "1" ]]; then
  _BRIEF="$(dirname "$LOG_PATH")/_BRIEF_FROM_CLAUDE.md"
  if [[ -f "$_BRIEF" ]]; then
    _missing=()
    # anchor to the BRIEF §0 heading syntax (`**DR check**:` / `**DR ingest check**:`)
    # so a body/prose mention of the strings does NOT count as present.
    grep -Eq '^\*\*DR check\*\*:' "$_BRIEF" || _missing+=("DR check")
    grep -Eq '^\*\*DR ingest check\*\*:' "$_BRIEF" || _missing+=("DR ingest check")
    if [[ ${#_missing[@]} -gt 0 ]]; then
      echo "⚠️  COWORK_BRIEF_GATE (warn-only): $_BRIEF is missing required governance line(s): ${_missing[*]}" >&2
      echo "    (per docs/conventions/cowork_and_commits.md §DR-trigger / §DR-ingest checks). Dispatch proceeds; add the line(s) before relying on this cowork. Set COWORK_BRIEF_GATE_OK=1 to silence for a legitimately brief-less dispatch." >&2
    fi
  fi
fi

# Reset state files
mkdir -p "$(dirname "$LOG_PATH")"
: > "$LOG_PATH"
rm -f "$STALL_MARKER"

# Launch codex in background; stdin from /dev/null (mandatory)
codex exec \
  --skip-git-repo-check \
  -s workspace-write \
  -m gpt-5.5 \
  -c approval_policy=never \
  -c model_reasoning_effort=xhigh \
  -C "$CWD" \
  "$PROMPT" \
  < /dev/null \
  >> "$LOG_PATH" 2>&1 &
CODEX_PID=$!

# Watchdog process
(
  LAST_SIZE=0
  TICKS_NO_GROWTH=0
  CHECK_INTERVAL=60
  STALL_TICKS=$(( STALL_SEC / CHECK_INTERVAL ))
  [[ "$STALL_TICKS" -lt 1 ]] && STALL_TICKS=1

  while kill -0 "$CODEX_PID" 2>/dev/null; do
    sleep "$CHECK_INTERVAL"
    CUR_SIZE=$(wc -c < "$LOG_PATH" 2>/dev/null | tr -d ' ' || echo 0)
    CUR_SIZE="${CUR_SIZE:-0}"
    if [[ "$CUR_SIZE" == "$LAST_SIZE" ]]; then
      TICKS_NO_GROWTH=$(( TICKS_NO_GROWTH + 1 ))
      if [[ "$TICKS_NO_GROWTH" -ge "$STALL_TICKS" ]]; then
        {
          echo "STALL_DETECTED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
          echo "STALL_LOG_SIZE_BYTES=$CUR_SIZE"
          echo "STALL_MINUTES_NO_GROWTH=$STALL_MIN"
          echo "STALL_CODEX_PID=$CODEX_PID"
          echo "STALL_LOG_PATH=$LOG_PATH"
          echo "STALL_LAST_LOG_LINE=$(tail -n1 "$LOG_PATH" 2>/dev/null || echo "<empty>")"
        } > "$STALL_MARKER"
        kill -9 "$CODEX_PID" 2>/dev/null
        # Also kill any child processes (codex spawns subprocesses)
        pkill -9 -P "$CODEX_PID" 2>/dev/null || true
        break
      fi
    else
      TICKS_NO_GROWTH=0
      LAST_SIZE="$CUR_SIZE"
    fi
  done
) &
WATCHDOG_PID=$!

# Wait for codex to finish (whether normally or via watchdog kill)
wait "$CODEX_PID" 2>/dev/null
CODEX_EXIT=$?

# Stop watchdog
kill "$WATCHDOG_PID" 2>/dev/null
wait "$WATCHDOG_PID" 2>/dev/null

# Final status line
if [[ -f "$STALL_MARKER" ]]; then
  {
    echo ""
    echo "=== DISPATCH_STATUS=stalled (killed by watchdog after ${STALL_MIN}min log inactivity) ==="
    cat "$STALL_MARKER"
  } >> "$LOG_PATH"
  exit 124
fi

# Layer 1.5: completed-but-no-output verification
# Defends against "codex exit 0 but produced no deliverable" failure mode.
# Only checks when caller passed an expected_output_path argument.
if [[ -n "$EXPECTED_OUTPUT" ]]; then
  if [[ ! -s "$EXPECTED_OUTPUT" ]]; then
    {
      echo ""
      echo "=== DISPATCH_STATUS=no_output (codex exit $CODEX_EXIT but expected deliverable not produced) ==="
      echo "EXPECTED_OUTPUT=$EXPECTED_OUTPUT"
      echo "EXPECTED_OUTPUT_EXISTS=$([[ -e "$EXPECTED_OUTPUT" ]] && echo yes || echo no)"
      echo "EXPECTED_OUTPUT_SIZE=$([[ -e "$EXPECTED_OUTPUT" ]] && wc -c < "$EXPECTED_OUTPUT" 2>/dev/null || echo 0)"
      echo "DIAGNOSIS=codex completed without writing deliverable; check log for off-target file path, refused-to-do-work pattern, or token-budget exhaustion"
    } >> "$LOG_PATH"
    exit 125
  fi
fi

echo "" >> "$LOG_PATH"
echo "=== DISPATCH_STATUS=completed (exit $CODEX_EXIT) ===" >> "$LOG_PATH"
exit "$CODEX_EXIT"
