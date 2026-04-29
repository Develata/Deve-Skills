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

Note: in repos using multi-account isolation per the `codex-account-switching` skill, the tool name is suffixed by the account label, e.g. `mcp__codex-main__codex`, `mcp__codex-b__codex`, `mcp__codex-c__codex` etc. This SKILL writes `mcp__codex__codex` as the generic placeholder; substitute your actual MCP server name.

### Account Dispatch Priority (multi-account setups)

When more than one codex MCP server is configured in the user's Claude harness (verified via the `codex-account-switching` skill), the default dispatch order is **`main` first, then `b`, then per-account fallback below**, applied per call (not per session — once a `threadId` is established on an account, all `codex-reply` calls for that thread MUST stay on that same account because session JSONLs and quota are per-account).

**Default dispatch order**:

1. `mcp__codex-main__codex` — primary; this is the account on `codex --version` PATH and gets the bulk of the workload.
2. `mcp__codex-b__codex` — secondary; reserved for parallel batches and main-account fallback.
3. Any further account labels (`codex-c`, `codex-personal`, ...) — tertiary, in alphabetical order.

**Fallback triggers** — switch to the next account when the current account returns:
- HTTP 429 / rate limit / quota exhausted
- HTTP 5xx / network error
- MCP timeout / no response
- Explicit "model not available on this account" error
- ApprovalDenied (after one retry on same account)

**Exemptions from the main-first rule** (state the reason inline at call site):
- **Active multi-account batches**: §9 Stage-2 parallel scoring / dual-review pairs that need 2 independent reviewers on different accounts to avoid same-account confirmation bias — assign main/b deliberately.
- **Quota preservation**: a long-running task that already used >50% of main's daily quota → explicitly route the next non-critical task to b.
- **User-pinned account**: user says "用 b 跑 / use codex-b" or similar — honor verbatim.
- **Continuing an existing thread**: `codex-reply` follow-ups MUST use the same `mcp__codex-<account>__codex-reply` as the thread's original `codex` call. Mixing accounts on one threadId fails because the session JSONL is account-local.

**Recording the chosen account**: per §1 "Model verification oracle" below, every dual artifact's Header annotation must verbatim-embed the stdout of the helper script that ships with this skill at `scripts/codex_session_meta.sh` (relative to this SKILL.md's directory; canonical path when skill is installed at user level: `~/.claude/skills/codex-orchestration/scripts/codex_session_meta.sh`). The `session_path` line in the helper's output disambiguates which `~/.codex{,-b,-c,...}/sessions/...` JSONL was used. The dispatch choice is therefore self-documenting in the artifact; no separate "account=" field is needed.

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
  prompt="Read code/engine_health/diagnosis/track_b_sequence_detection.py lines 28-50 and explain the TrackBSequenceDetectionConfig fields. Answer in under 200 words.",
  sandbox="read-only",
  approval-policy="never",
  cwd="<your project root, e.g. via ${CLAUDE_PROJECT_DIR}>"
)
```

### Example: Continue Session

```
mcp__codex__codex-reply(
  threadId="019d70b2-...",
  prompt="Now check what default threshold_mode is used and whether it matches the formal package."
)
```

### Model verification oracle

**原则**: LLM cannot reliably report its own model slug or CLI version, and different `CODEX_HOME` accounts can carry different CLI minor versions simultaneously. The single authoritative source is the per-account session jsonl. Any critical dual artifact (scorecard, decision packet, plan-prior or post-impl readout) must verbatim-embed the helper's 5-line stdout in its header, citing `session_path` as the primary anchor.

**Authoritative source per account**:
- codex-main: `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<threadId>.jsonl`
- codex-b: `~/.codex-b/sessions/YYYY/MM/DD/rollout-<timestamp>-<threadId>.jsonl`

**Mandatory recording recipe (use the helper, do NOT hand-grep)**: run `~/.claude/skills/codex-orchestration/scripts/codex_session_meta.sh <threadId>` and verbatim-embed the 5-line stdout (`model= / cli_version= / effort= / session_path= / session_first_ts=`) into the dual artifact header. The helper auto-discovers all `~/.codex*` homes and uses pipefail-safe grep so any reviewer can re-run it against the cited threadId and reproduce values byte-for-byte.

Manual fallback (only if helper is unavailable):
- Model slug: `grep -oE '"model":"[^"]*"' <rollout.jsonl> | head -1`
- CLI version: `head -1 <rollout.jsonl> | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['payload']['cli_version'])"`
- Reasoning effort (codex-main records this; codex-b currently does not): `grep -oE '"reasoning_effort":"[a-z]+"' <rollout.jsonl> | head -1`

