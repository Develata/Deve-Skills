#!/usr/bin/env bash
# Guard: block `dispatch_codex.sh` invocations that double-background.
#
# Failure mode this hook prevents:
#   - User dispatches codex via `bash scripts/dispatch_codex.sh ... &` (or nohup/disown)
#     together with run_in_background:true on the Bash tool call.
#   - Harness tracks the parent bash shell (which exits immediately after `&`).
#   - "completed (exit 0)" fires within seconds while the actual codex grandchild
#     keeps running for many minutes → task invisible in harness UI.
#
# Right pattern:
#   Bash(run_in_background=true, command='bash scripts/dispatch_codex.sh "$LOG" <stall_min> "$PROMPT" "$EXPECTED"')
# Wrong pattern:
#   Bash(run_in_background=true, command='bash scripts/dispatch_codex.sh ... &')
#   Bash(command='nohup bash scripts/dispatch_codex.sh ... > log 2>&1 &')
#   Bash(command='bash scripts/dispatch_codex.sh ... & disown')
#
# Override: append `# OVERRIDE_HOOK_<reason>` to the command (rare).
#
# Precision: this hook performs structural analysis to avoid false positives
# from commit messages, documentation, echo strings, etc. It only flags when
# dispatch_codex.sh appears as an EXECUTED token (not inside a quoted argument
# to git/echo/cat/printf/etc.).

INPUT=$(cat)

python3 - "$INPUT" <<'PY'
import json, re, shlex, sys

raw = sys.argv[1]
try:
    payload = json.loads(raw)
except Exception:
    sys.exit(0)

cmd = payload.get("tool_input", {}).get("command", "")
if not cmd:
    sys.exit(0)

# Override sentinel — operator-acknowledged.
if "OVERRIDE_HOOK" in cmd:
    sys.exit(0)

# Quick reject: token must literally appear.
if "dispatch_codex.sh" not in cmd:
    sys.exit(0)

# Tokenise into shell words; only flag if dispatch_codex.sh is an executed token
# (not embedded in a quoted argument to git/echo/cat/printf/etc.).
try:
    tokens = shlex.split(cmd, posix=True)
except ValueError:
    # If quoting is unbalanced (multi-line strings, heredoc fragments), fall back
    # to conservative regex check below.
    tokens = None

if tokens is not None:
    # Skip if this is a string-bearing command (commit message, echo, etc.)
    # where dispatch_codex.sh appears inside an argument string.
    string_command_prefixes = {
        "git", "echo", "printf", "cat", "less", "more", "grep", "sed", "awk",
        "head", "tail", "rg", "ack", "fgrep", "egrep", "wc",
    }
    if tokens and tokens[0] in string_command_prefixes:
        # dispatch_codex.sh appears as a substring of a quoted argument; not an
        # execution.  Re-check by scanning unquoted tokens for the exact filename.
        has_exec_token = any(t.endswith("dispatch_codex.sh") or t == "dispatch_codex.sh"
                             for t in tokens)
        if not has_exec_token:
            sys.exit(0)
        # Even if the token appears, it may be a path argument (e.g. `git add
        # scripts/dispatch_codex.sh`). Only flag if it is being executed: the
        # token is preceded by `bash`/`nohup`/`./` or appears as the first token.
        exec_pos = []
        for i, t in enumerate(tokens):
            if t.endswith("dispatch_codex.sh"):
                exec_pos.append(i)
        is_exec = False
        for pos in exec_pos:
            if pos == 0:
                is_exec = True; break
            prev = tokens[pos - 1]
            if prev in {"bash", "sh", "nohup"} or prev.endswith("/bash") or prev.endswith("/sh"):
                is_exec = True; break
            if tokens[pos].startswith("./") or tokens[pos].startswith("scripts/"):
                # path-style without bash prefix — check if string_command absorbed it
                # in this string_command branch, treat as argument not execution
                pass
        if not is_exec:
            sys.exit(0)

# At this point: dispatch_codex.sh is being EXECUTED. Scan for double-backgrounding.
violations = []

# Pattern 1: nohup ... dispatch_codex.sh
if re.search(r'nohup\s+(bash\s+)?(\./)?scripts/dispatch_codex\.sh', cmd):
    violations.append("nohup-prefix")

# Pattern 2: trailing `&` on the dispatch line.
# Split into segments (; or newline) and scan each that contains dispatch_codex.sh.
segments = re.split(r"[;\n]", cmd)
for seg in segments:
    if "dispatch_codex.sh" not in seg:
        continue
    # Only consider this segment as an execution if dispatch_codex.sh is preceded by
    # bash/nohup/sh or appears at start (after optional whitespace) without a
    # string-command prefix.
    seg_stripped = seg.strip()
    is_exec_segment = bool(
        re.match(r"^(nohup\s+)?(bash|sh)\s+(\./)?scripts/dispatch_codex\.sh", seg_stripped)
        or re.match(r"^(\./)?scripts/dispatch_codex\.sh", seg_stripped)
    )
    if not is_exec_segment:
        continue
    # Strip safe `&` uses: `&&`, `2>&1`, `>&2`, `1>&2`, `|&`
    s = seg
    s = re.sub(r"&&", " ", s)
    s = re.sub(r"\d?>&\d?", " ", s)
    s = re.sub(r"\|&", " ", s)
    if "&" in s:
        violations.append("trailing-ampersand")
        break

# Pattern 3: ; disown after dispatch
if re.search(r'dispatch_codex\.sh[^;\n]*;\s*disown', cmd):
    violations.append("disown")

if not violations:
    sys.exit(0)

reasons = ", ".join(sorted(set(violations)))
sys.stderr.write(f"""DENIED: dispatch_codex.sh double-backgrounding detected ({reasons}).

Cause: shell '&' / nohup / disown puts the wrapper into the job table, parent
       bash exits immediately, harness fires premature 'completed (exit 0)'
       while codex (grandchild) keeps running invisibly for minutes.

Fix:   drop the trailing '&' / 'nohup' / 'disown'. Use Bash tool with
       run_in_background:true instead — the harness tracks the wrapper
       directly and the dispatch_codex.sh watchdog already wait()s on codex.

Canonical: bash scripts/dispatch_codex.sh "$LOG" <stall_min> "$PROMPT" "$EXPECTED"
Override:  append '# OVERRIDE_HOOK_<reason>' to the command.

See: the codex-dispatch-watchdog skill notes
""")
sys.exit(2)
PY
