---
name: write-research-readout
description: Produce presentation-grade markdown readouts for the Research1 (BYSJ Path B PINN / LEAP-1A QAR / D-scope dataset) workspace. Output is formula-first, symbol-tabled, artifact-cited prose with side-by-side 独立复现 columns, axis-structured amendments, and ASCII timelines — never function-name dumps or code blocks for what should be math. Trigger on requests like "写汇报 / 写组会 / 整理成 md / 出 readout / 出 report / 进度汇报 / presentation / deck 内容 / 给老师讲 / 写一份能讲的 md", or whenever the user wants experiment results, contract changes, or research progress consolidated into a markdown file suitable for slides/talk script.
---

# Research1 Reportable Readout — Authoring Protocol

## Canonical exemplar

**`presentation_4.27/group_meeting_2026-04-27.md`** is THE reference. Read it before drafting anything. When in doubt about wording, depth, formula density, or section ordering, mirror it section-by-section.

`presentation_4.23/report.md` is a secondary exemplar — only useful when the readout's lead is **research 转向叙事** (how the framing changed) rather than a contract amendment / impl + review readout.

## Why this skill exists

In this workspace the user's deliverable for汇报 / 组会 / 老师审 is **not** "what the script did" — it is **what the method is, what the numbers are, what changed, and where every claim lives in the artifact tree**. The 4.27 exemplar achieves this through ~12 distinctive fingerprints; this skill exists so future readouts reproduce those fingerprints rather than regressing to function-name narration.

## When to use

- User asks for a 汇报 / 组会 / report / deck content / readout / progress markdown.
- User finishes a run / a contract amendment / a (c) review and asks "整理一下" / "总结这一轮" / "出一份能讲的".
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

Paper-text wording is downstream. Do not lead with "how should §X be rewritten" unless the user explicitly reverses scope.

## Output location convention

- **Group-meeting / 老师汇报 deck content** → `presentation_<M.DD>/<descriptor>.md` (e.g. `presentation_4.27/group_meeting_2026-04-27.md`). Companion figures go in `presentation_<M.DD>/figures/`.
- **In-bundle run readout** → `outputs/reports/<bundle>/run_YYYYMMDD_<tag>/readout.md`.
- **Methodology note** → `docs/methodology-notes/<descriptor>_YYYY-MM-DD.md`.

If the location is ambiguous, ask the user once before writing.

---

## 4.27 风格 fingerprints — 12 patterns to reproduce

These are the moves that make 4.27 work. A readout missing several of these is regressing.

### F1. Header block with 6 explicit lines

```markdown
# <title> 进度汇报

**组会日期**：<YYYY-MM-DD>
**承接**：<上一份 deck/commit/contract 的相对路径>
**当前 commit**：`<short-hash>` (<branch / tag / DRAFT version>)
```

Then a 1-paragraph "0. 承接" section that states (a) the previous deck's headline numbers in a table, (b) what changed in framing since then, (c) the **operative reason** for the change in one sentence (e.g. "v2+ ρ=+0.326 在 method paper 评审里是弱信号；同样的证据包，在 dataset paper 里它是 usability validation. **换 venue 不换数字**.")

### F2. Symbol table BEFORE any formula

Every variable in §1 method gets a row. Two-column `| 符号 | 含义 |`. Use proper LaTeX: `$\eta_\text{LPC}$`, `$T_{t25}$`, `$N_1$`, `$\sigma_\text{pop}$`, `$c_\text{EOL}$`, `$\hat{p}_\text{KDE}$`. Never Unicode hacks (`η_LPC`, `σ_pop`).

### F3. 接受准则 named (Hk / Gk) + math definition + threshold + status

Every gate gets a name (H1...H8, G_γ1...G_γ3, etc.) and a row in a master table:

