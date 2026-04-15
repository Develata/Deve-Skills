---
name: context-first-exploration
description: Forces Claude to build a context map before writing or modifying code. Prevents the "read too little, act too fast" failure mode common in medium-to-large repos.
---

# Context-First Exploration Protocol

## Problem this solves

When Claude works directly (not delegating to Codex), it tends to:
1. Grab the first few "most relevant looking" files and start coding immediately.
2. Miss critical call chains, configs, or tests that would change the approach.
3. Produce changes that break unseen dependencies or duplicate existing logic.

This is worst when: the repo is large, naming is non-obvious, the task spans modules, or experiment outputs vary across runs.

## When to use

- **Always** when the task involves modifying code or analyzing results across more than one file.
- **Always** when Claude hasn't read the relevant module in this conversation yet.
- **Skip** only for: single-file edits where the user has explicitly named the file, pure Q&A, or trivial formatting.

## Core Rule: Two Phases, No Shortcut

Every non-trivial task is split into two mandatory phases. Claude must not start Phase 2 until Phase 1 is explicitly complete.

### Phase 1: Context Map (read-only, no edits)

Claude must:

1. **Existing implementation check** — before writing anything new, search the repo for existing implementations of the same or similar functionality. Use Grep with function/class names, keywords, and synonyms. If an existing implementation is found, the task may become "modify existing" instead of "create new." This prevents duplicate logic — a top failure mode in repos with 100+ files.
2. **Search broadly** — use Grep/Glob/Read to find relevant files. Start from the module map in `docs/architecture-map.md` (referenced by CLAUDE.md) if available.
3. **Read the call chain** — trace from entry point through core logic to output. Don't stop at the first file that "looks right."
4. **Check configs and tests** — read related config files and test files. Tests often reveal edge cases and invariants that source code doesn't make obvious.
5. **Produce a context report** before proceeding:

```
## Context Map

### Files read (with reason)
| # | File | Why relevant |
|---|------|-------------|
| 1 | path/to/entry.py | Entry point for the feature |
| 2 | path/to/core.py | Core logic called by entry |
| ... | ... | ... |

### Call chain
entry.py:main() → core.py:process() → utils.py:transform()

### Key invariants discovered
- [invariant 1 — from test or comment]
- [invariant 2]

### Not yet confirmed
- [ ] Whether X config affects this path
- [ ] Whether test Y covers the edge case

### Mandatory reads from CLAUDE.md (if applicable)
- [x] file_a.py (read)
- [x] file_b.py (read)
- [ ] file_c.py (not yet read — will read before Phase 2)
```

6. **Complete all mandatory reads** — if CLAUDE.md § Mandatory Reads maps the task type to specific files, every listed file must appear in the "Files read" table before Phase 2 begins.

### Phase 2: Execute (write code, run commands)

Only after Phase 1 is complete:
- Proceed with the implementation, fix, or analysis.
- Every code change must reference a file from the Phase 1 context map. If Claude needs to touch a file not in the map, it must first read that file and update the map.
- The final report must include the context map as an appendix.

## Enforcement Mechanism

Claude checks itself against these gates:

| Gate | Condition | Fail action |
|------|-----------|-------------|
| **Existing impl** | Must search for existing implementations before creating new ones | Report existing impl to user; do not duplicate |
| **File count** | Phase 1 must list ≥ 3 files read (non-trivial tasks) | Cannot proceed to Phase 2 |
| **Call chain** | At least one call chain must be traced | Cannot proceed to Phase 2 |
| **Mandatory reads** | All files from CLAUDE.md § Mandatory Reads for this task type must be checked | Cannot proceed to Phase 2 |
| **Unconfirmed items** | If any "not yet confirmed" item could change the approach, read it first | Cannot proceed to Phase 2 |
| **Edit scope** | Every file edited in Phase 2 must appear in the Phase 1 map | Must read the file and update map before editing |
| **Doc sync** | If Phase 2 created/deleted files, changed import paths, or altered call chains → `docs/architecture-map.md` must be updated in the same commit | Cannot commit until map is updated |

### Doc sync gate protocol

Before **every** `git commit`, Claude must emit a one-line Doc sync verdict in the conversation. This is mandatory even when the gate does not trigger.

