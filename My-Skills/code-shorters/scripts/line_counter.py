#!/usr/bin/env python3
"""Count total lines and scan code files."""

import sys
from pathlib import Path
from typing import Dict, List, Any


EXTENSION_MAP = {
    ".rs": "rust",
    ".py": "python",
    ".cpp": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".js": "js",
    ".ts": "js",
    ".jsx": "js",
    ".tsx": "js",
    ".md": "md",
}


def count_lines(file_path: str) -> int:
    lines: List[str] = []
    try:
        lines = Path(file_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except UnicodeDecodeError:
        lines = Path(file_path).read_text(encoding="gbk", errors="ignore").splitlines()
    return len(lines)


def get_language(file_path: str) -> str:
    return EXTENSION_MAP.get(Path(file_path).suffix.lower(), "unknown")


def batch_count(file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
    return {
        file_path: {"language": get_language(file_path), "lines": count_lines(file_path)}
        for file_path in file_paths
    }


def scan_directory(directory: str, recursive: bool = False) -> List[str]:
    base = Path(directory)
    pattern = "**/*" if recursive else "*"
    files = []
    for path in base.glob(pattern):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if "__pycache__" in path.parts:
            continue
        files.append(str(path))
    return files


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python line_counter.py <file_path>")
        sys.exit(1)

    target = sys.argv[1]
    print(f"File: {target}")
    print(f"Language: {get_language(target)}")
    print(f"Lines: {count_lines(target)}")