```markdown
| 准则 | 数学定义 | 阈值 | <prior version> status | <current version> status |
|---|---|---|---|---|
| **H6** | $\sigma_\text{pop}(\eta_k) \in [0.005, 0.020]$ | all 4 components | hard gate | unchanged, PASS |
| **H1** | $\overline{\text{overlap\_qar}}_k = \text{IoU}(...)$ | ≥0.80 / ≥5/6 | hard gate | **demote 到 informational** |
```

The demote pattern (hard gate → informational) is itself a fingerprint — when the contract amendment downgrades a criterion, show that explicitly in the status column.

### F4. Defect 历史 inline as `> blockquote`

Pattern, immediately after the corrected formula:

```markdown
> **Defect #1 历史**：v1 合同写的是 $\text{Uniform}(0.985, 1.00)$ → $\sigma_\text{pop} \approx 0.00433 < 0.005$，
> **数学上 H6 不可能通过**。pilot 12-unit 0/4 component 落入 band。v2 widening 修复。
```

The defect block must (a) state what v1/prior wrote, (b) **prove mathematically** why it failed (or cite the empirical number), (c) name the version that fixed it.

### F5. Multi-step recipe with sub-step naming + anti-confusion annotations

When a method has internal stages (e.g. 4-substep calibration chain, multi-stage training), name them `Step k.a` / `Step k.b` / `Step k.c` / `Step k.d` and give each a one-line title + formula + provenance:

```markdown
#### Step 5.4.a — ONNX 误差补偿

$$X^\text{comp}_k = X^\text{raw}_k + \text{ONNX}_k(W,\ X^\text{raw}) \quad \text{(注意是 ADD，不是 SUBTRACT)}$$

ONNX 网络组：8 个 `compensation_net_output_*.onnx` + 1 个 `normalization_params.npz`，全部 sha256 pinned.
```

`(注意是 ADD，不是 SUBTRACT)` is the anti-confusion-annotation pattern: any formula with sign / direction / unit ambiguity gets an inline parenthetical. Pinned artifacts cite sha256 inline (`sha256 4133...9726` truncated form).

### F6. Math-incompatibility proof for prior contract failures

When a prior version of a criterion is wrong **as math, not just as empirics**, prove it:

```markdown
v2.3 §76 字面：
> "Reject any sample violating ANY channel envelope. PASS = global reject rate < 5%."

数学上的不兼容：

$$\text{H2}^\text{static}: r_\text{global} = \mathbb{E}[\mathbb{1}(X_s \notin \text{env})] < 0.05$$

但 RTF 数据：

$$\mathbb{P}(X_s \notin \text{env} \mid c \to c_\text{EOL}) \to 1 \quad \text{by design}$$

故 $r_\text{global}$ 必然大 → 永远 FAIL。
```

This is the strongest move in 4.27 — a prior gate is shown to be math-impossible, not just empirically failed. Use this whenever a contract revision retracts a criterion on principled (not empirical) grounds.

### F7. Empirical readout table with `(c) 独立复现` column — NON-NEGOTIABLE

Every empirical number in the headline result table has a side-by-side **independent reproducer column**:

```markdown
| 项 | 值 | (c) 独立复现 |
|---|---|---|
| H2 global reject | 0.5655 | 0.5582 |
| HGBT regression Spearman ρ | **0.9326** | 0.9326 |
| 5-pin pre/post bit-identity | all match | all match |
```

Numbers without a 独立复现 column are not headline-acceptable; they go to a "单 seed 观察 / informational diagnostic" supplementary table with explicit labeling. This column **is** the artifact-grounded review evidence written into the readout — without it, a paper-facing claim cannot use the table.

### F8. Axis-structured amendments

When a contract / impl revision bundles multiple changes, organize them as numbered Axes with sub-items:

```markdown
## 5. v3.1 amendment 方法学（5 个 axis）

### 5.1 Axis 1 — H4 audit-table 对齐 (mix i+iii)
### 5.2 Axis 2 — Step 6a demote + drift 字段
### 5.3 Axis 3 — H2 cycle-K healthy-only
### 5.4 Axis 4 — HGBT regression-only
### 5.5 Axis 5 NEW — 5 sub-items 3-way 分类
```

