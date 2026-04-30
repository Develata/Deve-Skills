---
name: write-research-readout
description: Produce presentation-grade markdown readouts for the Research1 (BYSJ Path B PINN / LEAP-1A QAR / D-scope dataset) workspace. Output is formula-first, symbol-tabled, artifact-cited prose with side-by-side independent-reproduction columns, axis-structured amendments, and ASCII timelines — never function-name dumps or code blocks for what should be math. Trigger on requests like "write readout / write report / progress update / group meeting deck / 写汇报 / 写组会 / 整理成 md / 出 readout / 出 report / 进度汇报 / presentation / deck 内容 / 给老师讲 / 写一份能讲的 md", or whenever the user wants experiment results, contract changes, or research progress consolidated into a markdown file suitable for slides/talk script.
---

# Research1 Reportable Readout — Authoring Protocol

> **Note on language**: this skill's prose is English for international readability, but the actual readout deliverables typically target a Chinese-speaking academic audience (advisor / group meeting / 老师汇报). The fenced markdown templates below show example Chinese phrasing — when writing an actual readout, mirror the audience's language. The structural rules (F1–F13) apply regardless of language.

## Canonical exemplar

**`presentation_4.27/group_meeting_2026-04-27.md`** is THE reference. Read it before drafting anything. When in doubt about wording, depth, formula density, or section ordering, mirror it section by section.

`presentation_4.23/report.md` is a secondary exemplar — useful only when the readout's lead is **a research-direction pivot narrative** (how the framing changed) rather than a contract amendment / impl + review readout.

## Why this skill exists

In this workspace the user's deliverable for 汇报 / 组会 / advisor review is **not** "what the script did" — it is **what the method is, what the numbers are, what changed, and where every claim lives in the artifact tree**. The 4.27 exemplar achieves this through ~12 distinctive fingerprints; this skill exists so future readouts reproduce those fingerprints rather than regressing to function-name narration.

## When to use

- User asks for a 汇报 / 组会 / report / deck content / readout / progress markdown.
- User finishes a run / a contract amendment / a (c) review and asks "整理一下" / "总结这一轮" / "wrap up this round" / "give me something I can present".
- User asks to update or extend an existing `presentation_*/...md` or `outputs/reports/<bundle>/run_*/readout.md`.

## When NOT to use

- Drafting `paper/sections/0X_*.md` — those follow journal-section conventions.
- Dual-review verdict artifacts — those follow `artifact-grounded-review` skill.
- Research contracts — those follow `docs/research-contract-template.md`.
- Inline answer to a quick question.

## Project-frame reminder

Per active feedback memory `feedback_scope_paper_to_experiment.md` (2026-04-26), this project is in **experiment-optimization** mode. Readouts default to four-step ordering for Track B results:

1. **Closure** — what direction can we now stop investing in?
2. **Working hypothesis update** — does this strengthen / weaken §5.2.4 reference-semantics divergence?
3. **Methodology debt revealed** — does this expose a prior result that needs re-audit?
4. **Next-experiment design** — what is the cheapest experiment that maximally moves the working hypothesis?

Paper-text wording is downstream. Don't lead with "how should §X be rewritten" unless the user explicitly reverses scope.

## Output location convention

- **Group-meeting / advisor deck content** → `presentation_<M.DD>/<descriptor>.md` (e.g. `presentation_4.27/group_meeting_2026-04-27.md`). Companion figures go in `presentation_<M.DD>/figures/`.
- **In-bundle run readout** → `outputs/reports/<bundle>/run_YYYYMMDD_<tag>/readout.md`.
- **Methodology note** → `docs/methodology-notes/<descriptor>_YYYY-MM-DD.md`.

If the location is ambiguous, ask the user once before writing.

---

## 4.27-style fingerprints — 12 patterns to reproduce

These are the moves that make 4.27 work. A readout missing several of these is regressing.

### F1. Header block with 6 explicit lines

```markdown
# <title> 进度汇报

**组会日期**：<YYYY-MM-DD>
**承接**：<previous deck/commit/contract relative path>
**当前 commit**：`<short-hash>` (<branch / tag / DRAFT version>)
```

