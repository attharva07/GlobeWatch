"""Tests for priority/color mapping."""

from __future__ import annotations

from ..core.mapping import build_mapping, color_to_priority, priority_to_color


def test_priority_to_color(monkeypatch) -> None:
    mapping = build_mapping()
    assert priority_to_color("low") == mapping.forward["low"]
    assert priority_to_color("urgent") == mapping.forward["urgent"]


def test_color_to_priority() -> None:
    mapping = build_mapping()
    for priority, color in mapping.forward.items():
        assert color_to_priority(color) == priority
