---
name: codex-orchestration
description: Claude Code + Codex CLI collaboration framework. Covers invocation, role assignment, efficiency defaults, cost routing, and dispatch patterns. Load when Claude Code delegates work to the `codex` CLI via Bash.
---

# Codex CLI Orchestration

This skill describes **defaults and judgment**, not enforced rules. Hard enforcement lives in the harness `UserPromptSubmit` hook (rules 2/3 there). Skill content guides; harness gates.

## 1. How to Call Codex CLI

Default mechanism: Claude Code invokes the `codex` CLI through the `Bash` tool. (The `mcp__codex__*` MCP tools still exist as fallback but are not the default.)

### Basic invocation

```bash
# Prompt as argument
codex exec --full-auto -s read-only -C "$PWD" \
  "Read code/foo.py:28-50 and explain the bar() function. Answer in <200 words."

# Prompt from stdin (preferred for any prompt > a few lines)
codex exec --full-auto -s read-only -C "$PWD" < /tmp/codex_task_a3f1.md

# Long-running: route via Bash run_in_background
codex exec --full-auto -s workspace-write -C "$PWD" \
  -o /tmp/codex_result_a3f1.md < /tmp/codex_task_a3f1.md > /tmp/codex_log_a3f1.txt 2>&1 &
```

### Key flags

| Flag | Meaning | Default for analytical tasks |
|---|---|---|
| `-s, --sandbox <mode>` | `read-only` / `workspace-write` / `danger-full-access` | `read-only` for inspection, `workspace-write` for impl |
| `--full-auto` | low-friction auto execution (analog of MCP `approval-policy=never`) | recommended for trusted projects |
| `-m, --model <slug>` | model override | omit (inherits `~/.codex/config.toml`) — see § Model selection |
| `-c <key=value>` | config override (TOML) | `-c model_reasoning_effort=xhigh` for hard reviews |
| `-C, --cd <dir>` | working directory | project root |
| `-o, --output-last-message <file>` | write final agent message to file (clean for parsing) | use for any background dispatch |
| `--json` | emit JSONL events to stdout | use when downstream parser needs structure |
| `--ephemeral` | do not persist session jsonl | only for throwaway probes; default is persist |

### Multi-account dispatch

`CODEX_HOME` env var selects the account (per `codex-account-switching` skill):

```bash
# codex-main (default — ~/.codex)
codex exec --full-auto ...

# codex-b (~/.codex-b)
CODEX_HOME=~/.codex-b codex exec --full-auto ...
```

Default order when multiple accounts exist: `main` → `b` → others alphabetical. Switch when current account hits 429 / 5xx / quota / model-not-available / repeated `ApprovalDenied`. Once a session is created on an account, follow-ups (`codex exec resume <session-id>`) should stay on that account — sessions and quota are per-`CODEX_HOME`.

Exemptions to main-first (state inline at call site): parallel scoring batches that need account independence (§9 Stage-2), main quota >50% used → route non-critical to b, user-pinned account.

### Model verification oracle

**Principle**: LLM cannot reliably report its own model slug or CLI version, and different `CODEX_HOME` accounts can carry different CLI minor versions simultaneously. The single authoritative source is the per-account session jsonl. Critical dual artifacts should verbatim-embed the helper's 5-line stdout in their header, citing `session_path` as the primary anchor.

**Authoritative source per account**:
- `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<session-id>.jsonl` (default `~/.codex` if `CODEX_HOME` unset)

**Recording recipe** (prefer the helper over hand-grep): run `~/.claude/skills/codex-orchestration/scripts/codex_session_meta.sh <session-id>` and verbatim-embed the 5-line stdout (`model= / cli_version= / effort= / session_path= / session_first_ts=`) into the dual artifact header. The helper auto-discovers all `~/.codex*` homes and uses pipefail-safe grep.

