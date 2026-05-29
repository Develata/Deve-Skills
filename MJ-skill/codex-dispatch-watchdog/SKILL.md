---
name: codex-dispatch-watchdog
description: Use for ANY codex CLI dispatch via dispatch wrapper (no time threshold; presence-of-risk triggers, not estimated wall — stdin-EOF stalls occur at <60s). Combines internal log-inactivity watchdog wrapper + external Claude-session cron probe + sentinel hook enforcement. Detects stalls in ≤60-270s vs hours-without-detection failure mode.
---

# Codex CLI silent-stall defense

## Scope (when to invoke)

**Triggers** — set up probe for any of:

- Any invocation of `dispatch_codex.sh` (project wrapper) — **regardless of expected wall time**
- Any direct `codex exec` with expected wall >2 min (rare — prefer wrapper)

**Does NOT trigger**:

- Inline `codex exec "<short prompt>"` whose stdout returns in seconds — stall is immediately visible
- `codex exec resume <session-id>` for short queries (inline visibility)

**Why no time threshold for wrapper**: stdin-EOF silent-stall has occurred at <60s wall (PID 70280 2026-05-15 initial freeze). Time-based filtering misses these; presence-of-risk is the only safe trigger. Cost: probe = 1 cron tick / 3 min for dispatch duration ≈ trivial vs cost of an undetected stall (updated 2026-05-19; was 1/min before).

## Why this skill exists

`codex exec` can fail invisibly in multiple ways — process alive but log frozen, or process exits cleanly but produces no deliverable. Single-mechanism defenses fail:

| Defense | Failure mode |
|---|---|
| `task-notification` only | Fires on process exit only; silent-stall never exits |
| Log inactivity watchdog inside dispatch wrapper | Wrapper itself can be killed externally (SessionStart hook re-fire, OOM, `kill -9` of parent) — no marker written |
| Single ScheduleWakeup probe | One-shot; cascade depends on Claude correctly re-arming each fire (failed multiple times in practice 2026-05-16/17) |
| Exit-code-based success check | codex CAN exit 0 with no deliverable produced (acknowledges task, runs reasoning, exits cleanly without writing the expected output file) — wrapper sees exit 0 + no stall → reports "completed" → Claude believes failure didn't happen until they check artifact path |

**Defense in depth required**: (1) wrapper-internal watchdog + (1.5) deliverable-existence check + (2) Claude-session-external cron probe + (3) PreToolUse hook enforcing probe presence before dispatch + (4) **Claude post-completion re-verification protocol**.

Historical baseline: 2026-05-15 PID 70280 wasted 2h17min in stdin EOF silent-stall before user-led discovery. 2026-05-17 E1 v2 wrapper externally killed → no `.stall` marker → 1h 50min undetected. 2026-05-19 #52+#53 cowork: codex completed successfully but Claude checked artifact paths 3s after dispatch start (before codex started exec calls) and treated the early snapshot as final → wrote a "codex no-show" report based on stale data; the actual codex report was written ~5 min later. Root cause: Claude treated pre-completion snapshot as truth instead of treating the wrapper completion notification as the trigger to re-verify.

## The 3-layer defense

### Layer 1 — Dispatch wrapper (internal watchdog)

`scripts/dispatch_codex.sh <log_path> <stall_min> <prompt> [expected_output_path]` (project-specific implementation). Contract:

- stdin → `/dev/null` (defends against stdin-EOF stall — known codex bug)
- Spawn watchdog process checking log size every 60s
- If log size unchanged for `stall_min` minutes → `kill -9` codex + write `<log_path>.stall` marker
- Append `DISPATCH_STATUS=completed (exit N)` OR `DISPATCH_STATUS=stalled` to log
- Exit: codex's exit code, 124 if killed by watchdog, 125 if Layer 1.5 deliverable check fails

Why insufficient alone: (a) external kill of the wrapper process leaves no markers; (b) codex can exit 0 with no deliverable written (next layer).

### Layer 1.5 — Deliverable-existence check (post-exit verification)

**ADDED 2026-05-19** after #52+#53 cowork failure-mode discovery.

When the caller passes the optional `expected_output_path` argument to the wrapper, after codex exits cleanly the wrapper checks whether the deliverable file exists with size > 0. If NOT:

- Append `DISPATCH_STATUS=no_output (codex exit N but expected deliverable not produced)` to log
- Append diagnostic block (`EXPECTED_OUTPUT_EXISTS`, `EXPECTED_OUTPUT_SIZE`, `DIAGNOSIS=...`)
- Exit 125 (distinguishable from stall=124 and codex exit code)

**MANDATORY when caller knows the expected output path** — almost always true for cowork dispatches following a brief that specifies an output file.

Why: codex can complete reasoning, output acknowledgment + analysis to STDOUT (which goes to log), but never invoke `write_file` for the deliverable — particularly when the prompt asks codex to "write report" but codex interprets it as "describe the report". Exit-code-based success looks healthy in this scenario; deliverable-existence check catches it.

### Layer 2 — Cron probe (external observer, Claude-session)

**MANDATORY for every wrapper dispatch** — no time threshold (see Scope/§"Why no time threshold": stdin-EOF stalls occur at <60s, so wall-time gating is unsafe). Run AT SAME TURN as `dispatch_codex.sh` invocation:

```
CronCreate(
  cron="*/3 * * * *",       # every 3 minutes (was * * * * * pre-2026-05-19)
  recurring=true,
  durable=false,            # session-only OK; cron survives Claude turns
  prompt=<probe instructions below>
)
```

**Why CronCreate not ScheduleWakeup** (first-principles): ScheduleWakeup is one-shot — cascade continuation depends on Claude manually re-arming each fire, an AND-chain failure mode (any miss breaks the cascade; observed multiple times). Cron fires deterministically every tick without Claude state.

**Why 3-min cadence (updated 2026-05-19; was 60s before)**: 60s cadence produces excessive REPL noise during long codex tasks (30+ fires for a 30-min dispatch, each forcing context refresh). 3-min cadence ~10 fires/30-min still well within 5-min Anthropic prompt cache TTL. Wrapper Layer 1 watchdog (60s log-silence kill) provides faster intra-dispatch stall detection independently; cron probe is the orthogonal external observer for wrapper-death case, where 3-min detection latency is acceptable. Threshold pair: cron `*/3` + hook 270s = 1.5× cron with ~10% scheduler jitter margin.

**Probe prompt contents** (each tick):

1. (FIRST) `touch <sentinel_file>` — proves probe alive (required by Layer 3 hook)
2. Read-only status check:
   - `tail -3 <log_file>` — latest activity
   - `grep DISPATCH_STATUS <log_file>` — completion line
   - `ls <expected_artifact_path>` — has deliverable landed
   - `ls <log_basename>.stall` — watchdog kill marker
   - `NOW=$(date +%s); MTIME=$(stat -f %m <log>); echo log_age_seconds=$((NOW-MTIME))` — silent-stall detection
3. Decision rule (UPDATED 2026-05-24 — 2-tick grace self-delete; supersedes 2026-05-18 idempotent-fire pattern):
   - Maintain a per-probe counter file: `COUNTER=.claude/codex_probe_terminal_count_<tag>`
   - `.stall` exists OR `DISPATCH_STATUS=` present OR artifact landed → **TERMINAL**:
     - If `$COUNTER` does NOT exist → write `1` to `$COUNTER`; report `[<task>] TERMINAL DETECTED (tick 1/2 — grace; will self-delete on next fire if still terminal). Claude should advance now.`
     - If `$COUNTER` exists → report `[<task>] TERMINAL DETECTED (tick 2/2 — self-deleting now)`, then `CronDelete <own_id>` and `rm $COUNTER`
   - `log_age > 5 * 60s` → **STALL** → same 2-tick grace pattern using the same counter file
   - Otherwise → 1-line `PROBE_OK: ...`; if `$COUNTER` exists (state recovered, no longer terminal) → `rm $COUNTER` to reset
   - Why 2-tick grace: 2026-05-18 E2 R0 silent-stuck showed fire-then-delete is single-point-of-failure when the terminal fire's message is lost in transit. 2-tick guarantees ≥2 fires (≥3 min apart) before deletion — second fire re-delivers if first was lost, so Claude has a redundant receipt path before the probe disappears.

### Layer 3 — Sentinel + PreToolUse hook (enforce probe presence)

PreToolUse hook on `Bash` matcher, regex matches `dispatch_codex.sh`:

- Check `<sentinel_file>` exists AND mtime within threshold (~1.5× cron interval; e.g. 270s for `*/3` cron — matches project hook 2026-05-19)
- If sentinel missing or stale → BLOCK with message "create CronCreate probe FIRST + touch sentinel"
- If override marker (`# OVERRIDE_HOOK_<reason>`) present in command → allow (rare cases; auto-mode classifier may block bypass without user authorization)

Implementation: project supplies hook script (e.g., `scripts/hooks/codex_probe_guard.sh`) reading sentinel mtime.

## Lifecycle

```
T=0       create cron probe (Layer 2) + touch sentinel
T=+ε      dispatch via wrapper (Layer 1; Layer 3 hook validates Layer 2 alive)
T=~3min   first cron fire — touch sentinel + status check
T=~6min   second cron fire — same
...
T=N min   codex completes / stalls / errors
          → probe detects DISPATCH_STATUS / .stall marker / log silence > threshold
          → Fire 1 (tick 1/2): writes counter file, reports "TERMINAL DETECTED (tick 1/2 — grace)"
          → Fire 2 (≥3 min later, tick 2/2): re-reports terminal, then self-CronDelete + rm counter
          → Claude (on any wake): step-0 full state sweep, advance state machine.
            Claude MAY also CronDelete explicitly any time after tick 1 (faster cleanup);
            redundant-delete is safe (CronDelete is idempotent for already-gone IDs).
```

## Multi-dispatch & autonomous-mode handling

### Unique-tag naming

Each dispatch gets its own cron probe with a unique tag — recommended format:
`codex_probe_<short_task>_<utc_yyyymmddThhmmZ>` (e.g., `codex_probe_e1_r2_brief_20260518T143022Z`).

Why: `CronList` can disambiguate parallel probes; the timestamp identifies orphan probes during GC.

### Concurrent dispatch

Parallel dispatches each get their own probe (per unique tag). Multi-account (`CODEX_HOME=~/.codex-b`) uses the same pattern — one probe per dispatch regardless of account.

Soft cap: **≤4 concurrent probes per Claude session**. >4 → serialize (per `codex-orchestration` § 3 Parallel dispatch threshold — user permission UI floods at ≥3 parallel codex jobs anyway).

### Terminal-state lifecycle (UPDATED 2026-05-24 — 2-tick grace self-delete)

**Evolution**:
1. v1 (pre-2026-05-18): probe self-`CronDelete`d on first terminal detect → 2026-05-18 E2 R0 silent-stuck (fire-then-delete is single-point-of-failure; terminal message lost in transit, probe gone, chain stuck)
2. v2 (2026-05-18 → 2026-05-24): probe never self-deletes; Claude must `CronDelete` after advance → reliable but Claude often forgot, leaving probes firing forever (orphan accumulation, REPL noise)
3. **v3 (current, 2026-05-24): 2-tick grace self-delete** — probe writes a counter file on first terminal fire (tick 1/2: report + grace), self-deletes on second terminal fire (tick 2/2: report + `CronDelete` + `rm counter`). Guarantees ≥2 terminal fires (≥3 min apart) before deletion: the redundant fire path eliminates the v1 single-point failure while restoring auto-cleanup.

**Why this satisfies both constraints**:
- v1 failure was "single fire, lost in transit, deleted" → v3 fires twice before delete, so the second is a redundant receipt path
- v2 failure was "no auto-cleanup, Claude forgets" → v3 deletes within ≤6 min of terminal without requiring Claude action
- Claude MAY still `CronDelete` explicitly any time after tick 1 (faster cleanup); redundant delete is safe