When an Axis itself has internal heterogeneity, give it a 3-way (or N-way) sub-frame **categorization table**:

```markdown
| Sub-frame | Sub-item | 内容 |
|---|---|---|
| Calibration-drift | **5.1** | H1 demote 到 informational |
| Calibration-drift | **5.4** | Cohort-scope coherence |
| Validator/governance | **5.2** | H5 / `n_units` dev-only 7 → 全 12 unit |
| Validator/governance | **5.3** | 新 JSON 加 `global_conclusion` 键 |
| Wording cleanup | **5.5** | `H1_per_channel_ops_overlap` → `H1_per_channel_overlap` |
```

### F9. Risk roster as "comparability-neutral vs 已主动避开" pairing

Risk discussion is **two sub-lists**, not a generic risk paragraph:

```markdown
### 6.3 风险盘点

**当前 (v3.1 picks) comparability-neutral**：
- 5-pin guards 全 untouched
- 4-substep chain recipe / canonical-hash recipe / RTF 退化模型 / 工况采样: 全 untouched
- v2+ headline ρ=+0.587 / c6c3 / b1b3 paper number 不需要重跑

**两条会触发 comparability-critical declaration 的路（已主动避开）**：
- Axis 2 (i)/(iv): 重做 affine calibration JSON → 失效 5-pin → v2+ baseline_audit 全部要重算
- Axis 4 (i): 强制 N≥24 unit regen → multi-week 重算 + dataset_v1_seed42.h5 被 supersede
```

Frame risks as **what we deliberately avoided + why**, not "things that could go wrong". The "避开" framing is what makes the readout decision-grade rather than worry-grade.

### F10. ASCII timeline / 顺序路径 in fenced code blocks

For multi-day timelines and sequential work plans, use ASCII arrows in a fenced code block:

````markdown
### 6.1 4-day timeline

```
2026-04-23  v2+ deck 汇报 (ρ=+0.326)
            ↓ 当晚 thesis Ch.5 reframing
2026-04-26  framing decision aide → Data Descriptor 路线
            D-scope v1 contract FROZEN → impl STOP at pilot gate
            (Defect #1 H6 不可能 + Defect #2 单位错乱)
2026-04-27  v2 → v2.1 → v2.2 → v2.3 (3 rounds (a) review) FROZEN
            v3 DRAFT → v3 (a) round-1 BLOCKING (Axis 5 新增)
            v3.1 DRAFT  ← 我们在这里
```

### 6.2 顺序路径（不能并发）

```
v3.1 DRAFT (今天)
  → user review
  → 下一 session: round-2 (a) dispatch (NEW codex thread)
  → round-2 verdict converge
  → user FREEZE 授权
  → v3.1 impl session: validator script 5 处 fix
  → v3.1 (c) re-review
  → 解锁 paper-facing 引用
```
````

The "← 我们在这里" anchor and the explicit "（不能并发）" labeling are signature moves.

### F11. Claim 演化 vs 上一份 deck (comparison table)

A dedicated section, not a paragraph:

```markdown
## 7. Claim 演化 (vs 4.23 deck)

| 维度 | 4.23 deck | 4.27 现状 |
|---|---|---|
| 主线发表载体 | method paper (暗示) | **Data Descriptor** (archetype B 主文) |
| 数据集本体 | 1344-trace legacy pool | **N=12 RTF dataset_v1_seed42.h5** |
| Usability 证据 | ρ=+0.326 (157 flights) | ρ=+0.326 不变 + **HGBT severity-rank ρ=0.9326** |
| 接受准则 | composite H1-H8 全 PASS | **per-criterion**: 6 gate + 4 informational diagnostic |
| Failure 证据 | 无 (deck 全部正向) | (c) review 暴露 calibration drift +10% N1 / +5% EGT |
| Comparability | v2+ headline 守住 | 仍守住；新 dataset 独立 |
```

