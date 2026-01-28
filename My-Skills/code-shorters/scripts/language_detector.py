#!/usr/bin/env python3
"""Language detection based on extension and content patterns."""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


EXTENSION_MAP: Dict[str, str] = {
    ".rs": "rust",
    ".py": "python",
    ".cpp": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".js": "js",
    ".ts": "js",
    ".jsx": "js",
    ".tsx": "js",
}

LANGUAGE_PATTERNS: Dict[str, List[str]] = {
    "rust": [
        r"\buse\s+\w+::",
        r"\bfn\s+\w+\s*\(",
        r"\bpub\s+struct\s+\w+",
        r"\bimpl\s+\w+\s+for\s+\w+",
        r"\bmod\s+\w+;",
    ],
    "python": [
        r"^import\s+\w+",
        r"\bdef\s+\w+\s*\(",
        r"\bclass\s+\w+.*:",
        r"if\s+__name__\s*==\s*[\"\']__main__\"",
        r"^from\s+\w+\s+import",
    ],
    "cpp": [
        r"^#include\s*[<\"][\w+\.h]",
        r"\bnamespace\s+\w+\s*\{",
        r"\bclass\s+\w+.*:",
        r"\btemplate\s*<\s*\w+\s*>",
    ],
    "js": [
        r"\bfunction\s+\w+\s*\(",
        r"\bconst\s+\w+\s*=",
        r"\b=>\s*\{",
        r"\bimport\s+.*\s+from\s+",
        r"export\s+(default\s+)?",
    ],
}


def detect_by_extension(file_path: str) -> Optional[str]:
    ext = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(ext)


def detect_by_content(file_path: str, sample_bytes: int = 5000) -> Optional[str]:
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")[
            :sample_bytes
        ]
    except Exception:
        return None

    scores: Dict[str, int] = {}
    for lang, patterns in LANGUAGE_PATTERNS.items():
        score = sum(
            len(re.findall(pattern, content, re.MULTILINE)) for pattern in patterns
        )
        if score:
            scores[lang] = score

    if not scores:
        return None

    best_lang = None
    best_score = -1
    for lang, score in scores.items():
        if score > best_score:
            best_lang = lang
            best_score = score

    return best_lang


def detect_language(file_path: str) -> str:
    lang = detect_by_extension(file_path)
    if lang:
        return lang
    return detect_by_content(file_path) or "unknown"


def batch_detect(file_paths: List[str]) -> Dict[str, str]:
    return {file_path: detect_language(file_path) for file_path in file_paths}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python language_detector.py <file_path>")
        sys.exit(1)

    target = sys.argv[1]
    print(f"File: {target}")
    print(f"Language: {detect_language(target)}")