Manual fallback (if helper unavailable):
```bash
grep -oE '"model":"[^"]*"' <rollout.jsonl> | head -1
head -1 <rollout.jsonl> | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['payload']['cli_version'])"
grep -oE '"reasoning_effort":"[a-z]+"' <rollout.jsonl> | head -1
```

**Calibration example** — what a compliant header looks like:
```
model=gpt-5.5
cli_version=0.125.0
effort=xhigh
session_path=/Users/charles/.codex/sessions/2026/04/29/rollout-20260429T172949Z-019dd892-c24d-7321-9820-09d7ecf63e41.jsonl
session_first_ts=2026-04-29T17:29:49Z
```
Verbatim from helper stdout. `session_path` disambiguates which `CODEX_HOME` and which exact JSONL.

**Counter-example** — Codex's text reply self-reports `GPT-5 codex-cli 0.125.0`; jsonl shows `0.125.0-alpha.3` on one home and `0.125.0` on another. Transcribing the text reply silently loses the `alpha.3` suffix and conflates the two accounts. The catch: model self-report is a hallucination surface; jsonl is ground truth.

### Recommended scaffolds

Copy the matching boundary template from `~/.claude/skills/codex-orchestration/templates/`:

| Boundary | Template |
|---|---|
| (a) plan-prior | `(a)_plan_prior_dual_artifact_template.md` |
| (b) decision-node | `(b)_decision_node_dual_artifact_template.md` |
| (c) post-impl | `(c)_postimpl_dual_artifact_template.md` |

Header annotation slot = first content block; paste helper stdout verbatim. Each template encodes its boundary's evidence requirements (e.g. (c) reviewer independently re-runs source-code trace + reproduces empirical numbers per harness rule 3(c)).

## 2. Executor / Reviewer Role Assignment

Default role mapping by task type:

| Task Type | Executor | Reviewer | Rationale |
|---|---|---|---|
| **Implementation** | Codex | Claude | Codex is cheaper for bounded execution; Claude has deeper context for correctness review. |
| **Analysis / research** | Codex | Claude | Claude has stronger critical judgment for synthesis. |
| **Critical decisions** | Both independently | Claude synthesizes | Avoids single-model blind spots. |
| **Mechanical / low-priority** | Codex alone | None | Reviewer overhead not worth it. |

### Reviewer selection defaults

- Claude produced the analysis → prefer Codex as reviewer (avoids confirmation bias).
- Codex produced the implementation → prefer Claude as reviewer (deeper context + correctness).
- Same agent producing and reviewing without explicit user approval → avoid by default.

## 3. Call Efficiency Rules

- **Two-file handoff for non-trivial tasks**: write the user's recent messages to `/tmp/codex_user_context_<ID>.md` and Claude's instructions to `/tmp/codex_task_<ID>.md`, then `codex exec ... < /tmp/codex_task_<ID>.md` (or have the prompt instruct codex to read both files). Keeps Claude's conversation context small and separates raw user intent from Claude's framing. CLI has no MCP-style 8 KB transport limit, but disk handoff still preserves auditability and lets you cite the exact prompt later.
- **Pass `--full-auto`** (or `-c approval_policy=never`) for trusted projects to avoid interactive prompts. Equivalent of MCP `approval-policy=never`. Without it, codex may prompt for shell commands and block autonomous execution.
- **Prefer `-s read-only`** for analysis/inspection tasks. Use `workspace-write` only when the task actually edits files.
- **Reuse sessions** via `codex exec resume <session-id>` for follow-up questions in the same domain — avoids cold-start.
- **Narrow the prompt**: target 1–3 specific files or one specific question. "Analyze the entire X module" → "Read X.py:100-200 and explain function Y."
- **Specify file paths in prompt** when known. When unknown, use the Iterative Retrieval Protocol (§6) instead of guessing.
- **Cap output expectations**: "answer in <300 words" or "list only file paths" when prose isn't needed.
- **Avoid redundant delegation**: if Claude already read a file in this conversation, synthesize from existing context instead of asking codex to re-read.
- **Parallel over serial**: 2–4 independent questions → launch parallel `codex exec ...` background jobs (each `&` in Bash, then `wait`), not sequential.
- **Parallel dispatch threshold**: ≥3 concurrent codex jobs may flood the user's permission dialog (Claude Code's outer Bash permission, separate from codex's own approval). For batch dispatch (§9 Stage-2), either confirm pre-approval with the user in one round or serialize. Default to serialize when a dual is live and the user is actively reviewing.
- **Fail fast**: if a codex call hangs or returns partial results, do not retry the same broad prompt. Narrow scope or fall back to Claude's own Read/Grep tools.