One row per dimension that moved. **What stayed the same** also gets rows — they are the conservation evidence.

### F12. Q&A 备料 — preempt actual likely critiques, NOT generic FAQs

For 组会 decks, this section is mandatory. Each Q must be **anchored in a specific likely audience challenge**, not a generic FAQ. The 4.27 exemplar:

- **Q1**: 为什么不直接修 impl，要走 amendment? → because impl is correct (4-substep chain bit-exact + 5-pin 守恒 + canonical hash 匹配); the contract is what needs modification.
- **Q2**: N=12 是不是太少? → yes; written into §6.1 limitation; severity regression unaffected (ρ=0.9326).
- **Q3**: Calibration drift +10% N1 published 出去会不会被 reject? → Data Descriptor venue 评审重视 honest limitation > 漂亮数字 (cite N-CMAPSS PHM Society Data Challenge 2021 precedent).
- **Q4**: 4 天产生 v1 → v2.3 → v3 → v3.1 chain 是不是过快? → 每轮 (a) review 都是独立 codex artifact-grounded review; 所有 verdict 有 archived dual artifact.
- **Q5**: v2+ headline ρ=+0.326 如何 "接住"? → not redone, not retracted; enters Data Descriptor §6.1 usability validation.

Each answer (a) acknowledges the challenge directly, (b) cites a concrete artifact / precedent / mechanism, (c) does not retreat. Generic FAQ-style answers ("good question, we plan to investigate") are rejected.

### F13 (附录). Two-block 附录: commit + artifact + schema

附录 A is two tables — commits and artifacts:

```markdown
## 附录 A：关键 commit 与 artifact 索引

| Commit | 对象 |
|---|---|
| `8360180` | v3 DRAFT |
| `a27b327` | v3 (a) round-1 dual review verdict (BLOCKING) |
| `3ad3f8e` | **v3.1 DRAFT**（今天） |

| Artifact | 路径 |
|---|---|
| v2.3 FROZEN contract | `outputs/reports/<bundle>/run_*/research_contract_v1.md` |
| 数据集 HDF5 | `outputs/reports/<bundle>/run_*/dataset_v1_seed42.h5` |
| H1-H8 readout | `outputs/reports/<bundle>/run_*/validation_report_seed42.json` |
| 5-pin pre/post 哈希 | `outputs/reports/<bundle>/run_*/_pin_hash_post_impl_v2.json` |
```

附录 B (when a data artifact is the deliverable): HDF5 / NPZ / file-tree schema as ASCII tree:

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
*End <date> <descriptor>. 承接 <prior deck/commit>; 时段 <YYYY-MM-DD> → <YYYY-MM-DD> 进度 N 天. 下一 session（<next action>）需 <user 授权 | ...>.*
```

---

## Required structure (full skeleton)

```
# <title> 进度汇报          ← F1 Header
0. 承接                      ← prior deck headline numbers + 框架 reframing reason
1. <主题主体>                ← e.g. 数据集构造方法
   1.1 物理框架与符号        ← F2 symbol table
   1.2 ... 1.k               ← F3 acceptance criteria + F4 defect history + F5 sub-step recipe
2. 验证方法学：H1-H8 接受准则  ← F3 master table (multi-version status columns)
3. 实证 readout              ← F7 (c) 独立复现 column NON-NEGOTIABLE
4. <病灶诊断>                ← F6 math-incompatibility proof (when applicable)
5. <amendment 方法学>         ← F8 axis structure + sub-frame categorization
6. 当前位置与下一步           ← F10 ASCII timeline + 顺序路径
   6.3 风险盘点              ← F9 comparability-neutral vs 已避开
