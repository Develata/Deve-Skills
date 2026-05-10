param (
    [int]$SinceDays = 40,
    [int]$AlignWindow = 2
)

<#
codex_tokens.ps1

Purpose:
- Use ccusage to collect Codex token usage.
- Create a data folder under the script directory.
- Generate one Markdown file per month.
- File name format: YYYYMM.md.
- Each row represents one day:
  Date | InputTokens | OutputTokens | TotalTokens | CostUSD | Status

Rules:
1. Each month has its own Markdown file.
2. Updates are allowed only after finding a continuous alignment window of AlignWindow days.
3. Records before or inside the alignment window are not modified.
4. After the alignment window:
   - If new costUSD > old costUSD: overwrite as UPDATED.
   - If new costUSD < old costUSD: append as CONFLICT.
   - If costUSD is equal but token fields differ: append as CONFLICT.
5. If no continuous alignment window is found, do not overwrite existing records; append CONFLICT only.
6. New dates are appended as NEW.
#>

# ---------------------------
# Path setup: always use the script directory
# ---------------------------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataDir = Join-Path $scriptDir "data"

if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}

# ---------------------------
# Helper functions
# ---------------------------
function Test-CostEqual {
    param (
        [double]$A,
        [double]$B
    )

    return ([math]::Abs($A - $B) -lt 0.000001)
}

function Parse-TokenLine {
    param (
        [string]$Line
    )

    if ($Line -notmatch '^\|\s*\d{8}\s*\|') {
        return $null
    }

    $parts = $Line -split '\|'

    if ($parts.Count -lt 7) {
        return $null
    }

    try {
        return [PSCustomObject]@{
            Date         = $parts[1].Trim()
            InputTokens  = [int64]($parts[2].Trim())
            OutputTokens = [int64]($parts[3].Trim())
            TotalTokens  = [int64]($parts[4].Trim())
            CostUSD      = [double]($parts[5].Trim())
            Status       = $parts[6].Trim()
            RawLine      = $Line
        }
    }
    catch {
        return $null
    }
}

function Test-RecordAligned {
    param (
        $OldRecord,
        $NewRecord
    )

    if ($null -eq $OldRecord -or $null -eq $NewRecord) {
        return $false
    }

    if ([int64]$OldRecord.InputTokens -ne [int64]$NewRecord.InputTokens) {
        return $false
    }

    if ([int64]$OldRecord.OutputTokens -ne [int64]$NewRecord.OutputTokens) {
        return $false
    }

    if ([int64]$OldRecord.TotalTokens -ne [int64]$NewRecord.TotalTokens) {
        return $false
    }

    if (-not (Test-CostEqual ([double]$OldRecord.CostUSD) ([double]$NewRecord.CostUSD))) {
        return $false
    }

    return $true
}

function New-TokenLine {
    param (
        $Record,
        [string]$Status
    )

    return "| $($Record.Date) | $($Record.InputTokens) | $($Record.OutputTokens) | $($Record.TotalTokens) | $($Record.CostUSD) | $Status |"
}

# ---------------------------
# Check bunx
# ---------------------------
try {
    $bunxVersion = & bunx --version 2>&1
}
catch {
    Write-Host "ERROR: bunx was not found. Please install bunx first." -ForegroundColor Red
    exit 1
}

if (-not $bunxVersion -or $bunxVersion -notmatch '^\d+\.\d+\.\d+') {
    Write-Host "ERROR: bunx was not found or the version format is invalid. Please install bunx first." -ForegroundColor Red
    exit 1
}

Write-Host "Detected bunx version: $bunxVersion"

# ---------------------------
# Get ccusage daily JSON
# ---------------------------
$sinceDate = (Get-Date).AddDays(-$SinceDays).ToString("yyyyMMdd")

Write-Host "Running command: bunx @ccusage/codex@latest daily --json --since $sinceDate"

