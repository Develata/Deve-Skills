# `_harness/` — 把两个 skill 变成项目默认工作模式

这里是一个 **Claude Code UserPromptSubmit hook 示例**，用于把 `artifact-grounded-review` + `context-first-exploration` 强制成某个项目的默认工作模式（non-opt-in）。适用于你希望 Claude 在**每一次对话输入**时都被提醒遵守这两个 skill 的项目。

## 它做了什么

Claude 自己偶尔会忘记加载这两个 skill（尤其任务看起来"显然简单"时）。这个 hook 在每次用户提交 prompt 时由 harness（而非 Claude）注入一段硬性规则，Claude 无法绕过。

- `settings.json` — 注册 `UserPromptSubmit` hook
- `enforce_default_skills.sh` — 输出 `hookSpecificOutput.additionalContext`，内容是两个 skill 的默认启用声明 + 逃生口（`quick` / `直接做` / `skip context`）

## 启用方法

1. 确认你的项目里已有这两个 skill（`MJ-skill/artifact-grounded-review/` 和 `MJ-skill/context-first-exploration/`，或放在 `.claude/skills/` 下）。
2. 把本目录两个文件拷到项目的 `.claude/` 下：
   ```
   your-project/
   └── .claude/
       ├── settings.json             ← 来自本目录
       └── hooks/
           └── enforce_default_skills.sh ← 来自本目录
   ```
3. 确保脚本可执行：`chmod +x .claude/hooks/enforce_default_skills.sh`
4. 重启 Claude Code session。下一次提交 prompt 时应看到注入的 `[项目名 硬性规则 — harness 注入]` 文本。

## 路径注意

`settings.json` 里用 `"$CLAUDE_PROJECT_DIR"` 引用项目根，这是 Claude Code 运行 hook 时自动注入的环境变量，任何机器上都能用。**不要改成绝对路径**，否则别人 clone 你的项目后 hook 会找不到脚本。

## 定制

- 改 `enforce_default_skills.sh` 里的 `additionalContext` 文本，把项目名、规则内容换成你自己的。
- 改 skill 名字指向你真正要强制的 skill。
- 想给某类 prompt 例外：改 hook 的 `matcher` 正则。
