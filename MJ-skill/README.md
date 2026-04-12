# MJ-skill

Personal Claude Code skills collection, synced from local development environment.

## Skills

| Skill | Description | Key Features |
|-------|-------------|-------------|
| **artifact-grounded-review** | Enforces that both Claude and Codex must read actual code and result artifacts before any dual analysis — not just scoring, but any collaborative analytical task. | Staleness check (mtime vs git), enforced independent reading order, scoring + non-scoring output templates |
| **codex-account-switching** | Multi-account Codex MCP isolation for Claude Desktop / CLI. Use when multiple OpenAI API keys need to coexist on the same machine. | Portable paths, helper scripts, account removal/upgrade docs, failure mode table |
| **codex-orchestration** | Claude + Codex MCP collaboration framework. Covers call methods, role assignment, efficiency rules, cost routing, and task templates. | Multi-account tool mapping, fallback protocol, session lifecycle, Two-File Handoff (authoritative source) |
| **dual-agent-original-request-review** | Ensures both executor and reviewer work directly from the same raw user request, avoiding paraphrase drift. | Verdict-affecting claims audit, verification dedup, B→A misclassification guard, tiered convergence cap |
| **superpowers** | Full-featured skill suite including brainstorming, plan writing, TDD, systematic debugging, subagent-driven development, code review, and more. | Third-party skill (not custom-written) |

## How Skills Connect

```
dual-agent-original-request-review   (top-level workflow)
  ├── codex-orchestration            (Codex API, Two-File Handoff, fallback, session mgmt)
  │     └── codex-account-switching  (multi-account isolation layer)
  └── artifact-grounded-review       (read-before-conclude rule for all analytical tasks)
```

- `dual-agent` defines the overall collaboration process (checklist, dispatch, review, convergence).
- `codex-orchestration` owns the authoritative Two-File Handoff protocol; `dual-agent` references it.
- `artifact-grounded-review` adds the "read primary sources before concluding" discipline on top.
- `codex-account-switching` is the infrastructure layer for multi-account routing.

## Usage

Copy the desired skill folder into your project's `.claude/skills/` directory (project-level) or `~/.claude/skills/` (global-level), then reference it in your `CLAUDE.md`.

For the full collaboration framework, install all four custom skills together — they cross-reference each other.

## License

MIT
