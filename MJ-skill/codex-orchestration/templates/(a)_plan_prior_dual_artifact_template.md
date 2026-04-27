# (a) Plan-Prior Dual Review Artifact — <subject>

<!--
USAGE
=====

This template scaffolds a (a) plan-prior dual-review artifact per:
- Harness rule 3(a): 需求边界 / plan-prior — 推翻已过 dual 的 plan 前提 /
  切路径 / 拒绝一条方案 → plan-prior review
- AGENTS.md "Dual Artifact Header Annotation Rule"
- .claude/skills/codex-orchestration/SKILL.md §1 "Model verification oracle"
  + §"Account Dispatch Priority"
- .claude/skills/artifact-grounded-review/SKILL.md (executor + reviewer 都读
  primary source / artifact 后再形成结论)

PRE-WRITING CHECKLIST
- [ ] Reviewer (Codex) has independently read primary sources + artifacts
      with explicit file:line citations; no pre-digested summary dispatch.
- [ ] Pre-review independence note: write your local first-pass findings to
      `/tmp/claude_pre_review_<short-id>.md` BEFORE reading the second
      reviewer's output.
- [ ] Run `scripts/codex_session_meta.sh <threadId>` and paste its 5-line
      stdout verbatim into the Header annotation block below.
- [ ] Do NOT delete or trim any line of the helper output. The
      `session_path` line is the disambiguation anchor — it identifies
      which codex home (codex-main vs codex-b vs ...) was used.

REPLACE every `<placeholder>` and remove this comment block before commit.
-->

## Header annotation (verbatim from `scripts/codex_session_meta.sh`)

```
<paste 5-line helper stdout here, e.g.:
model=gpt-5.5
cli_version=0.125.0
effort=xhigh
session_path=/Users/charles/.codex/sessions/2026/04/27/rollout-2026-04-27T...jsonl
session_first_ts=2026-04-27T...Z>
```

> Source disambiguation: see `session_path` line above. Account in use is identifiable from the `~/.codex/` vs `~/.codex-b/` vs `~/.codex-<suffix>/` prefix.

## Pre-review independence

- Local pre-review note (written before reading reviewer output): `</tmp/claude_pre_review_<short-id>.md>`
- Second reviewer model + threadId: `<model name>` (`<threadId>`)
- Both reviewers read the same primary sources + artifacts independently? **<yes / no — explain>**

## Track + comparability scope

- Track: `<B | governance | skills | docs | infra | outputs>`
- Comparability-critical touched by this review: `<no | yes — list affected runs / paper numbers>`
- Frozen contract this review extends or examines: `<path:line | n/a>`

## Verdict

**<NO_BLOCKERS | REVISE_THEN_FREEZE | BLOCKING_REVISIONS_REQUIRED | STOP_AND_AMEND>**

One-paragraph verdict statement:

<text>

## Per-axis findings

| # | Axis | Status | Finding (with file:line / artifact:key citations) | Recommended fix |
|---|------|--------|---------------------------------------------------|-----------------|
| 1 | <axis name> | `<PASS / REVISE / BLOCKING>` | `<finding ...>` | `<fix ...>` |
| 2 | <axis name> | ... | ... | ... |
| 3 | ... | ... | ... | ... |

Add or remove rows to match the contract / plan structure under review.

## Cross-cutting concerns

1. **<concern title>** — `<one-paragraph explanation with citations>`
2. ...

## Independent factual claims verified

| Claim | Evidence (file:line / artifact:key) |
|-------|-------------------------------------|
| `<claim 1>` | `<file:lineA-B>` |
| `<claim 2>` | `<artifact_key.json:fieldX>` |

## Pre-blessed alternatives

If the verdict is `REVISE_THEN_FREEZE` or `BLOCKING_REVISIONS_REQUIRED`, list pre-blessed fixes the contract author can apply without triggering a round-N+1 re-review:

1. `<fix 1>` — at `<file:line>`
2. `<fix 2>` — at `<file:line>`

## Disposition / next step

- [ ] Round-2 (a) review needed? `<yes — round-2 scope: ...>` / `<no — apply fixes inline>`
- [ ] User authorization needed before next step? `<yes — what authority>` / `<no>`
- [ ] Next milestone: `<freeze | implementation | round-2 dispatch | other>`

## Archival metadata

- Run dir: `outputs/reports/<experiment_name>/run_YYYYMMDD_<descriptor>/`
- Companion archive: `dual_packet_archive/` (codex_task.md + codex_user_context.md mirrored from /tmp)
- Commit hash that introduces this artifact: `<filled at commit time>`

---

*End (a) plan-prior dual review artifact. Do not modify post-commit; if subsequent review converges differently, write a new artifact (`(a)_plan_prior_dual_artifact_round2.md`, etc.) and reference this one as the round-1 source.*
