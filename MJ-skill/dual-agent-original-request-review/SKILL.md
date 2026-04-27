---
name: dual-agent-original-request-review
description: Use when executor and reviewer must both work directly from the same raw user request, avoiding paraphrase drift.
---

# Raw-Requirement Dual-Agent Collaboration

Use this skill when the user explicitly wants multiple agents to work from the same original request, or when the risk of requirement paraphrase drift is high.

## When to Use

Dual-agent mode is a **boundary protocol**. The three boundary triggers below are **mandatory** — skipping them means the workflow is procedurally incomplete, and any paper-facing wording / final verdict / source-trace conclusion / empirical numerical claim derived without the corresponding dual is **not admissible** until the dual is run.

### Mandatory triggers (cannot be skipped)

- **(a) Requirement boundary**: major direction shift, cross-stage alignment, or overturning a ≥3-day-old self-authored pre-reg as a load-bearing argument. → requirement-side alignment review.
- **(b) Decision node**: overturning a plan premise that previously passed dual, switching paths, or rejecting an approach. → plan-prior review.
- **(c) Post-implementation verification**: after substantive code or readout production, the reviewer **must independently re-run the source-code trace and independently reproduce empirical numbers in the readout**. Acceptance gate: reviewer's independent re-derivation must converge on the same number / the same trace conclusion before the verdict is admitted into paper-facing context. **Not acceptable substitutes**: executor's self-assessment; single-source numbers; caveats embedded in commit body; "I caught the issue myself" as a stand-in for an independent second opinion.

If (a), (b), or (c) is triggered and dual is not run in the same session, the **next session inheriting the work must run the missed dual before advancing any paper-facing claim derived from the unreviewed work** — the burden does not expire.

### Other valid triggers

- **High paraphrase-drift risk**: the user's raw request has subtle wording that an executor's restatement is likely to lose.
- **Explicit user request**: the user wants two agents on the same raw request.

## When NOT to Use

- Routine implementation, debugging, probes (in the implementation flow, before the (c) post-impl checkpoint), variant trials in progress, single-file edits, Q&A, governance-meta-doc tweaks.
- Tasks already clear enough that an extra reviewer adds no value **AND** none of (a)/(b)/(c) is triggered.
- Tasks with critical requirement ambiguity — clarify with the user first; entering dual mode on an ambiguous brief just multiplies the misreading.

Note: "routine implementation" is NOT an excuse to skip (c). Once code/readout is finalized, (c) triggers regardless of how routine the implementation felt.

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
- The agent challenging or relying on a critical claim must independently verify it — do not trust the other party's trail alone for verdict-affecting claims
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
- If verification is impossible with current access, report the conflict as unresolved and `assumption-dependent` rather than picking a side
- After verification, both parties must update their conclusion to match the verified ground truth, even if it contradicts their original position

## Stuck Detection & Recovery

When Claude or Codex is making no forward progress, use this self-diagnosis protocol instead of retrying blindly.

### Stuck signals (any one triggers diagnosis)

- Same tool call attempted 3+ times with identical or near-identical parameters
- Two consecutive correction rounds that produce no meaningful change in output
- Context usage exceeds 80% with no clear path to completion
- Codex returns errors or timeouts on 2+ consecutive calls

### Diagnosis steps (in order)

1. **Name the symptom**: which stuck signal fired?
2. **Classify the cause**:
   | Symptom | Likely cause | Verification |
   |---------|-------------|-------------|
   | Repeated identical tool calls | Loop — same approach keeps failing | Check if the error message is identical each time |
   | Correction rounds produce no change | Requirement ambiguity or misaligned checklist | Re-read the raw user request |
   | Context >80% | Too much intermediate reasoning accumulated | Check TodoWrite for completed items that can be compacted |
   | Codex errors/timeouts | Service issue or prompt too broad | Try a narrower prompt; if still fails, fall back to Claude |
3. **Apply the smallest reversible fix**:
   - Loop → change approach (different tool, different file, different hypothesis)
   - Ambiguity → escalate to user with specific question
   - Context overflow → `/compact` at the nearest phase boundary, then re-read critical files
   - Codex unavailable → Claude proceeds directly (per `codex-orchestration` § Fallback Protocol)
4. **If fix doesn't work after 1 attempt** → stop and report to user: "I'm stuck. Symptom: X. Tried: Y. Need your input on Z."

### Anti-pattern: silent retry loops

Never retry the same failing operation more than twice without changing something. The third attempt must use a different approach, or the task must be escalated.

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
- **Experience distillation** (1-2 sentences): did this task reveal a reusable pattern, a new failure mode, or a codebase invariant that should be captured? If yes, suggest where to record it:
  - New or updated **skill rule** → name the skill and section
  - New **MEMORY.md entry** → draft the one-liner
  - New **mandatory read** → suggest the file and task area for `docs/architecture-map.md`
  - **Nothing worth capturing** → state "No new reusable pattern identified" (this is a valid answer; do not force extraction)