## 4. Cost-Aware Routing

Claude tokens are expensive, codex tokens are cheap. Route accordingly:

| Task Profile | Route To | Reason |
|---|---|---|
| High-stakes (architecture, tradeoff, review, final synthesis) | Claude directly | Quality matters more than cost. |
| Low-priority mechanical (bulk inspection, formatting, docs, simple summaries) | **Codex** | Save Claude token budget. |
| Bounded execution (implementation, testing, debugging) | **Codex** | Well-scoped, codex is sufficient. |
| Open-ended planning, synthesis, multi-source integration | Claude | Requires deep reasoning. |

### General defaults

- Avoid nesting broad planning inside codex — codex should receive already-planned tasks.
- Don't use codex as primary orchestrator when Claude is already the top-level agent.
- When Claude can answer directly from already-loaded context, don't delegate unnecessarily.
- Use parallel codex jobs for independent subtasks to maximize throughput.

### Model selection

**Principle**: Default behavior is to **omit** `-m` so the call inherits the per-account `~/.codex/config.toml` setting. Explicit `-m` only when (i) API-key account with non-ChatGPT-allowed slug, (ii) reproducing a historical session's model for continuity audit, or (iii) deliberate regression testing. Before passing any explicit `-m`, run the verification recipe.

**Calibration example** — a compliant analytical-task dispatch:
```bash
codex exec --full-auto -s read-only -C "$PWD" \
  -o /tmp/codex_result_a3f1.md \
  < /tmp/codex_task_a3f1.md
# no `-m` — inherits config.toml gpt-5.5
```
Verification trail (cite in artifact): `grep '^model\s*=' ~/.codex/config.toml` → `model = "gpt-5.5"`. Account default matches project's dominant historical pattern.

**Counter-example** — copying from a tool-schema description without verifying:
```bash
codex exec -m gpt-5.2 ...   # ← pulled from MCP schema example text
```
Account default is `gpt-5.5`; project's historical dual artifacts use `gpt-5.5`. Override silently routes to a different model than every prior dual, breaking cross-batch consistency. Catch: the verification recipe forces a `grep` against `config.toml` and historical artifacts before any explicit override — if the slug doesn't match either, abort.

**Pre-dispatch verification recipe** (artifact-grounded; before passing any explicit `-m`):

```bash
# 1. account default
grep -E '^model\s*=' ~/.codex/config.toml          # codex-main
grep -E '^model\s*=' ~/.codex-b/config.toml        # codex-b (if exists)

# 2. project-historical usage distribution
grep -rh '^model=' outputs/reports/*/run_*/dual* \
    outputs/reports/*/run_*/'(a)'* \
    outputs/reports/*/run_*/'(b)'* \
    outputs/reports/*/run_*/'(c)'* 2>/dev/null \
  | sort | uniq -c | sort -rn

# 3. effort distribution (same paths)
grep -rh '^effort=' <same paths as above> | sort | uniq -c | sort -rn
```

Pick the model that matches (i) account default OR (ii) project's dominant historical pattern. Cite the verification step in the dispatch artifact's "dispatch configuration" block.

### Reasoning effort tier

`gpt-5.5` supports `low | medium | high | xhigh`. Default in `~/.codex/config.toml` is `high`. Override per-call:

```bash
codex exec --full-auto -c model_reasoning_effort=xhigh ...
```

**Consider `xhigh`** (extra cost + latency, ~2× reasoning_output_tokens):
- §9 Stage-2 strict-rubric scoring on contribution-level decisions.
- Critical-decision dual reviews where reviewer must independently re-derive a source-code trace or multi-artifact synthesis.
- Single-shot judgment calls where wrong answer cascades.

**Keep `high`** (default):
- Bounded implementation / debug / mechanical tasks.
- Stage-2 batches once started — keep effort consistent within a batch (mixing creates intra-batch heterogeneity that confounds rank comparison).
- Tasks where you've already paid for `xhigh` once and the answer was clear.

Verify actual effort applied: `grep -oE '"effort":"[^"]*"' <rollout.jsonl> | head -1`.

## 5. Task Framing Template

When delegating to codex, frame each task using this template:

```
Scope:           [files, directories, or modules]
Goal:            [what to accomplish]
Constraints:     [what not to change, time/size limits]
Expected output: [format and content of the result]
Non-goals:       [what this task explicitly does NOT cover]
```

### Framing defaults

- Avoid vague repo-wide prompts ("understand everything about this project").
- Prefer bounded, testable requests with clear completion criteria.
- State assumptions explicitly rather than leaving them implicit.
- Don't treat guesses as facts — verify before acting on uncertain information.
- When assumptions are necessary, declare them and mark them as assumptions.
- Verification discipline (when, who, how, what trail) for factual claims is in `dual-agent-original-request-review/SKILL.md` § Verification Discipline. Codex tasks that touch the codebase or real artifacts inherit those defaults.

## 6. Iterative Retrieval Protocol

### When to use

When Claude **cannot confidently determine all relevant file paths** before dispatching codex. Common triggers:

- Bug investigation in an unfamiliar module
- Tracing a data flow across unknown boundaries
- Locating experiment outputs whose naming/location varies across runs
- Understanding a subsystem Claude hasn't read before

**Don't use** when file paths are already known — go directly to standard Two-File handoff. Decision rule: if Claude can fill the `Scope` field of the Task Framing Template (§5) with specific paths, skip this protocol.

### Protocol: DISPATCH → EVALUATE → REFINE → LOOP

```
Round 1 — Broad discovery (codex searches, Claude evaluates)
  Claude → codex: "Search <directory/module> for <keywords/patterns>.
                   List files with: path, one-line summary, relevance tier, mtime (if artifact).
                   Cap at 15 files."
  codex → Claude: file list + relevance notes

  Claude evaluates: assign relevance tiers, pick top 3-5 files for Round 2.
  Claude may add new keywords discovered from codex's file list.

Round 2 — Narrowed inspection (standard Two-File handoff resumes)
  Claude writes discovered paths into /tmp/codex_task_<ID>.md as the Scope field.
  Claude → codex: "Read <specific files/line ranges>.
                   Answer <targeted analytical question>."
  codex → Claude: detailed findings

Round 3 — Targeted verification (only if Round 2 reveals a gap)
  Allowed only for: verifying a specific claim, chasing one newly discovered dependency.
  NOT allowed for: introducing a new hypothesis or widening scope.
  Claude → codex (via `codex exec resume <session-id>`):
                   "Read <newly discovered file> lines X-Y.
                   Verify whether <specific claim from Round 2>."
  codex → Claude: verification result
```

**Soft cap: 3 rounds.** If relevant files still cannot be located after 3 rounds, escalate to user rather than expanding further.

### Relevance tiers

| Tier | Meaning | Action |
|---|---|---|
| **High** | Directly implements or contains the target logic/data | Read in Round 2 |
| **Medium** | Tangentially related (imports, configs, test files) | Read only if High files are insufficient |
| **Low** | Unlikely relevant (naming coincidence, unrelated module) | Drop unless no better candidates exist |

