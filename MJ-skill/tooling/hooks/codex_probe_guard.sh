#!/usr/bin/env bash
# PreToolUse:Bash hook — enforce active CronCreate probe before dispatch_codex.sh
#
# Why this hook exists (first-principles):
#   The dispatch_codex.sh wrapper has an internal watchdog (kills on log silence).
#   But the wrapper itself can be killed externally (SessionStart hook, OOM, etc).
#   When the wrapper dies, no .stall marker is written, no DISPATCH_STATUS line is
#   appended, and the dispatch is in zombie state for hours.
#
#   The ONLY reliable defense is an external observer outside the dispatch's
#   bash process lineage. CronCreate `*/3 * * * *` probe is that observer — it
#   lives in Claude's session, polls logs/markers, and detects stall regardless
#   of what kills the wrapper.
#
#   Manual cron setup is unreliable (Claude forgets). This hook enforces it.
#
# False-positive defense (2026-05-18 patch):
#   The literal string "dispatch_codex.sh" appearing inside quoted message text
#   (e.g., `git commit -m "fix dispatch_codex.sh"`) is NOT an invocation.
#   The hook strips single- and double-quoted regions before substring matching.
#   Known limitation: `bash -c "dispatch_codex.sh ..."` and `eval`-wrapped
#   invocations evade detection — extremely rare in this project; documented
#   but not handled. If you actually need to invoke via bash -c, add OVERRIDE.
#
# Mechanism:
#   - Sentinel file: `.claude/codex_probe_heartbeat` (gitignored)
#   - Cron probe must `touch $SENTINEL` on every tick → proves probe is alive
#   - This hook checks sentinel exists AND mtime < 270s before allowing dispatch_codex.sh
#     (270s = 1.5× cron period 180s, accommodates `*/3 * * * *` cron + ~10% scheduler jitter)
#   - If sentinel missing or stale → BLOCK with setup instructions
#
# Override: append `# OVERRIDE_HOOK_<reason>` to Bash command (rare cases only).
#
# Hook never blocks on non-dispatch commands. Read-only ops on the wrapper file
# (tail/cat/grep/git/etc) also pass through unblocked.

set -u

INPUT=$(cat)
RAW_CMD=$(echo "$INPUT" | python3 -c 'import json,sys; d=json.load(sys.stdin).get("tool_input",{}); print(d.get("command",""))' 2>/dev/null)

# Strip single- and double-quoted regions (multi-line aware via re.DOTALL).
# After this, `git commit -m "...dispatch_codex.sh..."` no longer contains the
# substring; `bash scripts/dispatch_codex.sh "$(cat prompt.txt)"` still does
# (the wrapper invocation is outside the quoted region).
CMD=$(printf '%s' "$RAW_CMD" | python3 -c '
import sys, re
cmd = sys.stdin.read()
cmd = re.sub(r"\x27[^\x27]*\x27", "", cmd, flags=re.DOTALL)
cmd = re.sub(r"\"[^\"]*\"",       "", cmd, flags=re.DOTALL)
sys.stdout.write(cmd)
' 2>/dev/null)

# OVERRIDE marker check (on stripped CMD — OVERRIDE inside a quoted string is
# a message mention, not an actual override directive).
if echo "$CMD" | grep -q 'OVERRIDE_HOOK'; then
  exit 0
fi

# No dispatch invocation outside quotes → pass.
if ! echo "$CMD" | grep -q 'dispatch_codex.sh'; then
  exit 0
fi

# Read-only / inspection ops on the wrapper file itself (not invocation) → pass.
# After strip, command-leading position is identifiable via start-of-line or
# shell separator.
if echo "$CMD" | grep -qE '(^|;|&&|\|\|)[[:space:]]*(tail|cat|head|grep|less|ls|chmod|wc|diff|find|git|stat|file|sed|awk|man|which|cp|mv|touch|vim|nano)[[:space:]]'; then
  exit 0
fi

# At this point: dispatch_codex.sh appears outside quoted regions AND it's not
# a read-only inspection. Treat as actual dispatch invocation — enforce probe.

SENTINEL=".claude/codex_probe_heartbeat"

if [[ ! -f "$SENTINEL" ]]; then
  cat >&2 <<EOF
DENIED: codex dispatch requires active CronCreate probe with sentinel.
Sentinel file '$SENTINEL' does not exist.

REQUIRED before this dispatch:
  1. Create recurring CronCreate cron='*/3 * * * *' (every 3 minutes; updated 2026-05-19 from every minute)
  2. Probe prompt MUST include: \`touch $SENTINEL\` on every tick (proves probe alive)
  3. Touch sentinel ONCE manually now: \`touch $SENTINEL\`

Per ~/.claude/skills/codex-dispatch-watchdog/SKILL.md §Scope: probe is MANDATORY
external observer for ANY wrapper invocation (no time threshold; stdin-EOF stall
observed at <60s — PID 70280 2026-05-15). Wrapper internal watchdog cannot help
if wrapper itself is killed (2026-05-17 E1 v2 stall: dispatch_codex.sh parent
killed externally, no .stall marker, no DISPATCH_STATUS).

Override: append '# OVERRIDE_HOOK_<reason>' to command (rare cases only).
EOF
  exit 2
fi

NOW=$(date +%s)
MTIME=$(stat -f %m "$SENTINEL" 2>/dev/null || stat -c %Y "$SENTINEL" 2>/dev/null)
AGE=$(( NOW - MTIME ))

if [[ "$AGE" -gt 270 ]]; then
  cat >&2 <<EOF
DENIED: codex dispatch probe sentinel is stale (${AGE}s old, > 270s threshold).
Sentinel: $SENTINEL

CronCreate probe is not running (cron jobs lost on session restart, or probe
was deleted/expired). Without an active probe, codex dispatch has no external
observer for silent-stall detection.

REQUIRED: Recreate CronCreate probe (cron='*/3 * * * *') with \`touch $SENTINEL\`
in its prompt, then re-attempt dispatch.

Override: append '# OVERRIDE_HOOK_<reason>' to command (rare cases only).
EOF
  exit 2
fi

exit 0
