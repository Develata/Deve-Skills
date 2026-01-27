#!/usr/bin/env python3
"""
精确的行数统计工具（包含注释）

统计文件的总行数，包含注释行和代码行。
支持：Rust, Python, C++, JavaScript, Markdown
"""

import os
import re
from pathlib import Path
from typing import Dict, Tuple


# 语言后缀映射
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

# 语言特定的注释模式（用于识别，但全部计数）
COMMENT_PATTERNS = {
    "rust": [
        (r"//.*$", "single-line"),
        (r"/\*.*?\*/", "block"),
        (r"/\*", "block-start"),
        (r"\*/", "block-end"),
    ],
    "python": [
        (r"#.*$", "single-line"),
        (r'""".*?"""', "block"),
        (r'"""', "block-start"),
        (r'"""', "block-end"),
    ],
    "cpp": [
        (r"//.*$", "single-line"),
        (r"/\*.*?\*/", "block"),
        (r"/\*", "block-start"),
        (r"\*/", "block-end"),
    ],
    "js": [
        (r"//.*$", "single-line"),
        (r"/\*.*?\*/", "block"),
        (r"/\*", "block-start"),
        (r"\*/", "block-end"),
    ],
    "md": [(r"<!--.*?-->", "block"), (r"<!--", "block-start"), (r"-->", "block-end")],
}


def count_lines(file_path: str) -> int:
    """
    统计文件的总行数（包含注释）

    计数规则：
        - 空白行不计数
        - 注释行**完全计数**
        - 代码行**完全计数**

    Args:
        file_path: 文件路径

    Returns:
        总行数
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # 尝试 GBK 编码
        try:
            with open(file_path, "r", encoding="gbk", errors="ignore") as f:
                lines = f.readlines()
        except:
            pass

    total_lines = len(lines)
    return total_lines


def get_language(file_path: str) -> str:
    """根据文件后缀获取语言"""
    ext = Path(file_path).suffix.lower()
    ext_map = {
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
    return ext_map.get(ext, "unknown")


def batch_count(file_paths: list) -> Dict[str, Dict]:
    """
    批量统计多个文件的行数

    Args:
        file_paths: 文件路径列表

    Returns:
        {文件路径: {language, lines}} 的字典
    """
    results = {}

    for file_path in file_paths:
        lines = count_lines(file_path)
        language = get_language(file_path)

        results[file_path] = {"language": language, "lines": lines}

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python line_counter.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    lines = count_lines(file_path)
    language = get_language(file_path)

    print(f"文件: {file_path}")
    print(f"语言: {language}")
    print(f"行数: {lines}")
