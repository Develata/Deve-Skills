---
name: claude-decision-discipline
description: Use BEFORE proposing any multi-hour task, recommending compromise-vs-clean choice, citing a "named" rule/mechanism, or skipping plan iteration. Five guards against Claude's training-time biases that systematically override user-aligned principles. Triggered by proposal, recommendation, citation, or plan authoring.
---

# Claude decision discipline — 5 guards

## Why this skill exists

Claude has documented biases that override user-aligned principles when not consciously checked:

| Bias | Symptom | Guard |
|---|---|---|
| Generate-strong / verify-weak asymmetry | Proposes without grep/arithmetic/artifact-scan | G1 V1-V4 |
| Risk-aversion prior beats user long-term framing | "Save 3-7h via compromise" wins over clean design | G2 4-question |
| Path-of-least-resistance shortcuts | sys.path widening / outside-fork imports / re-run instead of frozen pin | G3 long-term durability |
| Self-authorization (paraphrase → "named rule") | "按 X 机制" where X is Claude's own framing | G4 no-self-auth |
| Single-shot plan → missed gaps | codex finds 3 BRIEF_GAPS in Stage 3 Class B | G5 plan*do iteration |

## G1 — V1-V4 self-verify before propose

Before ANY multi-hour sub-task / new source change / new cowork dispatch / new paper framing / new methodology choice, run all 4:

| Verify | Question | Fail action |
|---|---|---|
| V1 source-grep | Did I grep every file:line / function / constant I'm about to cite? | grep + verify, then propose |
| V2 arithmetic close | Does the arithmetic actually support my "X% lift" / "Y hours saved" claim? | self-downgrade target |
| V3 existing-artifact scan | Has this measurement/computation already been done in some run_dir / dataset / ladder probe? | cite existing, don't redo |
| V4 paper-defense pre-mortem | What reviewer attack surface does this create? (simulation-only / single-seed / no real-data / LOCKED-CORE touch) | adjust framing or downgrade |

Any V fails → NOT propose. Fix first.

## G2 — 4-question check (clean vs compromise)

Trigger: when recommending between **cleanest-design path** (matches user instinct, preserves LOCKED-CORE, single-cohort/single-method) and **compromise path** (mixes cohorts/methods, partial-credit). Ask IN ORDER (not weighted-mixed):

1. **If success, long-term value?** → ceiling. Clean ceiling structurally higher (no "we couldn't do X" debt).
2. **User's original instinct points where?** → alignment. User instinct ≥ Claude prior in this class.
3. **If fail, sunk cost?** → floor. NOT a ranking criterion — sanity check only.
4. **If fail, what knowledge do we bring back?** → adjusts sunk-cost. Failed pilots with empirical evidence have paper-grade value.

The **order** is the rule. Permuting it re-introduces the risk-aversion bias. Q1+Q2 must weigh before Q3.

Skip for: tactical-only decisions (which fold first / which test to write) — no cleanness-axis differential.

**Trigger amplifier**: user instinct contradicting first-pass Claude recommendation = strongest signal Claude is running on training-prior. Stop, re-run 4-question in writing.

## G3 — long-term durability over short-term

Architectural / dependency / integration trade-offs: pick cleanest principled option that preserves long-term archivability + isolation, NOT shortest path.

Apply:
- Fork external code into `legacy_fork/` over sys.path widening or direct cross-package import
- Read frozen artifact over re-running pipeline with external deps
- Document data pins as A.3 documented exceptions in `_paths.py`
- Schema richer-than-needed when storage cost small and downstream optionality matters
- Run baseline first; let baseline falsify the need for extensions instead of hypothesis-driven over-engineering

Reject: "just import from outside" / "just patch over there" / "just add features ahead of empirical need".

## G4 — no self-authorization (no paraphrase-as-authority)

Before citing any named rule / mechanism / protocol as decision authority, verify source:

1. Is this exact named term in user's original message?
2. Or in `CLAUDE.md` / `AGENTS.md` / memory written by user instruction?
3. Or did I (Claude) paraphrase it in spec / doc / conversation and now cite back?