Then a 1-paragraph "0. 承接" (Carry-forward) section that states (a) the previous deck's headline numbers in a table, (b) what changed in framing since then, (c) the **operative reason** for the change in one sentence (e.g. "v2+ ρ=+0.326 在 method paper 评审里是弱信号；same evidence pack, in dataset paper it is usability validation. **Switch venue, not numbers**.")

### F2. Symbol table BEFORE any formula

Every variable in §1 method gets a row. Two-column `| Symbol | Meaning |`. Use proper LaTeX: `$\eta_\text{LPC}$`, `$T_{t25}$`, `$N_1$`, `$\sigma_\text{pop}$`, `$c_\text{EOL}$`, `$\hat{p}_\text{KDE}$`. Avoid Unicode hacks (`η_LPC`, `σ_pop`).

### F3. Acceptance criteria named (Hk / Gk) + math definition + threshold + status

Every gate gets a name (H1...H8, G_γ1...G_γ3, etc.) and a row in a master table:

```markdown
| 准则 | 数学定义 | 阈值 | <prior version> status | <current version> status |
|---|---|---|---|---|
| **H6** | $\sigma_\text{pop}(\eta_k) \in [0.005, 0.020]$ | all 4 components | hard gate | unchanged, PASS |
| **H1** | $\overline{\text{overlap\_qar}}_k = \text{IoU}(...)$ | ≥0.80 / ≥5/6 | hard gate | **demote to informational** |
```

The demote pattern (hard gate → informational) is itself a fingerprint — when the contract amendment downgrades a criterion, show that explicitly in the status column.

### F4. Defect history inline as `> blockquote`

Pattern, immediately after the corrected formula:

```markdown
> **Defect #1 历史**：v1 contract wrote $\text{Uniform}(0.985, 1.00)$ → $\sigma_\text{pop} \approx 0.00433 < 0.005$,
> **mathematically H6 cannot pass**. Pilot 12-unit 0/4 components fall in band. v2 widening fixes.
```

The defect block (a) states what v1/prior wrote, (b) **proves mathematically** why it failed (or cites the empirical number), (c) names the version that fixed it.

### F5. Multi-step recipe with sub-step naming + anti-confusion annotations

When a method has internal stages (e.g. 4-substep calibration chain, multi-stage training), name them `Step k.a` / `Step k.b` / `Step k.c` / `Step k.d` and give each a one-line title + formula + provenance:

```markdown
#### Step 5.4.a — ONNX error compensation

$$X^\text{comp}_k = X^\text{raw}_k + \text{ONNX}_k(W,\ X^\text{raw}) \quad \text{(NOTE: ADD, not SUBTRACT)}$$

ONNX network group: 8 × `compensation_net_output_*.onnx` + 1 × `normalization_params.npz`, all sha256 pinned.
```

`(NOTE: ADD, not SUBTRACT)` is the anti-confusion-annotation pattern: any formula with sign / direction / unit ambiguity gets an inline parenthetical. Pinned artifacts cite sha256 inline (`sha256 4133...9726` truncated form).

### F6. Math-incompatibility proof for prior contract failures

When a prior version of a criterion is wrong **as math, not just as empirics**, prove it:

```markdown
v2.3 §76 verbatim:
> "Reject any sample violating ANY channel envelope. PASS = global reject rate < 5%."

Mathematical incompatibility:

$$\text{H2}^\text{static}: r_\text{global} = \mathbb{E}[\mathbb{1}(X_s \notin \text{env})] < 0.05$$

But under RTF data:

$$\mathbb{P}(X_s \notin \text{env} \mid c \to c_\text{EOL}) \to 1 \quad \text{by design}$$

Therefore $r_\text{global}$ must be large → always FAIL.
```

This is the strongest move in 4.27 — a prior gate is shown to be math-impossible, not just empirically failed. Use this whenever a contract revision retracts a criterion on principled (not empirical) grounds.

### F7. Empirical readout table with `(c) 独立复现` column — non-negotiable

Every empirical number in the headline result table has a side-by-side **independent reproducer column**:

```markdown
| Item | Value | (c) Independent reproduction |
|---|---|---|
| H2 global reject | 0.5655 | 0.5582 |
| HGBT regression Spearman ρ | **0.9326** | 0.9326 |
| 5-pin pre/post bit-identity | all match | all match |
```

