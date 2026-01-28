#!/usr/bin/env python3
"""Batch refactor dispatcher (serial mode)."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

from git_checker import check_git_environment


BASE_DIR = Path(__file__).resolve().parent.parent

SUBSKILL_SCRIPTS = {
    "rust": BASE_DIR / "rust-shorter" / "scripts" / "rust_modularizer.py",
    "python": BASE_DIR / "python-shorter" / "scripts" / "python_modularizer.py",
    "cpp": BASE_DIR / "cpp-shorter" / "scripts" / "cpp_modularizer.py",
    "js": BASE_DIR / "js-shorter" / "scripts" / "js_modularizer.py",
    "md": BASE_DIR / "md-shorter" / "scripts" / "md_modularizer.py",
}


def invoke_subskill(language: str, file_path: str) -> Dict[str, Any]:
    script_path = SUBSKILL_SCRIPTS.get(language)
    if not script_path or not script_path.exists():
        return {
            "file_path": file_path,
            "language": language,
            "status": "failed",
            "message": "Subskill script not found",
        }

    result = subprocess.run(
        [sys.executable, str(script_path), file_path],
        capture_output=True,
        text=True,
    )

    status = "success" if result.returncode == 0 else "failed"
    message = result.stdout.strip() or result.stderr.strip() or "No output"

    return {
        "file_path": file_path,
        "language": language,
        "status": status,
        "message": message,
        "script": str(script_path),
    }


def run_batch(
    analysis_data: Dict[str, Any], include_warning: bool
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    targets = list(analysis_data.get("critical_files", []))
    if include_warning:
        targets.extend(analysis_data.get("warning_files", []))

    for file_info in targets:
        language = file_info.get("language", "unknown")
        if language not in SUBSKILL_SCRIPTS:
            results.append(
                {
                    "file_path": file_info.get("path"),
                    "language": language,
                    "status": "skipped",
                    "message": "Unsupported language",
                }
            )
            continue

        result = invoke_subskill(language, file_info.get("path"))
        result["original_lines"] = file_info.get("lines", 0)
        results.append(result)

    return results


def save_results(results: List[Dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "batch_refactor_results.json"
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch refactor")
    parser.add_argument("analysis_file", help="Analysis JSON file")
    parser.add_argument(
        "--include-warning", action="store_true", help="Include warning files"
    )
    parser.add_argument("--skip-git", action="store_true", help="Skip Git check")
    args = parser.parse_args()

    analysis_path = Path(args.analysis_file)
    analysis_data = json.loads(analysis_path.read_text(encoding="utf-8"))

    if not args.skip_git:
        check_git_environment(str(analysis_path.parent))

    results = run_batch(analysis_data, args.include_warning)
    output_path = save_results(results, Path("reports"))
    print(f"Batch results saved: {output_path}")

    report_script = Path(__file__).parent / "report_generator.py"
    subprocess.run(
        [sys.executable, str(report_script), str(analysis_path), "markdown"],
        check=False,
    )