- **Triggered**: `"Doc sync: triggered — <reason>. Updating architecture-map.md."` → update the map in the same commit.
- **Not triggered**: `"Doc sync: not triggered — <reason>."` (e.g., "only docs/outputs changed, no src file count/import/call chain changes.")

Omitting the verdict line is itself a gate failure. The purpose is to make the check visible so the user can audit it and so Claude cannot silently skip it.

## Evidence Standard

In both phases, Claude must:
- **Cite file paths** for every factual claim about the codebase.
- **Mark assumptions** explicitly: "I haven't confirmed X; assuming Y based on naming convention."
- **Never say** "the code probably does X" without citing the specific file and line.
- This aligns with the verification discipline in `dual-agent-original-request-review/SKILL.md`.

## Integration with Codex Delegation

When Claude delegates to Codex after Phase 1:
- Phase 1's context map becomes the `Scope` field in the Two-File Handoff (see `codex-orchestration/SKILL.md` § 3).
- If Phase 1 couldn't determine all relevant files, use the Iterative Retrieval Protocol (`codex-orchestration/SKILL.md` § 6) for Codex's discovery round.
- Codex inherits the mandatory reads list — it must also read those files before executing.

## Architecture Map Staleness Detection

During Phase 1, if Claude discovers that the actual codebase disagrees with the Architecture Map in `docs/architecture-map.md`:
- A module listed in the map no longer exists, or a new module exists that is not listed.
- A key file listed for a module has been renamed, moved, or deleted.
- The call chain described in the map no longer matches the actual import/call structure.

Then Claude must:
1. **Flag the discrepancy** in the context report: "Architecture Map drift detected: [specific mismatch]."
2. **Use the actual code as ground truth** — never follow the map over reality.
3. **Suggest a map update** to the user at the end of the task (do not silently fix it).

This prevents the map from becoming a misleading artifact that causes Claude to skip real files or read phantom ones.

## Context Hygiene

Long sessions degrade Claude's output quality. These rules prevent context overflow and ensure key information survives compaction.

### When to compact

Suggest `/compact` at these **phase boundaries** (not mid-phase):
- After Phase 1 completes, before Phase 2 begins (research done, ready to execute)
- After a major implementation subtask completes, before starting the next
- After a failed approach is abandoned, before trying an alternative
- When TodoWrite shows 3+ completed items and context feels sluggish

**Never compact** in the middle of: an active debugging trace, a partially written function, or an unfinished code review.

### What survives vs. what is lost after `/compact`

| Survives | Lost |
|----------|------|
| CLAUDE.md instructions | Previously-read file contents |
| TodoWrite task list | Intermediate reasoning and analysis |
| On-disk files and git state | Tool call history |
| Memory files | Context map from Phase 1 |

### Post-compact recovery rule

After `/compact`, Claude must:
1. Re-read the context map if it was produced in Phase 1 (it was lost). If the map was not saved to a file, rebuild it from the TodoWrite task list and `docs/architecture-map.md`.
2. Re-read any file that is about to be edited (do not rely on pre-compact memory of its contents).
3. State explicitly: "Post-compact: re-read X files to restore working context."

### Token budget awareness

- If a Phase 1 context map exceeds 8 files, consider saving it to `/tmp/context_map_<ID>.md` so it can be re-read after compact instead of rebuilt.
- Prefer `Read` with specific line ranges over full-file reads to conserve tokens.
- When delegating to Codex, use the Two-File Handoff (which offloads context to disk) rather than inlining everything in the prompt.

## Quick-Mode Override

When the user says `quick` / `直接做` / `skip context`:
- Phase 1 is reduced to a single sentence: "Editing X based on user instruction, skipping full context map."
- Phase 2 proceeds immediately.
- The final report must note: "Context map was skipped per user request."

## Anti-Patterns

- Reading one file and immediately starting to code ("I see the function, let me fix it").
- Listing files in the context map that were not actually read (padding the list).
- Saying "based on the project structure, I assume..." without reading the actual file.
- Skipping tests and configs during Phase 1 ("I only need the source code").
- Producing a context map but ignoring it during Phase 2 (editing files not in the map).
- Running Phase 1 on the entire repo instead of the relevant module subtree.
