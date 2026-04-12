---
name: dual-agent-original-request-review
description: Use when executor and reviewer must both work directly from the same raw user request, avoiding paraphrase drift.
---

# Raw-Requirement Dual-Agent Collaboration

Use this skill when the user explicitly wants multiple agents to work from the same original request, or when the risk of requirement paraphrase drift is high.

## When to Use

- **Always on** — every task that involves code changes automatically enters dual-agent mode
- The only exception is pure Q&A or clarification questions that require no code changes

## When NOT to Use

- Trivial, mechanical, single-file changes
- Task is already clear enough that an extra reviewer adds no value
- Requirements have critical ambiguity — clarify with user first before entering dual-agent mode

If the third case applies, clarify the ambiguity with the user before deciding whether to enter dual-agent mode.

## Core Principles

1. Both executor and reviewer must receive the raw user request verbatim.
2. Reviewer judges against "raw request + acceptance checklist + actual output," not executor's paraphrase alone.
3. Executor and reviewer must have asymmetric roles — avoid duplicate work.
4. All key assumptions must be stated explicitly — never package guesses as confirmed facts.
5. If reviewer finds deviation, report the specific gap, evidence, and impact rather than giving vague endorsement.
6. Any factual claim about codebase, data, or completed work that can change scope, implementation, review verdict, final status, or conflict outcome must be either verified with a traceable trail or explicitly marked as an assumption. See **Verification Discipline** below.

## Default Role Assignment

- Claude: planner, task framer, final synthesizer
- Executor: implementation, local verification, deliverable production
- Reviewer: independent requirement decomposition, acceptance checklist, deviation check

If Claude serves as reviewer, it must write the acceptance checklist independently before seeing executor output.

## Standard Process

1. **Preserve raw request**
   - Keep user's original words verbatim — do not compress before forwarding.
2. **Claude generates acceptance checklist**
   - Goals
   - Non-goals
   - Constraints
   - High-risk misunderstanding points
   - Minimum completion criteria
3. **Codex independently generates its own acceptance checklist**
   - Dispatch Codex with the raw user request only (no Claude checklist) and ask: "Read the user request and produce your own acceptance checklist: goals, non-goals, constraints, high-risk misunderstanding points, minimum completion criteria."
   - Claude compares both checklists. If they diverge on a key point, classify the divergence:
     - **Requirement ambiguity** → surface to the user before proceeding
     - **Factual disagreement about codebase / data state** → Claude performs the minimal verification (read source / grep / inspect artifact) before proceeding; the verified result is binding
4. **Dispatch executor task**
   - Raw request verbatim
   - Merged checklist (reconciled from step 2-3)
   - Constraints
   - Expected output
   - Non-goals
   - Known verified facts (with trail) — anything verified during steps 2-3
   - Open assumptions requiring verification — anything not yet verified that would change implementation choices
