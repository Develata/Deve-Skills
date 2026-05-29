---
name: artifact-grounded-review
description: Enforces that Claude (and Codex when applicable) must read actual code and artifacts before any claim — covers both REVIEW tasks (dual analysis) and AUTHORING tasks (writing briefs / specs that reference code state).
---

# Artifact-Grounded Authoring + Dual-Analysis Protocol

## Scope

This protocol applies to **two complementary task families**:

### A. Authoring + user-facing analysis (brief / spec / RFC / analysis answer / explanation / verdict / progress update)

Any user-facing or artifact-persisted text that makes a claim about current code / data / manifest / artifact state:
- "Module X currently does Y" / "no code change to Z" / "builder is no-code-change"
- Threshold references ("existing gate is p > 0.01")
- API / schema assumptions ("Component-C outputs envelope with 6 fields")
- Manifest distribution assumptions ("180 unique sources" / "~9k windows")
- Call-order / data-flow assumptions ("generator emits length-bounded trajectory")
- **User analysis questions** ("how does this work" / "what's the difference between v1 and v2" / "is X using Y" / "where is Z defined")
- **Progress reports / verdicts** ("we have N units" / "current run produced X" / "the last commit did Y")

All of the above trigger **Rule 0** below.

### B. Dual-analytical tasks (review / RCA / interpretation)

- Dual review / peer review / evaluation
- Research quality assessment
- Bug investigation and root-cause analysis
- Architecture review and design critique
- Results interpretation and discussion
- Any task where both agents form judgments about the codebase or its outputs

## Problem this solves

When Claude feeds Codex a pre-digested summary instead of raw file paths, two failures occur:
1. **Codex operates on Claude's framing**, not on ground truth — inheriting any bias, omission, or inflation.
2. **Neither agent truly understands the code** — both work from abstractions, missing implementation details, edge cases, and gaps between claims and artifacts.

## Core Rules

### Rule 0: Claim-time artifact ground (NEW 2026-05-19; broadened 2026-05-19)

**Trigger**: any user-facing claim OR artifact-persisted text making an assertion about current code / data / manifest / artifact state. Covers brief / spec / RFC AND analysis-question answers / progress reports / verdict explanations.