Numbers without an independent-reproduction column are not headline-acceptable; they go to a "single-seed observation / informational diagnostic" supplementary table with explicit labeling. This column **is** the artifact-grounded review evidence written into the readout — without it, a paper-facing claim cannot use the table.

### F8. Axis-structured amendments

When a contract / impl revision bundles multiple changes, organize them as numbered Axes with sub-items:

```markdown
## 5. v3.1 amendment methodology (5 axes)

### 5.1 Axis 1 — H4 audit-table alignment (mix i+iii)
### 5.2 Axis 2 — Step 6a demote + drift fields
### 5.3 Axis 3 — H2 cycle-K healthy-only
### 5.4 Axis 4 — HGBT regression-only
### 5.5 Axis 5 NEW — 5 sub-items 3-way categorization
```

When an Axis itself has internal heterogeneity, give it a 3-way (or N-way) sub-frame **categorization table**:

```markdown
| Sub-frame | Sub-item | Content |
|---|---|---|
| Calibration-drift | **5.1** | H1 demote to informational |
| Calibration-drift | **5.4** | Cohort-scope coherence |
| Validator/governance | **5.2** | H5 / `n_units` dev-only 7 → all 12 unit |
| Validator/governance | **5.3** | New JSON adds `global_conclusion` key |
| Wording cleanup | **5.5** | `H1_per_channel_ops_overlap` → `H1_per_channel_overlap` |
```

### F9. Risk roster as "comparability-neutral vs deliberately avoided" pairing

Risk discussion is **two sub-lists**, not a generic risk paragraph:

```markdown
### 6.3 Risk inventory

**Current (v3.1 picks) comparability-neutral**:
- 5-pin guards all untouched
- 4-substep chain recipe / canonical-hash recipe / RTF degradation model / operating-condition sampling: all untouched
- v2+ headline ρ=+0.587 / c6c3 / b1b3 paper number does not need rerun

**Two paths that would trigger comparability-critical declaration (deliberately avoided)**:
- Axis 2 (i)/(iv): redo affine calibration JSON → invalidate 5-pin → v2+ baseline_audit all to recompute
- Axis 4 (i): force N≥24 unit regen → multi-week recompute + dataset_v1_seed42.h5 superseded
```

Frame risks as **what we deliberately avoided + why**, not "things that could go wrong". The deliberately-avoided framing is what makes the readout decision-grade rather than worry-grade.

### F10. ASCII timeline / sequential path in fenced code blocks

For multi-day timelines and sequential work plans, use ASCII arrows in a fenced code block:

````markdown
### 6.1 4-day timeline

```
2026-04-23  v2+ deck 汇报 (ρ=+0.326)
            ↓ thesis Ch.5 reframing that evening
2026-04-26  framing decision aide → Data Descriptor route
            D-scope v1 contract FROZEN → impl STOP at pilot gate
            (Defect #1 H6 impossible + Defect #2 unit-scrambling)
2026-04-27  v2 → v2.1 → v2.2 → v2.3 (3 rounds (a) review) FROZEN
            v3 DRAFT → v3 (a) round-1 BLOCKING (Axis 5 added)
            v3.1 DRAFT  ← we are here
```

### 6.2 Sequential path (cannot be parallelized)

```
v3.1 DRAFT (today)
  → user review
  → next session: round-2 (a) dispatch (NEW codex thread)
  → round-2 verdict converges
  → user FREEZE authorization
  → v3.1 impl session: validator script 5 fixes
  → v3.1 (c) re-review
  → unlock paper-facing citation
```
````

The "← we are here" anchor and the explicit "(cannot be parallelized)" labeling are signature moves.

### F11. Claim evolution vs prior deck (comparison table)

A dedicated section, not a paragraph:

```markdown
## 7. Claim evolution (vs 4.23 deck)

| Dimension | 4.23 deck | 4.27 current |
|---|---|---|
| Primary publication venue | method paper (implicit) | **Data Descriptor** (archetype B main) |
| Dataset itself | 1344-trace legacy pool | **N=12 RTF dataset_v1_seed42.h5** |
| Usability evidence | ρ=+0.326 (157 flights) | ρ=+0.326 unchanged + **HGBT severity-rank ρ=0.9326** |
| Acceptance criteria | composite H1-H8 all PASS | **per-criterion**: 6 gate + 4 informational diagnostic |
| Failure evidence | none (deck all positive) | (c) review exposed calibration drift +10% N1 / +5% EGT |
| Comparability | v2+ headline preserved | still preserved; new dataset independent |
```