**校准样例** — what a compliant header looks like:
```
model=gpt-5.5
cli_version=0.125.0-alpha.3
effort=xhigh
session_path=/Users/charles/.codex/sessions/2026/04/29/rollout-20260429T172949Z-019dd892-c24d-7321-9820-09d7ecf63e41.jsonl
session_first_ts=2026-04-29T17:29:49Z
```
Verbatim from helper stdout. `session_path` disambiguates which codex home + exact JSONL.

**避坑样例** — Codex's text reply self-reports `GPT-5 codex-cli 0.125.0`; the actual jsonl shows `0.125.0-alpha.3` on codex-main and `0.125.0` on codex-b. Transcribing the text reply silently loses the `alpha.3` suffix and conflates the two accounts. The catch: model self-report is a hallucination surface; jsonl is ground truth.

**Required scaffolds**: instead of recreating the artifact structure each time, copy the matching boundary template from the per-skill templates directory and fill in:

| Boundary | Template path |
|----------|---------------|
| (a) plan-prior | `.claude/skills/codex-orchestration/templates/(a)_plan_prior_dual_artifact_template.md` |
| (b) decision-node | `.claude/skills/codex-orchestration/templates/(b)_decision_node_dual_artifact_template.md` |
| (c) post-impl | `.claude/skills/codex-orchestration/templates/(c)_postimpl_dual_artifact_template.md` |

Each template's first content block is the Header annotation slot — copy the helper's 5-line stdout there verbatim. Each template encodes the boundary-specific evidence requirements (e.g. (c) requires the reviewer to independently re-run source-code trace + reproduce empirical numbers per harness rule 3(c)). The templates are forward-only from 2026-04-27; pre-existing dual artifacts that predate the templates are immutable provenance and are not retroactively rewritten.

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
- **Transport safety hard rule**:
  - **原则**: any prompt over ~8 KB or containing large pasted artifacts must use file-only handoff (write to `/tmp/codex_*.md`, MCP call sends only the short "Read these two files" instruction). When an MCP call closes unexpectedly, inspect the rollout jsonl's `role=user` entry before treating the result as Codex output — `Connection closed` with anomalous user content means the transport failed *before* Codex saw the task; discard the thread and retry with file-only handoff.
  - **校准样例**: a 30 KB analytical task → write to `/tmp/codex_task_a3f1.md` + `/tmp/codex_user_context_a3f1.md` → MCP `prompt = "Read /tmp/codex_user_context_a3f1.md and /tmp/codex_task_a3f1.md, execute accordingly."` (~80 char prompt). Rollout jsonl shows the short instruction as `role=user`, Codex reads the files, normal response.
  - **避坑样例**: ~30 KB raw prompt sent directly through MCP `prompt` parameter → rollout jsonl `role=user` content shows `reply OK` (truncation artifact), followed by `Connection closed`. Result text appears valid but Codex never saw the actual task. Catch mechanism: post-call, grep the jsonl `role=user` entry — if it's not the intended prompt, the thread is dead, restart via file-only.