5. **Claude reviews executor output against**
   - Raw request verbatim
   - Merged acceptance checklist
   - Executor's actual output
   - Verification trail for any claim that affects acceptance, rejection, or major criticism — Claude must independently verify critical claims (do not rely on executor's trail alone)
   - **Verdict-affecting claims audit**: Executor must tag its verdict-affecting claims (any claim that would change the final Met/Not Met/Partially Met status). Reviewer must explicitly disposition every tagged claim:
     - ✅ Verified (with trail)
     - ⚠️ Cannot verify (mark `assumption-dependent`)
     - ❌ Verification failed (with counter-evidence)
     - Leaving a tagged claim without disposition is not allowed — silent pass-through is treated as a review gap.
6. **Final summary distinguishes three statuses**
   - Met
   - Partially met or assumption-dependent
   - Not met, deviated, or unverifiable

## Two-File Handoff

All Codex dispatches use two files to keep Claude's context small and separate raw user intent from Claude's framing:

- `/tmp/codex_user_context.md` — user's recent messages verbatim (last 1-3 turns)
- `/tmp/codex_task.md` — Claude's instructions (executor or reviewer packet below)

Codex prompt: `"Read /tmp/codex_user_context.md for the raw user request and /tmp/codex_task.md for your task instructions. Execute accordingly."`

## Verification Discipline

When a factual claim about the codebase, data, or completed work could change scope, implementation, review verdict, final status, or conflict outcome, that claim must be either verified with a traceable trail or explicitly marked as an assumption.

### When verification is mandatory

- Any claim that affects checklist content, implementation direction, review verdict, final summary, or conflict resolution
- Any rejection or approval of a critical claim made by the other party

### When verification is NOT required

- General knowledge (language semantics, library defaults, well-known patterns)
- The user's just-spoken words (re-reading the message is enough)
- Style preferences and subjective "this is cleaner" judgments
- Implementation details that don't affect any verdict

### Who performs verification

- The agent making the claim performs the first verification using the cheapest sufficient method
- The other agent **first reviews the existing trail** (re-read the same file:line cited) rather than running an independent verification from scratch
- Independent re-verification from scratch is only required when:
  - The trail is incomplete, ambiguous, or points to the wrong file/line
  - The trail's conclusion doesn't follow from the cited evidence
  - The claim is verdict-affecting AND the trail was produced by the same agent whose work is being judged (self-grading risk)
- When both agents discover the same factual dispute simultaneously, the agent with lower verification cost goes first (Codex for code reading, Claude for cross-module judgment); the other reviews the trail
- Conflict resolution: confidence and persistence are not tiebreakers; verified evidence is

### How (ordered by cost — prefer the cheapest sufficient)

1. Re-read the user message verbatim
2. Read source with file path + line numbers
3. `grep` / `rg` for symbol or pattern
4. Inspect artifact (CSV / JSON / NPZ row + field)
5. `git log` / `git blame` for historical claims
6. Run a narrow probe (small script, single test case)

If verification cost would exceed roughly 5 minutes (heavy experiment, external system access), scope it down or escalate to the user; do not silently skip.

### What counts as a sufficient trail

- `path/to/file.py:123-145` (file + line range)
- `command + key output excerpt`
- `artifact path + row/field/value`
- Screenshots reserved for UI / external system claims

### Where the trail is recorded

- In the report (reviewer findings, executor completion notes, final summary)
- Format: `claim → evidence → implication`
- No separate audit log file required

### Failure mode

- If verification cannot be completed (no read access, external system, blocked), mark the item `assumption-dependent` or `blocked` with the missing access named explicitly
- Never present an unverifiable claim as `confirmed`

## Executor Task Packet Template (`/tmp/codex_task.md`)

```md
Role: Executor
(Raw user request is in /tmp/codex_user_context.md — read it first.)

Goal:
<objective only — do not rewrite business goals>

Constraints:
- <constraint 1>
- <constraint 2>

Expected output:
- <code / documentation / tests / plan / explanation>

Non-goals:
- <non-goal 1>
- <non-goal 2>

Working rules:
- State key assumptions explicitly
- Do not expand scope unilaterally
- Verify any factual claim that affects implementation choices or completion status (cite file:line, command output, or artifact path)
- Report only decision-relevant verification results with a traceable trail — do not log every action
- Mark unresolved facts as assumption-dependent or blocked rather than guessing
- Tag verdict-affecting claims: list claims that would change Met/Not Met status under a "Verdict-Affecting Claims" section so the reviewer can audit them
```

## Reviewer Task Packet Template (`/tmp/codex_task.md`)

```md
Role: Reviewer
(Raw user request is in /tmp/codex_user_context.md — read it first.)

Review target:
<executor's plan or actual output>

What to produce:
- Requirement decomposition
- Acceptance checklist
- Potential misunderstanding points
- Deviations from raw request
- Missing items / over-implementation / risks

Review rules:
- Do not substitute executor's paraphrase for user's request
- First judge "was the right problem solved," then "was it solved well"
- If the request itself has critical ambiguity, state how that ambiguity affects the conclusion
- Do not approve or reject a decision-critical factual claim without independent verification
- When challenging executor on factual grounds, cite the verification trail (file:line, command + output, or artifact path)
- Distinguish requirement ambiguity (escalate to user) from factual disagreement (verify against ground truth)
```

## Acceptance Checklist Template

- Input: what the user explicitly asked for
- Processing: does the approach directly serve that goal
- Output: does the deliverable match the request
- Boundaries: any unauthorized scope expansion, missed constraints, or changed non-goals
- Verification: were key behaviors actually verified
- Risks: what unverified assumptions remain

## Conflict Resolution

- First classify the disagreement:
  - **Requirement interpretation dispute** → go back to the raw request and compare item by item; if ambiguity remains, surface it to the user — neither role may decide unilaterally
  - **Factual dispute about code, data, artifacts, or completed work** → resolve by verification against ground truth; confidence or persistence is not a tiebreaker
  - **Output visibility dispute** → provide the complete output before continuing review
- For factual disputes, the party challenging a claim must provide counter-evidence (file:line, command + output, or artifact path) or show that the original trail is insufficient; vague rejection is not acceptable
- **Misclassification guard (B→A downgrade):** If both agents find valid, non-contradictory evidence supporting their respective positions (i.e., evidence points to different dimensions rather than conflicting facts), the dispute is **not** factual — it is a requirement interpretation dispute disguised as a factual one. Force-reclassify to requirement interpretation and escalate to the user with both evidence sets: "Code supports both interpretation X and Y — which did you intend?" The test: if resolving the dispute requires knowing the user's priority or preference rather than a ground-truth fact, it is always type A regardless of how much code evidence exists.
- If verification is impossible with current access, report the conflict as unresolved and `assumption-dependent` rather than picking a side
- After verification, both parties must update their conclusion to match the verified ground truth, even if it contradicts their original position

## Convergence Limits

Correction rounds are capped to prevent infinite loops and token waste:

| Task type | Max rounds | Notes |
|-----------|-----------|-------|
| Implementation, refactor, documentation | 2 | Standard cap |
| Bug investigation, cross-module analysis | 3 | Round 3 is restricted: only targeted verification of a narrowed hypothesis — no new hypotheses allowed |

After hitting the cap:
- Stop the loop immediately
- Report to user: divergence point, both parties' evidence, and recommended next step
- User decides whether to continue, redirect, or accept current state
- Do not restart the loop from round 1 without user instruction

## Anti-Patterns

- Both agents only receive executor's paraphrase of the request
- Reviewer only gives style comments without checking goal alignment
- Forcing dual-agent on trivial tasks where cost exceeds benefit
- Describing process or governance improvements as model/algorithm/detector performance gains
- Treating a decision-critical claim as true because one agent sounds more confident
- Marking work as satisfied, broken, or verified without a traceable evidence trail
- Conceding to the other party's claim without verifying it first

## Final Report Format

Every final report must include:

- Whether dual-agent mode was used
- Reason for using or not using it
- Executor output summary
- Reviewer's key findings
- Whether the raw request was satisfied
- Ambiguities still requiring user decision
- Key decision-critical claims with evidence trail or explicit assumption status
