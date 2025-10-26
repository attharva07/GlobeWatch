"""Google Calendar client integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

try:  # pragma: no cover - optional dependency handling
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import Resource, build
except ImportError:  # pragma: no cover
    Request = None  # type: ignore[assignment]
    Credentials = None  # type: ignore[assignment]
    InstalledAppFlow = None  # type: ignore[assignment]
    build = None  # type: ignore[assignment]
    if TYPE_CHECKING:  # pragma: no cover
        from googleapiclient.discovery import Resource as _Resource
    else:
        _Resource = Any
    Resource = _Resource  # type: ignore[assignment]

from .config import get_config
from .mapping import priority_to_color
from .models import Task

LOGGER = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = Path("token.json")
_SERVICE: Resource | None = None


def _load_credentials() -> Credentials:
    cfg = get_config()
    creds: Credentials | None = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to refresh credentials: %s", exc)
            creds = None
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(cfg.google_client_secret_file), SCOPES
        )
        creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def ensure_client() -> Resource:
    """Return an authenticated Google Calendar resource client."""

    global _SERVICE
    if _SERVICE is None:
        if build is None or Credentials is None or InstalledAppFlow is None or Request is None:
            raise RuntimeError("Google API client libraries are not installed")
        creds = _load_credentials()
        _SERVICE = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return _SERVICE


def _build_event_payload(task: Task) -> Dict[str, Any]:
    description = (
        f"{task.description}\n\n"
        f"[Priority:{task.priority}][Status:{task.status}][LocalID:{task.id}]"
    )
    start_ts = task.start_ts or (
        (task.due_ts - timedelta(hours=1)) if task.due_ts else datetime.now(timezone.utc)
    )
    end_ts = task.due_ts or (start_ts + timedelta(hours=1))
    payload = {
        "summary": task.title,
        "description": description,
        "start": {"dateTime": start_ts.astimezone(timezone.utc).isoformat()},
        "end": {"dateTime": end_ts.astimezone(timezone.utc).isoformat()},
        "colorId": priority_to_color(task.priority),
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": 10}],
        },
    }
    return payload


def upsert_event(task: Task) -> str:
    """Create or update a Google Calendar event and return its ID."""

    service = ensure_client()
    cfg = get_config()
    event_body = _build_event_payload(task)
    calendar_id = task.gcal_calendar_id or cfg.default_calendar_id
    if task.gcal_event_id:
        updated = (
            service.events()
            .update(calendarId=calendar_id, eventId=task.gcal_event_id, body=event_body)
            .execute()
        )
    else:
        updated = (
            service.events()
            .insert(calendarId=calendar_id, body=event_body, supportsAttachments=False)
            .execute()
        )
    return updated["id"]


def delete_event(task: Task) -> None:
    """Delete an event on Google Calendar if it exists."""

    service = ensure_client()
    cfg = get_config()
    if not task.gcal_event_id:
        return
    try:
        service.events().delete(
            calendarId=task.gcal_calendar_id or cfg.default_calendar_id,
            eventId=task.gcal_event_id,
        ).execute()
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to delete Google event %s: %s", task.gcal_event_id, exc)


def pull_changed_events(sync_token: str | None) -> Tuple[List[Dict[str, Any]], str | None]:
    """Fetch changed events since the last sync token."""

    service = ensure_client()
    cfg = get_config()
    events: List[Dict[str, Any]] = []
    page_token: str | None = None
    new_sync_token: str | None = None

    while True:
        kwargs: Dict[str, Any] = {
            "calendarId": cfg.default_calendar_id,
            "singleEvents": True,
            "showDeleted": True,
            "maxResults": 250,
        }
        if sync_token:
            kwargs["syncToken"] = sync_token
        else:
            kwargs["timeMin"] = datetime.now(timezone.utc) - timedelta(days=30)
            kwargs["timeMin"] = kwargs["timeMin"].isoformat()
        if page_token:
            kwargs["pageToken"] = page_token
        response = service.events().list(**kwargs).execute()
        events.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        new_sync_token = response.get("nextSyncToken", new_sync_token)
        if not page_token:
            break
    return events, new_sync_token