- **Always pass `approval-policy`**: Every `mcp__codex__codex` call must include `approval-policy="never"` to prevent interactive approval popups. Omitting this parameter may cause Codex to prompt for every shell command, blocking autonomous execution. **Scope clarification**: `approval-policy="never"` only controls codex's internal shell-command approvals. Claude Code's outer MCP permission layer is separate — each distinct `mcp__codex*` call triggers its own allow/deny prompt unless pre-approved in `settings.local.json` or the session's allow-list. The "never" flag does NOT bypass the outer prompt.
- **Reuse sessions**: After the first `mcp__codex__codex` call returns a `threadId`, use `mcp__codex__codex-reply` with that `threadId` for follow-up questions in the same domain. This avoids cold-start overhead.
- **Prefer `read-only` sandbox**: For pure analysis/inspection tasks, pass `sandbox: "read-only"`. This reduces sandbox overhead.
- **Narrow the prompt**: Each Codex prompt should target 1-3 specific files or one specific question. Never send "analyze the entire X module" — instead send "read X.py lines 100-200 and explain function Y."
- **Specify file paths in prompt**: When you already know the relevant files, include their paths directly in the Codex prompt so it doesn't need to search. When you don't know the paths, use the Iterative Retrieval Protocol (§6) instead of guessing.
- **Cap output expectations**: Tell Codex "answer in under 300 words" or "list only file paths" when full prose is unnecessary.
- **Avoid redundant delegation**: If Claude already read a file this conversation, do not ask Codex to re-read it. Synthesize from existing context.
- **Parallel over serial**: When 2-4 independent questions are needed, launch parallel `mcp__codex__codex` calls rather than sequential ones.
- **Parallel dispatch threshold**: launching ≥3 concurrent `mcp__codex*__codex` calls in one message floods the user's approval dialog queue; users commonly reject 4-of-7 out of confusion rather than intent. For §9 Stage-2 parallel scoring or any batch dispatch, **either** (a) announce the batch and confirm pre-approval with the user in one round, **or** (b) serialize: one call, wait for result, dispatch next. Default to serialize when a dual is live and the user is actively reviewing.
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

### Model selection

**原则**: MCP tool schema's `model` parameter description carries *illustrative* placeholder slugs, not project recommendations. Default behavior is to **omit** `model` so the call inherits the per-account `~/.codex/config.toml` setting. Explicit override only in three cases: (i) API-key account with non-ChatGPT-allowed slug, (ii) reproducing a historical thread's model for continuity audit, (iii) deliberate regression testing. Before passing any explicit `model`, run the pre-dispatch verification recipe below.

**校准样例** — a compliant analytical-task dispatch:
```
mcp__codex-main__codex(
  prompt="Read /tmp/codex_task_a3f1.md ...",
  approval-policy="never",
  sandbox="read-only",
  cwd="${CLAUDE_PROJECT_DIR}"
  # no `model` key — inherits codex-main config.toml gpt-5.5
)
```
Verification trail (cite in artifact): `grep '^model\s*=' ~/.codex/config.toml` → `model = "gpt-5.5"`. Account default matches project's dominant historical pattern. No override needed.

**避坑样例** — copying from the schema description without verifying:
```
mcp__codex-main__codex(prompt=..., model="gpt-5.2")  # ← pulled from schema example text
```
The schema description reads "e.g. 'gpt-5.2', 'gpt-5.2-codex'"; the slug is illustrative. Account default is `gpt-5.5`; project's historical dual artifacts use `gpt-5.5`. Override silently routes to a different model than every prior dual in the audit trail, breaking cross-batch consistency. Catch mechanism: the verification recipe forces a `grep` against `config.toml` and historical artifacts before any explicit override — if the slug doesn't match either, abort.

**Pre-dispatch verification recipe** (artifact-grounded; do this before passing any explicit
`model` value):

```bash
# 1. account default (the one your call will inherit if model is omitted)
grep -E '^model\s*=' ~/.codex/config.toml          # codex-main default
grep -E '^model\s*=' ~/.codex-b/config.toml        # codex-b default (if exists)

# 2. project-historical usage distribution (cite-don't-guess)
grep -rh '^model=' outputs/reports/*/run_*/dual* \
    outputs/reports/*/run_*/'(a)'* \
    outputs/reports/*/run_*/'(b)'* \
    outputs/reports/*/run_*/'(c)'* 2>/dev/null \
  | sort | uniq -c | sort -rn

# 3. effort distribution (same files)
grep -rh '^effort=' <same paths as above> | sort | uniq -c | sort -rn
```

Pick the model that matches (i) the account's config.toml default OR (ii) the project's
dominant historical pattern. Cite the verification step in the dispatch artifact's
"dispatch configuration" block so future audits can re-verify.

### Reasoning effort tier

`gpt-5.5` supports `low | medium | high | xhigh` reasoning effort. Default in `~/.codex/config.toml` is `high`. Override per-call via the `config` parameter:

```
mcp__codex__codex(prompt=..., config={"model_reasoning_effort": "xhigh"}, ...)
```

When to consider `xhigh` (extra cost + latency, ~2× reasoning_output_tokens):

