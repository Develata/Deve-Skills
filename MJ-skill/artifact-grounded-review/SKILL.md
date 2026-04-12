---
name: artifact-grounded-review
description: Enforces that both Claude and Codex must read actual code and result artifacts before any dual analysis — not just scoring, but any collaborative analytical task.
---

# Artifact-Grounded Dual Analysis Protocol

## Scope

This protocol applies to **all dual-agent analytical tasks**, not just scoring:
- Dual review / 审稿 / evaluation
- Research quality assessment
- Bug investigation and root-cause analysis
- Architecture review and design critique
- Results interpretation and discussion
- Any task where both agents form judgments about the codebase or its outputs

## Problem this solves

When Claude feeds Codex a pre-digested summary instead of raw file paths, two failures occur:
1. **Codex operates on Claude's framing**, not on ground truth — inheriting any bias, omission, or inflation.
2. **Neither agent truly understands the code** — both work from abstractions, missing implementation details, edge cases, and gaps between claims and artifacts.

## Core Rules

### Rule 1: Read before concluding

Both Claude and Codex must **read primary sources** before forming any analytical conclusion.

- "Primary sources" = source code, result artifacts (JSON/CSV/NPZ), paper/report drafts, git history, config files.
- Reading means opening the file and examining its content — not recalling a summary from a prior conversation turn.
- An analytical conclusion is **unsupported** unless the agent can cite the specific file path and line/key.

### Rule 2: No pre-digested summaries in dispatch

When Claude dispatches Codex for any analytical task:

**DO:**
- Give Codex **file paths to read**.
- Give Codex the **analytical task** (what to determine, what to check, what to evaluate).
- Give Codex **verification questions** if applicable.

**DO NOT:**
- Summarise what the code does or what the results show.
- Include Claude's own conclusions, impressions, or scores.
- Frame the project with adjectives (strong, robust, comprehensive, weak, etc.).
- Pre-interpret results — let Codex form its own reading.

### Rule 3: Claude reads independently

- Claude must read the same primary sources, not just relay Codex findings.
- Claude must form its own view **before** seeing Codex's output.
- If both agents read the same file and reach different conclusions, they resolve by citing specific lines/keys — not by deferring to whoever sounds more confident.

### Rule 4: Claims require artifacts

- A claim about system behavior requires code evidence (file:line showing the logic).
- A claim about experimental results requires artifact evidence (file:key showing the number).
- "The script exists" ≠ "the result was produced." Output artifacts must exist.
- Design intent without executed artifact = 0 credit for that claim.

## How to apply per task type

### Evaluation / scoring tasks

Before emitting any score:
1. Read key source modules — actual logic.
2. Read every result artifact referenced by the paper or report.
3. Cross-check: for each quantitative claim, verify it appears in an artifact.
4. Flag phantom results (claims without artifact backing).
5. Check overfitting indicators in result files.
6. Check claim–script correspondence (does the script actually produce what's claimed?).

Codex dispatch template for scoring:
```
Read these files, then evaluate:

Source: [paths]
Artifacts: [paths]
Paper: [path]

Checklist: [specific verification questions]
Rubric: [dimensions]

Rules: cite file:key for every justification. Flag UNVERIFIED for unbacked claims.
```

### Research analysis / discussion tasks

Before forming interpretive conclusions:
1. Read the result artifacts being discussed.
2. Read the code that produced them — understand what was actually computed.
3. Verify that the numbers being interpreted match the artifacts.
4. Check edge cases: did the computation cover all claimed conditions?

### Bug investigation / code review tasks

Before diagnosing or judging:
1. Read the relevant source modules.
2. Trace the actual data flow, not the documented intent.
3. Run or inspect test outputs if available.
4. Check git history for context on why code looks the way it does.

## Convergence rules (for scored evaluations)

- Divergence > 1.5 on any dimension: both cite evidence. Lower score wins unless higher-scorer provides an artifact path the other missed.
- Report must always include an "Evidence Gaps" section first.
- Design intent, planned features, or "should work" reasoning never override missing evidence.

## Output format (for scored evaluations)

```
## Evidence Gaps (MUST be first section)
- [claim] — [missing artifact or code evidence]

## Dimension Scores
| Dimension | Claude | Codex | Converged | Evidence |
|---|---:|---:|---:|---|

## Overall
- 毕设: X/10
- 期刊: X/10

## Integrity Risks
1. [risk + specific file:line or artifact:key]
```
