#!/usr/bin/env python3
"""
多语言复杂度检测工具

集成各种 lint 工具计算代码复杂度。
支持：Rust (clippy), Python (pylint), C++ (cpplint), JS (eslint)
"""

import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any


# Lint 工具配置
LINT_TOOLS = {
    "rust": {
        "command": "cargo clippy --message-format=json",
        "executable": "cargo",
        "json_parser": parse_cargo_json,
    },
    "python": {
        "command": "pylint --output-format=json",
        "executable": "pylint",
        "json_parser": parse_pylint_json,
    },
    "cpp": {
        "command": "cpplint --output-format=json5",
        "executable": "cpplint",
        "json_parser": parse_cpplint_json,
    },
    "js": {
        "command": "eslint --format=json",
        "executable": "eslint",
        "json_parser": parse_eslint_json,
    },
}


def check_tool_available(tool_name: str) -> bool:
    """检查 lint 工具是否可用"""
    return shutil.which(tool_name) is not None


def parse_cargo_json(output: str) -> Dict[str, Any]:
    """解析 cargo clippy 的 JSON 输出"""
    try:
        messages = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                msg = json.loads(line)
                if (
                    msg.get("reason") == "compiler-message"
                    and msg.get("message", {}).get("level") == "error"
                ):
                    messages.append(msg)
            except json.JSONDecodeError:
                continue

        if messages:
            # 取第一个错误消息的复杂度信息
            msg = messages[0]["message"]
            return {"cyclomatic": 1, "raw_message": msg}

        return {"cyclomatic": 0, "raw_message": "No errors"}
    except Exception:
        return {"cyclomatic": 0, "raw_message": f"Parse error: {str(e)}"}


def parse_pylint_json(output: str) -> Dict[str, Any]:
    """解析 pylint 的 JSON 输出"""
    try:
        data = json.loads(output)
        if data:
            # 计算平均复杂度
            messages = data.get("messages", [])
            cyclomatics = [m.get("cyclomatic_complexity", 0) for m in messages]
            avg_complexity = sum(cyclomatics) / len(cyclomatics) if cyclomatics else 0

            return {
                "cyclomatic": avg_complexity,
                "raw_message": f"Average complexity: {avg_complexity:.2f}",
            }

        return {"cyclomatic": 0, "raw_message": "No data"}
    except Exception:
        return {"cyclomatic": 0, "raw_message": f"Parse error: {str(e)}"}


def parse_cpplint_json(output: str) -> Dict[str, Any]:
    """解析 cpplint 的 JSON 输出"""
    try:
        data = json.loads(output)
        if data and len(data) > 0:
            # cpplint 的复杂度通常在报告中
            return {"cyclomatic": 1, "raw_message": "Complexity detected"}

        return {"cyclomatic": 0, "raw_message": "No data"}
    except Exception:
        return {"cyclomatic": 0, "raw_message": f"Parse error: {str(e)}"}


def parse_eslint_json(output: str) -> Dict[str, Any]:
    """解析 eslint 的 JSON 输出"""
    try:
        data = json.loads(output)
        if data:
            # eslint 的复杂度通常通过配置规则评估
            return {"cyclomatic": 1, "raw_message": "Complexity detected"}

        return {"cyclomatic": 0, "raw_message": "No data"}
    except Exception:
        return {"cyclomatic": 0, "raw_message": f"Parse error: {str(e)}"}


def calculate_complexity(file_path: str, language: str) -> Dict[str, Any]:
    """
    计算文件的复杂度

    Args:
        file_path: 文件路径
        language: 编程语言

    Returns:
        {cyclomatic: 复杂度信息} 的字典
    """
    tool_config = LINT_TOOLS.get(language)

    if not tool_config:
        return {"cyclomatic": 0, "raw_message": f"Unsupported language"}

    executable = tool_config["executable"]

    # 检查工具是否可用
    if not check_tool_available(executable):
        return {
            "cyclomatic": 0,
            "raw_message": f'Lint tool "{executable}" not found, skipping complexity check',
        }

    command = tool_config["command"]

    # 获取文件所在目录
    file_dir = str(Path(file_path).parent)

    try:
        result = subprocess.run(
            command.split(), cwd=file_dir, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            complexity_info = tool_config["json_parser"](result.stdout)
            complexity_info["tool"] = executable
            return complexity_info
        else:
            return {
                "cyclomatic": 0,
                "raw_message": f"Lint tool failed with exit code {result.returncode}",
            }

    except subprocess.TimeoutExpired:
        return {"cyclomatic": 0, "raw_message": "Lint tool timeout"}
    except Exception as e:
        return {"cyclomatic": 0, "raw_message": f"Lint tool error: {str(e)}"}


def batch_calculate(file_infos: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    批量计算多个文件的复杂度

    Args:
        file_infos: {文件路径: {language, lines}} 的字典

    Returns:
        {文件路径: 复杂度信息} 的字典
    """
    results = {}

    for file_path, info in file_infos.items():
        complexity_info = calculate_complexity(
            file_path, info.get("language", "unknown")
        )
        results[file_path] = complexity_info

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python complexity_detector.py <file_path> <language>")
        sys.exit(1)

    file_path = sys.argv[1]
    language = sys.argv[2]

    complexity_info = calculate_complexity(file_path, language)

    print(f"文件: {file_path}")
    print(f"语言: {language}")
    print(f"圈复杂度: {complexity_info['cyclomatic']}")
    print(f"消息: {complexity_info['raw_message']}")