- §9 Stage-2 strict-rubric scoring on contribution-level decisions (novelty/anti-goal trade-offs).
- Critical-decision dual reviews where reviewer must independently re-derive a source-code trace or multi-artifact synthesis.
- Single-shot judgment calls where wrong answer cascades (e.g. "should we kill this paper section").

When to keep `high` (default):

- Bounded implementation / debug / mechanical tasks.
- Stage-2 batches once started — do NOT mix effort levels mid-batch (creates intra-batch heterogeneity that confounds rank comparison; observed 04-25: C1-C8 all at `high`).
- Any task where you've already paid for `xhigh` once and the answer was clear.

Verify actual effort applied via session jsonl: `grep -oE '"effort":"[^"]*"' <rollout.jsonl> | head -1`.

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
- Passing a large pasted prompt directly through MCP instead of a file-only handoff; `Connection closed` plus a rollout `role=user` entry like `reply OK` indicates transport failure, not a valid Codex response.
- Asking Codex to re-read files Claude already has in context.
- Using `workspace-write` sandbox for read-only tasks.
- Launching a single large Codex call instead of multiple narrow parallel calls.
- Retrying a failed broad prompt without narrowing scope first.
- Letting Codex make architectural decisions that should be Claude's responsibility.
- Treating Codex output as final without Claude review for non-trivial tasks.
- Using standard narrow dispatch when file paths are unknown (use Iterative Retrieval Protocol §6 instead).

## 8. Literature Triage Dispatch

### When to use

任何新增文献调研任务：related work 写作、baseline 探索、方法发散、综述补洞。

### 三级读入策略

```
Level 1 — Triage（判定是否相关）
  每篇论文只喂：abstract + introduction。
  获取优先级：arXiv TeX 源 > 期刊 HTML/Markdown > 本地 PDF 前 ~2 页。
  Codex 输出（每篇一条）：
    - go / kill
    - 一句话理由
    - relevance tag（与本项目哪条研究线相关）

Level 2 — Method Reading（通过 triage 的论文）
  只喂相关 section（method / experiments），不灌入全文。
  优先级同 Level 1。

Level 3 — Full Paper（需要复现或深度引用）
  完整加载，但必须同轮更新
  `docs/10_diagnosis/literature_*/literature_manifest.json` 登记。
```

### 获取顺序

1. **arXiv TeX 源**：`https://arxiv.org/e-print/<id>`（arxiv.org 已在 `settings.local.json` WebFetch 白名单）。
2. **期刊 HTML**：MDPI / Springer / ScienceDirect / PMC / PHM Society 域已在白名单。
3. **本地 PDF**：仅当 1/2 均失败时回退，且 Level 1 triage 只读 abstract + intro 的前 ~2 页。
4. **整篇 PDF 灌入**：禁止用作 triage 手段；只允许出现在 Level 3，且配 `literature_manifest.json` 登记。

### 登记义务

Level 3 新增条目最少包含：

- `paper_id`
- `title`
- `year`
- `download_url`
- `project_use`（如何用到本项目，具体到 claim / baseline / method）
- `not_for`（明示不可外推的场景，避免未来误引）

落点：
- Track B 方向：`docs/10_diagnosis/literature_track_b/literature_manifest.json`
- Fault injection 方向：`docs/10_diagnosis/literature_fault_injection/literature_manifest.json`

### 防误杀

- Triage kill 必须给出一句话理由，不允许 "not relevant" 单独出现，否则视为 UNVERIFIED。
- 若 Level 1 一次 kill 掉超过 80%，Claude 回读 20% kill 理由抽样复核，防止关键词错配导致的系统性误杀。
- 与 `artifact-grounded-review` 一致：任何基于文献做出的判断须引用具体 paper:section，禁止从 Codex 的单行 summary 直接上升为 claim。

### PDF Admission Gate（强制执行）

Claude 在读任何 PDF 或向 Codex 派发 PDF 前，必须先回答三问：

1. 当前属于哪个 Level（triage / method / full paper）？
2. 手头唯一格式是 PDF，还是同时有 TeX 源 / HTML / Markdown？
3. 根据下表决定是否允许整篇 PDF 进入上下文：

