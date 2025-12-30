"""Utility helpers for cleaning and normalizing movie/person JSON data."""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, Generator, Iterable, List, Optional

UNICODE_ESCAPE_PATTERN = re.compile(r"\\u[0-9a-fA-F]{4}")


def clean_text(value: Any) -> Optional[str]:
    """Normalize text fields by stripping, decoding escapes, and removing empties."""

    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return decode_unicode_escape(text)
    return str(value)


def parse_int(value: Any) -> Optional[int]:
    """Extract digits from mixed strings and cast to int when possible."""

    if value is None:
        return None
    cleaned = re.sub(r"[^0-9]", "", str(value))
    return int(cleaned) if cleaned else None


def decode_unicode_escape(text: str) -> str:
    """Decode literal ``\\uXXXX`` sequences without touching normal backslashes."""

    if not UNICODE_ESCAPE_PATTERN.search(text):
        return text
    try:
        return text.encode("utf-8").decode("unicode_escape")
    except UnicodeDecodeError:
        return text


def decode_unicode_tree(obj: Any) -> Any:
    """Recursively decode escaped Unicode values inside nested JSON structures."""

    if isinstance(obj, str):
        return decode_unicode_escape(obj)
    if isinstance(obj, list):
        return [decode_unicode_tree(item) for item in obj]
    if isinstance(obj, dict):
        return {key: decode_unicode_tree(value) for key, value in obj.items()}
    return obj


def normalize_json_list(values: Any) -> Optional[List[Any]]:
    """Ensure values are stored as a list while preserving nested escapes."""

    if values is None:
        return None
    if isinstance(values, list):
        return decode_unicode_tree(values)
    return decode_unicode_tree([values])


def parse_date_field(value: Optional[str]) -> tuple[Optional[date], Optional[str]]:
    """Parse loose date strings into ``date`` objects while keeping the raw text."""

    raw = clean_text(value)
    if not raw:
        return None, None

    numbers = [int(x) for x in re.findall(r"\d+", raw)]
    if not numbers:
        return None, raw

    year = numbers[0]
    month = numbers[1] if len(numbers) > 1 else 1
    day = numbers[2] if len(numbers) > 2 else 1
    try:
        return date(year, month, day), raw
    except ValueError:
        return None, raw


def chunked(iterable: Iterable[Dict[str, Any]], size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """Yield ``size``-bounded batches from an iterable."""

    batch: List[Dict[str, Any]] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


__all__ = [
    "clean_text",
    "parse_int",
    "decode_unicode_escape",
    "decode_unicode_tree",
    "normalize_json_list",
    "parse_date_field",
    "chunked",
]
