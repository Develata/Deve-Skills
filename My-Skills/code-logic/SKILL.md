---
name: code-logic
description: A rigorous code logic analyzer that converts source code (Rust/Python) into a Universal Logic Graph (ULG). Outputs AI-optimized Logic DSL and Graphviz SVG. Supports single-file analysis, recursive project scanning, and unified atlas generation.
---

# Code Logic Analyzer

This skill provides unassailable, AST-based control flow analysis for Rust and Python. It maps code into a rigorous graph structure, capturing implicit flows like Rust's `?` operator or Python's `try/except` scopes.

## Usage

### 1. Single File Analysis

Analyze a specific file to understand its local control flow.

```bash
python scripts/main.py /path/to/source.rs
```

### 2. Project Mode (Recursive)

Scan a directory to generate logic graphs for all source files found within.

```bash
python scripts/main.py /path/to/project/ --svg-dir documentation/graphs
```

### 3. Unified Atlas (Experimental)

Generate a single, massive graph connecting all modules via symbol resolution.

```bash
python scripts/main.py /path/to/project/ --unified --svg-dir documentation/atlas
```

## Configuration

You can customize descriptions and behavior using `scripts/logic_config.yaml`.
See [DESIGN_SPEC.md](references/DESIGN_SPEC.md) for architecture details and [logic_dsl.md](references/logic_dsl.md) for the output format specification.

## Outputs

*   **Logic DSL (`.lisp`)**: A Lisp-style S-expression representing the logical skeleton. Optimized for AI context windows.
*   **Visualization (`.svg`)**: A high-precision vector graphic using orthogonal layout. Best for human review.

## Dependencies

*   Python 3.8+
*   GCC (for compiling tree-sitter grammars)
*   Graphviz (must be in system PATH)
*   See `scripts/requirements.txt`
