# MJ-skill

Personal Claude Code skills collection, synced from local development environment.

## Skills

| Skill | Description |
|-------|-------------|
| **artifact-grounded-review** | Enforces that both Claude and Codex must read actual code and result artifacts before giving evaluation scores. Prevents score inflation from summary-based prompts. |
| **codex-account-switching** | Multi-account Codex MCP isolation for Claude Desktop / CLI. Use when multiple OpenAI API keys need to coexist on the same machine. |
| **codex-orchestration** | Claude + Codex MCP collaboration framework. Covers call methods, role assignment, efficiency rules, cost routing, and task templates. |
| **dual-agent-original-request-review** | Ensures both executor and reviewer work directly from the same raw user request, avoiding paraphrase drift. |
| **superpowers** | Full-featured skill suite including brainstorming, plan writing, TDD, systematic debugging, subagent-driven development, code review, and more. |

## Usage

Copy the desired skill folder into your project's `.claude/skills/` directory (project-level) or `~/.claude/skills/` (global-level), then reference it in your `CLAUDE.md`.

## License

MIT
