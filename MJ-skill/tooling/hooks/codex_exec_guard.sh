#!/usr/bin/env bash
# PreToolUse:Bash hook — block raw 'codex exec' without dispatch_codex.sh wrapper.
#
# Why this hook exists (first-principles):
#   The dispatch_codex.sh wrapper provides three protections:
#     - stdin → /dev/null (defends against stdin EOF stall, a known codex CLI bug)
#     - 60s log-inactivity watchdog (kills wrapper on stall, writes .stall marker)
#     - DISPATCH_STATUS line on exit (cron probe terminal-state detection)
#   Raw `codex exec` bypasses all three. PID 70280 wasted 2h17min in stdin EOF
#   stall on 2026-05-15 because of raw exec.
#
# False-positive defense (2026-05-18 patch — sibling to codex_probe_guard.sh):
#   Literal "codex exec" appearing inside quoted message text (e.g.,
#   `git commit -m "moved from codex exec to wrapper"`) is NOT an invocation.
#   Hook strips single- and double-quoted regions before substring matching.
#   Known limitation: `bash -c "codex exec ..."` evades detection — extremely
#   rare; use OVERRIDE if intentional.
#
# Override: append `# OVERRIDE_HOOK_<reason>` to Bash command (rare cases only).

set -u

INPUT=$(cat)
RAW_CMD=$(echo "$INPUT" | python3 -c 'import json,sys; d=json.load(sys.stdin).get("tool_input",{}); print(d.get("command",""))' 2>/dev/null)

# Strip single- and double-quoted regions (multi-line aware via re.DOTALL).
CMD=$(printf '%s' "$RAW_CMD" | python3 -c '
import sys, re
cmd = sys.stdin.read()
cmd = re.sub(r"\x27[^\x27]*\x27", "", cmd, flags=re.DOTALL)
cmd = re.sub(r"\"[^\"]*\"",       "", cmd, flags=re.DOTALL)
sys.stdout.write(cmd)
' 2>/dev/null)

# OVERRIDE check on stripped CMD (consistency with codex_probe_guard.sh).
if echo "$CMD" | grep -q 'OVERRIDE_HOOK'; then
  exit 0
fi

# Match `codex exec` as actual command position: start-of-line OR non-alnum-non-slash
# boundary char, then `codex`, then whitespace, then `exec`.
if ! echo "$CMD" | grep -qE '(^|[^/[:alnum:]])codex[[:space:]]+exec'; then
  exit 0
fi

# Escape via wrapper: if dispatch_codex.sh also present in stripped CMD, the
# codex exec is INSIDE the wrapper (legitimate path). Pass.
if echo "$CMD" | grep -q 'dispatch_codex.sh'; then
  exit 0
fi

cat >&2 <<EOF
DENIED: raw 'codex exec' bypasses scripts/dispatch_codex.sh watchdog wrapper.

The wrapper provides:
  - stdin -> /dev/null (defends against stdin EOF stall — codex CLI bug)
  - 60s log-inactivity watchdog (writes .stall marker on stall)
  - DISPATCH_STATUS line on exit (cron probe terminal-state detection)

See ~/.claude/skills/codex-dispatch-watchdog/SKILL.md for the 3-layer defense
(prevented 2h17min stall like PID 70280 on 2026-05-15).

Use:  bash scripts/dispatch_codex.sh <log_path> <stall_min> "\$(cat /tmp/prompt.txt)"
  or: CODEX_HOME=~/.codex-b bash scripts/dispatch_codex.sh ...

Override: append '# OVERRIDE_HOOK_<reason>' to command (rare cases only).
EOF
exit 2