| Level | TeX / HTML / Markdown | PDF |
|-------|----------------------|-----|
| **1. Triage** | ✅ 只喂 abstract + intro | ❌ 整篇禁。如只有 PDF，先手工 / 脚本抽 abstract+intro 段落，再喂纯文本 |
| **2. Method reading** | ✅ 只喂相关 section | ⚠️ 仅允许按 page range 抽取的节选（例：pp. 3–7），整篇禁 |
| **3. Full paper** | ✅ | ✅ 但必须同轮更新 `literature_manifest.json` 登记 |

Gate 被违反的后果：上下文被稀释、后续决策质量下降（作者实测现象）。违反后的自救：立刻 `/compact` 已灌入的整篇 PDF 内容，按正确 Level 重新喂摘取版。Gate 不依赖 Codex，是 Claude 主线程的责任。

## 9. Divergent–Strict–Decisive Dispatch Pattern

### When to use

开放式技术决策：候选未知、多个方案可行、需要广覆盖的发散 + 强约束的严审。典型触发：

- "下一步加哪个 ablation / 换哪个 baseline"
- "哪几个 signal family 值得纳入本轮 regen"
- "三种 threshold 策略里哪一种最贴合 journal bar"

**不要用**于：执行已决定的任务、bug fix、实现已知接口——那些走标准 Two-File Handoff（§3）。

### Three-stage protocol（全部通过 `mcp__codex__codex` 新 session 完成）

```
Stage 1 — Divergent Generator (Codex session A)
  Input: raw user request + baseline context + constraints only.
  NO "prior attempts"、NO "previously rejected ideas"、NO Claude 自己的 lean。
  Ask: "Generate N=10 candidate approaches, each with: name, one-paragraph
        rationale, key assumption, failure mode. Do not rank. Do not self-filter."
  Output: 10 candidates, flat list.

Stage 2 — Strict Scorer (Codex session B, isolated from A)
  Input: raw user request + baseline context + ONE candidate at a time.
  Session B sees NO other candidates, NO generator's self-assessment.
  Ask: "Score this candidate on: novelty, feasibility, baseline-compatibility,
        implementation complexity, expected gain. Give go / revise / kill plus
        rationale. Cite specific code or artifact paths from baseline when
        claiming compatibility."
  Output: 10 independent score cards (parallel dispatch, different threadIds).

Stage 3 — Decisive Synthesis (Claude, main thread)
  Read all 10 score cards. Rank by score + fit with project constraints
  (journal bar / Track B scope / comparability_impact risk).
  Produce a single ranked short-list (top 2-3) with rationale.
  If top candidate has UNVERIFIED compatibility claim, route to Codex
  for verification before committing.
```

### Context isolation rules（硬性约束）

- Stage 1 和 Stage 2 **必须是新 session**（`mcp__codex__codex`，不是 `codex-reply`）。
- Stage 2 的 10 次 scoring 并行调用，每次都是独立新 session，**不得复用 threadId**。
- Stage 1 的 10 个候选整包发给 Stage 2 是错误——必须一人一份隔离。
- Claude 在 Stage 3 前不得先把自己的 ranking 告诉 Codex，防止 anchoring。
- 用户的 raw request 和 baseline context 在 Stage 1/2 均逐字保留（沿用 `dual-agent-original-request-review` 的 raw-request preservation）。

### Mid-dual interruption & resume

If Stage 2 stalls for external reasons (CLI upgrade, auth expiry, Claude Code restart, user-interrupt), maintain a resume-state file. Working copy lives at `/tmp/<dual_name>_state_<date>.md`; **mirror to the packet dir** (`docs/methodology-notes/<dual_name>_packet_<date>/resume_state.md`) on every update — `/tmp` is volatile (wiped on reboot / disk pressure), so the packet dir is the durable source of truth.

State file contents:

- completed scorecards with verdicts + sums, **each annotated `model=<slug>, cli=<ver>`** pulled from session jsonl (see §1 "Model verification oracle"), so cross-session / cross-CLI resume is auditable
- pending candidate list
- explicit block cause (if blocked; "none" if clean pause)
- resume plan (first action on return)

**Write-through discipline**: update the state file **immediately** after each scorecard completes, before dispatching the next one. Do not batch updates — state file drift is the root cause of "I thought C4 was pending but it was already done" bugs (observed 2026-04-25). State file is single source of truth, not session memory's shadow.

