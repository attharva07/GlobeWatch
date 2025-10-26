"""Tests for the AI parser module."""

from __future__ import annotations

import json
from typing import Any

import pytest

from ..core import ai_parser
from ..core.config import reset_config_cache


class DummyResponse:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._data


class DummyClient:
    def __init__(self, response: DummyResponse) -> None:
        self._response = response
        self.post_called_with: dict[str, Any] | None = None

    def __enter__(self) -> "DummyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, json: dict[str, Any], headers: dict[str, str]) -> DummyResponse:
        self.post_called_with = {"url": url, "json": json, "headers": headers}
        return self._response


@pytest.fixture(autouse=True)
def _setup_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    reset_config_cache()


def test_parse_free_text(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_payload = {
        "title": "Write report",
        "description": "Prepare the Q1 summary",
        "priority": "high",
        "status": "pending",
        "start_ts": "2023-09-01T09:00:00Z",
        "due_ts": "2023-09-01T11:00:00Z",
    }
    dummy_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(expected_payload),
                }
            }
        ]
    }
    response = DummyResponse(dummy_data)

    def fake_client(*args, **kwargs):
        return DummyClient(response)

    monkeypatch.setattr(ai_parser.httpx, "Client", fake_client)
    result = ai_parser.parse_free_text("Write report tomorrow morning")
    assert result["title"] == "Write report"
    assert result["priority"] == "high"
    assert result["due_ts"].isoformat().endswith("+00:00")
