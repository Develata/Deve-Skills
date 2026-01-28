#!/usr/bin/env python3
"""Main analyzer for code-shorters."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from git_checker import check_git_environment
from language_detector import detect_language
from line_counter import count_lines, scan_directory
from complexity_detector import calculate_complexity, calculate_priority_score


def analyze_files(file_paths: List[str], use_complexity: bool) -> Dict[str, Any]:
    results = []
    warning = []
    critical = []

    for file_path in file_paths:
        language = detect_language(file_path)
        if language == "unknown":
            continue
        lines = count_lines(file_path)
        complexity = 0
        nesting = 0
        func_count = 0
        if use_complexity and language != "unknown":
            detail = calculate_complexity(file_path, language)
            complexity = detail.get("cyclomatic", 0)
            nesting = detail.get("nesting_depth", 0)
            func_count = detail.get("function_count", 0)

        score = calculate_priority_score(lines, complexity, nesting, func_count)
        info = {
            "path": file_path,
            "language": language,
            "lines": lines,
            "priority_score": score,
        }
        results.append(info)

        if 130 < lines < 250:
            warning.append(info)
        elif lines >= 250:
            critical.append(info)

    statistics = {
        "total_files": len(results),
        "warning_count": len(warning),
        "critical_count": len(critical),
    }

    return {
        "warning_files": sorted(
            warning, key=lambda x: x["priority_score"], reverse=True
        ),
        "critical_files": sorted(
            critical, key=lambda x: x["priority_score"], reverse=True
        ),
        "statistics": statistics,
        "scan_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def save_report(data: Dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"analysis_{timestamp}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze code for modularization")
    parser.add_argument("--path", default=".", help="Scan path")
    parser.add_argument("--recursive", action="store_true", help="Recursive scan")
    parser.add_argument("--exclude", default="", help="Exclude pattern")
    parser.add_argument("--no-complexity", action="store_true", help="Skip complexity")
    parser.add_argument("--skip-git", action="store_true", help="Skip Git check")
    parser.add_argument("--output-dir", default="reports", help="Output directory")
    args = parser.parse_args()

    if not args.skip_git:
        check_git_environment(args.path)

    files = scan_directory(args.path, recursive=args.recursive)
    default_excludes = [
        "code-shorters\\scripts",
        "code-shorters\\test_files",
        "code-shorters/scripts",
        "code-shorters/test_files",
    ]
    files = [fp for fp in files if not any(ex in fp for ex in default_excludes)]
    if args.exclude:
        files = [fp for fp in files if args.exclude not in fp]
    analysis = analyze_files(files, use_complexity=not args.no_complexity)
    report_path = save_report(analysis, Path(args.output_dir))
    print(f"Report saved: {report_path}")