try {
    $jsonText = & bunx @ccusage/codex@latest daily --json --since $sinceDate
    $json = $jsonText | ConvertFrom-Json
}
catch {
    Write-Host "ERROR: Failed to parse ccusage output as JSON." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

if ($null -eq $json -or $null -eq $json.daily) {
    Write-Host "No daily data was returned."
    exit 0
}

# ---------------------------
# Group current ccusage data by month
# ---------------------------
$daysByMonth = @{}

foreach ($day in $json.daily) {
    $dateObj = Get-Date $day.date
    $monthKey = $dateObj.ToString("yyyyMM")
    $dayKey = $dateObj.ToString("yyyyMMdd")

    if (-not $daysByMonth.ContainsKey($monthKey)) {
        $daysByMonth[$monthKey] = @()
    }

    $record = [PSCustomObject]@{
        Date         = $dayKey
        InputTokens  = [int64]$day.inputTokens
        OutputTokens = [int64]$day.outputTokens
        TotalTokens  = [int64]$day.totalTokens
        CostUSD      = [double]$day.costUSD
    }

    $daysByMonth[$monthKey] += $record
}

# ---------------------------
# Process each month
# ---------------------------
foreach ($monthKey in $daysByMonth.Keys) {

    $filePath = Join-Path $dataDir "$monthKey.md"

    if (-not (Test-Path $filePath)) {
        $header = @(
            "| Date | InputTokens | OutputTokens | TotalTokens | CostUSD | Status |",
            "|------|-------------|--------------|-------------|---------|--------|"
        )

        $header | Set-Content -Path $filePath -Encoding utf8
    }

    $lines = @(Get-Content -Path $filePath -Encoding utf8)

    # Read existing Markdown records.
    # If one date has multiple rows:
    # - CONFLICT rows are treated as audit logs only.
    # - The last non-CONFLICT row is used as the trusted baseline.
    $oldMap = @{}
    $oldIndexMap = @{}

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $parsed = Parse-TokenLine $lines[$i]

        if ($null -eq $parsed) {
            continue
        }

        if ($parsed.Status -ne "CONFLICT") {
            $oldMap[$parsed.Date] = $parsed
            $oldIndexMap[$parsed.Date] = $i
        }
    }

    $currentDays = @($daysByMonth[$monthKey] | Sort-Object Date)

    # ---------------------------
    # Find the latest continuous alignment window
    # ---------------------------
    $alignedEndDate = $null

    if ($currentDays.Count -ge $AlignWindow) {
        for ($i = 0; $i -le ($currentDays.Count - $AlignWindow); $i++) {
            $windowAligned = $true

            for ($j = 0; $j -lt $AlignWindow; $j++) {
                $currentDay = $currentDays[$i + $j]
                $date = $currentDay.Date

                if (-not $oldMap.ContainsKey($date)) {
                    $windowAligned = $false
                    break
                }

                if (-not (Test-RecordAligned $oldMap[$date] $currentDay)) {
                    $windowAligned = $false
                    break
                }
            }

            if ($windowAligned) {
                $alignedEndDate = $currentDays[$i + $AlignWindow - 1].Date
            }
        }
    }

    if ($null -eq $alignedEndDate) {
        Write-Host "[$monthKey] No continuous alignment window of $AlignWindow days was found. Existing records will not be overwritten." -ForegroundColor Yellow
    }
    else {
        Write-Host "[$monthKey] Found a continuous alignment window of $AlignWindow days. Window end date: $alignedEndDate"
    }

    # ---------------------------
    # Process each day
    # ---------------------------
    foreach ($currentDay in $currentDays) {

        $date = $currentDay.Date
        $newCost = [double]$currentDay.CostUSD

        # Case 1: This date does not exist in the old Markdown file.
        if (-not $oldMap.ContainsKey($date)) {
            $newLine = New-TokenLine $currentDay "NEW"
            Add-Content -Path $filePath -Value $newLine -Encoding utf8
            $lines += $newLine

            $oldMap[$date] = [PSCustomObject]@{
                Date         = $currentDay.Date
                InputTokens  = $currentDay.InputTokens
                OutputTokens = $currentDay.OutputTokens
                TotalTokens  = $currentDay.TotalTokens
                CostUSD      = $currentDay.CostUSD
                Status       = "NEW"
                RawLine      = $newLine
            }

            $oldIndexMap[$date] = $lines.Count - 1

            Write-Host "NEW: $date costUSD=$newCost"
            continue
        }

        $oldRecord = $oldMap[$date]
        $oldCost = [double]$oldRecord.CostUSD
        $oldIndex = $oldIndexMap[$date]

        # Case 2: Records before or inside the alignment window are not modified.
        if ($null -ne $alignedEndDate -and $date -le $alignedEndDate) {
            continue
        }

        # Case 3: No alignment window was found.
        if ($null -eq $alignedEndDate) {
            if (-not (Test-RecordAligned $oldRecord $currentDay)) {
                $conflictLine = New-TokenLine $currentDay "CONFLICT"
                Add-Content -Path $filePath -Value $conflictLine -Encoding utf8
                $lines += $conflictLine
                Write-Host "CONFLICT: $date no alignment window, old=$oldCost, new=$newCost" -ForegroundColor Yellow
            }
            else {
                Write-Host "SKIP: $date equal but no continuous alignment window"
            }

            continue
        }

        # Case 4: New cost is smaller than old cost. Do not overwrite.
        if ($newCost -lt $oldCost) {
            $conflictLine = New-TokenLine $currentDay "CONFLICT"
            Add-Content -Path $filePath -Value $conflictLine -Encoding utf8
            $lines += $conflictLine
            Write-Host "CONFLICT: $date cost decreased, old=$oldCost, new=$newCost" -ForegroundColor Yellow
            continue
        }

        # Case 5: New cost is greater than old cost. Overwrite as UPDATED.
        if ($newCost -gt $oldCost) {
            $updatedLine = New-TokenLine $currentDay "UPDATED"
            $lines[$oldIndex] = $updatedLine
            $lines | Set-Content -Path $filePath -Encoding utf8

            Write-Host "UPDATED: $date costUSD $oldCost -> $newCost"

            $oldMap[$date] = [PSCustomObject]@{
                Date         = $currentDay.Date
                InputTokens  = $currentDay.InputTokens
                OutputTokens = $currentDay.OutputTokens
                TotalTokens  = $currentDay.TotalTokens
                CostUSD      = $currentDay.CostUSD
                Status       = "UPDATED"
                RawLine      = $updatedLine
            }

            $oldIndexMap[$date] = $oldIndex

            continue
        }

        # Case 6: costUSD is equal but token fields differ.
        if (-not (Test-RecordAligned $oldRecord $currentDay)) {
            $conflictLine = New-TokenLine $currentDay "CONFLICT"
            Add-Content -Path $filePath -Value $conflictLine -Encoding utf8
            $lines += $conflictLine
            Write-Host "CONFLICT: $date costUSD is equal but token fields differ" -ForegroundColor Yellow
            continue
        }

        Write-Host "SKIP: $date unchanged"
    }
}

Write-Host ""
Write-Host "DONE. Data directory: $dataDir"
