#!/usr/bin/env python3
"""Lightweight complexity detector with linter integration."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any


def calculate_priority_score(lines: int, complexity: float) -> float:
    if complexity > 0:
        return (lines * 0.4) + (complexity * 0.3)
    return lines * 0.7


def _run_command(command: str, workdir: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            command.split(),
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
    except Exception as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc)}


def calculate_complexity(file_path: str, language: str) -> Dict[str, Any]:
    tool_map = {
        "rust": "cargo clippy --message-format=json",
        "python": "pylint --output-format=json",
        "cpp": "cpplint --output-format=json5",
        "js": "eslint --format=json",
    }

    command = tool_map.get(language)
    if not command:
        return {"cyclomatic": 0, "raw_message": "Unsupported language"}

    tool = command.split()[0]
    if shutil.which(tool) is None:
        return {"cyclomatic": 0, "raw_message": f"Lint tool {tool} not found"}

    result = _run_command(command, str(Path(file_path).parent))
    if not result["ok"]:
        return {"cyclomatic": 0, "raw_message": result["stderr"]}

    return {"cyclomatic": 1, "raw_message": "Lint executed"}


def batch_calculate(file_infos: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    results = {}
    for file_path, info in file_infos.items():
        results[file_path] = calculate_complexity(file_path, info.get("language", "unknown"))
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python complexity_detector.py <file_path> <language>")
        sys.exit(1)

    target, lang = sys.argv[1], sys.argv[2]
    info = calculate_complexity(target, lang)
    print(f"File: {target}")
    print(f"Language: {lang}")
    print(f"Cyclomatic: {info['cyclomatic']}")
    print(f"Message: {info['raw_message']}")
