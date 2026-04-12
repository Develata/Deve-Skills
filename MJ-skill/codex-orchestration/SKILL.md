---
name: codex-orchestration
description: Claude + Codex MCP 完整协作框架。涵盖调用方法、角色分配、效率规则、成本路由和任务模板。当 Claude 需要委派任务给 Codex MCP 或与 Codex 协作时加载此 skill。
---

# Codex MCP Orchestration

## 1. How to Call Codex MCP

### Tool Names

| Tool | Purpose | Key Return |
|------|---------|------------|
| `mcp__codex__codex` | Start a new Codex session | `{ threadId, content }` |
| `mcp__codex__codex-reply` | Continue an existing session | `{ threadId, content }` |

### Parameters for `mcp__codex__codex`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `prompt` | Yes | The task description. Be specific, include file paths. |
| `sandbox` | No | `"read-only"` (analysis/inspection) or `"workspace-write"` (file changes). Default: `"workspace-write"`. Prefer `"read-only"` when possible. |
| `cwd` | No | Working directory. Default: project root. |
| `approval-policy` | No | `"never"` (recommended for trusted projects — fully autonomous, no prompts), `"on-failure"` (auto-execute, prompt only on failure), `"on-request"` (auto-execute, prompt only when Codex asks), or `"untrusted"` (prompt for every command). **Always pass this parameter explicitly** — omitting it may default to `"untrusted"` which causes frequent approval popups. |

### Parameters for `mcp__codex__codex-reply`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `threadId` | Yes | The `threadId` returned by the initial `mcp__codex__codex` call. |
| `prompt` | Yes | The follow-up question or instruction. |

### Example: New Session

```
mcp__codex__codex(
  prompt="Read src/engine_health/diagnosis/track_b_sequence_detection.py lines 28-50 and explain the TrackBSequenceDetectionConfig fields. Answer in under 200 words.",
  sandbox="read-only",
  approval-policy="never",
  cwd="/Users/charles/Desktop/BYSJ/projectv2"
)
```

### Example: Continue Session

```
mcp__codex__codex-reply(
  threadId="019d70b2-...",
  prompt="Now check what default threshold_mode is used and whether it matches the formal package."
)
```

## 2. Executor / Reviewer Role Assignment

Default role mapping by task type:

| Task Type | Executor | Reviewer | Rationale |
|-----------|----------|----------|-----------|
| **Implementation** | Codex | Claude | Codex is cheaper for bounded execution; Claude has deeper context for correctness review. |
| **Analysis / research** | Codex | Claude | Claude has stronger critical judgment for synthesis and review. |
| **Critical decisions** | Both independently | Claude synthesizes | Avoids single-model blind spots. |
| **Mechanical / low-priority** | Codex alone | None | Not worth reviewer overhead. |

### Reviewer Selection Principles

- If Claude produced the analysis, prefer Codex as reviewer (avoids confirmation bias).
- If Codex produced the implementation, prefer Claude as reviewer (deeper context + correctness).
- Never let the same agent both produce and review without explicit user approval.

## 3. Call Efficiency Rules

- **Two-file task handoff**: Always use two separate files to dispatch tasks to Codex:
  1. `/tmp/codex_user_context_<ID>.md` — the user's recent messages (verbatim, last 1-3 turns as relevant). This is the raw requirement source.
  2. `/tmp/codex_task_<ID>.md` — Claude's analysis, scope, constraints, expected output, and non-goals. This is Claude's instruction layer.
  `<ID>` is a short unique suffix (e.g., first 8 chars of a UUID or timestamp) to avoid collisions between concurrent sessions.
  Then pass Codex a short prompt: `"Read /tmp/codex_user_context_<ID>.md for the raw user request and /tmp/codex_task_<ID>.md for your task instructions. Execute accordingly."` This keeps Claude's conversation context small and preserves a clean separation between raw user intent and Claude's framing.
