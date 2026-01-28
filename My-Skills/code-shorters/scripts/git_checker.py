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
    """Check if directory is inside a git repository"""
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print("[X] Git not found")
        sys.exit(1)


def has_uncommitted_changes(directory: str = ".") -> bool:
    """Check for uncommitted changes"""
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
        print(f"[X] Failed to check git status: {e}")
        sys.exit(1)


def check_git_environment(directory: str = ".") -> bool:
    """
    Check Git environment status

    Returns:
        True - Passed
        False - Failed (exits)
    """
    print("Checking Git environment...")

    # Check 1: Is inside git repo
    if not is_git_repo(directory):
        print("[X] Error: Current directory is not inside a Git repository")
        print("Tip: Run 'git init' or run inside a git repo")
        sys.exit(1)

    print("[OK] Git repository check passed")

    # Check 2: Uncommitted changes
    if has_uncommitted_changes(directory):
        print("[X] Error: Uncommitted changes detected")
        print("\nUncommitted files:")
        subprocess.run(["git", "status", "--short"], cwd=directory)
        print("\nTip: Please commit or stash changes first")
        print("  git status")
        print("  git add <files>")
        print("  git commit -m 'message'")
        sys.exit(1)

    print("[OK] Working directory is clean")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."

    check_git_environment(directory)
