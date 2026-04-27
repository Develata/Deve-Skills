# MJ-skill

Personal Claude Code skills collection, synced from local development environment.

## Skills

| Skill | Description | Key Features |
|-------|-------------|-------------|
| **artifact-grounded-review** | Enforces that both Claude and Codex must read actual code and result artifacts before any dual analysis — not just scoring, but any collaborative analytical task. | Staleness check (mtime vs git), enforced independent reading order, scoring + non-scoring output templates |
| **codex-account-switching** | Multi-account Codex MCP isolation for Claude Desktop / CLI. Use when multiple OpenAI API keys need to coexist on the same machine. | Portable paths, helper scripts, account removal/upgrade docs, failure mode table |
| **codex-orchestration** | Claude + Codex MCP collaboration framework. Covers call methods, role assignment, efficiency rules, cost routing, and task templates. | Multi-account tool mapping, **Account Dispatch Priority** (main→b→c routing with fallback triggers + exemptions, §1), **Model verification oracle** (helper-driven `session_path` provenance, hallucinated-slug guard, §1), **Reasoning effort tier** (low\|medium\|high\|xhigh, §4), **Parallel dispatch threshold** (≥3 concurrent calls flood the approval queue, §3), iterative retrieval protocol, session lifecycle, Two-File Handoff (authoritative source), approval-policy=never (codex-internal scope only — does not bypass Claude Code's outer MCP allow/deny), **three-level literature triage + PDF admission gate** (§8), **divergent-strict-decisive dispatch** for open-ended technical decisions (§9), **long-running task discipline** via TaskCreate chains (§10). Ships with `scripts/codex_session_meta.sh` + 3 boundary-specific dual-artifact templates under `templates/(a\|b\|c)_*_template.md`. |
| **context-first-exploration** | Forces Claude to build a context map before writing or modifying code. Prevents the "read too little, act too fast" failure mode in medium-to-large repos. | Two-phase protocol (read → execute), existing implementation check, enforcement gates, mandatory reads, context hygiene (compact rules), architecture map staleness detection |
| **dual-agent-original-request-review** | Ensures both executor and reviewer work directly from the same raw user request, avoiding paraphrase drift. | Verdict-affecting claims audit, verification dedup, B→A misclassification guard, tiered convergence cap, stuck detection & recovery, experience distillation |
| **write-research-readout** *(project-scoped: Research1 / BYSJ Path B)* | Produce presentation-grade markdown readouts for research deliverables — formula-first, symbol-tabled, artifact-cited prose with side-by-side `(c) 独立复现` columns and axis-structured amendments. Never function-name dumps or code blocks for what should be math. | 13 style fingerprints derived from a canonical group-meeting deck exemplar: 符号表 → 公式化方法 → named acceptance criteria with multi-version status columns → Defect-history blockquotes with mathematical falsification → sub-step recipes with anti-confusion annotations → math-incompatibility proofs for retracted gates → axis-structured amendments with N-way sub-frame categorization → ASCII timeline + 顺序路径 blocks → comparability-neutral vs 已主动避开 risk pairing → Claim-evolution comparison tables → preempt-actual-critique Q&A → two-block 附录 with commit + artifact + ASCII schema. **The mandatory `(c) 独立复现` column on every empirical number writes dual-review boundary (c) into the readout itself**, so a paper-facing claim cannot enter a deck without the second-reviewer rerun number alongside. **Reusable on other projects only after substituting the workspace-specific harness rules and exemplar references.** |
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
        ├── write-research-readout     (deliverable layer — consumes (c) discipline as
        │                               a `(c) 独立复现` column requirement; project-scoped)
        │
superpowers (global)                   (brainstorming, planning, TDD, debugging — nested inside dual-agent)
```

- `context-first-exploration` is the pre-condition: build a context map before writing any code. Works for both Claude-solo and Claude+Codex workflows.
- `dual-agent` defines the overall collaboration process (checklist, dispatch, review, convergence, stuck detection, experience distillation).
- `codex-orchestration` owns the authoritative Two-File Handoff protocol and iterative retrieval; `dual-agent` references it.
- `artifact-grounded-review` adds the "read primary sources before concluding" discipline on top.
- `codex-account-switching` is the infrastructure layer for multi-account routing.
- `write-research-readout` is the **deliverable / output-formatting layer**, downstream of the analytical stack. It does not change the dual-agent or artifact-grounded protocols — it codifies how their outputs become 汇报 markdown, and structurally enforces the boundary-(c) discipline on the deck itself rather than delegating to commit-body caveats. Project-scoped (Research1 / BYSJ Path B).
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

For the full collaboration framework, install the **five generic methodology skills** together (`artifact-grounded-review`, `codex-account-switching`, `codex-orchestration`, `context-first-exploration`, `dual-agent-original-request-review`) — they cross-reference each other. Also add an Architecture Map and Mandatory Reads table to a `docs/architecture-map.md` file, referenced from your `CLAUDE.md` (see `context-first-exploration` skill for the expected format).

**Project-scoped skills** (currently: `write-research-readout`) are kept in this collection for provenance and cross-machine portability, but they encode the conventions of one specific workspace (Research1 / BYSJ Path B PINN / LEAP-1A QAR). To reuse on a different project, fork the SKILL.md and substitute (a) the project-frame harness rules referenced in its body, (b) the canonical exemplar paths (`presentation_4.27/...`, `presentation_4.23/...`), and (c) the deliverable file-location convention. The 13 style fingerprints themselves are project-agnostic and transfer directly.

## License

MIT
