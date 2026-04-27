# (b) Decision-Node Dual Review Artifact — <decision subject>

<!--
USAGE
=====

This template scaffolds a (b) decision-node dual-review artifact per:
- Harness rule 3(b): 决策节点 / plan-prior — 推翻已过 dual 的 plan 前提 /
  切路径 / 拒绝一条方案 → plan-prior review.
- AGENTS.md "Dual Artifact Header Annotation Rule"
- .claude/skills/codex-orchestration/SKILL.md §1 + §"Account Dispatch Priority"

(b) DIFFERS FROM (a) IN SCOPE:
- (a) reviews a *new* plan / contract / framing decision before its first run.
- (b) reviews a *path-switch / rejection / overruling* of a prior dual-passed
  plan: e.g. user wants to flip §A to path B, kill experiment X, waive a
  pre-registered gate, or treat a prior verdict as superseded.

PRE-WRITING CHECKLIST
- [ ] Codex (reviewer) has independently read the prior dual-passed plan +
      its current state + the proposed change, with file:line citations.
      Pre-digested summary dispatch is NOT acceptable.
- [ ] Pre-review independence: write local findings to
      `/tmp/claude_pre_review_<short-id>.md` before reading reviewer output.
- [ ] Run `scripts/codex_session_meta.sh <threadId>` and paste its 5-line
      stdout verbatim into the Header annotation block below.
- [ ] Cite the prior dual-passed plan's commit hash + verdict (the thing
      being overruled).

REPLACE every `<placeholder>` and remove this comment block before commit.
-->

## Header annotation (verbatim from `scripts/codex_session_meta.sh`)

```
<paste 5-line helper stdout here>
```

> Source disambiguation: see `session_path` line above.

## Decision under review

- **What is being changed**: `<one-sentence description of the path switch / rejection / waiver>`
- **Prior dual-passed plan being overruled**: `<path:line>` at commit `<hash>` (verdict: `<NO_BLOCKERS / REVISE_THEN_FREEZE / ...>`)
- **Trigger of this (b) review**: `<user instruction | new evidence | impl-revealed defect | external constraint>`
- **Authority for the proposed change**: `<user explicit ... | new artifact ... | scope-shift amendment ...>`

## Pre-review independence

- Local pre-review note: `</tmp/claude_pre_review_<short-id>.md>`
- Second reviewer model + threadId: `<model>` (`<threadId>`)
- Both reviewers read primary sources independently? **<yes / no — explain>**

## Track + comparability scope

- Track: `<B | governance | skills | docs | infra | outputs>`
- Comparability-critical touched: `<no | yes — list affected runs>`
- Affected frozen artifacts: `<list any frozen contracts whose validity depends on the prior plan>`

## Verdict

**<APPROVE_PATH_SWITCH | REJECT_KEEP_CURRENT | CONDITIONAL_APPROVE_WITH_FIXES | STOP_NEEDS_AMENDMENT>**

One-paragraph verdict statement:

<text>

## Path comparison

### Path A — current (the prior dual-passed plan)

- Strengths: `<...>`
- Weaknesses revealed since prior dual: `<...>`
- Sunk-cost considerations: `<...>`

### Path B — proposed switch

- Strengths: `<...>`
- Weaknesses / risks: `<...>`
- New evidence supporting path B: `<file:line / artifact:key citations>`

### Cost of switch

- Comparability impact: `<...>`
- Throwaway artifacts: `<list runs / readouts that become superseded>`
- Re-execution requirements: `<list contracts that need re-run>`

## Per-axis findings

| # | Axis | Path A result | Path B prediction | Verdict (`PREFER_A | PREFER_B | TIE`) |
|---|------|---------------|-------------------|----------------------------------------|
| 1 | <axis> | `<...>` | `<...>` | `<...>` |
| 2 | ... | ... | ... | ... |

## Independent factual claims verified

| Claim | Evidence (file:line / artifact:key) |
|-------|-------------------------------------|
| `<claim>` | `<source>` |

## Pre-blessed conditions for path-switch approval

If verdict is `CONDITIONAL_APPROVE_WITH_FIXES`, list conditions that must be met before path B can proceed:

1. `<condition 1>` — at `<file:line>` or `<deliverable>`
2. ...

## Disposition / next step

- [ ] User authorization needed for path switch? `<yes — what authority>` / `<no>`
- [ ] Subsequent (a) plan-prior review needed for the new path? `<yes / no — justification>`
- [ ] Worklog + topical doc amendment needed? `<yes — which docs>` / `<no>`
- [ ] Comparability declaration in worklog? `<must include comparability_impact field per AGENTS.md>`

## Archival metadata

- Run dir: `outputs/reports/<experiment_name>/run_YYYYMMDD_<descriptor>/`
- Companion archive: `dual_packet_archive_b/` (if any)
- Commit hash that introduces this artifact: `<filled at commit time>`
- Prior plan commit being overruled: `<hash>`

---

*End (b) decision-node dual review artifact. Path B may not proceed until this artifact is committed AND user authorization is recorded (per scope-shift amendment pattern).*