- **Always pass `approval-policy`**: Every `mcp__codex__codex` call must include `approval-policy="never"` to prevent interactive approval popups. Omitting this parameter may cause Codex to prompt for every shell command, blocking autonomous execution.
- **Reuse sessions**: After the first `mcp__codex__codex` call returns a `threadId`, use `mcp__codex__codex-reply` with that `threadId` for follow-up questions in the same domain. This avoids cold-start overhead.
- **Prefer `read-only` sandbox**: For pure analysis/inspection tasks, pass `sandbox: "read-only"`. This reduces sandbox overhead.
- **Narrow the prompt**: Each Codex prompt should target 1-3 specific files or one specific question. Never send "analyze the entire X module" — instead send "read X.py lines 100-200 and explain function Y."
- **Specify file paths in prompt**: When you already know the relevant files, include their paths directly in the Codex prompt so it doesn't need to search. When you don't know the paths, use the Iterative Retrieval Protocol (§6) instead of guessing.
- **Cap output expectations**: Tell Codex "answer in under 300 words" or "list only file paths" when full prose is unnecessary.
- **Avoid redundant delegation**: If Claude already read a file this conversation, do not ask Codex to re-read it. Synthesize from existing context.
- **Parallel over serial**: When 2-4 independent questions are needed, launch parallel `mcp__codex__codex` calls rather than sequential ones.
- **Fail fast**: If a Codex call is taking too long or returns partial results, do not retry the same broad prompt. Narrow scope and retry, or fall back to Claude's own Read/Grep tools for the specific data needed.

## 4. Cost-Aware Routing

Claude tokens are expensive, Codex tokens are cheap. Route accordingly:

| Task Profile | Route To | Reason |
|-------------|----------|--------|
| High-stakes (architecture, tradeoff, review, final synthesis) | Claude directly | Quality matters more than cost. |
| Low-priority mechanical (bulk inspection, formatting, docs, simple summaries) | **Codex** | Save Claude token budget. |
| Bounded execution (implementation, testing, debugging) | **Codex** | Well-scoped, Codex is sufficient. |
| Open-ended planning, synthesis, multi-source integration | Claude | Requires deep reasoning. |

### General Rules

- Avoid nesting broad planning inside Codex — Codex should receive already-planned tasks.
- Do not use Codex as the primary orchestrator when Claude is already the top-level agent.
- When Claude can answer directly from already-loaded context, do not delegate unnecessarily.
- Use parallel Codex calls for independent subtasks to maximize throughput.

## 5. Task Framing Template

When delegating to Codex MCP, frame each task using this template:

```
Scope:           [files, directories, or modules]
Goal:            [what to accomplish]
Constraints:     [what not to change, time/size limits]
Expected output: [format and content of the result]
Non-goals:       [what this task explicitly does NOT cover]
```

### Framing Rules

- Avoid vague repo-wide prompts like "understand everything about this project."
- Prefer bounded, testable requests with clear completion criteria.
- State assumptions explicitly rather than leaving them implicit.
- Do not treat guesses as facts — verify before acting on uncertain information.
- When assumptions are necessary, declare them and mark them as assumptions.
- Verification discipline (when, who, how, what trail) for factual claims is defined in the **Verification Discipline** section of `dual-agent-original-request-review/SKILL.md`. Codex tasks that touch the codebase or real artifacts inherit those rules.

## 6. Iterative Retrieval Protocol

### When to use

Use when Claude **cannot confidently determine all relevant file paths** before dispatching Codex. Common triggers:

- Bug investigation in an unfamiliar module
- Tracing a data flow across unknown boundaries
- Locating experiment outputs whose naming/location varies across runs
- Understanding a subsystem Claude hasn't read before

**Do NOT use** when file paths are already known — go directly to the standard Two-File Handoff. The decision rule: if Claude can fill the `Scope` field of the Task Framing Template (§5) with specific paths, skip this protocol.

### Protocol: DISPATCH → EVALUATE → REFINE → LOOP