**Principle**: Before saying or writing "code is X" / "no code change to Y" / quoting a threshold / API contract / manifest fact / runtime behavior, the author MUST Read the relevant file(s) and cite file:line. Text-level reasoning over remembered facts (including the author's own prior text within this session) is insufficient.

**Why**: text-level reasoning systematically misses generator call order, manifest cardinality drift, API schema details, silent threshold shifts, and post-commit state changes. In review tasks codex catches these as "blocking spec bugs"; in direct user analysis, unverified claims become false answers the user acts on. Both failure modes were preventable at claim time.

**How to apply** (during drafting / answering):
1. Every time the response asserts a code/data fact, immediately Read the cited file and replace the assertion with file:line citation
2. Claims that cannot be verified at claim time get tagged `[TODO-VERIFY: <file>]` inline (briefs) OR explicitly disclosed as "from memory, may be stale" (user analysis) — they do NOT survive to finalized text without Read+cite
3. Re-using own prior text (e.g., v2 → v3 brief; or "as I said earlier") does NOT count as verification — re-Read every cited file
4. For user analysis questions where Read overhead matters, batch Reads at start of analysis BEFORE writing the response, not after
5. **Execution-time premise check** (added 2026-05-29, Claude+Codex cowork): when the task is to implement / escalate / delete / mechanically apply a *prior verdict* — from Claude, Codex, a header/title-level scan, an old brief, or any "already decided" authority — treat that verdict as a **hypothesis, not evidence**. Read the underlying artifact / log / content the verdict depends on before acting; if ground truth contradicts the premise, revise or stop rather than execute the stale verdict. **Fires on** durable/destructive actions driven by a prior verdict (hook escalation, rule growth, deletion/slimming, LOCK or amendment wording, report verdicts, "X already said so, apply X"). **Does NOT fire on** premise-free mechanical tasks (formatting, running a requested command, a user-specified single-line edit), facts already Read this turn and unchanged, or merely citing a LOCKED anchor.

**Trigger calibration (RCA 2026-05-29, Claude+Codex cowork)**: Rule 0 fires by fact type and artifact / user-facing consequence, **not by felt uncertainty**. High-confidence convention facts (signatures, CLI flags, config keys, exact quotes, numbers) are still Read+cite facts when they enter durable text or a final answer; "I'm sure" is a reason to open the source, not to skip it. (You are *most* confident on convention-bound facts — exactly where a project-specific tail you cannot know hides.) Scope = Rule 0's Trigger + Counter-example list above; this is not a new trigger, it removes "I'm certain" as a valid reason to skip an existing one.

**Calibration example (authoring)**: v2 brief said "drop `_assign_envelopes_length_aware()` from builder is the only change". Author should have Read `r3_cohort_builder.py:292-305` to discover the function runs AFTER full-100 HP10 generation, meaning v2's "Group A 1:1 inheritance" requires reversing the entire generator call order. Codex round-2 caught this with read-only re-derivation showing 20/144 units would violate EOL constraint.

**Calibration example (user analysis)**: user asks "现在 Component-C 输出的 envelope schema 是什么". Wrong: answer from memory of P2 v2 brief text. Right: Read `component_c_io.py:119-122` first, then cite the actual schema with file:line.

**Counter-example (where this rule does NOT apply)**:
- Pure strategic / narrative decisions ("which DA tier", "which baseline model") — these go through lit + cowork, not code-Read
- Stable architectural facts already in `CLAUDE.md` / `AGENTS.md` LOCKED anchors — by-construction verified at lock time (but cite the anchor)
- Cross-references to peer-reviewed lit anchors — need WebSearch / lit-grounded skill, not code-Read
- Pure conversational / clarifying meta-questions ("did you mean X?", "let me confirm scope")
- Facts already established in current conversation turn via Read tool output (no need to re-Read in same turn)

### Rule 1: Read before concluding

Both Claude and Codex must **read primary sources** before forming any analytical conclusion.

- "Primary sources" = source code, result artifacts (JSON/CSV/NPZ), paper/report drafts, git history, config files.
- Reading means opening the file and examining its content — not recalling a summary from a prior conversation turn.
- An analytical conclusion is **unsupported** unless the agent can cite the specific file path and line/key.

### Rule 2: No pre-digested summaries in dispatch

When Claude dispatches Codex for any analytical task:

**DO:**
- Give Codex **file paths to read**.
- Give Codex the **analytical task** (what to determine, what to check, what to evaluate).
- Give Codex **verification questions** if applicable.

**DO NOT:**
- Summarise what the code does or what the results show.
- Include Claude's own conclusions, impressions, or scores.
- Frame the project with adjectives (strong, robust, comprehensive, weak, etc.).
- Pre-interpret results — let Codex form its own reading.

### Rule 3: Claude reads independently (enforced ordering)

- Claude must read the same primary sources, not just relay Codex findings.
- Claude must form its own view **before** seeing Codex's output.
- **Enforcement mechanism**: Before reading Codex's analytical output, Claude writes its own preliminary findings to `/tmp/claude_pre_review_<ID>.md` (even if brief). This creates an immutable record that prevents unconscious anchoring to Codex's framing. The pre-review file is referenced in the final report's evidence trail.
- If both agents read the same file and reach different conclusions, they resolve by citing specific lines/keys — not by deferring to whoever sounds more confident.
- This rule integrates with the **verdict-affecting claims audit** defined in `dual-agent-original-request-review/SKILL.md` § Standard Process step 5 — the pre-review file serves as Claude's independent baseline for the audit.

### Rule 4: Claims require artifacts

Behavior claims need code evidence (file:line); result claims need artifact evidence (file:key). Script existence ≠ result production; design intent without executed artifact = 0 credit. Trail format and verification cost rules: see `dual-agent-original-request-review/SKILL.md` § Verification Discipline.

## Artifact Staleness Check

Before trusting any result artifact, verify it is not stale:

1. **Compare timestamps**: artifact mtime vs. the last commit that touched the generating script.
   - If the script was modified after the artifact was produced, the artifact is **stale** — it reflects old logic.
   - Quick check: `stat -f '%m' <artifact>` vs `git log -1 --format='%ct' -- <script>`
2. **Check git status of the generating script**: if it has uncommitted changes, any existing artifact is potentially stale regardless of mtime.
3. **Cross-check artifact content**: if the artifact contains a version field, run ID, or timestamp, verify it matches the current configuration (not a leftover from a different experiment run).

Staleness verdict:
- **Fresh**: artifact postdates the latest script change and matches current config → trust it.
- **Stale**: artifact predates script changes → flag as `STALE` in the report; do not use for scoring or conclusions without re-running.
- **Unknown**: cannot determine relationship (e.g., no git history for the script) → mark as `assumption-dependent`.

## How to apply per task type

### Evaluation / scoring tasks

Before emitting any score:
1. Read key source modules — actual logic.
2. Read every result artifact referenced by the paper or report.
3. Cross-check: for each quantitative claim, verify it appears in an artifact.
4. Flag phantom results (claims without artifact backing).
5. Check overfitting indicators in result files.
6. Check claim–script correspondence (does the script actually produce what's claimed?).

Codex dispatch template for scoring:
```
Read these files, then evaluate:

Source: [paths]
Artifacts: [paths]
Paper: [path]

Checklist: [specific verification questions]
Rubric: [dimensions]

Rules: cite file:key for every justification. Flag UNVERIFIED for unbacked claims.
```

### Research analysis / discussion tasks

Before forming interpretive conclusions:
1. Read the result artifacts being discussed.
2. Read the code that produced them — understand what was actually computed.
3. Verify that the numbers being interpreted match the artifacts.
4. Check edge cases: did the computation cover all claimed conditions?

### Bug investigation / code review tasks

Before diagnosing or judging:
1. Read the relevant source modules.
2. Trace the actual data flow, not the documented intent.
3. Run or inspect test outputs if available.
4. Check git history for context on why code looks the way it does.

### Error-report cowork (≤3 round template + 1 arbitration)

For run-level errors in dispatched experiments. Composes Rules 1-4 above + `dual-agent-original-request-review` § Conflict Resolution.

**Trigger**: codex dispatch FAIL / `.stall` marker / artifact missing / acceptance gate FAIL / metric outside expected band / `DISPATCH_STATUS=stalled`.

**Round 1 — Parallel independent RCA**

Both parties read failing artifacts directly (Rule 1); each writes its own `_rca_<side>.md` BEFORE reading the other (Rule 3). Each RCA must include:

| Field | Content |
|---|---|
| Root cause | One-sentence smallest causal claim |
| Evidence | path:line / artifact:key (Rule 4) |
| Class | code-bug / data-corruption / spec-drift / dep-change / seed / env / external |
| Cost | Minutes-to-hours remediation estimate |
| Confidence | HIGH / MEDIUM / LOW |

**Round 2 — Convergence** (verdict labels per `websearch-cowork` § Stage 4):

- **STRONG** (same class + same cause) → write `_RCA_CONVERGE.md` + remediation plan, exit cowork
- **PARTIAL** (same class, different cause) → Round 3 narrow
- **CLAUDE_ONLY** / **CODEX_ONLY** (one side missed evidence) → other side reads the missing artifact + updates RCA
- **DISJOINT** (different class) → Round 3 broad re-investigation

**Round 3 — Focused re-investigation on disputed axis only**

Both sides re-read the single artifact / line range that disambiguates the dispute. Do NOT expand scope.

**Round 4 (arbitration) — Claude decides 1-shot**

Per autonomous-mode governance (≤3 cowork rounds hard cap + Claude arbitration on convergence failure):

- Claude reads both `_rca_*.md` outputs side by side + any additional evidence cited by either side
- Writes `_RCA_ARBITRATION.md` with final verdict + reasoning + evidence cited
- This binds — exit cowork

**Deliverables** (one per error event):

```
<run_dir>/_rca_claude.md
<run_dir>/_rca_codex.md
<run_dir>/_RCA_CONVERGE.md     (if R1/R2/R3 converges)
<run_dir>/_RCA_ARBITRATION.md  (if Round 4 arbitration fires)
<run_dir>/_REMEDIATION_PLAN.md (always, after verdict)
```

**Anti-patterns**:

- Skipping artifact read because "we know this codebase" — Rule 1 violation
- Resolving disagreement via authority ("Claude is usually right") instead of evidence read
- Treating STALE artifact as canonical (run § Artifact Staleness Check before RCA)
- Letting cost-of-fix or confidence steer verdict choice (verdict = evidence-derived only)

## Convergence rules (for scored evaluations)

- Divergence > 1.5 on any dimension: both cite evidence. Lower score wins unless higher-scorer provides an artifact path the other missed.
- Report must always include an "Evidence Gaps" section first.
- Design intent, planned features, or "should work" reasoning never override missing evidence.

## Output formats

### For scored evaluations

```
## Evidence Gaps (place first)
- [claim] — [missing artifact or code evidence]

## Dimension Scores
| Dimension | Claude | Codex | Converged | Evidence |
|---|---:|---:|---:|---|

## Overall
- Thesis: X/10
- Journal: X/10

## Integrity Risks
1. [risk + specific file:line or artifact:key]
```

### For non-scoring analytical tasks (bug investigation, architecture review, research discussion, etc.)

```
## Evidence Gaps (place first)
- [claim] — [missing artifact or code evidence]
- [artifact] — staleness status: Fresh / Stale / Unknown

## Findings (ordered by impact)
| # | Finding | Evidence (file:line or artifact:key) | Confidence |
|---|---------|--------------------------------------|------------|

## Points of Agreement
- [both agents agree on X — shared evidence trail]

## Points of Divergence
- [Claude: X (evidence)] vs [Codex: Y (evidence)] → resolution or escalation

## Verdict-Affecting Claims Audit
| Claim | Executor status | Reviewer disposition | Trail |
|-------|----------------|---------------------|-------|

## Residual Unknowns
- [what remains unverified and why]

## Recommendation
- [actionable next step with justification]
```
