---
name: autonomous-chain-control-flow
description: Wake-signal handling in user-authorized autonomous chains (arc plan / long-running /loop / multi-round research arc). Encodes two principles — (1) "wake signal = advance trigger, NOT inbound notification": any signal that lifts Claude out of idle (cron probe tick, background task completion notification, ScheduleWakeup fire, mid-chain user message) is a state-machine advance trigger; (2) "wake-source paths are independently failable + silent-stuck is a real risk": on any wake, Claude executes step 0 full chain-state sweep BEFORE reacting to the wake's literal content, because the wake that just arrived may not be the only newly-terminal event. Probe mechanics and terminal lifecycle are delegated to `codex-dispatch-watchdog` (current: v3 2-tick grace self-delete); this skill handles wake-signal semantics + the step-0 sweep/advance behavior. Counter-mode for ordinary request-response. Use whenever an autonomous chain is active (plan committed by user + L2-equivalent "no pause between rounds" authorization) and you observe a wake signal. Composes with `codex-dispatch-watchdog` (probe is one physical wake-signal carrier) and `research-round-lifecycle` (chain state = round state machine).
---

# Autonomous Chain Control Flow — Wake-Signal Handling

## The principle (1 paragraph)

In an **autonomous chain** (user-authorized multi-step task that proceeds without per-step approval — arc plan / long /loop / multi-round research), Claude's execution model is an **event loop + state machine**, not request-response. Any signal that wakes Claude from idle — `task-notification` (background bash done), cron probe tick (CronCreate fire-as-input), `ScheduleWakeup` fire, mid-chain user message — is a **state-machine advance trigger**, NOT an inbound message to merely acknowledge. **Wake-source paths are independently failable** (each has known failure modes — see §Wake-source independence below), so on any wake, Claude's first action MUST be: (0) **full chain-state sweep** (don't trust the current wake to be exhaustive), (1) read state implications, (2) find next executable transition, (3) execute until next true yield point (= external dispatch / wait-on-external / user-checkpoint).

## When to use

- Arc plan or long-running task is active AND user gave "no pause between rounds" authorization
- A `<task-notification>` arrives mid-chain (background bash completion)
- A cron probe tick fires as a user-message-shaped input
- `ScheduleWakeup` fires
- User sends a mid-chain message that is NOT a redirect (continuation prompts like "autonomous" / "继续" / "下一步")

## When NOT to use

- Single-turn user query with no chain context (ordinary request-response)
- User explicitly redirects ("stop", "pause", "do X instead") — that's a new directive, not a wake-on-state
- No chain state exists yet (first message of conversation)

## The 4-step wake handler (mandatory order)

On any wake signal in autonomous chain context:

```
0. FULL STATE SWEEP — do NOT trust the current wake to be exhaustive. Independent of
                      what the wake signal says, scan ALL in-flight chain state:
                        - all in-flight background tasks: read their log tail + grep DISPATCH_STATUS
                        - all active CronList probes: check each probe's sentinel + corresponding log
                        - all expected output artifacts: ls -la the run dir for new files
                        - TodoWrite: which task is in_progress?
                      If sweep reveals a TERMINAL state the current wake didn't mention
                      (e.g., a different background task also completed silently), include
                      that transition in steps 1-3.

1. READ STATE IMPLICATIONS — given the sweep findings, what round / stage was I in?
                              What was the last yield point waiting for? Which TERMINAL
                              states are newly visible?

2. FIND TRANSITION(S) — given current state + ALL newly-terminal items (not just the
                        wake source), what is/are the next executable transition(s)?
                        Examples:
                          - "background task completed" + sweep finds OTHER task also done → handle both
                          - "probe tick: codex DISPATCH_STATUS=completed" → CronDelete probe + read artifact + advance
                          - "ScheduleWakeup fire" → continue from where the loop left off + sweep for any other state change
                          - "user mid-chain 'continue'" → sweep, then resume next pending todo (likely covering items the user is implicitly flagging by saying "continue")

3. EXECUTE TO NEXT YIELD — run all transitions until reaching a true yield (= external
                           codex dispatch in flight, wait-on-user-input, waiting for
                           human review). Do NOT stop early. Do NOT report
                           "ready to advance" and wait.
```

**Step 0 is the silent-stuck defense.** If a wake source fails (probe message lost / task-notification suppressed / etc.), the sweep at the NEXT wake (from any other source — including a user message) catches the missed terminal. Without step 0, a lost wake = permanently lost chain advance.

## Wake-signal taxonomy

| Signal type | Source | Wake semantics |
|---|---|---|
| Background-task completion | `<task-notification>` from `run_in_background:true` Bash | dispatch finished → check artifact + advance |
| Cron probe tick | CronCreate `recurring=true` fires as user-shaped input | check sentinel + dispatch status + advance or report progress |
| ScheduleWakeup fire | Self-scheduled (rare in arc plans, common in `/loop`) | continue the loop logic |
| Mid-chain user message | User types during autonomous chain | check if redirect (new directive) or continuation (advance) |

All four collapse to the same handler: sweep → read state → find transition → execute.

## Wake-source independence (defense against silent-stuck)

Each wake source has independent failure modes; no single source is reliable enough alone:

| Source | Known failure mode |
|---|---|
| `<task-notification>` | Codex CLI internal errors (e.g., `record rollout items: thread not found`) can suppress harness's notification dispatch even when child process exits 0 cleanly. Observed 2026-05-18 E2 R0. |
| Cron probe tick | Fire-then-input mechanism can lose messages: probe fires + `CronDelete`s itself on terminal detect, but the fire's user-message payload doesn't always reach Claude's input stream (race / queue / harness state). Observed 2026-05-18 E2 R0 (`c23ca85e` self-deleted but no PROBE_TICK message ever landed). |
| `ScheduleWakeup` | Only fires when scheduled; if author forgot to schedule it as a backup, no fallback exists. |
| Mid-chain user message | Requires the human to notice silence — defeats autonomous-chain purpose. |

**Architectural conclusion**: Redundancy across sources, plus Step 0 full-state sweep on any wake (including user messages), is the only robust handler. Belt + suspenders, not pick-one.

**Operational defense per dispatch**:
- Set up the probe per `codex-dispatch-watchdog` — current lifecycle: v3 2-tick grace self-delete.
- Run dispatch in background (`<task-notification>` is the primary path).
- If chain-level halt markers are used, include them as additive terminal predicates while preserving the watchdog lifecycle.
- Optionally add a `ScheduleWakeup` at estimated-dispatch-time + 5 min as a last-resort backup for dispatches >10 min wall.

## Probe lifecycle — source of truth

Probe terminal detection, prompt template, sentinel touch, counter file, and self-delete lifecycle live in `codex-dispatch-watchdog` § "Layer 2 — Cron probe" and § "Terminal-state lifecycle". Current lifecycle at this review: **v3 2-tick grace self-delete** (probe re-reports terminal on tick 1, self-deletes on tick 2).

This skill adds only the *semantic* rule: any probe fire is a wake signal. On a terminal probe fire, run the 4-step wake handler starting with step-0 full state sweep, then advance the chain. Claude MAY explicitly `CronDelete` after acting for faster cleanup; otherwise the watchdog v3 lifecycle self-deletes on the second terminal tick.

If an autonomous chain adds extra terminal predicates (e.g. a `HALT` marker), treat them as additive status checks inside the watchdog pattern, not as a separate probe lifecycle.

## Naming hygiene (cosmetic but important)

Avoid wake-signal names that imply "passive notification" (`PROBE_TICK`, `notification`, `update`). Prefer **active-voice** naming (`CHAIN_TICK`, `RESUME_TRIGGER`, `ADVANCE_SIGNAL`) — this is the linguistics fix that makes the principle harder to forget.

If you author probe prompts, end the terminal-report line with a verb command, not a status noun:

| ❌ "next: Stage 4 convergence" | ✅ "advance to Stage 4 NOW (wake = advance trigger)" |
|---|---|

## Failure mode reference

### Incident 1 (2026-05-18 E1 R0): wake-as-notification confusion

Observed failure: probe `0f71a526` fired with content `PROBE_TICK ... DISPATCH_STATUS=completed`. Claude:
1. Read the message
2. CronDelete'd the probe (which the prior pattern said to do)
3. Reported "[E1 R0 codex lit] COMPLETE; next: Stage 4 convergence"
4. **Stopped, waiting for "next main-session activation"**

User correction: "为什么没走autonomous". The probe tick **was** the main-session activation. Step (4) was the failure — Claude treated the wake as a notification to acknowledge, not as an advance trigger to execute on.

Root cause (per first-principles diagnosis at the time): Claude carried a request-response mental model into autonomous-chain context. The wake-signal taxonomy + 4-step handler above counters this.

### Incident 2 (2026-05-18 E2 R0): silent wake-source failure

Observed failure: codex E2 R0 lit review dispatch (bg `br34irrbe`, probe `c23ca85e`) ran ~10 min, completed cleanly:
- log final marker: `=== DISPATCH_STATUS=completed (exit 0) ===`
- artifact `_LIT_REVIEW_CODEX.md` (16551 bytes) written
- codex CLI logged `ERROR codex_core::session: failed to record rollout items: thread ... not found` before exit

But Claude never got woken:
- `<task-notification>` never arrived (suppressed, probably by the rollout-items session error)
- Probe `c23ca85e` was already deleted by the time Claude looked (`CronDelete c23ca85e` → "No scheduled job") — it self-deleted on terminal detect (prior pattern) but its fire message never reached Claude's input stream
- ScheduleWakeup wasn't set up as backup

Claude waited silently for ~5 min until the user manually said "进入下部分, autonomous", which finally triggered investigation.

Root cause (per first-principles diagnosis at the time): wake-source paths are independently failable, and the prior architecture treated probe self-delete on terminal as fire-and-forget — single point of failure. Fix: Step 0 full state sweep on ANY wake (including user messages) catches missed terminals; the probe lifecycle (now v3 2-tick grace self-delete, per `codex-dispatch-watchdog`) prevents permanent loss of the probe-signal path by guaranteeing ≥2 terminal fires before deletion.

## Composing skills

| Composes with | Role |
|---|---|
| `codex-dispatch-watchdog` | cron probe is the **physical carrier** of one wake-signal class; this skill describes the **semantic handling** of all wake signals including probe ticks |
| `research-round-lifecycle` | chain state = round state machine; this skill describes the wake-to-advance protocol that moves between rounds in autonomous mode |
| `claude-decision-discipline` G5 | plan*do iteration assumes plan-state is queried at each step; this skill operationalizes "query plan-state on every wake" |

## Anti-patterns

- Treating `<task-notification>` as just a status update + reporting it to user without advancing
- Stopping after CronDelete on probe terminal detect ("ready for next activation" — there is no separate activation in autonomous chain; probe firing IS the activation)
- Confusing yield (legitimate wait on external) with stop (silent end of work)
- Asking user "should I continue?" mid-chain when authorization already covers continuation
- Pausing at a round boundary in autonomous chain to write a summary "checkpoint" — round boundary advancement is what the chain is for

## Calibration checklist (mental, before stopping)

Before ending a turn in autonomous chain, verify:
- [ ] Did I run a step-0 full state sweep on this wake? (NOT just react to the wake's literal content)
- [ ] Did I reach a TRUE yield (external dispatch in flight / user-checkpoint required / explicit redirect from user)?
- [ ] Did I `CronDelete` any probe whose terminal I've already acted on? (v3 probes self-delete on the 2nd terminal tick; explicit CronDelete after advance is just faster cleanup — see `codex-dispatch-watchdog`)
- [ ] Did I update TodoWrite to reflect the new state?
- [ ] Did I commit any artifact produced during this transition?
- [ ] If wake came from user message in chain: did I sweep BEFORE responding to the user's literal content? (User's "continue" may be implicitly flagging a missed terminal — sweep first.)

If any item is "no" — keep going, you have not yet reached a yield.