**Artifact archival discipline**: all dual working artifacts are evidence, not scratch. `/tmp` is working space only. On any of these boundaries, copy all dual artifacts from `/tmp` into the packet dir and commit:

- Every state file update (mirror resume_state.md)
- Before any Claude Code restart / session handoff
- Before any `git commit` touching the packet — skeleton-only commits are insufficient if S1 divergent output or S2 scorecards exist

Mapping convention (packet dir filenames):

- `/tmp/codex_stage1_<topic>_output_<date>.md` → `S1_divergent_output.md`
- `/tmp/codex_stage2_scorecard_C<n>_<date>.md` → `S2_scorecard_C<n>.md`
- `/tmp/claude_pre_review_<ID>.md` → `01_claude_pre_review.md` (already in skeleton)
- `/tmp/<dual_name>_state_<date>.md` → `resume_state.md`

On resume, do **not** re-run completed stages. The sealed pre-review and Stage 1 output remain authoritative across interruptions; re-dispatch only the pending Stage-2 scorecards. Stage 3 synthesis must read all scorecards from the packet dir (not `/tmp`, which may be empty after reboot), because some may have been produced in a prior Claude session.

### Relation to existing rules

- 本模式是 §2 "Critical decisions" 行（"Both independently, Claude synthesizes"）的具体化实现路径。
- 不与 `artifact-grounded-review` 冲突：Stage 2 的严审必须 cite 具体 `file:line` / `artifact:key`，缺失证据的评分标 UNVERIFIED。
- 不替代 `dual-agent-original-request-review` Verification Discipline；Stage 3 产出如果改变项目走向（trainer / baseline / 评分口径），仍须回到 dual-agent review 做正式验收。
- 与 §8 Literature Triage 互补：Stage 1 的 candidate 可以源自 Level 2 通过的论文；Stage 2 严审时允许引用那些 paper:section 作为 compatibility 依据。

### Output format（Stage 3 的最终输出）

```
## Divergent-Strict-Decisive Decision Log

Stage 1 candidates (Codex session A, threadId=<...>):
1. <name> — <one-sentence>
2. ...
10. ...

Stage 2 score cards (parallel, 10 independent sessions):
| Candidate | novelty | feasibility | compat | complexity | gain | verdict | key evidence |
|-----------|---------|-------------|--------|------------|------|---------|--------------|

Stage 3 ranked short-list (Claude):
1. <top pick> — rationale + UNVERIFIED claims to resolve
2. <runner-up>
```

缺 Stage 2 的证据栏 或 Stage 3 的 short-list 理由，视为流程未完整，回流到 Claude 补齐。

## 10. Long-Running Task Discipline

### When to create a TaskCreate chain

主线程在开工**之前**就建 TaskCreate 链。满足任一条件即触发：

- 工作分解为 ≥3 个有序步骤
- 任一步骤涉及外部长耗时 job（Phase-1 / Phase-2 / baseline_audit / sample_generator / 任何远程 `ssh_tmux` session）
- 跨多轮 Codex dispatch 或跨多次 user 交互
- 结果会更新 paper-facing 数字（每步需要 checkpoint 便于事后追溯）

### Rules

- **粒度**：每个可分离阶段一条 task；不把整个 run 塞成一条，也不细到每个 shell 命令一条。
- **状态同步**：开始前 `TaskUpdate status=in_progress`，完成**立刻** `status=completed`，不批量攒到最后。
- **完成态绑 contract**：任务描述写清"完成态"判据，与 §15 Research Contract 的 `success_signal` / `artifact_output_paths` 对齐。
- **遇 blocker 新建 task**（而非改现 task 含义）。原 task 若被阻塞，仍保留 in_progress，新 task 描述 blocker + 解决路径。

### 为什么

- 上下文可能被压缩、session 可能被切换、用户可能离开再回来；Task 状态比对话内容更持久。
- 报错或中途停机时，下一任 Claude（或用户自己）能从 task list 拿到"刚到第 N 步"的快照。
- 配合 §15 Research Contract 双重锚定：task 是过程侧，contract 是结果侧。

### Anti-patterns

- 只 create 不 update：状态失真等于没有。
- Task 描述与对话内容重复：只写"对未来 Claude 也有信息量"的内容（完成态、blocker、关键决策点）。
- 长任务跑起来才补 TaskCreate：错过了前期规划阶段的价值。
