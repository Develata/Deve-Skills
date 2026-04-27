# (c) Post-Impl Dual Review Artifact — <implementation subject>

<!--
USAGE
=====

This template scaffolds a (c) post-impl dual-review artifact per:
- Harness rule 3(c): 代码 / readout 写完后 — post-implementation
  verification review. **reviewer 必须独立重跑 source-code trace + 独立
  复现 readout 经验数值**；不接受 executor 自评、不接受单源数字、不接受
  "caveat 写在 commit body 里"代替正式 review、不接受"我自己 catch 了
  问题"代替独立第二意见.
- AGENTS.md "Dual Artifact Header Annotation Rule"
- .claude/skills/codex-orchestration/SKILL.md §1 + §"Account Dispatch Priority"
- .claude/skills/artifact-grounded-review/SKILL.md

(c) IS THE STRICTEST OF THE THREE BOUNDARIES. The reviewer (Codex on a
different account from the executor when account-multiplexed) must:
1. Independently re-run the source-code trace from the frozen contract
   forward through the implementation.
2. Independently reproduce every empirical readout number cited as
   paper-facing or as gate-evidence — not just inspect the executor's
   JSON.
3. Cite file:line / artifact:key for EVERY claim.

PRE-WRITING CHECKLIST
- [ ] Reviewer (Codex) has independently:
      - re-run scripts (or step-by-step simulation in the artifact-grounded
        sense) for at least 1 unit / 1 batch / 1 cycle
      - recomputed canonical hashes if H8-class reproducibility applies
      - re-derived statistical claims (Spearman ρ, accuracy, CoV, etc.)
      - verified file structure matches contract spec (HDF5 schema, JSON
        keys, etc.)
      - re-hashed all dependency pin guards pre-run vs post-run
- [ ] Pre-review independence note: write your local first-pass findings to
      `/tmp/claude_pre_review_<short-id>.md` BEFORE reading the second
      reviewer's output.
- [ ] Run `scripts/codex_session_meta.sh <threadId>` and paste its 5-line
      stdout verbatim into the Header annotation block below.
- [ ] CRITICAL: do NOT accept the executor's self-reported numbers as
      authoritative. The reviewer's job is to either reproduce them or
      refute them with independent computation.

REPLACE every `<placeholder>` and remove this comment block before commit.
-->

## Header annotation (verbatim from `scripts/codex_session_meta.sh`)

```
<paste 5-line helper stdout here>
```

> Source disambiguation: see `session_path` line above. Note: per harness rule 3(c), the reviewer's account SHOULD differ from the executor's account when the implementation involved Codex (e.g. executor on codex-main → reviewer on codex-b) to avoid same-account confirmation bias.

## Implementation under review

- **Frozen contract**: `<path:line>` at commit `<hash>`
- **Implementation commits being reviewed**: `<commit hash 1>`, `<commit hash 2>`, ...
- **Run dir**: `outputs/reports/<experiment_name>/run_YYYYMMDD_<descriptor>/`
- **Primary output artifacts**: `<list HDF5 / JSON / NPZ paths>`

## Pre-review independence

- Local pre-review note (written before reading reviewer output): `</tmp/claude_pre_review_<short-id>.md>`
- Second reviewer model + threadId: `<model>` (`<threadId>`)
- Reviewer account differs from executor account? **<yes — executor=codex-X, reviewer=codex-Y / no — explain why same account>**
- Both reviewers independently re-ran source-code trace + reproduced readout numbers? **<yes / no — block until yes>**

## Track + comparability scope

- Track: `<B | governance | skills | docs | infra | outputs>`
- Comparability-critical touched: `<no | yes — list affected runs>`
- Pin guards verified bit-identical pre vs post? `<yes — N pins | no — what changed>`

## Verdict

**<ACCEPT | ACCEPT_WITH_CAVEATS | REJECT_REOPEN_AMENDMENT | STOP_AND_AMEND_v_NEXT>**

One-paragraph verdict statement:

