#!/usr/bin/env bash

set -euo pipefail

SINCE_DAYS=40
ALIGN_WINDOW=2

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--since-days)
            SINCE_DAYS="$2"
            shift 2
            ;;
        -a|--align-window)
            ALIGN_WINDOW="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--since-days N] [--align-window N]"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"

mkdir -p "$DATA_DIR"

# ---------------------------
# Check dependencies
# ---------------------------
if ! command -v bunx >/dev/null 2>&1; then
    echo "ERROR: bunx was not found. Please install bunx first." >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq was not found. Please install jq first." >&2
    exit 1
fi

BUNX_VERSION="$(bunx --version 2>&1 || true)"

if [[ ! "$BUNX_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]]; then
    echo "ERROR: bunx was not found or the version format is invalid." >&2
    echo "bunx output: $BUNX_VERSION" >&2
    exit 1
fi

echo "Detected bunx version: $BUNX_VERSION"

# ---------------------------
# Date helper
# ---------------------------
if date -d "today" "+%Y%m%d" >/dev/null 2>&1; then
    SINCE_DATE="$(date -d "$SINCE_DAYS days ago" "+%Y%m%d")"
else
    echo "ERROR: GNU date is required. This script is intended for Linux or WSL." >&2
    exit 1
fi

echo "Running command: bunx @ccusage/codex@latest daily --json --since $SINCE_DATE"

JSON_TEXT="$(bunx @ccusage/codex@latest daily --json --since "$SINCE_DATE")"

if ! echo "$JSON_TEXT" | jq -e '.daily' >/dev/null 2>&1; then
    echo "ERROR: Failed to parse ccusage daily JSON." >&2
    exit 1
fi

TMP_TSV="$(mktemp)"
trap 'rm -f "$TMP_TSV"' EXIT

echo "$JSON_TEXT" | jq -r '
    .daily[]
    | [
        (.date | gsub("-"; "")),
        .inputTokens,
        .outputTokens,
        .totalTokens,
        .costUSD
      ]
    | @tsv
' | awk -F'\t' '
    {
        day=$1;
        month=substr(day, 1, 6);
        print month "\t" day "\t" $2 "\t" $3 "\t" $4 "\t" $5;
    }
' > "$TMP_TSV"

if [[ ! -s "$TMP_TSV" ]]; then
    echo "No daily data was returned."
    exit 0
fi

# ---------------------------
# Helper functions
# ---------------------------
cost_equal() {
    local a="$1"
    local b="$2"

    awk -v a="$a" -v b="$b" 'BEGIN {
        diff = a - b
        if (diff < 0) diff = -diff
        exit !(diff < 0.000001)
    }'
}

cost_less() {
    local a="$1"
    local b="$2"

    awk -v a="$a" -v b="$b" 'BEGIN {
        exit !(a < b)
    }'
}

cost_greater() {
    local a="$1"
    local b="$2"

    awk -v a="$a" -v b="$b" 'BEGIN {
        exit !(a > b)
    }'
}

record_aligned() {
    local old_input="$1"
    local old_output="$2"
    local old_total="$3"
    local old_cost="$4"

    local new_input="$5"
    local new_output="$6"
    local new_total="$7"
    local new_cost="$8"

    [[ "$old_input" == "$new_input" ]] || return 1
    [[ "$old_output" == "$new_output" ]] || return 1
    [[ "$old_total" == "$new_total" ]] || return 1
    cost_equal "$old_cost" "$new_cost" || return 1

    return 0
}

new_token_line() {
    local date="$1"
    local input="$2"
    local output="$3"
    local total="$4"
    local cost="$5"
    local status="$6"

    printf '| %s | %s | %s | %s | %s | %s |\n' \
        "$date" "$input" "$output" "$total" "$cost" "$status"
}

replace_line_in_file() {
    local file="$1"
    local line_number="$2"
    local new_line="$3"
    local tmp_file

    tmp_file="$(mktemp)"

    awk -v n="$line_number" -v replacement="$new_line" '
        NR == n { print replacement; next }
        { print }
    ' "$file" > "$tmp_file"

    mv "$tmp_file" "$file"
}

