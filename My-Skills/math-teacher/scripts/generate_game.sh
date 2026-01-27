#!/bin/bash
# Math Teacher - Game Generator (Lightweight)
set -e

# Default Values
GAME_TYPE="急速挑战"
TOPIC="心算"
OUTPUT_FILE="math-game.html"
OUTPUT_DIR="./math-games"

# Parse Arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --type) GAME_TYPE="$2"; shift ;;
        --topic) TOPIC="$2"; shift ;;
        --output) OUTPUT_FILE="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Resolve Paths
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
TEMPLATE_PATH="$SCRIPT_DIR/../assets/templates/games/speed_math.html"
OUTPUT_PATH="$OUTPUT_DIR/$OUTPUT_FILE"

# Validation
if [[ ! -f "$TEMPLATE_PATH" ]]; then
    echo "Error: Template not found at $TEMPLATE_PATH"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Generating Math Game..."
echo "Type: $GAME_TYPE"
echo "Topic: $TOPIC"

# Process Template
# We use sed to replace placeholders. 
# Note: Using | as delimiter to avoid issues with slashes in variables if any.
sed "s|{{TOPIC}}|$TOPIC|g; s|{{GAME_TYPE}}|$GAME_TYPE|g" "$TEMPLATE_PATH" > "$OUTPUT_PATH"

echo "✓ Game created: $OUTPUT_PATH"
