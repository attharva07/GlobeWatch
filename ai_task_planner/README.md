# AI Task Planner & Tracker

AI Task Planner & Tracker is a desktop productivity application that combines an AI-assisted task parser, a local SQLite task database, and two-way Google Calendar synchronization. The application provides a PyQt6-based interface with calendar and list views, automatic scheduling and notifications, and offline-friendly queueing of local changes.

## Features

- **AI-assisted task capture** – Paste plain-text notes and let the integrated ChatGPT parser extract structure.
- **SQLite-backed task store** – Tasks persist locally with SQLAlchemy models and automatic timestamps.
- **Two-way Google Calendar sync** – Keep desktop tasks and Google Calendar events aligned using incremental sync tokens.
- **Dark-themed PyQt6 UI** – Calendar, list, and detail panes with keyboard shortcuts and quick actions.
- **Desktop notifications** – Plyer-based alerts for upcoming deadlines and urgent tasks.
- **Automated scheduling** – APScheduler runs background sync and notification scans.

## Getting Started

### Prerequisites

- Python 3.11
- Google Cloud project with the Calendar API enabled

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Google API Setup

1. Visit the [Google Cloud Console](https://console.cloud.google.com/), enable the Calendar API, and configure an OAuth consent screen for an installed application.
2. Create OAuth 2.0 credentials (Desktop application) and download the `client_secret.json` file.
3. Place `client_secret.json` in the project root (next to `pyproject.toml`).

### Environment Configuration

Copy the example environment file and fill in the required values:

```bash
cp .env.example .env
```

Set the following keys in `.env`:

- `OPENAI_API_KEY` – OpenAI API key with access to Chat Completions.
- `GOOGLE_CLIENT_SECRET_FILE` – Path to your downloaded `client_secret.json` (default `./client_secret.json`).
- `DEFAULT_CALENDAR_ID` – Google Calendar ID to sync (default `primary`).
- `NOTIFY_LEAD_MINUTES` – Minutes before due time to trigger notifications (default `30`).
- `TIMEZONE` – IANA timezone string (default `America/New_York`).
- Optional overrides for the priority color mapping:
  - `PRIORITY_COLOR_LOW`
  - `PRIORITY_COLOR_MEDIUM`
  - `PRIORITY_COLOR_HIGH`
  - `PRIORITY_COLOR_URGENT`

### Running the Application

```bash
python -m src.app
```

On first launch, the Google OAuth flow opens in your default browser. After authorizing the application, a `token.json` file is stored in the project root for future sessions.

The main window displays a calendar on the left, a task list for the selected day, and a detail pane on the right. Use the toolbar buttons or keyboard shortcuts:

- **Ctrl+N** – Add Task
- **Ctrl+S** – Save changes
- **Ctrl+F** – Focus search
- **F5** – Run sync

### Priority Color Mapping

By default, task priorities map to Google Calendar color IDs as follows:

| Priority | Color ID |
|----------|----------|
| low      | 2        |
| medium   | 9        |
| high     | 11       |
| urgent   | 4        |

Override these IDs through `.env` values for custom calendars.

### Sync & Conflict Handling

The sync engine performs bi-directional updates:

- **Local to Google** – Newly created or modified tasks are pushed as Google Calendar events. The engine includes metadata markers in the event description to help reverse mapping.
- **Google to Local** – Incremental changes are retrieved using Google sync tokens. New events become tasks, and updates merge using a *last write wins* policy comparing `Task.updated_at` against the Google event's `updated` timestamp.

If Google reports a cancellation, the corresponding local task is marked as `done` and its Google references cleared unless the configuration requests deletion. Offline changes remain queued locally and are pushed the next time sync succeeds.

### Troubleshooting

| Issue | Resolution |
|-------|------------|
| `invalid_grant` during OAuth | Delete `token.json`, ensure system clock is accurate, and repeat the sign-in process. |
| Rate limit errors | Sync automatically backs off; try again later or reduce sync frequency in configuration. |
| Network errors | The application queues local updates and retries sync when connectivity is restored. Check logs under `logs/app.log`. |

### Development

- Logging is configured via `core/logging_conf.py` with rotation in `logs/app.log`.
- Tests run with `pytest`.
- Static analysis is configured with Ruff and mypy.

### License

This project template is provided as-is for integration into the PeopleHunt workspace.
