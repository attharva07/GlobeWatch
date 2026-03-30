"""In-memory cache for live layer data with provider status tracking."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

# Structure: {key: {"data": [...], "ts": float, "source": str, "count": int}}
_layer_cache: dict[str, dict[str, Any]] = {}


def set_cache(key: str, data: list[dict], *, source: str = "live") -> None:
    _layer_cache[key] = {
        "data": data,
        "ts": time.monotonic(),
        "wall": time.time(),
        "source": source,
        "count": len(data),
    }


def get_cache(key: str) -> list[dict] | None:
    entry = _layer_cache.get(key)
    return entry["data"] if entry else None


def get_status() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for key, entry in _layer_cache.items():
        result[key] = {
            "count": entry["count"],
            "last_fetch": datetime.fromtimestamp(entry["wall"], UTC).isoformat(),
            "source": entry["source"],
            "status": "ok",
        }
    return result