trim() {
    local s="$1"

    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"

    printf '%s' "$s"
}

# ---------------------------
# Process each month
# ---------------------------
mapfile -t MONTHS < <(cut -f1 "$TMP_TSV" | sort -u)

for month in "${MONTHS[@]}"; do
    FILE_PATH="$DATA_DIR/$month.md"

    if [[ ! -f "$FILE_PATH" ]]; then
        {
            echo "| Date | InputTokens | OutputTokens | TotalTokens | CostUSD | Status |"
            echo "|------|-------------|--------------|-------------|---------|--------|"
        } > "$FILE_PATH"
    fi

    declare -A OLD_INPUT=()
    declare -A OLD_OUTPUT=()
    declare -A OLD_TOTAL=()
    declare -A OLD_COST=()
    declare -A OLD_STATUS=()
    declare -A OLD_INDEX=()

    line_no=0

    while IFS= read -r line; do
        line_no=$((line_no + 1))

        if [[ ! "$line" =~ ^\|[[:space:]]*[0-9]{8}[[:space:]]*\| ]]; then
            continue
        fi

        IFS='|' read -r _ raw_date raw_input raw_output raw_total raw_cost raw_status _ <<< "$line"

        date_value="$(trim "$raw_date")"
        input_value="$(trim "$raw_input")"
        output_value="$(trim "$raw_output")"
        total_value="$(trim "$raw_total")"
        cost_value="$(trim "$raw_cost")"
        status_value="$(trim "$raw_status")"

        if [[ "$status_value" == "CONFLICT" ]]; then
            continue
        fi

        OLD_INPUT["$date_value"]="$input_value"
        OLD_OUTPUT["$date_value"]="$output_value"
        OLD_TOTAL["$date_value"]="$total_value"
        OLD_COST["$date_value"]="$cost_value"
        OLD_STATUS["$date_value"]="$status_value"
        OLD_INDEX["$date_value"]="$line_no"
    done < "$FILE_PATH"

    CURRENT_LINES=()

    while IFS= read -r row; do
        CURRENT_LINES+=("$row")
    done < <(awk -F'\t' -v m="$month" '$1 == m { print }' "$TMP_TSV" | sort -k2,2)

    CURRENT_COUNT="${#CURRENT_LINES[@]}"
    ALIGNED_END_DATE=""

    if (( CURRENT_COUNT >= ALIGN_WINDOW )); then
        for ((i = 0; i <= CURRENT_COUNT - ALIGN_WINDOW; i++)); do
            window_aligned=1

            for ((j = 0; j < ALIGN_WINDOW; j++)); do
                row="${CURRENT_LINES[$((i + j))]}"

                IFS=$'\t' read -r _ date_value input_value output_value total_value cost_value <<< "$row"

                if [[ -z "${OLD_COST[$date_value]+x}" ]]; then
                    window_aligned=0
                    break
                fi

                if ! record_aligned \
                    "${OLD_INPUT[$date_value]}" \
                    "${OLD_OUTPUT[$date_value]}" \
                    "${OLD_TOTAL[$date_value]}" \
                    "${OLD_COST[$date_value]}" \
                    "$input_value" \
                    "$output_value" \
                    "$total_value" \
                    "$cost_value"
                then
                    window_aligned=0
                    break
                fi
            done

            if (( window_aligned == 1 )); then
                row="${CURRENT_LINES[$((i + ALIGN_WINDOW - 1))]}"
                IFS=$'\t' read -r _ aligned_date _ _ _ _ <<< "$row"
                ALIGNED_END_DATE="$aligned_date"
            fi
        done
    fi

    if [[ -z "$ALIGNED_END_DATE" ]]; then
        echo "[$month] No continuous alignment window of $ALIGN_WINDOW days was found. Existing records will not be overwritten."
    else
        echo "[$month] Found a continuous alignment window of $ALIGN_WINDOW days. Window end date: $ALIGNED_END_DATE"
    fi

    for row in "${CURRENT_LINES[@]}"; do
        IFS=$'\t' read -r _ date_value input_value output_value total_value cost_value <<< "$row"

        if [[ -z "${OLD_COST[$date_value]+x}" ]]; then
            line="$(new_token_line "$date_value" "$input_value" "$output_value" "$total_value" "$cost_value" "NEW")"
            echo "$line" >> "$FILE_PATH"

            OLD_INPUT["$date_value"]="$input_value"
            OLD_OUTPUT["$date_value"]="$output_value"
            OLD_TOTAL["$date_value"]="$total_value"
            OLD_COST["$date_value"]="$cost_value"
            OLD_STATUS["$date_value"]="NEW"
            OLD_INDEX["$date_value"]="$(wc -l < "$FILE_PATH" | tr -d ' ')"

            echo "NEW: $date_value costUSD=$cost_value"
            continue
        fi

        old_cost="${OLD_COST[$date_value]}"
        old_index="${OLD_INDEX[$date_value]}"

        if [[ -n "$ALIGNED_END_DATE" ]] && [[ "$date_value" < "$ALIGNED_END_DATE" || "$date_value" == "$ALIGNED_END_DATE" ]]; then
            continue
        fi

        if [[ -z "$ALIGNED_END_DATE" ]]; then
            if ! record_aligned \
                "${OLD_INPUT[$date_value]}" \
                "${OLD_OUTPUT[$date_value]}" \
                "${OLD_TOTAL[$date_value]}" \
                "${OLD_COST[$date_value]}" \
                "$input_value" \
                "$output_value" \
                "$total_value" \
                "$cost_value"
            then
                line="$(new_token_line "$date_value" "$input_value" "$output_value" "$total_value" "$cost_value" "CONFLICT")"
                echo "$line" >> "$FILE_PATH"
                echo "CONFLICT: $date_value no alignment window, old=$old_cost, new=$cost_value"
            else
                echo "SKIP: $date_value equal but no continuous alignment window"
            fi

            continue
        fi

        if cost_less "$cost_value" "$old_cost"; then
            line="$(new_token_line "$date_value" "$input_value" "$output_value" "$total_value" "$cost_value" "CONFLICT")"
            echo "$line" >> "$FILE_PATH"
            echo "CONFLICT: $date_value cost decreased, old=$old_cost, new=$cost_value"
            continue
        fi

        if cost_greater "$cost_value" "$old_cost"; then
            line="$(new_token_line "$date_value" "$input_value" "$output_value" "$total_value" "$cost_value" "UPDATED")"
            replace_line_in_file "$FILE_PATH" "$old_index" "$line"

            OLD_INPUT["$date_value"]="$input_value"
            OLD_OUTPUT["$date_value"]="$output_value"
            OLD_TOTAL["$date_value"]="$total_value"
            OLD_COST["$date_value"]="$cost_value"
            OLD_STATUS["$date_value"]="UPDATED"

            echo "UPDATED: $date_value costUSD $old_cost -> $cost_value"
            continue
        fi

        if ! record_aligned \
            "${OLD_INPUT[$date_value]}" \
            "${OLD_OUTPUT[$date_value]}" \
            "${OLD_TOTAL[$date_value]}" \
            "${OLD_COST[$date_value]}" \
            "$input_value" \
            "$output_value" \
            "$total_value" \
            "$cost_value"
        then
            line="$(new_token_line "$date_value" "$input_value" "$output_value" "$total_value" "$cost_value" "CONFLICT")"
            echo "$line" >> "$FILE_PATH"
            echo "CONFLICT: $date_value costUSD is equal but token fields differ"
            continue
        fi

        echo "SKIP: $date_value unchanged"
    done

    unset OLD_INPUT
    unset OLD_OUTPUT
    unset OLD_TOTAL
    unset OLD_COST
    unset OLD_STATUS
    unset OLD_INDEX
done

echo
echo "DONE. Data directory: $DATA_DIR"
