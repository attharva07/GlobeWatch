"""AI-powered free text task parsing."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

import httpx

from .config import get_config
from .validators import validate_payload

LOGGER = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a strict JSON parser. Convert user task notes to JSON with keys: "
    "title, description, priority (low|medium|high|urgent), status (pending|in_progress|done), "
    "start_ts (ISO8601 or null), due_ts (ISO8601 or null). "
    "Infer reasonable defaults. Do not include extra keys. Respond with JSON only."
)


class AIParsingError(RuntimeError):
    """Raised when the AI parser returns an invalid payload."""


def _build_request_payload(text: str) -> Dict[str, Any]:
    return {
        "model": "gpt-3.5-turbo",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }


def parse_free_text(text: str) -> dict[str, Any]:
    """Parse free-form text into structured task data using OpenAI Chat Completions."""

    cfg = get_config()
    if not cfg.openai_api_key:
        raise AIParsingError("OPENAI_API_KEY is not configured")

    payload = _build_request_payload(text)
    headers = {"Authorization": f"Bearer {cfg.openai_api_key}"}

    with httpx.Client(timeout=30.0) as client:
        response = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, json.JSONDecodeError) as exc:
        LOGGER.error("Failed to parse AI response: %s", data)
        raise AIParsingError("Invalid response from AI parser") from exc

    try:
        validated = validate_payload(parsed)
    except Exception as exc:  # noqa: BLE001 - surface validation issues
        LOGGER.debug("AI payload validation error", exc_info=exc)
        raise AIParsingError(str(exc)) from exc

    return validated
