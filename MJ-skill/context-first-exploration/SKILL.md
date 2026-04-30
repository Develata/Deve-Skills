---
name: context-first-exploration
description: Encourages Claude to build a context map before writing or modifying code. Counters the "read too little, act too fast" failure mode common in medium-to-large repos.
---

# Context-First Exploration Protocol

This skill describes a default working pattern, not enforced gates. Hardness lives in the harness `UserPromptSubmit` hook (rule 1, soft and reducible). Skill content guides; harness gates.

## Problem this solves

When Claude works directly (not delegating to Codex), it tends to:
1. Grab the first few "most relevant looking" files and start coding immediately.
2. Miss critical call chains, configs, or tests that would change the approach.
3. Produce changes that break unseen dependencies or duplicate existing logic.

Worst when: the repo is large, naming is non-obvious, the task spans modules, or experiment outputs vary across runs.

## When to use

- **Default trigger**: tasks that modify code or analyze results across more than one file, when Claude hasn't read the relevant module yet.
- **Skip without going through Phase 1** (no Phase 1 needed):
  - single-file edits where the user named the file
  - pure Q&A and clarification questions
  - governance-meta-doc tweaks (this skill itself, hooks, settings.json, CLAUDE.md / AGENTS.md prose)
  - trivial formatting / typo fixes
  - **strict single-file probes** — exactly one new script, no new outputs subdirectory, imports only from modules already read in this conversation, ≤ ~100 lines
- **Not Skip — Phase 1 still applies**, even if the user or I call it a "probe":
  - new analytical script that imports ≥3 production modules
  - new analytical script that creates a new outputs subdirectory
  - new script ≥150 lines
  - cross-flight / cross-cohort / cross-seed analytical pipeline that depends on more than one production helper file

  Rule of thumb: if the script reuses production helpers across modules and writes a new outputs tree, treat it as cross-file analysis, not a "daily probe".
- **Always reducible**: when the user says `quick` / `直接做` / `skip context`, Phase 1 collapses to a one-sentence declaration.

## Core pattern: Two phases (preferred default)

Non-trivial tasks default to a two-phase split: Phase 1 (read-only context map) before Phase 2 (execute). This is the preferred working pattern, not an unconditional gate — when the task fits a Skip case above, Phase 1 collapses or is dropped, and the rest of this skill describes what Phase 1 looks like *when* it runs.

### Phase 1: Context Map (read-only, no edits)

Steps:

1. **Existing implementation check** — before writing anything new, search the repo for existing implementations of the same or similar functionality. Use Grep with function/class names, keywords, and synonyms. If an existing implementation is found, the task may become "modify existing" instead of "create new." Prevents duplicate logic — a top failure mode in repos with 100+ files.
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

6. **Complete mandatory reads** — if CLAUDE.md § Mandatory Reads maps the task type to specific files, every listed file should appear in the "Files read" table before Phase 2 begins.

### Phase 2: Execute (write code, run commands)

After Phase 1 is complete:
- Proceed with the implementation, fix, or analysis.
- Every code change should reference a file from the Phase 1 context map. If Claude needs to touch a file not in the map, read that file first and update the map.
- The final report includes the context map as an appendix.

## Self-check signals

These are signals to slow down, not blocked gates. Skill text can't actually enforce — it can only orient. The harness hook (rule 1) is the actual escalation layer when these defaults are repeatedly skipped.

| Signal | Condition | Recommended response |
|---|---|---|
| **Existing impl** | Searched for existing implementations before creating new ones? | If no, search now; report any existing impl to user before duplicating. |
| **File count** | Phase 1 lists ≥3 files read for non-trivial tasks? | If <3, likely missing context — extend Phase 1 before continuing. |
| **Call chain** | At least one call chain traced? | If no, trace one before Phase 2. |
| **Mandatory reads** | All files from CLAUDE.md § Mandatory Reads checked? | If no, finish them before Phase 2. |
| **Unconfirmed items** | "Not yet confirmed" items that could change the approach? | Resolve those before committing to direction. |
| **Edit scope** | Every Phase 2 edit lands on a file already in the map? | If editing outside the map, read the file and update the map first. |
| **Doc sync** | Phase 2 created/deleted files, changed imports, or altered call chains? | Update `docs/architecture-map.md` in the same commit. |

