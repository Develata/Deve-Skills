#!/usr/bin/env python3
"""
多层级语言检测工具

通过文件后缀名和内容特征双重检测，确定编程语言。
支持：Rust, Python, C++, JavaScript/TypeScript, Markdown
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple


# 语言后缀映射（一级检测）
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

# 语言内容特征模式（二级检测）
LANGUAGE_PATTERNS = {
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
        r'if\s+__name__\s*==\s*["\']__main__"',
        r"^from\s+\w+\s+import",
    ],
    "cpp": [
        r'^#include\s*[<"][\w+\.h',
        r"\bnamespace\s+\w+\s*\{",
        r"\bclass\s+\w+.*:",
        r"\btemplate\s*<\s*\w+\s*>",
        r"\bstd::(vector|map|string|iostream)",
    ],
    "js": [
        r"\bfunction\s+\w+\s*\(",
        r"\bconst\s+\w+\s*=",
        r"\b=>\s*\{",
        r"\blet\s+\w+\s*=",
        r"\bimport\s+.*\s+from\s+",
        r"export\s+(default\s+)?",
        r"\bvar\s+\w+\s*=",
    ],
    "md": [r"^#+\s+\w+", r"\[.*\]\(.*\)", r"\*\*[^*]+\*\*", r"^>\s+\w+", r"<!--\s*-->"],
}


def detect_by_extension(file_path: str) -> Optional[str]:
    """通过文件后缀名检测语言（一级检测）"""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(ext)


def detect_by_content(file_path: str, sample_lines: int = 50) -> Optional[str]:
    """
    通过文件内容特征检测语言（二级检测）

    Args:
        file_path: 文件路径
        sample_lines: 采样行数（默认50行）

    Returns:
        检测到的语言，或 None
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(sample_lines * 100)  # 读取前面部分
    except Exception:
        return None

    scores = {}

    for lang, patterns in LANGUAGE_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            score += len(matches)

        if score > 0:
            scores[lang] = score

    if not scores:
        return None

    # 返回匹配次数最多的语言
    return max(scores, key=scores.get)


def detect_language(file_path: str) -> str:
    """
    多层级语言检测（一级 + 二级）

    Args:
        file_path: 文件路径

    Returns:
        检测到的编程语言
    """
    # 一级检测：后缀名
    lang = detect_by_extension(file_path)

    if lang:
        return lang

    # 二级检测：内容特征
    lang = detect_by_content(file_path)

    if lang:
        return lang

    # 都检测不到
    return "unknown"


def batch_detect(file_paths: list) -> Dict[str, Any]:
    """
    批量检测文件语言

    Args:
        file_paths: 文件路径列表

    Returns:
        {文件路径: 语言} 的字典
    """
    results = {}

    for file_path in file_paths:
        results[file_path] = detect_language(file_path)

    return results


if __name__ == "__main__":
    if len(os.sys.argv) < 2:
        print("用法: python language_detector.py <file_path>")
        os.sys.exit(1)

    file_path = os.sys.argv[1]
    lang = detect_language(file_path)

    print(f"文件: {file_path}")
    print(f"语言: {lang}")
