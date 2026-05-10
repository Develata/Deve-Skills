---
name: codex-tokens
description: Collect and audit Codex token usage with bundled PowerShell, Bash, and Windows batch scripts. Use this skill when the user asks to check Codex token usage, generate daily token audit logs, calculate monthly CostUSD totals, review Codex spending, or run the codex token usage scripts on Windows, PowerShell, Bash, WSL, or Linux.
---

# Codex Token Usage Audit

Use the bundled scripts to collect Codex token usage, store daily audit logs, and calculate monthly `CostUSD` totals.

## Bundled Scripts

```text
scripts/
├─ codex_tokens.ps1
├─ codex_tokens.sh
├─ run_codex_tokens.bat
├─ calc_monthly_cost.ps1
├─ calc_monthly_cost.sh
└─ calc_monthly_cost.bat
```

Choose the script by environment:

- Use `.bat` files for Windows double-click workflows.
- Use `.ps1` files for PowerShell workflows.
- Use `.sh` files for Bash, WSL, or Linux workflows.

## Requirements

- Install `bunx` before collecting usage.
- Install `jq` before using Bash scripts.
- Use GNU `date` for `codex_tokens.sh`; this is normally available on Linux and WSL.

## Collect Daily Usage

Run the collector from the skill root.

PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex_tokens.ps1 -SinceDays 40 -AlignWindow 2
```

Windows double-click:

```text
scripts/run_codex_tokens.bat
```

Bash, WSL, or Linux:

```bash
chmod +x ./scripts/codex_tokens.sh
./scripts/codex_tokens.sh --since-days 40 --align-window 2
```

The collector writes monthly daily logs:

```text
scripts/data/YYYYMM.md
```

Each daily log uses this row format:

```markdown
| Date | InputTokens | OutputTokens | TotalTokens | CostUSD | Status |
```

## Calculate Monthly Cost

Run the monthly calculator after collecting daily usage.

PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\calc_monthly_cost.ps1
```

Windows double-click:

```text
scripts/calc_monthly_cost.bat
```

Bash, WSL, or Linux:

```bash
chmod +x ./scripts/calc_monthly_cost.sh
./scripts/calc_monthly_cost.sh
```

The calculator writes:

```text
scripts/CostUSD.md
```

## Audit Logic

Treat `scripts/data/YYYYMM.md` as the daily audit log and `scripts/CostUSD.md` as the monthly summary.

`codex_tokens` updates an existing trusted row only after finding `AlignWindow` consecutive matching days. A day matches only when all of these fields are equal:

```text
InputTokens
OutputTokens
TotalTokens
CostUSD
```

Interpret statuses as follows:

- `NEW`: append a newly observed day.
- `UPDATED`: update a trusted row because `CostUSD` increased after the alignment window.
- `CONFLICT`: append a suspicious mismatch and never overwrite the trusted row.

Exclude `CONFLICT` rows from `scripts/CostUSD.md`.

## Safety Notes

Run collection scripts only when the user wants to query local Codex usage data. Do not fabricate usage data. If `bunx @ccusage/codex@latest` fails or returns an unexpected JSON shape, report the failure and inspect the command output before changing audit files.