One row per dimension that moved. **What stayed the same** also gets rows — they are the conservation evidence.

### F12. Q&A preparation — preempt actual likely critiques, not generic FAQs

For group-meeting decks, this section is essential. Each Q is **anchored in a specific likely audience challenge**, not a generic FAQ. The 4.27 exemplar:

- **Q1**: Why not just fix impl, why go through amendment? → because impl is correct (4-substep chain bit-exact + 5-pin conserved + canonical hash matches); the contract is what needs modification.
- **Q2**: N=12 too few? → yes; written into §6.1 limitation; severity regression unaffected (ρ=0.9326).
- **Q3**: Will published calibration drift +10% N1 be rejected? → Data Descriptor venue values honest limitation > pretty numbers (cite N-CMAPSS PHM Society Data Challenge 2021 precedent).
- **Q4**: Is the 4-day v1 → v2.3 → v3 → v3.1 chain too fast? → each (a) review is an independent codex artifact-grounded review; all verdicts have archived dual artifacts.
- **Q5**: How is v2+ headline ρ=+0.326 "carried forward"? → not redone, not retracted; enters Data Descriptor §6.1 usability validation.

Each answer (a) acknowledges the challenge directly, (b) cites a concrete artifact / precedent / mechanism, (c) does not retreat. Generic FAQ-style answers ("good question, we plan to investigate") fail the bar.

### F13 (Appendix). Two-block appendix: commit + artifact + schema

Appendix A is two tables — commits and artifacts:

```markdown
## Appendix A: key commit and artifact index

| Commit | Subject |
|---|---|
| `8360180` | v3 DRAFT |
| `a27b327` | v3 (a) round-1 dual review verdict (BLOCKING) |
| `3ad3f8e` | **v3.1 DRAFT** (today) |

| Artifact | Path |
|---|---|
| v2.3 FROZEN contract | `outputs/reports/<bundle>/run_*/research_contract_v1.md` |
| Dataset HDF5 | `outputs/reports/<bundle>/run_*/dataset_v1_seed42.h5` |
| H1-H8 readout | `outputs/reports/<bundle>/run_*/validation_report_seed42.json` |
| 5-pin pre/post hash | `outputs/reports/<bundle>/run_*/_pin_hash_post_impl_v2.json` |
```

Appendix B (when a data artifact is the deliverable): HDF5 / NPZ / file-tree schema as ASCII tree:

```
dataset_v1_seed42.h5
├── /W_{dev,test,val}    (M, 3)   [Mach, alt_km, fuel_flow_kgps]
├── /X_s_{dev,test,val}  (M, 6)   [Tt25, Tt3, N1, N2, EGT, Ps3] + noise
├── /Y_{dev,test,val}    (M,)     RUL in cycles; -1 = right-censored
├── /A_{dev,test,val}    (M, 6)   [unit_id, cycle, fault_component_id, ...]
├── /H_{dev,test,val}    (M, 4)   [η_LPC, η_HPC, η_HPT, η_LPT]
└── /metadata
    ├── canonical_content_hash
    ├── affine_calibration_provenance (sha256 + path + mtime)
    ├── stated_limitations
    └── calibration_drift_per_channel  ← v3.1 NEW
```

Footer line:

```markdown
*End <date> <descriptor>. Carry-forward <prior deck/commit>; period <YYYY-MM-DD> → <YYYY-MM-DD>, N days. Next session (<next action>) requires <user authorization | ...>.*
```

---

## Required structure (full skeleton)

