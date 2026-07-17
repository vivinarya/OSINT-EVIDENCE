from __future__ import annotations
from datetime import datetime, timezone


def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, TypeError):
        return ts


def truncate_url(url: str, max_len: int = 60) -> str:
    return url if len(url) <= max_len else url[:max_len] + "..."


def confidence_color(confidence: float) -> str:
    if confidence >= 0.7:
        return "#3fb950"
    if confidence >= 0.4:
        return "#d2a8ff"
    return "#f85149"


def confidence_label(confidence: float) -> str:
    if confidence >= 0.7:
        return "High"
    if confidence >= 0.4:
        return "Medium"
    return "Low"