```
Round 1 — Broad discovery (Codex searches, Claude evaluates)
  Claude → Codex: "Search <directory/module> for <keywords/patterns>.
                   List files with: path, one-line summary, relevance tier, mtime (if artifact).
                   Cap at 15 files."
  Codex → Claude: file list + relevance notes

  Claude evaluates: assign relevance tiers, pick top 3-5 files for Round 2.
  Claude may add new keywords discovered from Codex's file list.

Round 2 — Narrowed inspection (standard Two-File Handoff resumes)
  Claude writes discovered paths into /tmp/codex_task_<ID>.md as the Scope field.
  Claude → Codex: "Read <specific files/line ranges>.
                   Answer <targeted analytical question>."
  Codex → Claude: detailed findings

Round 3 — Targeted verification (only if Round 2 reveals a gap)
  Allowed only for: verifying a specific claim, chasing one newly discovered dependency.
  NOT allowed for: introducing a new hypothesis or widening scope.
  Claude → Codex (via codex-reply on same threadId):
                   "Read <newly discovered file> lines X-Y.
                   Verify whether <specific claim from Round 2>."
  Codex → Claude: verification result
```

**Hard cap: 3 rounds.** If relevant files still cannot be located after 3 rounds, Claude reports the gap to the user rather than expanding further.

### Relevance tiers

Claude assigns a tier to each file Codex returns in Round 1:

| Tier | Meaning | Action |
|------|---------|--------|
| **High** | Directly implements or contains the target logic/data | Read in Round 2 |
| **Medium** | Tangentially related (imports, configs, test files) | Read only if High files are insufficient |
| **Low** | Unlikely relevant (naming coincidence, unrelated module) | Drop unless no better candidates exist |

Threshold: at least 2 High-tier files needed before proceeding to Round 2. If Round 1 yields 0 High files, refine keywords and retry Round 1 once (counts toward the 3-round cap).

### Integration with existing protocols

**Two-File Handoff**: Round 1 uses a lightweight inline prompt (no Two-File needed — it's a search task). Round 2+ transitions to standard Two-File Handoff once scope is known.

**Session reuse**: use `codex-reply` with the same `threadId` across all rounds — Codex retains its discovery context, reducing cold-start overhead.

**Artifact-Grounded Review**: when iterative retrieval locates result artifacts, the staleness check (`artifact-grounded-review/SKILL.md` § Artifact Staleness Check) applies to every discovered artifact. Codex must report artifact mtimes in Round 1 so Claude can filter stale ones before Round 2.

**Verdict-Affecting Claims**: files discovered via iterative retrieval that become the basis of a verdict-affecting claim must be tagged in the executor's claim list (per `dual-agent-original-request-review/SKILL.md` § Standard Process step 5).

### Dispatch template — Round 1

```
Scope:    <top-level directory or module — intentionally broad>
Goal:     Find files related to <topic/keywords/patterns>.
          For each file report: path | one-line summary | relevance (High/Med/Low) | mtime (artifacts only).
Constraints:
  - Cap at 15 files
  - Do NOT read file contents — list only
  - Include mtime for result artifacts (JSON/CSV/NPZ) so staleness can be assessed
Expected output: Markdown table
Non-goals: Deep analysis — that comes in Round 2.
```

### When iterative retrieval ends early

- If Round 1 yields 3+ High-tier files and Claude can confidently fill the Scope field → skip directly to standard analytical task (no Round 3 needed).
- If Round 2 fully answers the question → stop, do not force Round 3.
- Only enter Round 3 when Round 2 explicitly reveals a gap that one more targeted read can close.

### Anti-patterns for iterative retrieval

- Skipping Round 1 and asking Codex to "find and analyze" in one shot (too broad, low quality).
- Running Round 1 on the entire repo root (`/`) instead of a targeted directory.
- Continuing past 3 rounds without user input.
- Using iterative retrieval when Claude already knows the file paths (unnecessary overhead).
- Treating Round 1 results as analytical conclusions (they are search results, not findings).

## 7. Anti-Patterns

- Sending Codex a prompt that requires the full conversation context it doesn't have.
- Asking Codex to re-read files Claude already has in context.
- Using `workspace-write` sandbox for read-only tasks.
- Launching a single large Codex call instead of multiple narrow parallel calls.
- Retrying a failed broad prompt without narrowing scope first.
- Letting Codex make architectural decisions that should be Claude's responsibility.
- Treating Codex output as final without Claude review for non-trivial tasks.
- Using standard narrow dispatch when file paths are unknown (use Iterative Retrieval Protocol §6 instead).
