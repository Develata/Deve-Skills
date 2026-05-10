#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
OUTPUT_FILE="$SCRIPT_DIR/CostUSD.md"

if [[ ! -d "$DATA_DIR" ]]; then
    echo "ERROR: data directory was not found: $DATA_DIR" >&2
    exit 1
fi

shopt -s nullglob
MONTH_FILES=("$DATA_DIR"/*.md)
shopt -u nullglob

if [[ ${#MONTH_FILES[@]} -eq 0 ]]; then
    echo "ERROR: no Markdown files were found under: $DATA_DIR" >&2
    exit 1
fi

{
    echo "| Month | Days | CostUSD |"
    echo "|-------|------|---------|"
} > "$OUTPUT_FILE"

GRAND_TOTAL="0"

for file in "${MONTH_FILES[@]}"; do
    filename="$(basename "$file")"
    month="${filename%.md}"

    if [[ ! "$month" =~ ^[0-9]{6}$ ]]; then
        continue
    fi

    result="$(
        awk -F'|' '
            function trim(s) {
                gsub(/^[ \t\r\n]+/, "", s)
                gsub(/[ \t\r\n]+$/, "", s)
                return s
            }

            BEGIN {
                total = 0
                days = 0
            }

            /^\|[[:space:]]*[0-9]{8}[[:space:]]*\|/ {
                date = trim($2)
                cost = trim($6)
                status = trim($7)

                if (status == "CONFLICT") {
                    next
                }

                if (cost ~ /^-?[0-9]+(\.[0-9]+)?$/) {
                    total += cost
                    days += 1
                }
            }

            END {
                printf "%d %.6f", days, total
            }
        ' "$file"
    )"

    days="$(echo "$result" | awk '{print $1}')"
    month_total="$(echo "$result" | awk '{print $2}')"

    printf '| %s | %s | %.6f |\n' "$month" "$days" "$month_total" >> "$OUTPUT_FILE"

    GRAND_TOTAL="$(
        awk -v a="$GRAND_TOTAL" -v b="$month_total" 'BEGIN {
            printf "%.6f", a + b
        }'
    )"
done

printf '| TOTAL | - | %.6f |\n' "$GRAND_TOTAL" >> "$OUTPUT_FILE"

echo "DONE. Monthly cost summary written to: $OUTPUT_FILE"
echo "TOTAL CostUSD: $GRAND_TOTAL"