#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import subprocess
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
SUMMARY_FILE = SCRIPT_DIR / "CostUSD.md"
EPSILON = Decimal("0.000001")
HEADER = [
    "| Date | InputTokens | CachedInputTokens | OutputTokens | ReasoningOutputTokens | TotalTokens | CostUSD | Models | FallbackModels | Status |",
    "|------|-------------|-------------------|--------------|-----------------------|-------------|---------|--------|----------------|--------|",
]


@dataclass(frozen=True)
class Record:
    date: str
    input_tokens: int
    cached_input_tokens: Optional[int]
    output_tokens: int
    reasoning_output_tokens: Optional[int]
    total_tokens: int
    cost_usd: Decimal
    models: Optional[Tuple[str, ...]] = None
    fallback_models: Optional[Tuple[str, ...]] = None
    status: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect and audit Codex token usage.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Collect daily usage and update audit logs.")
    collect.add_argument("--since-days", type=positive_int, default=40)
    collect.add_argument("--align-window", type=positive_int, default=2)
    collect.add_argument("--json-file", type=Path, help="Read ccusage JSON from a file instead of bunx.")

    subparsers.add_parser("summary", help="Calculate monthly CostUSD totals.")
    return parser.parse_args()


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return parsed


def decimal_from(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid CostUSD value: {value!r}") from exc


def cost_equal(left: Decimal, right: Decimal) -> bool:
    return abs(left - right) < EPSILON


def compare_cost(left: Decimal, right: Decimal) -> int:
    if left < right:
        return -1
    if left > right:
        return 1
    return 0


def parse_date(value: str) -> str:
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        return text
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            return dt.datetime.strptime(text, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    raise ValueError(f"invalid date value: {value!r}")


def record_from_day(day: Dict[str, Any]) -> Record:
    date = parse_date(day["date"])
    models = day.get("models") or {}
    model_names = tuple(sorted(str(name) for name in models))
    fallback_names = tuple(
        sorted(str(name) for name, model in models.items() if model.get("isFallback"))
    )
    return Record(
        date=date,
        input_tokens=int(day["inputTokens"]),
        cached_input_tokens=int(day.get("cachedInputTokens", 0)),
        output_tokens=int(day["outputTokens"]),
        reasoning_output_tokens=int(day.get("reasoningOutputTokens", 0)),
        total_tokens=int(day["totalTokens"]),
        cost_usd=decimal_from(day["costUSD"]),
        models=model_names,
        fallback_models=fallback_names,
    )


def token_line(record: Record, status: str) -> str:
    cached = "" if record.cached_input_tokens is None else str(record.cached_input_tokens)
    reasoning = "" if record.reasoning_output_tokens is None else str(record.reasoning_output_tokens)
    models = "<br>".join(record.models or ()) or "-"
    fallback_models = "<br>".join(record.fallback_models or ()) or "-"
    return (
        f"| {record.date} | {record.input_tokens} | {cached} | {record.output_tokens} | "
        f"{reasoning} | {record.total_tokens} | {record.cost_usd} | {models} | "
        f"{fallback_models} | {status} |"
    )


def parse_optional_int(value: str) -> Optional[int]:
    text = value.strip()
    return int(text) if text else None


def parse_models(value: str) -> Optional[Tuple[str, ...]]:
    text = value.strip()
    if not text:
        return None
    if text == "-":
        return tuple()
    text = text.replace("<br />", "<br>").replace("<br/>", "<br>")
    return tuple(item.strip() for item in text.split("<br>") if item.strip())


def parse_token_line(line: str) -> Optional[Record]:
    if not line.startswith("|"):
        return None
    parts = [part.strip() for part in line.split("|")]
    if len(parts) < 12 or not parts[1].isdigit() or len(parts[1]) != 8:
        return None
    try:
        return Record(
            date=parts[1],
            input_tokens=int(parts[2]),
            cached_input_tokens=parse_optional_int(parts[3]),
            output_tokens=int(parts[4]),
            reasoning_output_tokens=parse_optional_int(parts[5]),
            total_tokens=int(parts[6]),
            cost_usd=decimal_from(parts[7]),
            models=parse_models(parts[8]),
            fallback_models=parse_models(parts[9]),
            status=parts[10],
        )
    except (IndexError, ValueError):
        return None


def optional_field_aligned(old: Optional[Any], new: Optional[Any]) -> bool:
    return old is None or old == new


def records_aligned(old: Record, new: Record) -> bool:
    return (
        old.input_tokens == new.input_tokens
        and optional_field_aligned(old.cached_input_tokens, new.cached_input_tokens)
        and old.output_tokens == new.output_tokens
        and optional_field_aligned(old.reasoning_output_tokens, new.reasoning_output_tokens)
        and old.total_tokens == new.total_tokens
        and cost_equal(old.cost_usd, new.cost_usd)
        and optional_field_aligned(old.models, new.models)
        and optional_field_aligned(old.fallback_models, new.fallback_models)
    )


def load_json(args: argparse.Namespace) -> Dict[str, Any]:
    if args.json_file:
        return json.loads(args.json_file.read_text(encoding="utf-8"))

    since = (dt.date.today() - dt.timedelta(days=args.since_days)).strftime("%Y%m%d")
    command = ["bunx", "@ccusage/codex@latest", "daily", "--json", "--since", since]
    print("Running command:", " ".join(command))
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "ccusage failed")
    return json.loads(result.stdout)


def group_by_month(days: List[Dict[str, Any]]) -> Dict[str, List[Record]]:
    months: Dict[str, List[Record]] = {}
    for day in days:
        record = record_from_day(day)
        months.setdefault(record.date[:6], []).append(record)
    for records in months.values():
        records.sort(key=lambda item: item.date)
    return months


def read_month_file(path: Path) -> Tuple[List[str], Dict[str, Record], Dict[str, int]]:
    if not path.exists():
        path.write_text("\n".join(HEADER) + "\n", encoding="utf-8")
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        lines = HEADER[:]
    else:
        lines[0:2] = HEADER
    trusted: Dict[str, Record] = {}
    indexes: Dict[str, int] = {}
    for index, line in enumerate(lines):
        record = parse_token_line(line)
        if record and record.status != "CONFLICT":
            lines[index] = token_line(record, record.status)
            trusted[record.date] = record
            indexes[record.date] = index
    return lines, trusted, indexes


def find_alignment_end(current: List[Record], trusted: Dict[str, Record], window: int) -> Optional[str]:
    aligned_end: Optional[str] = None
    if len(current) < window:
        return None
    for start in range(0, len(current) - window + 1):
        chunk = current[start : start + window]
        if all(day.date in trusted and records_aligned(trusted[day.date], day) for day in chunk):
            aligned_end = chunk[-1].date
    return aligned_end


def collect(args: argparse.Namespace) -> None:
    payload = load_json(args)
    daily = payload.get("daily")
    if not daily:
        print("No daily data was returned.")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for month, current_days in sorted(group_by_month(daily).items()):
        path = DATA_DIR / f"{month}.md"
        lines, trusted, indexes = read_month_file(path)
        aligned_end = find_alignment_end(current_days, trusted, args.align_window)
        if aligned_end is None:
            print(f"[{month}] No continuous alignment window of {args.align_window} days was found.")
        else:
            print(f"[{month}] Found alignment window ending at {aligned_end}.")

        for current in current_days:
            if current.date not in trusted:
                line = token_line(current, "NEW")
                lines.append(line)
                trusted[current.date] = Record(**{**current.__dict__, "status": "NEW"})
                indexes[current.date] = len(lines) - 1
                print(f"NEW: {current.date} costUSD={current.cost_usd}")
                continue

            old = trusted[current.date]
            if aligned_end is not None and current.date <= aligned_end:
                continue
            if aligned_end is None:
                if not records_aligned(old, current):
                    lines.append(token_line(current, "CONFLICT"))
                    print(f"CONFLICT: {current.date} no alignment window")
                continue

            comparison = compare_cost(current.cost_usd, old.cost_usd)
            if comparison < 0:
                lines.append(token_line(current, "CONFLICT"))
                print(f"CONFLICT: {current.date} cost decreased")
            elif comparison > 0:
                line = token_line(current, "UPDATED")
                lines[indexes[current.date]] = line
                trusted[current.date] = Record(**{**current.__dict__, "status": "UPDATED"})
                print(f"UPDATED: {current.date} costUSD {old.cost_usd} -> {current.cost_usd}")
            elif not records_aligned(old, current):
                lines.append(token_line(current, "CONFLICT"))
                print(f"CONFLICT: {current.date} costUSD is equal but token fields differ")

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"DONE. Data directory: {DATA_DIR}")


def summary() -> None:
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"data directory was not found: {DATA_DIR}")
    output = ["| Month | Days | CostUSD |", "|-------|------|---------|"]
    grand_total = Decimal("0")
    for path in sorted(DATA_DIR.glob("*.md")):
        if len(path.stem) != 6 or not path.stem.isdigit():
            continue
        total = Decimal("0")
        days = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            record = parse_token_line(line)
            if record and record.status != "CONFLICT":
                total += record.cost_usd
                days += 1
        grand_total += total
        output.append(f"| {path.stem} | {days} | {total:.6f} |")
    output.append(f"| TOTAL | - | {grand_total:.6f} |")
    SUMMARY_FILE.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"DONE. Monthly cost summary written to: {SUMMARY_FILE}")
    print(f"TOTAL CostUSD: {grand_total:.6f}")


def main() -> None:
    args = parse_args()
    if args.command == "collect":
        collect(args)
    elif args.command == "summary":
        summary()


if __name__ == "__main__":
    main()