**Counter file convention**: `.claude/codex_probe_terminal_count_<tag>` (gitignored; same `<tag>` as the probe's unique-tag naming). On non-terminal tick where counter exists (i.e., state flipped back to healthy — should not happen in practice, but defensive), probe `rm`s the counter to reset.

Accumulation defense is now: 2-tick auto-delete (primary) + orphan-probe GC (§next, secondary safety net for v3 counter-file corruption / probe killed mid-cycle).

### Orphan-probe garbage collection (autonomous mode)

In multi-hour autonomous mode where Claude session may compact / restart / lose track:

- **Every 30 min (or at every major task boundary)**, inline check: `CronList` → for each `codex_probe_*` entry, verify the dispatch is still active (check sentinel file mtime + corresponding log file)
- If sentinel mtime > 5 min AND log shows `DISPATCH_STATUS=` line OR `.stall` marker → probe is orphaned → `CronDelete`
- If `CronList` shows no `codex_probe_*` entries but a dispatch is ongoing (log file growing) → probe failed to spawn → STOP and re-create probe before any further dispatch

### Autonomous-mode probe budget

Each running probe = 1 cron tick / 3 min ≈ trivial cost (was 1/min pre-2026-05-19; reduced for less REPL noise). With ≤4 concurrent + per-dispatch 30-60 min lifetime, no quota concern for a 20h autonomous session. The concern is **orphan accumulation, not active count**.

## Layer 4 — Claude post-completion re-verification protocol

**ADDED 2026-05-19** after Claude-side procedural error in #52+#53 cowork: Claude checked artifact paths 3s after dispatch start (before codex started exec calls), saw only the brief file + 1700-byte log with just "I'll read the brief first...", concluded "codex no-show", and wrote a fallback report. Codex actually completed correctly 5 minutes later; the early snapshot was misleading.

**The rule** (binding when dispatching codex via wrapper):

1. **`run_in_background:true` + sleep 3 snapshots are NEVER ground truth.** Pre-completion snapshots can show: (a) just the brief file, (b) log with only acknowledgment line, (c) no deliverable yet. These are normal mid-dispatch states.
2. **Source of truth = the explicit wrapper completion notification** ("Background command [...] completed (exit code N)").
3. **After receiving the completion notification**, Claude MUST:
   - Grep the log for `DISPATCH_STATUS=...` (completed / stalled / no_output)
   - List the run dir to check if the expected deliverable exists
   - Read the deliverable if it exists, before forming any judgment
4. **Never** write a fallback "codex failed" report based on a pre-completion snapshot.

The mistake pattern to avoid:

```
dispatch (run_in_background:true)
→ sleep 3
→ ls $RUN_DIR/ → only brief + 1700-byte log
→ CONCLUSION (premature): codex no-show
→ write _CLAUDE_REPORT.md saying "codex failed"
→ commit
→ ... 5 min later: completion notification arrives, codex actually completed
   correctly — but Claude has already moved past
```

Right pattern:

```
dispatch (run_in_background:true)
→ keep working on parallel tasks (Claude's own analysis, etc.)
→ wait for explicit completion notification
→ THEN re-check the run dir for deliverable
→ form judgment based on artifact + log DISPATCH_STATUS, not premature snapshot
```

If a partial-progress snapshot is needed, it should be informational only, with explicit "this is mid-dispatch, not conclusive" framing in any user-facing report.

## Anti-patterns

- Any wrapper dispatch without a cron probe → silent stall undetected for hours (stdin-EOF stalls hit at <60s; wall-time gating misses them — see Scope)
- ScheduleWakeup cascade for monitoring (Claude forgets to re-arm)
- Probe prompt that DOESN'T touch sentinel → Layer 3 hook blocks NEXT dispatch
- Claude skipping `CronDelete` after advance → under v3 the probe self-cleans on the 2nd terminal tick, so explicit `CronDelete` after advance is just faster cleanup (tidier, not required)
- Probe self-`CronDelete`s on the FIRST terminal tick (deprecated v1 pattern, 2026-05-18 — the single fire's message can be lost in transit → silent-stuck); v3 self-deletes only on the SECOND terminal tick, after a grace re-report
- Use `tail -f log | grep -m 1` thinking it'll exit on completion (it won't — log goes quiet, pipe hangs)
- **Claude concluding "codex failed" from a pre-completion snapshot** (added 2026-05-19 — concrete incident: #52+#53 cowork's _CLAUDE_REPORT.md was written claiming "codex no-show" while codex was still running normally; the actual codex report landed 4 minutes after the snapshot). Always wait for explicit wrapper completion notification before forming a verdict.
- Calling the wrapper WITHOUT `expected_output_path` for cowork briefs that specify an output file — gives up Layer 1.5 protection for no good reason.

## Cross-reference

- `codex-orchestration` § 3 Call Efficiency Rules — dispatch invocation basics
- `codex-account-switching` — multi-account isolation
- `autonomous-chain-control-flow` — wake-signal *semantic* handling in autonomous chains (this skill = probe *mechanics*; that one = how Claude reacts to a probe fire)
- `loop` skill — alternative for recurring tasks (NOT a substitute; codex dispatch monitoring needs cron probe pattern specifically)
- Project's concrete script/hook paths documented in project `CLAUDE.md`