```
# <title> 进度汇报          ← F1 Header
0. 承接 (Carry-forward)      ← prior deck headline numbers + framing reframing reason
1. <main subject>            ← e.g. dataset construction method
   1.1 Physical framework + symbols  ← F2 symbol table
   1.2 ... 1.k                       ← F3 acceptance criteria + F4 defect history + F5 sub-step recipe
2. Validation methodology: H1-H8 acceptance criteria  ← F3 master table (multi-version status columns)
3. Empirical readout         ← F7 (c) independent-reproduction column non-negotiable
4. <defect diagnosis>        ← F6 math-incompatibility proof (when applicable)
5. <amendment methodology>   ← F8 axis structure + sub-frame categorization
6. Current position and next steps  ← F10 ASCII timeline + sequential path
   6.3 Risk inventory        ← F9 comparability-neutral vs deliberately-avoided
7. Claim evolution (vs prior) ← F11 comparison table
8. Q&A preparation           ← F12 preempt actual critiques (essential for group meeting)
Appendix A: commit + artifact ← F13
Appendix B: schema (when applicable)
*End footer line*
```

Skip a section only if it does not apply. Keep Header, §3 readout, §6, and Appendix A.

---

## Reject-grade signals (any of these makes the readout fail the bar)

1. **No function-name lists.** "通过 `compute_spearman_per_seed_per_flight()` to compute ρ" is rejected. Describe as math: "for the 157 cohort flights, compute Spearman ρ(residual, alert_count) on the residuals; train independently on 3 seeds, report mean ± std." Code pointers (file:line) only in Appendix.
2. **No `def` / class blocks** in body. Reproducibility pseudocode → Appendix fenced block, never §1/2/3 method.
3. **Every empirical number in §3 has a `(c) Independent reproduction` column** (F7). Numbers lacking this column → either move to informational diagnostic with "single-seed observation, not main-line evidence" label, or remove. **This rule alone enforces dual-review at boundary (c) within the readout itself.**
4. **Math-impossible criteria are proved, not narrated** (F6). When demoting/retracting a gate on principled grounds, write the formal proof.
5. **LaTeX math, not Unicode hacks.** `$\eta_\text{LPC}$` not `η_LPC`. (Inline integers / percentages can stay plain text.)
6. **Anti-confusion annotations on direction-sensitive formulas** (F5). Sign / unit / order / inclusion ambiguity → inline parenthetical.
7. **Pinned artifacts cite sha256 inline** in truncated form (e.g. `sha256 4133...9726`).
8. **Defect history inline, not deleted** (F4). Provenance is a feature.
9. **Risk roster uses deliberately-avoided framing** (F9), not generic worry-list.
10. **Carry-forward / period / next session in Footer expected** even for self-contained readouts.
11. **Figures: real-artifact only**. Concept diagrams (timeline boxes, pipeline frames, architecture boxes) explicitly punted to "PPT-stage rendering" in Header.
12. **Q&A preparation questions preempt actual critiques** (F12), not generic FAQs. "Why are results good?" is rejected; "Why didn't you just rerun impl instead of amending the contract?" is accepted.
13. **Single-seed numbers labeled in-line** "single-seed observation, not main-line evidence" — same line as the number.
14. **Un-dual-reviewed paper-facing claims explicitly flagged**: "this section is executor's single-side reading; awaiting dual review before paper-facing use." Don't silently let an un-reviewed claim into a deck for paper use.

---

## Triggering checklist (before writing a single line)

Confirm with the user (or from conversation context):

- [ ] File location (`presentation_*/...md` vs `outputs/reports/.../readout.md` vs `docs/methodology-notes/...`).
- [ ] Carry-forward commit / deck / contract.
- [ ] Does this round include a new run? If new, the run path already exists with frozen artifacts before drafting (no synthesizing the future).
- [ ] Audience: advisor / group meeting / self-archive / submission. Q&A preparation is essential for group meeting, optional otherwise.
- [ ] Whether figures exist in the artifact tree, or need a separate render step (out of this skill's scope).
- [ ] Whether `(c) Independent reproduction` column data is available for §3. If not, either flag the readout as pre-(c) draft or scope to non-paper-facing self-archive use.
- [ ] Whether any planned claim crosses a dual-review boundary (cf. project rule 3) without dual review — if yes, flag and gate.

## Reference exemplars (read before writing)

- **Primary**: `presentation_4.27/group_meeting_2026-04-27.md` — full deck (Header + 8 body sections + Q&A + 2 appendices). All 13 fingerprints exhibited.
- **Secondary**: `presentation_4.23/report.md` — advisor briefing leading with research pivot + main-line strengthening + follow-up research, real-data figure references throughout. Use only when the readout's primary structure is a pivot narrative.

When in doubt, mirror 4.27 section by section.
