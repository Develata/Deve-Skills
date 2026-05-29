---
name: user-explanation-5step
description: Use when giving the user an INLINE reply that carries a trade-off, a decision, a verdict, or a non-trivial finding (decision brief / round verdict / failure root-cause). NOT for "done"/status confirmations, one-line answers, or pure data dumps. Forces a compact decision-brief shape and blocks internal tool-name / file-path bleed into user-facing text.
---

# User-facing decision brief

Apply the shared `research-comms-policy` (style + evidence + no-internal-bleed + Chinese/English density) alongside this skill.

## When to use / not use
- **USE**: an inline reply carrying options / a trade-off / a decision / a verdict / a non-trivial finding, to the user.
- **NOT**: "done" / status confirmation · single-line answer · pure data dump · internal reasoning that never reaches the user. For a standalone .md report → `write-research-readout`; for method teaching → `write-explanation-readout`.

## Shape — use the elements that apply; do NOT force the skeleton on small calls
1. **Symptom + root cause** — lead here; formula/table when denser than prose.
2. **Options** — only when real alternatives exist: a compact matrix (改动量 / 复杂度 / 是否解决根因 / 对 paper-or-system 的影响).
3. **What would change the recommendation** — the counter-evidence that would invalidate the pick. (Models recommend too cleanly without this.)
4. **Recommendation + one-line why**, then the **decision point** — what the user must decide / approve / redirect, with explicit options. Omit the ask when the next action is already implied.

## The durable bit (why this skill still earns its keep)
- No tool / hook / file-path / internal-mechanism names in the body — this has leaked to the user before and forced corrections. Evidence paths / hashes are allowed in an appendix or evidence table when traceability genuinely matters.
- Decision criteria in natural form (`|Δ| < 0.02 且 CI 上界 < +0.05`), not code-style (`abs(delta) < 0.02 AND ...`).
- Language density per `research-comms-policy` §5 (professional terms in English; everyday process words in Chinese; no mid-clause mixing).