### Doc sync verdict (default discipline)

Before each `git commit`, emit a one-line Doc sync verdict in the conversation — even when the gate doesn't trigger. Visibility lets the user audit and prevents silent skip.

- **Triggered**: `"Doc sync: triggered — <reason>. Updating architecture-map.md."` → update the map in the same commit.
- **Not triggered**: `"Doc sync: not triggered — <reason>."` (e.g., "only docs/outputs changed, no src file count / import / call-chain changes.")

## Evidence standard

In both phases:
- **Cite file paths** for every factual claim about the codebase.
- **Mark assumptions** explicitly: "I haven't confirmed X; assuming Y based on naming convention."
- **Avoid** "the code probably does X" without citing the specific file and line.
- Aligns with verification discipline in `dual-agent-original-request-review/SKILL.md`.

## Integration with Codex delegation

When Claude delegates to Codex after Phase 1:
- Phase 1's context map becomes the `Scope` field in the Two-File handoff (see `codex-orchestration/SKILL.md` § 3).
- If Phase 1 couldn't determine all relevant files, use the Iterative Retrieval Protocol (`codex-orchestration/SKILL.md` § 6) for Codex's discovery round.
- Codex inherits the mandatory reads list — it should also read those files before executing.

## Architecture map staleness detection

During Phase 1, if the actual codebase disagrees with `docs/architecture-map.md`:
- A module listed in the map no longer exists, or a new module exists that is not listed.
- A key file listed for a module has been renamed, moved, or deleted.
- The call chain described in the map no longer matches the actual import/call structure.

Response:
1. **Flag the discrepancy** in the context report: "Architecture Map drift detected: [specific mismatch]."
2. **Use the actual code as ground truth** — don't follow the map over reality.
3. **Suggest a map update** to the user at the end of the task (don't silently fix it).

Prevents the map from becoming a misleading artifact that causes Claude to skip real files or read phantom ones.

## Context hygiene

Long sessions degrade Claude's output quality. These defaults reduce context overflow and help key information survive compaction.

### When to compact

Suggest `/compact` at these **phase boundaries** (not mid-phase):
- After Phase 1 completes, before Phase 2 begins (research done, ready to execute).
- After a major implementation subtask completes, before starting the next.
- After a failed approach is abandoned, before trying an alternative.
- When TodoWrite shows 3+ completed items and context feels sluggish.

**Avoid compacting** in the middle of: an active debugging trace, a partially written function, or an unfinished code review.

### What survives vs. what is lost after `/compact`

| Survives | Lost |
|---|---|
| CLAUDE.md instructions | Previously-read file contents |
| TodoWrite task list | Intermediate reasoning and analysis |
| On-disk files and git state | Tool call history |
| Memory files | Context map from Phase 1 |

### Post-compact recovery

After `/compact`:
1. Re-read the context map if it was produced in Phase 1 (it was lost). If the map wasn't saved to a file, rebuild it from the TodoWrite task list and `docs/architecture-map.md`.
2. Re-read any file about to be edited (don't rely on pre-compact memory).
3. State explicitly: "Post-compact: re-read X files to restore working context."

### Token budget awareness

- If a Phase 1 context map exceeds 8 files, consider saving it to `/tmp/context_map_<ID>.md` so it can be re-read after compact instead of rebuilt.
- Prefer `Read` with specific line ranges over full-file reads to conserve tokens.
- When delegating to Codex, use the Two-File handoff (offloads context to disk) rather than inlining everything in the prompt.

## Quick-mode override

When the user says `quick` / `直接做` / `skip context`:
- Phase 1 collapses to a single sentence: "Editing X based on user instruction, skipping full context map."
- Phase 2 proceeds immediately.
- The final report notes: "Context map was skipped per user request."

## Anti-patterns

- Reading one file and immediately starting to code ("I see the function, let me fix it").
- Listing files in the context map that were not actually read (padding the list).
- Saying "based on the project structure, I assume..." without reading the actual file.
- Skipping tests and configs during Phase 1 ("I only need the source code").
- Producing a context map but ignoring it during Phase 2 (editing files not in the map).
- Running Phase 1 on the entire repo instead of the relevant module subtree.