7. Claim 演化 (vs 上一份)     ← F11 comparison table
8. Q&A 备料                   ← F12 preempt actual critiques (mandatory for 组会)
附录 A: commit + artifact     ← F13
附录 B: schema (when applicable)
*End footer line*
```

Skip a section only if it does not apply. Never skip Header, §3 readout, §6, or 附录 A.

---

## Reject-grade signals (any of these makes the readout fail the bar)

1. **No function-name lists.** "通过 `compute_spearman_per_seed_per_flight()` 计算 ρ" is forbidden. Describe as math: "对 157 条 cohort flights 上的残差计算 Spearman ρ(residual, alert_count), 在 3 个 seed 上独立训练后报告均值 ± std." Code pointers (file:line) only in 附录.
2. **No `def` / class blocks** in body. Reproducibility pseudocode → 附录 fenced block, never §1/2/3 method.
3. **Every empirical number in §3 has a `(c) 独立复现` column** (F7). Numbers lacking this column → either move to informational diagnostic with "单 seed 观察, 不作主线证据" label, or remove. **This rule alone enforces dual-review at boundary (c) within the readout itself.**
4. **Math-impossible criteria are proved, not narrated** (F6). When demoting/retracting a gate on principled grounds, write the formal proof.
5. **LaTeX math, not Unicode hacks.** `$\eta_\text{LPC}$` not `η_LPC`. (Inline integers / percentages can stay plain text.)
6. **Anti-confusion annotations on direction-sensitive formulas** (F5). Sign / unit / order / inclusion ambiguity → inline parenthetical.
7. **Pinned artifacts cite sha256 inline** in truncated form (e.g. `sha256 4133...9726`).
8. **Defect 历史 inline, not deleted** (F4). Provenance is a feature.
9. **Risk roster uses 避开-framing** (F9), not generic worry-list.
10. **承接 / 时段 / 下一 session in Footer mandatory** even for self-contained readouts.
11. **Figures: real-artifact only**. Concept diagrams (timeline boxes, pipeline frames, architecture盒图) explicitly punted to "PPT 版式阶段生成" in Header.
12. **Q&A 备料 questions preempt actual critiques** (F12), not generic FAQs. "Why are results good?" is rejected; "Why didn't you just rerun impl instead of amending the contract?" is accepted.
13. **Single-seed numbers labeled in-line** "单 seed 观察, 不作主线证据" — same line as the number.
14. **Un-dual-reviewed paper-facing claims explicitly flagged**: "本节为 executor 单边判读, 待 dual review 后才进 paper-facing 用途." Do not silently let an un-reviewed claim into a deck for paper use.

---

## Triggering checklist (before writing a single line)

Confirm with the user (or from conversation context):

- [ ] File location (`presentation_*/...md` vs `outputs/reports/.../readout.md` vs `docs/methodology-notes/...`).
- [ ] 承接 commit / deck / contract.
- [ ] 是否含本轮新跑实验? If 新跑, the run path must already exist with frozen artifacts before drafting (no synthesizing the future).
- [ ] Audience: 导师 / 组会 / 自留 / 投稿. Q&A 备料 is mandatory for 组会, optional otherwise.
- [ ] Whether figures exist in artifact tree, or need a separate render step (out of this skill's scope).
- [ ] Whether `(c) 独立复现` column data is available for §3. If not, either flag the readout as pre-(c) draft or scope to non-paper-facing 自留 use.
- [ ] Whether any planned claim crosses a dual-review boundary (cf. project rule 3) without dual review — if yes, flag and gate.

## Reference exemplars (read before writing)

- **Primary**: `presentation_4.27/group_meeting_2026-04-27.md` — full deck (Header + 8 body sections + Q&A + 2 附录). All 13 fingerprints exhibited.
- **Secondary**: `presentation_4.23/report.md` — 导师汇报 leading with 研究转向 + 主线强化 + 后续研究, real-data figure references throughout. Use only when the readout's primary structure is 转向叙事.

When in doubt, mirror 4.27 section by section.
