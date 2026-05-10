from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional, Tuple


EPSILON = Decimal("0.000001")
ALLOWED_STATUSES = {"NEW", "UPDATED", "CONFLICT"}
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


def decimal_from(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid CostUSD value: {value!r}") from exc


def cost_equal(left: Decimal, right: Decimal) -> bool:
    return abs(left - right) < EPSILON


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
    if len(parts) != 12 or not parts[1].isdigit() or len(parts[1]) != 8:
        return None
    status = parts[10]
    if status not in ALLOWED_STATUSES:
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
            status=status,
        )
    except (IndexError, ValueError):
        return None


def parse_required_token_line(path: Path, line_number: int, line: str) -> Record:
    record = parse_token_line(line)
    if record is None:
        raise ValueError(f"invalid audit row in {path} line {line_number}: {line}")
    return record
