#!/usr/bin/env python3
"""Generate markdown or HTML refactor reports."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def generate_markdown_report(analysis: Dict[str, Any]) -> str:
    stats = analysis.get("statistics", {})
    critical = analysis.get("critical_files", [])
    warning = analysis.get("warning_files", [])

    lines = ["# Refactor Report", "", f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}", ""]
    lines.extend(["## Summary", "| Metric | Value |", "| --- | --- |"])
    for key, value in stats.items():
        lines.append(f"| {key} | {value} |")

    lines.append("")
    if critical:
        lines.append("## Critical Files")
        for item in critical:
            lines.append(f"- {item.get('path')} ({item.get('lines', 0)} lines)")

    if warning:
        lines.append("")
        lines.append("## Warning Files")
        for item in warning:
            lines.append(f"- {item.get('path')} ({item.get('lines', 0)} lines)")

    if not critical and not warning:
        lines.append("\nNo files require refactor.")

    return "\n".join(lines)


def generate_html_report(analysis: Dict[str, Any]) -> str:
    return "<html><body><h1>Refactor Report</h1><pre>" + json.dumps(analysis, indent=2) + "</pre></body></html>"


def save_report(analysis: Dict[str, Any], output_path: str, fmt: str) -> str:
    content = generate_html_report(analysis) if fmt == "html" else generate_markdown_report(analysis)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <analysis.json> [markdown|html]")
        sys.exit(1)

    json_path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "markdown"

    with open(json_path, "r", encoding="utf-8") as handle:
        analysis_data = json.load(handle)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("reports")
    output_path = output_dir / f"refactor_report_{timestamp}.{output_format}"
    saved = save_report(analysis_data, str(output_path), output_format)
    print(f"Report saved: {saved}")
