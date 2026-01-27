#!/usr/bin/env python3
"""Batch refactor dispatcher (serial mode)."""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List


SUBSKILL_ROUTES = {
    "rust": "rust-shorter",
    "python": "python-shorter",
    "cpp": "cpp-shorter",
    "js": "js-shorter",
    "md": "md-shorter",
}


def invoke_subskill(skill_name: str, file_path: str) -> Dict[str, Any]:
    return {
        "file_path": file_path,
        "skill_name": skill_name,
        "status": "planned",
        "message": f"Invoke {skill_name} for {Path(file_path).name}",
    }


def run_batch(analysis_data: Dict[str, Any], include_warning: bool) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    targets = list(analysis_data.get("critical_files", []))
    if include_warning:
        targets.extend(analysis_data.get("warning_files", []))

    for file_info in targets:
        language = file_info.get("language", "unknown")
        skill_name = SUBSKILL_ROUTES.get(language)
        if not skill_name:
            results.append(
                {
                    "file_path": file_info.get("path"),
                    "language": language,
                    "status": "skipped",
                    "message": "Unsupported language",
                }
            )
            continue

        result = invoke_subskill(skill_name, file_info.get("path"))
        result["language"] = language
        result["original_lines"] = file_info.get("lines", 0)
        results.append(result)

    return results


def save_results(results: List[Dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "batch_refactor_results.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_refactor.py <analysis.json> [--include-warning]")
        sys.exit(1)

    analysis_path = Path(sys.argv[1])
    include_warning = "--include-warning" in sys.argv
    analysis_data = json.loads(analysis_path.read_text(encoding="utf-8"))

    results = run_batch(analysis_data, include_warning)
    output_path = save_results(results, Path("reports"))
    print(f"Batch results saved: {output_path}")