<text>

## Independent reproduction of source-code trace

| # | Contract clause | Implementation file:line | Reviewer's independent trace | Match? |
|---|-----------------|--------------------------|-------------------------------|--------|
| 1 | `<§4.3 EOL pre-clamp>` | `<src/...:123-145>` | `<reviewer's step-by-step>` | `<yes / no — discrepancy>` |
| 2 | ... | ... | ... | ... |

## Independent reproduction of empirical readout numbers

| # | Number cited in executor readout | Source artifact:key | Reviewer's independent value | Match within tolerance? |
|---|----------------------------------|---------------------|------------------------------|--------------------------|
| 1 | `<H1 overlap_qar = 0.83>` | `<validation_report_seed42.json:H1.overlap_qar>` | `<reviewer recomputed: 0.83>` | `<yes>` |
| 2 | `<HGBT classification top-1 = 0.0105>` | `<usability_validation_seed42.json:hgbt_classification.top1>` | `<...>` | `<...>` |
| 3 | `<canonical_content_hash = c8dad...>` | `<dataset_v1_seed42.content_sha256>` | `<reviewer rehashed: ...>` | `<...>` |

If ANY row is `no — discrepancy`, the verdict cannot be `ACCEPT`.

## Per-criterion (or per-hypothesis) findings

| # | Criterion | Executor result | Reviewer-confirmed result | Status |
|---|-----------|-----------------|---------------------------|--------|
| H1 | `<...>` | `<PASS / FAIL>` | `<PASS / FAIL>` | `<CONFIRMED / DISPUTED>` |
| H2 | ... | ... | ... | ... |

## Pin guard re-hash

| Pin target | Pre-run hash | Post-run hash | Pre = post? |
|------------|--------------|---------------|-------------|
| `<v2+ checkpoint_G0_42.pkl>` | `<sha>` | `<sha>` | `<yes / no — STOP>` |
| `<v2+ normalization_stats.json>` | `<sha>` | `<sha>` | `<yes / no>` |
| ... | ... | ... | ... |

## Wording discipline check

- Does the executor's commit body / readout text describe `operational label` / `review outcome` / `feedback outcome` as fault truth? `<no / yes — flag>`
- Does it conflate `governance/release improvement` with `detector/model optimization gain`? `<no / yes — flag>`
- Does it keep `statistics_only` and `diagnosis_usability` conclusions clearly separated? `<yes / no — flag>`

## Blocking findings (if any)

If verdict is not `ACCEPT`, list each blocking finding with:

1. **<finding title>** — `<one-paragraph explanation>`
   - Evidence: `<file:line / artifact:key>`
   - Required fix: `<what must change before acceptance>`
   - Affected paper-facing claims: `<list claims that become unverified>`

## Independent factual claims verified

| Claim | Evidence (file:line / artifact:key) |
|-------|-------------------------------------|
| `<claim 1>` | `<source>` |

## Disposition / next step

- [ ] Verdict block paper-facing promotion of any number from this run? `<yes — list claims>` / `<no>`
- [ ] v_NEXT amendment chain needed? `<yes — scope of amendment>` / `<no>`
- [ ] Worklog entry written same turn per AGENTS.md:368-394? `<yes — link>`
- [ ] Topical doc updated? `<yes — link>` / `<n/a>`

## Archival metadata

- Run dir: `outputs/reports/<experiment_name>/run_YYYYMMDD_<descriptor>/`
- Reviewer pre-review note: `/tmp/claude_pre_review_<short-id>.md` (committed to run dir as `pre_review_archive/` if blocking findings present)
- Commit hash that introduces this artifact: `<filled at commit time>`
- Frozen contract being verified: `<path>` at commit `<hash>`

---

*End (c) post-impl dual review artifact. Per harness rule 3(c) cross-session responsibility transfer: if the next session inherits paper-facing work that uses any number from this run BEFORE this artifact reaches `ACCEPT` verdict, the next session MUST run / re-run the (c) review before proceeding.*
