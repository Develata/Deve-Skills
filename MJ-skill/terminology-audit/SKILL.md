---
name: terminology-audit
description: Use for cross-file or cross-chapter terminology audits and corpus-wide term unification in thesis/paper sources — extract candidate term drift, build a decision queue, classify each occurrence, apply accepted replacements safely, and verify counts/build. Trigger on "术语审计", "术语统一", "术语一致性", "逐词审", "这个词全文怎么用", "把 X 全文改成 Y", "terminology audit", or "unify term X". Do NOT use for ordinary prose drafting or a single known-location edit; use academic-writing for prose quality and claim-boundary judgment.
---

# Terminology Audit + Context-Sensitive Replacement

This skill is the audit-and-replacement **process**, not the term standard itself. When present, use your project's domain-terminology reference to decide the preferred term. Follow `artifact-grounded-review`'s execution-time premise check: a prior assertion, an old draft's wording, model memory, or "it sounds like a signature term" is **not** evidence — check the actual corpus at execution time.

## When to use / not
- **USE**: cross-chapter term audit; unifying variants of one term; deciding and applying a flagged replacement; answering how a term is used across a document corpus.
- **NOT**: drafting/polishing prose quality; deciding one sentence's wording; one user-specified edit at a known location with no cross-doc consistency risk.

Before searching or replacing, **define the editable corpus** — usually the thesis/paper `.tex` sources. Exclude build products, `.aux`, old reports, scripts, generated outputs, and non-source files unless the user explicitly includes them.

## Phase 1 — dual-track candidate extraction
- **Stat track**: if present, run `python scripts/terminology_audit/extract_candidates.py <tex files> --out "$RUN/candidates_stat.jsonl"`.
- **LLM track**: inspect the same corpus for semantic flags; write `$RUN/candidates_llm.jsonl` rows with at least `term`, `suspicion`, `reason`, `context`, `line_hint`, `suggested_alternative`.
- **Merge**: if present, run `python scripts/terminology_audit/merge_candidates.py --stat "$RUN/candidates_stat.jsonl" --llm "$RUN/candidates_llm.jsonl" --out-jsonl "$RUN/candidates_final.jsonl" --out-md "$RUN/dashboard.md"`.
- If the scripts are absent, reproduce the same file contract manually: stat = frequency/variant signal, LLM = semantic signal, `llm_only` reviewed before `stat_only`.

## Phase 2 — decision queue (dashboard)
One row per candidate: `term | flagged_by | freq | suspicion | reason | suggested | decision`.
`suspicion` ∈ {`non_standard` (non-standard / broken Chinese term form, e.g. 空格断裂), `english_bleed` (bare English where a Chinese standard term exists), `inconsistent` (multiple variants for the same concept)}.
Triage high-confidence, low-blast-radius candidates first. Defer to Phase 3 with **user approval**: signature/innovation terms, headings/titles, abstract/contribution terms, ambiguous one-to-many mappings, and cross-chapter high-impact terms.

## Phase 3 — context-sensitive replacement (the core; highest error-risk)
For each accepted decision, **never blind global find-replace**. Run:
1. **Standard/source check**: check the local terminology reference first; if uncovered or the term is signature/high-stakes, verify against primary/domain sources before changing it. Do not treat an old model answer, a prior draft's wording, or "it sounds like a signature term" as evidence.
2. **In-corpus usage check before deciding**: grep the candidate AND the proposed replacement across the editable corpus; if the candidate is sometimes correct, or the replacement already carries a distinct meaning, split the decision by context.
3. **Old-and-new variant sweep**: search variants/synonyms of BOTH the old term and the new term — a replacement can create fresh inconsistency if near-synonyms of the new word already exist.
4. **Per-occurrence classification**: for each hit, mark replace / keep / needs-user-decision. Preserve code identifiers, command names, citation keys, `label`/`ref`/`eqref`/`autoref` keys, math, file paths, dataset names, and quoted artifact names unless explicitly approved. Visible prose inside headings/captions may change if it passes the same classification. (Same surface term may need different handling per occurrence.)
5. **Plan → approval → allowlisted apply → verify**: present `file:line | current | action | after`. User approval is REQUIRED for signature/innovation terms, headings/titles, abstract/contribution wording, ambiguous one-to-many mappings, or claim-changing replacements. Auto-apply only low-risk mechanical variants after the decision rule is accepted. Edit only allowlisted occurrences; then re-grep old/new terms (confirm the count moved as intended, no over-replacement), inspect the diff, and run the available LaTeX/project build (0 undefined, no ref breakage). If no build exists, say so.

## Calibration (real failures this discipline prevents)
- **Assumed-skip**: the model assumed "锚定" was a protected signature word and skipped the standard check — an *unverified assumption*. Signature words still need independent verification (step 1).
- **New-word not swept**: the model checked only the old word "运行至失效" and failed to sweep the newly introduced words ("全寿命" / "真实飞行条件") for pre-existing variants (step 3). Sweep both sides.

These are **process** failures, not permanent term-policy rules — do not hard-code that a specific word must always stay or always be replaced.

## Outputs
Default to a repo-conventional run dir (`outputs/terminology_audit/run_<UTC>_<scope>/`, or the project's existing convention). Keep `dashboard.md`, `candidates_*.jsonl`, and `audits/<term>.md` for non-trivial per-term decisions. Apply in confidence-batched patches / change sets; commit only if the user asks.
