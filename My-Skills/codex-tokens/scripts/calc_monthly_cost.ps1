param ()

<#
calc_monthly_cost.ps1

Purpose:
- Read monthly Markdown files under ./data.
- File format: YYYYMM.md.
- Read the CostUSD column.
- Sum daily CostUSD values for each month.
- Write the result to ./CostUSD.md.

Expected row format:
| Date | InputTokens | OutputTokens | TotalTokens | CostUSD | Status |
| 20260510 | ... | ... | ... | 0.123456 | NEW |
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataDir = Join-Path $scriptDir "data"
$outputFile = Join-Path $scriptDir "CostUSD.md"

if (-not (Test-Path $dataDir)) {
    Write-Host "ERROR: data directory was not found: $dataDir" -ForegroundColor Red
    exit 1
}

$monthFiles = Get-ChildItem -Path $dataDir -Filter "*.md" | Sort-Object Name

if ($monthFiles.Count -eq 0) {
    Write-Host "ERROR: no Markdown files were found under: $dataDir" -ForegroundColor Red
    exit 1
}

$results = @()

foreach ($file in $monthFiles) {

    $monthName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)

    if ($monthName -notmatch '^\d{6}$') {
        continue
    }

    $monthTotal = 0.0
    $validRows = 0

    $lines = Get-Content -Path $file.FullName -Encoding utf8

    foreach ($line in $lines) {

        if ($line -notmatch '^\|\s*\d{8}\s*\|') {
            continue
        }

        $parts = $line -split '\|'

        if ($parts.Count -lt 7) {
            continue
        }

        $date = $parts[1].Trim()
        $costText = $parts[5].Trim()
        $status = $parts[6].Trim()

        # CONFLICT rows are audit records, not trusted baseline rows.
        # Therefore they are excluded from monthly cost calculation.
        if ($status -eq "CONFLICT") {
            continue
        }

        try {
            $cost = [double]$costText
            $monthTotal += $cost
            $validRows += 1
        }
        catch {
            continue
        }
    }

    $results += [PSCustomObject]@{
        Month = $monthName
        Days = $validRows
        CostUSD = $monthTotal
    }
}

$grandTotal = 0.0
foreach ($item in $results) {
    $grandTotal += [double]$item.CostUSD
}

$outputLines = @()
$outputLines += "| Month | Days | CostUSD |"
$outputLines += "|-------|------|---------|"

foreach ($item in $results) {
    $formattedCost = "{0:F6}" -f ([double]$item.CostUSD)
    $outputLines += "| $($item.Month) | $($item.Days) | $formattedCost |"
}

$outputLines += "| TOTAL | - | $(""{0:F6}"" -f $grandTotal) |"

$outputLines | Set-Content -Path $outputFile -Encoding utf8

Write-Host "DONE. Monthly cost summary written to: $outputFile"
Write-Host ("TOTAL CostUSD: {0:F6}" -f $grandTotal)