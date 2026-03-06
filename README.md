# GlobeWatch Backend

GlobeWatch is a secure backend foundation for a public-data situational-awareness globe application. This backend currently serves normalized geospatial **news/event** markers and includes safe placeholders for weather, flights, and camera layers.

## Tech Stack
- Python 3.12+
- FastAPI + Pydantic
- SQLAlchemy + SQLite
- Uvicorn
- Pytest

## Quick Start
```bash
cd globewatch
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

API docs:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Run Tests
```bash
cd globewatch
pytest -q
```

## API Routes
- `GET /health`
- `GET /api/v1/globe/markers?layers=news&severity=high&category=weather_alert&limit=20`
- `GET /api/v1/news/events`
- `GET /api/v1/news/status`
- `GET /api/v1/locations/sample`
- `GET /api/v1/weather/status`
- `GET /api/v1/flights/status`
- `GET /api/v1/cameras/status`

## Environment Variables
See `.env.example`.

Key settings:
- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT`
- `API_PREFIX`
- `DATABASE_URL`
- `ALLOWED_ORIGINS`
- `DEBUG`
- `API_KEY_ENABLED`
- `API_KEY`

## Project Structure
```text
globewatch/
  app/
    api/routes/
    core/
    db/
    models/
    repositories/
    schemas/
    services/
    utils/
    main.py
  tests/
  run.py
  requirements.txt
  .env.example
```

## Architecture Notes
- **Service-based modular design** separates route handlers from business logic.
- **Repository layer** encapsulates SQLAlchemy query logic.
- **Marker normalization layer** ensures frontend receives consistent marker contracts.
- **Startup bootstrap** creates tables and seeds globally distributed mock events if DB is empty.
- **Safety baseline** includes configurable CORS, environment-based configuration, optional API key guard, and controlled exception handling.

## Product Safety Scope
This backend intentionally focuses on safe, public geospatial data. It does **not** implement people search, identity resolution, facial recognition, or person tracking.
