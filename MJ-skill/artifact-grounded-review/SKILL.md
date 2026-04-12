---
name: artifact-grounded-review
description: Enforces that both Claude and Codex must read actual code and result artifacts before giving evaluation scores. Prevents score inflation from summary-based prompts.
---

# Artifact-Grounded Dual Review Protocol

Use this skill whenever the user asks for dual evaluation, scoring, reviewer simulation, or quality assessment of research work ("dual审稿", "评估研究水平", "审稿人视角", etc.).

## Problem this solves

When Claude summarises a project's highlights in the Codex dispatch prompt, Codex scores based on the summary (which is inherently positive-framed), not on the actual evidence. This produces inflated scores that miss integrity gaps. Similarly, Claude can score based on "design intent" rather than "executed evidence."

## Core Rule

**Both Claude and Codex must read primary sources before scoring.**

- "Primary sources" = source code files, result JSON/CSV artifacts, paper/report drafts, git history.
- A score or claim is **unsupported** unless the reviewer can cite the specific file path and line/key where the evidence lives.
- Design intent without executed artifact = 0 credit for that claim.
- "The script exists but no output was saved" = missing evidence, not evidence.

## Pre-Scoring Checklist (both agents)

Before emitting any score, complete all of these:

1. **Read key source modules** — actual logic, not just filenames.
2. **Read every result artifact** referenced by the paper or report.
3. **Cross-check numbers**: for each quantitative claim in the paper, verify it appears in an artifact. Flag mismatches.
4. **Check for phantom results**: claims that lack ANY artifact backing.
5. **Check overfitting indicators**: `train_roc`, `train_loss`, train–heldout gaps in result JSONs.
6. **Check claim–artifact correspondence**: does the script that supposedly produced a result actually contain the code to do so?

## Codex Dispatch Rules

When dispatching Codex for evaluation:

### DO
- Give Codex a **list of file paths** to read.
- Give Codex a **verification checklist** (what to check).
- Give Codex a **scoring rubric** (dimensions and scale).
- Ask Codex to **cite file:line or artifact:key** for every score justification.

### DO NOT
- Summarise the project's results in the prompt.
- Include Claude's own scores, conclusions, or impressions.
- Frame the project positively or negatively — let Codex form its own view.
- Use adjectives like "strong", "robust", "comprehensive" in the dispatch prompt.

### Prompt template

```
You are a critical reviewer. Read these files, then score the work.

Source files to read:
- [path1]
- [path2]
...

Result artifacts to read:
- [path3]
- [path4]
...

Paper/report to review:
- [path5]

Verification checklist:
1. For each number in the paper, find the backing artifact. Flag any without backing.
2. Check if scripts match their claimed outputs.
3. Check train metrics for overfitting indicators.
4. [task-specific checks]

Score these dimensions (1-10):
[rubric]

Rules:
- Cite file:key for every justification.
- Flag "UNVERIFIED" for claims without artifact backing.
- Do not accept claims at face value.
```

## Claude's Review Obligations

- Claude must independently read the same artifacts Codex reads.
- Claude must not score any dimension higher than the evidence supports.
- If Claude discovers an artifact gap, it must flag it even if the "design intent" is sound.
- Claude must NOT pre-read Codex's scores before completing its own review.

## Convergence Rules

- When scores diverge by > 1.5 on any dimension: both cite evidence. Lower score wins unless higher-scorer provides an artifact path the other missed.
- Aggregate scores: arithmetic mean of converged dimension scores.
- Report must include an "Evidence Gaps" section listing every claim without artifact backing.

## Output Format

```
## Evidence Gaps (MUST be first section)
- [claim] — [missing artifact description]

## Dimension Scores
| Dimension | Claude | Codex | Converged | Evidence basis |
|---|---:|---:|---:|---|

## Overall
- 毕设: X/10
- 期刊: X/10

## Integrity Risks
1. [risk + specific file evidence]
```
