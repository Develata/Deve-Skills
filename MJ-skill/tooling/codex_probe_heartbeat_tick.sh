#!/usr/bin/env bash
# codex probe heartbeat tick — touch sentinel if codex dispatch active, else
# increment idle counter. Prints "EXPIRE" on stdout when idle_count >= 2 so the
# caller (cron prompt) can CronDelete the heartbeat job.
#
# Trigger semantic: a dispatch is "active" if any
# outputs/reports/cowork_*/run_*/_dispatch_log.txt was modified in the last 6
# minutes (= 2 cron ticks at */3 * * * *, slightly wider than tick jitter).
#
# Source-of-truth for rule: memory feedback_codex_heartbeat_two_idle_expire.md
# Created 2026-05-27 after user flagged the rule had been mentioned twice and
# not applied. Do not remove or weaken without updating the memory file.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SENTINEL=".claude/codex_probe_heartbeat"
COUNTER=".claude/codex_probe_idle_counter"
ACTIVE_WINDOW_MIN=6

mkdir -p "$(dirname "$SENTINEL")"

active=$(find . \
    -maxdepth 5 \
    -path "./outputs/reports/cowork_*/run_*/_dispatch_log.txt" \
    -mmin -${ACTIVE_WINDOW_MIN} \
    2>/dev/null | head -1)

if [ -n "${active:-}" ]; then
    touch "$SENTINEL"
    echo 0 > "$COUNTER"
    echo "ACTIVE"
    exit 0
fi

cnt=$(cat "$COUNTER" 2>/dev/null || echo 0)
cnt=$((cnt + 1))
echo "$cnt" > "$COUNTER"

if [ "$cnt" -ge 2 ]; then
    echo "EXPIRE"
else
    echo "IDLE-${cnt}"
fi
