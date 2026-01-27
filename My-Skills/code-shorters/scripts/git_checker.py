#!/usr/bin/env python3
"""
Git 环境检查工具

检查当前目录是否为 Git 仓库，以及是否有未提交的修改。
如果检查失败，则退出程序。
"""

import os
import sys
import subprocess
from pathlib import Path


def is_git_repo(directory: str = ".") -> bool:
    """检查指定目录是否为 Git 仓库"""
    git_dir = Path(directory) / ".git"
    return git_dir.exists() and git_dir.is_dir()


def has_uncommitted_changes(directory: str = ".") -> bool:
    """检查是否有未提交的修改"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return len(result.stdout.strip()) > 0
    except Exception as e:
        print(f"错误：无法检查 git 状态: {e}")
        sys.exit(1)


def check_git_environment(directory: str = ".") -> bool:
    """
    检查 Git 环境状态

    返回：
        True - 环境检查通过
        False - 检查失败，程序应退出
    """
    print("正在检查 Git 环境...")

    # 检查 1: 是否为 Git 仓库
    if not is_git_repo(directory):
        print("✗ 错误：当前目录不是 Git 仓库")
        print("提示：请先初始化 git 仓库")
        print("  运行: git init")
        sys.exit(1)

    print("✓ Git 仓库检查通过")

    # 检查 2: 是否有未提交的修改
    if has_uncommitted_changes(directory):
        print("✗ 错误：存在未提交的修改")
        print("\n未提交的文件列表：")
        subprocess.run(["git", "status", "--short"], cwd=directory)
        print("\n提示：请先提交或暂存修改")
        print("  查看状态: git status")
        print("  暂存修改: git add <files>")
        print("  提交修改: git commit -m 'commit message'")
        sys.exit(1)

    print("✓ 工作目录干净，无未提交修改")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."

    check_git_environment(directory)
