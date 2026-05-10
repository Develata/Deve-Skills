---
name: codex-tokens
description: Collect and audit Codex token usage with a bundled Python CLI and optional Windows batch launchers. Use this skill when the user asks to check Codex token usage, generate daily token audit logs, calculate monthly CostUSD totals, review Codex spending, or run Codex token usage scripts on Windows, Bash, WSL, or Linux.
---

# Codex Token Usage Audit

Use `scripts/codex_tokens.py` to collect Codex token usage into daily audit logs and calculate monthly `CostUSD` totals.

## Files

```text
scripts/
├─ codex_tokens.py
├─ run_codex_tokens.bat
└─ calc_monthly_cost.bat
```

## Requirements

- Python 3.8 or newer.
- `bunx` for `collect`.
- No third-party Python packages.
- Use `python3` on macOS/Linux/WSL. If only `python` exists, use it after confirming `python --version` reports Python 3.8+.

## Collect Daily Usage

Run the collector from the skill root.

```bash
python3 scripts/codex_tokens.py collect --since-days 40 --align-window 2
```

Windows double-click entry:

```text
scripts/run_codex_tokens.bat
```

The collector writes monthly daily logs:

```text
scripts/data/YYYYMM.md
```

Each daily log uses this row format:

```markdown
| Date | InputTokens | CachedInputTokens | OutputTokens | ReasoningOutputTokens | TotalTokens | CostUSD | Models | FallbackModels | Status |
```

## Calculate Monthly Cost

Run after collecting daily usage:

```bash
python3 scripts/codex_tokens.py summary
```

Windows double-click entry:

```text
scripts/calc_monthly_cost.bat
```

The calculator writes:

```text
scripts/CostUSD.md
```

## Audit Logic

Treat `scripts/data/YYYYMM.md` as the daily audit log and `scripts/CostUSD.md` as the monthly summary. `scripts/.gitignore` excludes both generated output paths from Git.

`collect` updates an existing trusted row only after finding `AlignWindow` consecutive matching days. A day matches when `InputTokens`, `CachedInputTokens`, `OutputTokens`, `ReasoningOutputTokens`, `TotalTokens`, `CostUSD`, `Models`, and `FallbackModels` all match; `CostUSD` equality uses a `1e-6` tolerance.

Interpret statuses as follows:

- `NEW`: append a newly observed day.
- `UPDATED`: update a trusted row because `CostUSD` increased after the alignment window.
- `CONFLICT`: append a suspicious mismatch and never overwrite the trusted row.

Exclude `CONFLICT` rows from `scripts/CostUSD.md`.

## Safety Notes

Run `collect` only when the user wants to query local Codex usage data. Do not fabricate usage data. If `bunx @ccusage/codex@latest` fails or returns unexpected JSON, report the failure before changing audit files.
