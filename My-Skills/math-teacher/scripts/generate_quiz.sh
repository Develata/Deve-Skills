#!/bin/bash
# Math Teacher - Quiz Generator
set -e

# Defaults
TOPIC="基础数学"
OUTPUT_FILE="math-quiz.html"
OUTPUT_DIR="./math-quizzes"
CUSTOM_DATA=""

# Parse Arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --topic) TOPIC="$2"; shift ;;
        --output) OUTPUT_FILE="$2"; shift ;;
        --questions) CUSTOM_DATA="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Resolve Paths
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
TEMPLATE_PATH="$SCRIPT_DIR/../assets/templates/games/quiz.html"
OUTPUT_PATH="$OUTPUT_DIR/$OUTPUT_FILE"

if [[ ! -f "$TEMPLATE_PATH" ]]; then
    echo "Error: Template not found at $TEMPLATE_PATH"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Generating Quiz for $TOPIC..."

# --- Data Generation Logic ---

if [[ -n "$CUSTOM_DATA" ]]; then
    # Use provided JSON data if available
    QUIZ_DATA="$CUSTOM_DATA"
else
    # Generate default data based on topic
    case $TOPIC in
        *"乘法"*|*"Multiplication"*)
            QUIZ_DATA='[
                { "q": "7 x 8 = ?", "options": ["54", "56", "58", "62"], "a": 1 },
                { "q": "9 x 6 = ?", "options": ["54", "52", "48", "56"], "a": 0 },
                { "q": "12 x 12 = ?", "options": ["124", "142", "144", "148"], "a": 2 },
                { "q": "5 x 15 = ?", "options": ["65", "70", "75", "80"], "a": 2 },
                { "q": "25 x 4 = ?", "options": ["100", "90", "110", "120"], "a": 0 }
            ]'
            ;;
        *"除法"*|*"Division"*)
            QUIZ_DATA='[
                { "q": "56 / 8 = ?", "options": ["6", "7", "8", "9"], "a": 1 },
                { "q": "81 / 9 = ?", "options": ["9", "8", "7", "6"], "a": 0 },
                { "q": "144 / 12 = ?", "options": ["10", "11", "12", "13"], "a": 2 },
                { "q": "100 / 25 = ?", "options": ["2", "3", "4", "5"], "a": 2 },
                { "q": "42 / 6 = ?", "options": ["7", "6", "8", "5"], "a": 0 }
            ]'
            ;;
        *"代数"*|*"Algebra"*)
            QUIZ_DATA='[
                { "q": "Solve for x: 2x + 5 = 15", "options": ["x=5", "x=10", "x=2", "x=7.5"], "a": 0 },
                { "q": "Solve for x: 3x - 9 = 0", "options": ["x=9", "x=3", "x=0", "x=6"], "a": 1 },
                { "q": "Simplify: 2(x + 3)", "options": ["2x + 3", "2x + 6", "x + 6", "2x + 5"], "a": 1 },
                { "q": "If x = 4, what is x^2?", "options": ["8", "16", "12", "20"], "a": 1 },
                { "q": "Solve for x: x/2 = 8", "options": ["x=4", "x=16", "x=10", "x=6"], "a": 1 }
            ]'
            ;;
        *)
            # Default Basic Math
            QUIZ_DATA='[
                { "q": "5 + 3 = ?", "options": ["7", "8", "9", "6"], "a": 1 },
                { "q": "12 - 4 = ?", "options": ["6", "8", "10", "7"], "a": 1 },
                { "q": "6 x 7 = ?", "options": ["42", "36", "48", "45"], "a": 0 },
                { "q": "20 / 5 = ?", "options": ["5", "3", "4", "6"], "a": 2 },
                { "q": "9 + 9 = ?", "options": ["16", "18", "19", "20"], "a": 1 }
            ]'
            ;;
    esac
fi

# Clean up newlines for sed replacement
QUIZ_DATA=$(echo "$QUIZ_DATA" | tr -d '\n' | sed 's/  / /g')

# Process Template
# Use python for safe replacement if possible, otherwise complex sed
# Here we use a safe sed delimiter and escape quotes for the JSON string
# But JSON contains quotes, so we need to be careful.
# Strategy: Use a temp file for the data and then concatenate parts

# 1. Split template
awk 'BEGIN{print_end=0} /{{QUIZ_DATA}}/{print_end=1; next} !print_end{print}' "$TEMPLATE_PATH" > "${OUTPUT_PATH}.part1"
awk 'BEGIN{found=0} /{{QUIZ_DATA}}/{found=1; next} found{print}' "$TEMPLATE_PATH" > "${OUTPUT_PATH}.part2"

# 2. Inject Data
echo "$QUIZ_DATA" > "${OUTPUT_PATH}.data"

# 3. Combine
cat "${OUTPUT_PATH}.part1" "${OUTPUT_PATH}.data" "${OUTPUT_PATH}.part2" > "$OUTPUT_PATH"

# 4. Final Replacements (Topic)
sed -i "s|{{TOPIC}}|$TOPIC|g" "$OUTPUT_PATH"

# Cleanup
rm "${OUTPUT_PATH}.part1" "${OUTPUT_PATH}.part2" "${OUTPUT_PATH}.data"

echo "✓ Quiz created: $OUTPUT_PATH"