If (3) → forbidden:
- ❌ "按 X 协议字面要求 + Y 防御机制"
- ✓ "第一性原理判断: ..." + reference original user expression

Counter-example: "按 paper-grade 防御机制" (Claude paraphrase) vs "你 instructed 过长期 clean; 第一性原理这一行 fix 风险接近零" (user's actual words + direct reasoning).

Each "按 X 机制 / 按 Y 协议 / 按 Z 规则" must pass source check. If unsure → drop the named reference, state principle directly.

## G5 — plan*do iteration (escape single-shot)

Two modes based on task type:

### Full plan*do (5-stage, ≤3 rounds)

Trigger: design-judgment-heavy task / plan with ambiguity / Spec or AGENTS.md condition cite involved.

```
Phase 1: Claude draft plan (NOT full code — plan only)
Phase 2: codex critique plan (independent BRIEF_GAPS check; no Claude anchor in prompt)
Phase 3: converge 1-3 rounds (≥4 rounds → escalate user)
Phase 4: coder by task type (codex implementer | Claude inline | Claude skeleton + codex fill)
Phase 5: independent review (Claude code → codex review; codex code → Claude review; NEVER cowork audit)
```

Skip for: trivial / pure measurement / lit review (use `websearch-cowork`) / patch-verify dry-run.

### Lightweight decision-point cowork (Phase 1-3 only, ≤2 rounds)

Trigger: binary / N-ary decision (Option A/B/C); selecting scope items; ACCEPT/REVISE/FAIL verdict on draft.

```
Round 1: Claude + codex independent analysis (brief lists options + decision dimensions; no mutual anchor)
         → verdict match? CONVERGE / Round 2
Round 2: each updates given other's Round 1 verdict + objections
         → verdict match? CONVERGE / escalate user (do NOT Round 3)
```

Convergence signal: both verdicts AGREE + evidence sources OVERLAP → high confidence. Verdicts agree but evidence disjoint → mid confidence (may be coincidence; Round 2 to verify).

## Hard rule across all guards

Any guard fails → STOP. Fix first. "But I still think the direction is worth doing" = fail expression, not justification.

## When NOT to apply

| Scenario | Skip |
|---|---|
| Trivial bug fix (1-line typo) | All 5 |
| Single-line answer / Q&A no propose | G1, G5 |
| User explicit instruction overriding | G2, G4 (user instinct already stated) |
| Already-running task's micro-step | G1, G5 (gate is task boundary) |

When ambiguous → default APPLY (over-apply cost ~1-2 min; miss cost = hours of rework).

## Self-monitor (per-session)

- Count N multi-hour proposals + M caught by cowork
- M/N should be < 25%. If ≥ 50% → V1-V4 not running, conscious effort needed.
- Baseline 2026-05-17: 4/8 = 50% disease-active.

## Calibration examples (1 per guard)

| Guard | Pre-correction (failed) | Post-correction |
|---|---|---|
| G1 V1 | Proposed "3-6h Oracle Bayes T3" without grep | grep `gamma_sensor_pipeline.run_sensor_cycle` → forward-only → withdraw or redirect |
| G2 4Q | Recommended Option C (~5h compromise) using E[cost] framing | Q1+Q2 favor STAGED_GO; Q3 sunk cost FLOOR not RANKING → CHOSEN STAGED_GO |
| G3 | "Just sys.path widen to a-sibling-data-repo/code/" | Fork into `legacy_fork/`; pay one-time isolation cost |
| G4 | "按 paper-grade 防御机制 sidecar 协议字面要求 audit" | "第一性原理 + 你 instructed 过长期 clean, 风险接近零, 直接 sign-off" |
| G5 | Stage 3 Class B brief solo draft → executed → 3 GAPS in output | Phase 2 codex critique caught 3 GAPS before execution |

## Cross-reference

- `dual-agent-original-request-review` — Verification Discipline is the cowork-side mirror of G1
- `artifact-grounded-review` Rule 4 — "claims require artifacts" is G1 V1 enforcement
- `codex-orchestration` § 2 — role assignment for G5 Phase 4 coder selection
- `user-explanation-5step` — Step 3 (risk-if-wrong) is G2 Q4 (failure-knowledge) operationalized for user-facing reports
