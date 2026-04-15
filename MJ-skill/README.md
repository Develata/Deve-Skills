# MJ-skill

Personal Claude Code skills collection, synced from local development environment.

## Skills

| Skill | Description | Key Features |
|-------|-------------|-------------|
| **artifact-grounded-review** | Enforces that both Claude and Codex must read actual code and result artifacts before any dual analysis — not just scoring, but any collaborative analytical task. | Staleness check (mtime vs git), enforced independent reading order, scoring + non-scoring output templates |
| **codex-account-switching** | Multi-account Codex MCP isolation for Claude Desktop / CLI. Use when multiple OpenAI API keys need to coexist on the same machine. | Portable paths, helper scripts, account removal/upgrade docs, failure mode table |
| **codex-orchestration** | Claude + Codex MCP collaboration framework. Covers call methods, role assignment, efficiency rules, cost routing, and task templates. | Multi-account tool mapping, iterative retrieval protocol, session lifecycle, Two-File Handoff (authoritative source), approval-policy=never, **three-level literature triage + PDF admission gate** (§8), **divergent-strict-decisive dispatch** for open-ended technical decisions (§9), **long-running task discipline** via TaskCreate chains (§10) |
| **context-first-exploration** | Forces Claude to build a context map before writing or modifying code. Prevents the "read too little, act too fast" failure mode in medium-to-large repos. | Two-phase protocol (read → execute), existing implementation check, enforcement gates, mandatory reads, context hygiene (compact rules), architecture map staleness detection |
| **dual-agent-original-request-review** | Ensures both executor and reviewer work directly from the same raw user request, avoiding paraphrase drift. | Verdict-affecting claims audit, verification dedup, B→A misclassification guard, tiered convergence cap, stuck detection & recovery, experience distillation |
| **superpowers** | Full-featured skill suite including brainstorming, plan writing, TDD, systematic debugging, subagent-driven development, code review, and more. | Third-party skill (not custom-written) — see Superpowers Compatibility below |

## How Skills Connect

```
context-first-exploration              (Phase 1: read → Phase 2: execute)
  │
dual-agent-original-request-review     (top-level dual-agent workflow)
  ├── codex-orchestration              (Codex API, Two-File Handoff, iterative retrieval, session mgmt)
  │     └── codex-account-switching    (multi-account isolation layer)
  └── artifact-grounded-review         (read-before-conclude rule for all analytical tasks)
        │
superpowers (global)                   (brainstorming, planning, TDD, debugging — nested inside dual-agent)
```

- `context-first-exploration` is the pre-condition: build a context map before writing any code. Works for both Claude-solo and Claude+Codex workflows.
- `dual-agent` defines the overall collaboration process (checklist, dispatch, review, convergence, stuck detection, experience distillation).
- `codex-orchestration` owns the authoritative Two-File Handoff protocol and iterative retrieval; `dual-agent` references it.
- `artifact-grounded-review` adds the "read primary sources before concluding" discipline on top.
- `codex-account-switching` is the infrastructure layer for multi-account routing.
- `superpowers` is nested **inside** the dual-agent planning phase, not alongside it.

## Superpowers Compatibility

When using this skill set alongside superpowers, some skills overlap or conflict. Resolution rules (defined in CLAUDE.md §1c):

| Superpowers skill | Status | Notes |
|-------------------|--------|-------|
| `brainstorming` | ✅ Use | Fills a gap — no equivalent in MJ-skill |
| `writing-plans` | ✅ Use | Complements dual-agent checklist with detailed plan docs |
| `using-git-worktrees` | ✅ Use | No equivalent in MJ-skill |
| `writing-skills` | ✅ Use | Useful when creating new skills |
| `finishing-a-development-branch` | ✅ Use | No equivalent in MJ-skill |
| `TDD` | ✅ Use | Include in Codex executor task packet when relevant |
| `systematic-debugging` | ✅ Use | Complementary with MJ-skill's Stuck Detection (technical bugs vs agent-level stuck) |
| `verification-before-completion` | ⚠️ Use with override | MJ-skill's `artifact-grounded-review` takes precedence for evidence standard (file:line + verdict audit) |
| `requesting/receiving-code-review` | ⚠️ Skip in dual-agent mode | MJ-skill's review protocol is more complete; use only in single-agent mode |
| `dispatching-parallel-agents` | ⚠️ MJ-skill preferred | `codex-orchestration` is better suited for Codex MCP parallel calls |
| **`subagent-driven-development`** | ❌ Disabled | Conflicts with Codex MCP execution path — would cause double dispatch |
| **`executing-plans`** | ❌ Disabled | Same conflict — dispatches Claude sub-agents instead of Codex |

## Design References

Key features were informed by practices from high-star repos:

| Feature | Inspired by |
|---------|------------|
| Existing implementation check | [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) (128K★) `search-first` |
| Architecture map + mandatory reads | [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) (38.7K★) |
| Architecture map staleness detection | [Understand-Anything](https://github.com/Lum1104/Understand-Anything) (8.2K★) |
| CLAUDE.md slim-down / progressive disclosure | [HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md) + [builder.io](https://www.builder.io/blog/claude-md-guide) |
| Context hygiene / compact rules | ECC `strategic-compact` |
| Stuck detection | ECC `agent-introspection-debugging` |
| Experience distillation | ECC `rules-distill` |
| Iterative retrieval | ECC `iterative-retrieval` |
| Literature triage (TeX-first, abstract+intro only) + PDF admission gate + divergent-strict-decisive dispatch structure | [linux.do: AI 科研不完全指北 (TOP10 PhD)](https://linux.do/t/topic/1969598) — structural methodology kept; author's Gemini-as-third-agent recommendation rejected after empirical test (0/5 CrossRef match vs Codex 5/5 on journal lit-scout, 2026-04-16) |

## Usage

Copy the desired skill folder into your project's `.claude/skills/` directory (project-level) or `~/.claude/skills/` (global-level), then reference it in your `CLAUDE.md`.

For the full collaboration framework, install all five custom skills together — they cross-reference each other. Also add an Architecture Map and Mandatory Reads table to a `docs/architecture-map.md` file, referenced from your `CLAUDE.md` (see `context-first-exploration` skill for the expected format).

## License

MIT
