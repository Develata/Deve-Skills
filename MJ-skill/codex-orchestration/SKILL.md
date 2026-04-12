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
| `approval-policy` | No | `"on-failure"` (recommended), `"untrusted"`, `"on-request"`, or `"never"`. |

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
- **Reuse sessions**: After the first `mcp__codex__codex` call returns a `threadId`, use `mcp__codex__codex-reply` with that `threadId` for follow-up questions in the same domain. This avoids cold-start overhead.
- **Prefer `read-only` sandbox**: For pure analysis/inspection tasks, pass `sandbox: "read-only"`. This reduces sandbox overhead.
- **Narrow the prompt**: Each Codex prompt should target 1-3 specific files or one specific question. Never send "analyze the entire X module" — instead send "read X.py lines 100-200 and explain function Y."
- **Specify file paths in prompt**: When you already know the relevant files, include their paths directly in the Codex prompt so it doesn't need to search.
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

## 6. Anti-Patterns

- Sending Codex a prompt that requires the full conversation context it doesn't have.
- Asking Codex to re-read files Claude already has in context.
- Using `workspace-write` sandbox for read-only tasks.
- Launching a single large Codex call instead of multiple narrow parallel calls.
- Retrying a failed broad prompt without narrowing scope first.
- Letting Codex make architectural decisions that should be Claude's responsibility.
- Treating Codex output as final without Claude review for non-trivial tasks.
