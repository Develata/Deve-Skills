#!/usr/bin/env python3
"""Lightweight complexity detector with heuristics and lint integration."""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any


def calculate_priority_score(
    lines: int, complexity: float, nesting: int = 0, functions: int = 0
) -> float:
    score = (lines * 0.4) + (complexity * 0.3) + (nesting * 0.2) + (functions * 0.1)
    if complexity == 0 and nesting == 0 and functions == 0:
        return lines * 0.7
    return score


def _keyword_complexity(content: str, language: str) -> int:
    keywords = {
        "rust": ["if", "for", "while", "match", "loop"],
        "python": ["if", "for", "while", "elif", "except"],
        "cpp": ["if", "for", "while", "switch", "catch"],
        "js": ["if", "for", "while", "switch", "catch"],
    }
    return sum(
        len(re.findall(rf"\b{key}\b", content)) for key in keywords.get(language, [])
    )


def _function_count(content: str, language: str) -> int:
    patterns = {
        "rust": r"\bfn\s+\w+\s*\(",
        "python": r"\bdef\s+\w+\s*\(",
        "cpp": r"\b\w+\s+\w+\s*\(",
        "js": r"\bfunction\s+\w+\s*\(",
    }
    pattern = patterns.get(language)
    return len(re.findall(pattern, content)) if pattern else 0


def _nesting_depth(content: str) -> int:
    depth = 0
    max_depth = 0
    for char in content:
        if char == "{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == "}":
            depth = max(0, depth - 1)
    return max_depth


def _run_lint(command: str, workdir: str) -> bool:
    if shutil.which(command.split()[0]) is None:
        return False
    result = subprocess.run(
        command.split(), cwd=workdir, capture_output=True, text=True
    )
    return result.returncode == 0


def calculate_complexity(file_path: str, language: str) -> Dict[str, Any]:
    content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    complexity = _keyword_complexity(content, language)
    functions = _function_count(content, language)
    nesting = _nesting_depth(content) if language in {"rust", "cpp", "js"} else 0

    lint_map = {
        "rust": "cargo clippy --message-format=json",
        "python": "pylint --output-format=json",
        "cpp": "cpplint --output-format=json5",
        "js": "eslint --format=json",
    }
    lint_cmd = lint_map.get(language)
    lint_ok = _run_lint(lint_cmd, str(Path(file_path).parent)) if lint_cmd else False

    return {
        "cyclomatic": max(1, complexity) if lint_ok else complexity,
        "function_count": functions,
        "nesting_depth": nesting,
        "raw_message": "Lint executed" if lint_ok else "Lint skipped",
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python complexity_detector.py <file_path> <language>")
        sys.exit(1)

    target, lang = sys.argv[1], sys.argv[2]
    info = calculate_complexity(target, lang)
    print(info)
