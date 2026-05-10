#!/usr/bin/env python3
from decimal import Decimal
from pathlib import Path

from audit_format import HEADER, parse_required_token_line


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
SUMMARY_FILE = SCRIPT_DIR / "CostUSD.md"


def calculate_monthly_cost() -> None:
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"data directory was not found: {DATA_DIR}")
    output = ["| Month | Days | CostUSD |", "|-------|------|---------|"]
    grand_total = Decimal("0")
    for path in sorted(DATA_DIR.glob("*.md")):
        if len(path.stem) != 6 or not path.stem.isdigit():
            continue
        total = Decimal("0")
        days = 0
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            if index < len(HEADER) or not line.strip():
                continue
            record = parse_required_token_line(path, index + 1, line)
            if record.status != "CONFLICT":
                total += record.cost_usd
                days += 1
        grand_total += total
        output.append(f"| {path.stem} | {days} | {total:.6f} |")
    output.append(f"| TOTAL | - | {grand_total:.6f} |")
    SUMMARY_FILE.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"DONE. Monthly cost summary written to: {SUMMARY_FILE}")
    print(f"TOTAL CostUSD: {grand_total:.6f}")


if __name__ == "__main__":
    calculate_monthly_cost()
