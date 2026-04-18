#!/bin/bash
# Enforces artifact-grounded-review + context-first-exploration as hard-default
# working modes for the journal_paper project. Called by UserPromptSubmit hook
# registered in .claude/settings.json. Output JSON per hookSpecificOutput schema.
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "[journal_paper 硬性规则 — harness 注入，非 Claude 自觉]\n本项目将 `artifact-grounded-review` + `context-first-exploration` 设为**默认工作模式**（非条件触发）。任何涉及代码修改 / 跨文件分析 / dual-agent 评审的任务：\n1. **Context-first**：动手前显式产出 Phase 1 context map（≥3 文件 + call chain + mandatory reads），完整遵守 .claude/skills/context-first-exploration/SKILL.md 的 gate 表（File count / Call chain / Edit scope / Doc sync）。\n2. **Artifact-grounded**：dual-agent 分析前，executor + reviewer 均需读 primary source（源码 + artifact）后才形成结论；claim 必须 cite file:line 或 artifact:key；禁止 pre-digested summary dispatch。\n跳过 gate = 流程未完成，即便任务看起来 trivial。\n唯一逃生口：用户明示 `quick` / `直接做` / `skip context` → Phase 1 降级为一句话声明。"
  }
}
EOF
