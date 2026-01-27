#!/bin/bash
# Math Teacher - Playground Generator (Lightweight)
set -e

# Defaults
TOPIC="Fractions"
OUTPUT_FILE="math-playground.html"
OUTPUT_DIR="./math-playgrounds"

# Parse Arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --topic) TOPIC="$2"; shift ;;
        --output) OUTPUT_FILE="$2"; shift ;;
        --level|--type|--difficulty) shift ;; # Ignore unused args for now
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Resolve Paths
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
TEMPLATE_DIR="$SCRIPT_DIR/../assets/templates/playgrounds"
OUTPUT_PATH="$OUTPUT_DIR/$OUTPUT_FILE"

# Select Template
case $TOPIC in
    "Fractions") TEMPLATE_FILE="fractions.html" ;;
    "Quadratic Functions") TEMPLATE_FILE="quadratic.html" ;;
    "Derivatives") TEMPLATE_FILE="derivatives.html" ;;
    *) TEMPLATE_FILE="generic.html" ;;
esac

FULL_TEMPLATE_PATH="$TEMPLATE_DIR/$TEMPLATE_FILE"

if [[ ! -f "$FULL_TEMPLATE_PATH" ]]; then
    echo "Error: Template not found at $FULL_TEMPLATE_PATH"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Generating Playground for $TOPIC..."

# Process Template
sed "s|{{TOPIC}}|$TOPIC|g" "$FULL_TEMPLATE_PATH" > "$OUTPUT_PATH"

echo "✓ Playground created: $OUTPUT_PATH"
