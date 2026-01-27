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
        lines = count_lines(file_path)
        complexity = 0
        if use_complexity and language != "unknown":
            complexity = calculate_complexity(file_path, language).get("cyclomatic", 0)

        score = calculate_priority_score(lines, complexity)
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
        "warning_files": sorted(warning, key=lambda x: x["priority_score"], reverse=True),
        "critical_files": sorted(critical, key=lambda x: x["priority_score"], reverse=True),
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
    parser.add_argument("--no-complexity", action="store_true", help="Skip complexity")
    parser.add_argument("--output-dir", default="reports", help="Output directory")
    args = parser.parse_args()

    check_git_environment(args.path)
    files = scan_directory(args.path, recursive=args.recursive)
    analysis = analyze_files(files, use_complexity=not args.no_complexity)
    report_path = save_report(analysis, Path(args.output_dir))
    print(f"Report saved: {report_path}")
