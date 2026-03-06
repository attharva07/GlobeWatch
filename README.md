# GlobeWatch

GlobeWatch is a secure backend foundation for a public-data situational-awareness globe application. The repository includes a FastAPI backend and a Vite frontend.

## Tech Stack
- Python 3.12+
- FastAPI + Pydantic
- SQLAlchemy + SQLite
- Uvicorn
- Pytest
- Node.js 20 + Vite

## Local Startup
1. Create backend environment variables:
   ```bash
   cp .env.example .env
   ```
2. Create frontend environment variables:
   ```bash
   cp frontend/.env.example frontend/.env
   ```
3. Start backend (binds to `127.0.0.1:8000`):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python run.py
   ```
4. Start frontend (binds to `localhost:5173`) in another shell:
   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

API docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Run Tests
```bash
pytest -q
```

## CI
GitHub Actions CI runs on every push and pull request via `.github/workflows/ci.yml`.

- **Backend job**: installs Python dependencies, writes CI `.env`, runs `pytest`, imports `app.main`, boots the backend, and curls `/health` plus `/api/v1/globe/markers?layers=news`.
- **Frontend job**: installs dependencies with `npm ci`, writes frontend `.env`, and runs `npm run build`.

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
See `.env.example` and `frontend/.env.example`.

## Project Structure
```text
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
frontend/
tests/
run.py
requirements.txt
.env.example
frontend/.env.example
```

## Architecture Notes
- **Service-based modular design** separates route handlers from business logic.
- **Repository layer** encapsulates SQLAlchemy query logic.
- **Marker normalization layer** ensures frontend receives consistent marker contracts.
- **Startup bootstrap** creates tables and seeds globally distributed mock events if DB is empty.
- **Safety baseline** includes configurable CORS, environment-based configuration, optional API key guard, and controlled exception handling.

## Product Safety Scope
This backend intentionally focuses on safe, public geospatial data. It does **not** implement people search, identity resolution, facial recognition, or person tracking.