Threshold: at least 2 High-tier files before proceeding to Round 2. If Round 1 yields 0 High files, refine keywords and retry Round 1 once (counts toward the 3-round cap).

### Integration with existing protocols

- **Two-File handoff**: Round 1 uses a lightweight inline prompt (no Two-File needed — it's a search task). Round 2+ transitions to standard Two-File once scope is known.
- **Session reuse**: use `codex exec resume <session-id>` across all rounds — codex retains discovery context, reducing cold-start.
- **Artifact-Grounded Review**: when iterative retrieval locates result artifacts, the staleness check (`artifact-grounded-review/SKILL.md` § Artifact Staleness Check) applies. Codex should report artifact mtimes in Round 1 so Claude can filter stale ones before Round 2.

### Dispatch template — Round 1

```
Scope:    <top-level directory or module — intentionally broad>
Goal:     Find files related to <topic/keywords/patterns>.
          For each file report: path | one-line summary | relevance (High/Med/Low) | mtime (artifacts only).
Constraints:
  - Cap at 15 files
  - Do not read file contents — list only
  - Include mtime for result artifacts (JSON/CSV/NPZ) so staleness can be assessed
Expected output: Markdown table
Non-goals: Deep analysis — that comes in Round 2.
```

### Anti-patterns

- Skipping Round 1 and asking codex to "find and analyze" in one shot (too broad, low quality).
- Running Round 1 on the entire repo root (`/`) instead of a targeted directory.
- Continuing past 3 rounds without user input.
- Using iterative retrieval when Claude already knows the file paths (unnecessary overhead).
- Treating Round 1 results as analytical conclusions (they are search results, not findings).

## 7. Anti-Patterns

- Sending codex a prompt that requires the full conversation context it doesn't have.
- Asking codex to re-read files Claude already has in context.
- Using `workspace-write` sandbox for read-only tasks.
- Launching a single large codex call instead of multiple narrow parallel calls.
- Retrying a failed broad prompt without narrowing scope first.
- Letting codex make architectural decisions that should be Claude's responsibility.
- Treating codex output as final without Claude review for non-trivial tasks.
- Using standard narrow dispatch when file paths are unknown (use Iterative Retrieval Protocol §6 instead).

## 8. Literature Triage Dispatch

### When to use

Any new literature task: related-work writing, baseline exploration, method divergence, survey gap-filling.

### Three-level reading strategy

```
Level 1 — Triage (relevance decision)
  Per paper: abstract + introduction only.
  Source priority: arXiv TeX > journal HTML/Markdown > local PDF first ~2 pages.
  Codex output (one row per paper): go/kill, one-line reason, relevance tag (which project line).

Level 2 — Method reading (papers that pass triage)
  Per paper: relevant section only (method / experiments), not full text.
  Same source priority as Level 1.

Level 3 — Full paper (needs reproduction or deep citation)
  Full load, but the same round must update
  `docs/10_diagnosis/literature_*/literature_manifest.json`.
```

### Source order

1. **arXiv TeX**: `https://arxiv.org/e-print/<id>` (arxiv.org in `settings.local.json` WebFetch allowlist).
2. **Journal HTML**: MDPI / Springer / ScienceDirect / PMC / PHM Society in allowlist.
3. **Local PDF**: only if 1/2 fail; Level 1 triage reads only abstract + intro of first ~2 pages.
4. **Full PDF ingestion**: not allowed for triage; Level 3 only, with manifest update in same round.

### Manifest entry (Level 3)

Minimum fields:
- `paper_id` / `title` / `year` / `download_url`
- `project_use` (specific to claim / baseline / method)
- `not_for` (scenarios where extrapolation would be wrong)

Locations:
- Track B: `docs/10_diagnosis/literature_track_b/literature_manifest.json`
- Fault injection: `docs/10_diagnosis/literature_fault_injection/literature_manifest.json`

### Anti-misclassification defaults

- Triage kill should give a one-line reason; "not relevant" alone counts as UNVERIFIED.
- If Level 1 kills >80% in one batch, Claude samples 20% of kill reasons for review — guards against keyword mismatch.
- Per `artifact-grounded-review`: any literature-based judgment cites specific paper:section; don't promote a codex one-line summary to a project claim.

### PDF admission gate

**Principle**: full PDFs dilute context and degrade subsequent decisions. Before reading any PDF or dispatching one to codex, answer three questions:

1. Which Level (triage / method / full)?
2. Is PDF the only format, or is TeX / HTML / Markdown also available?
3. Apply the table:

| Level | TeX / HTML / Markdown | PDF |
|---|---|---|
| **1. Triage** | abstract + intro only | full PDF avoid; if PDF-only, extract abstract+intro as plain text first |
| **2. Method reading** | relevant section only | page-range excerpt only (e.g. pp. 3–7); avoid full PDF |
| **3. Full paper** | OK | OK, with manifest update in same round |

Recovery if violated: `/compact` the ingested PDF, re-feed at correct Level. The gate is Claude's responsibility on the main thread, not codex's.

## 9. Divergent–Strict–Decisive Dispatch Pattern

### When to use

Open-ended technical decisions: candidates unknown, multiple paths viable, need broad divergence + strict scoring. Typical:

- "Which ablation / baseline next?"
- "Which signal families belong in this regen round?"
- "Which threshold strategy fits journal bar?"

**Don't use** for: executing already-decided tasks, bug fix, implementing known interfaces — those go through standard Two-File handoff (§3).

### Three-stage protocol (each via fresh `codex exec` — not `resume`)

```
Stage 1 — Divergent Generator (codex session A)
  Input: raw user request + baseline context + constraints only.
  No "prior attempts", no "previously rejected ideas", no Claude's own lean.
  Ask: "Generate N=10 candidate approaches, each with: name, one-paragraph
        rationale, key assumption, failure mode. Do not rank. Do not self-filter."
  Output: 10 candidates, flat list.

Stage 2 — Strict Scorer (codex session B, isolated from A)
  Input: raw user request + baseline context + ONE candidate at a time.
  Session B sees no other candidates, no generator's self-assessment.
  Ask: "Score this candidate on: novelty, feasibility, baseline-compatibility,
        implementation complexity, expected gain. Give go / revise / kill plus
        rationale. Cite specific code or artifact paths from baseline when
        claiming compatibility."
  Output: 10 independent score cards (parallel dispatch, fresh sessions).

Stage 3 — Decisive Synthesis (Claude, main thread)
  Read all 10 score cards. Rank by score + project constraints
  (journal bar / scope / comparability_impact risk).
  Produce a single ranked short-list (top 2-3) with rationale.
  If top candidate has UNVERIFIED compatibility claim, route to codex
  for verification before committing.
```

### Context isolation defaults

- Stage 1 and Stage 2 use **fresh sessions** (not `codex exec resume`).
- Stage 2's 10 scoring calls run in parallel as 10 independent fresh sessions; don't reuse session-ids.
- Don't send Stage 1's full candidate list to Stage 2 — score one at a time, isolated.
- Don't tell codex Claude's preliminary ranking before Stage 3 — anchoring risk.
- Raw user request + baseline context preserved verbatim through both stages (per `dual-agent-original-request-review` raw-request preservation).

### Mid-dual interruption & resume

If Stage 2 stalls (CLI upgrade, auth expiry, Claude Code restart, user interrupt), maintain a resume-state file. Working copy: `/tmp/<dual_name>_state_<date>.md`; mirror to packet dir (`docs/methodology-notes/<dual_name>_packet_<date>/resume_state.md`) on every update — `/tmp` is volatile, packet dir is durable source of truth.

State file contents:
- Completed scorecards with verdicts + sums, each annotated `model=<slug>, cli=<ver>` from session jsonl (see § Model verification oracle), so cross-session resume is auditable.
- Pending candidate list.
- Explicit block cause ("none" if clean pause).
- Resume plan (first action on return).

**Write-through**: update the state file immediately after each scorecard completes, before dispatching the next. Batched updates cause "I thought C4 was pending but it was already done" bugs.

**Artifact archival**: dual working artifacts are evidence, not scratch. `/tmp` is working space. On any of these boundaries, copy artifacts from `/tmp` into the packet dir and commit:
- Every state file update (mirror `resume_state.md`).
- Before any Claude Code restart / session handoff.
- Before any `git commit` touching the packet — skeleton-only commits are insufficient if S1 divergent output or S2 scorecards exist.

Mapping convention:
- `/tmp/codex_stage1_<topic>_output_<date>.md` → `S1_divergent_output.md`
- `/tmp/codex_stage2_scorecard_C<n>_<date>.md` → `S2_scorecard_C<n>.md`
- `/tmp/claude_pre_review_<ID>.md` → `01_claude_pre_review.md`
- `/tmp/<dual_name>_state_<date>.md` → `resume_state.md`

On resume: don't re-run completed stages. The sealed pre-review and Stage 1 output remain authoritative across interruptions; re-dispatch only pending Stage-2 scorecards. Stage 3 synthesis reads all scorecards from the packet dir (not `/tmp`, which may be empty post-reboot).

### Relation to existing rules

- This is the concretization of §2 "Critical decisions" row ("Both independently, Claude synthesizes").
- Compatible with `artifact-grounded-review`: Stage 2 cites `file:line` / `artifact:key`, missing-evidence scores marked UNVERIFIED.
- Doesn't replace `dual-agent-original-request-review` Verification Discipline; Stage 3 outputs that change project direction (trainer / baseline / scoring) still go through dual-agent review for formal acceptance.
- Complements §8 Literature Triage: Stage 1 candidates can come from Level-2-passed papers; Stage 2 may cite paper:section as compatibility evidence.

### Output format (Stage 3 final)

```
## Divergent-Strict-Decisive Decision Log

Stage 1 candidates (codex session A, session-id=<...>):
1. <name> — <one-sentence>
2. ...
10. ...

Stage 2 score cards (parallel, 10 independent sessions):
| Candidate | novelty | feasibility | compat | complexity | gain | verdict | key evidence |
|---|---|---|---|---|---|---|---|

Stage 3 ranked short-list (Claude):
1. <top pick> — rationale + UNVERIFIED claims to resolve
2. <runner-up>
```

Missing Stage 2 evidence column or Stage 3 short-list rationale → process incomplete; Claude fills in before proceeding.

## 10. Long-Running Task Discipline

### When to track via TodoWrite

Use the `TodoWrite` tool when work has these properties:

- Decomposes into ≥3 ordered steps.
- Any step involves an external long-running job (Phase-1 / Phase-2 / baseline_audit / sample_generator / any remote `ssh_tmux` session).
- Spans multiple codex dispatches or multiple user turns.
- Result updates paper-facing numbers (each step needs a checkpoint for later audit).

### Defaults

- **Granularity**: one task per separable phase; don't pack the whole run into one task, don't fragment to per-shell-command.
- **Status sync**: mark `in_progress` at start, `completed` immediately on finish — not batched.
- **Completion bound to contract**: task description states the completion criterion, aligning with the research contract's `success_signal` / `artifact_output_paths`.
- **Blocker → new task** (not edit existing). Original task stays `in_progress` if blocked; new task describes blocker + resolution path.

### Why

- Context may be compacted, sessions may switch, the user may step away. Task state is more durable than conversation content.
- On error or interruption, the next Claude (or the user) recovers a "you were at step N" snapshot.
- Pairs with the research contract: task list = process side, contract = result side.

### Anti-patterns

- Create-only without update: stale state = no state.
- Task description duplicates conversation: write only what's useful to a future Claude (completion criterion, blocker, key decision).
- Backfilling tasks after the long job already started: misses the planning phase value.
