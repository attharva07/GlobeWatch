# GlobeWatch

GlobeWatch now uses real-world ingestion (GDELT) and country-level aggregation for globe markers.

## Backend setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

## Frontend setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Provider configuration
Set in `.env`:
- `INGESTION_PROVIDER=gdelt`
- `INGESTION_ENABLED=true`
- `INGESTION_INTERVAL_SECONDS=900`
- `INGESTION_STARTUP_RUN=true`
- `GDELT_BASE_URL`
- `GDELT_QUERY`
- `GDELT_MAX_RECORDS`
- `ENABLE_MOCK_SEED=false` (default)

## Ingestion system
- Startup runs at most one ingestion cycle when `INGESTION_STARTUP_RUN=true`.
- The periodic async loop waits for `INGESTION_INTERVAL_SECONDS` after startup ingestion before the next cycle (prevents immediate duplicate calls).
- HTTP 429 responses are handled as provider rate-limit warnings: the current cycle is skipped, cached DB data is kept, and retry happens on the next scheduled interval.
- A periodic async loop fetches provider events, normalizes fields, deduplicates by `external_id` or a fingerprint hash (`title + timestamp + location`), and upserts into DB.
- Mock seed remains available only as an explicit development fallback.

## Region aggregation logic
- Country is the V1 aggregation unit.
- `GET /api/v1/globe/regions` returns aggregated markers (`region_id`, `region_name`, centroid lat/lon, `event_count`, top categories, severity).
- `GET /api/v1/globe/regions/{region_id}/events` returns events for a selected region.
- Frontend renders one marker per region and loads region event cards on click.

## API
- `GET /api/v1/globe/markers` (legacy per-event markers)
- `GET /api/v1/globe/regions`
- `GET /api/v1/globe/regions/{region_id}/events`
- `GET /api/v1/news/events`
- `GET /api/v1/news/status`
