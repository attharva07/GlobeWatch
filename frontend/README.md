# GlobeWatch Frontend (Phase 3)

React + Vite + TypeScript interface for rendering GlobeWatch backend markers on a 3D Cesium globe.

## Setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend runs on default Vite port (`5173`) and reads backend URL from `VITE_API_BASE_URL`.

## Backend integration

- `GET /health`
- `GET /api/v1/globe/markers?layers=news`

No mock marker data is used; markers are fetched directly from backend API.

## Build

```bash
npm run build
npm run preview
```
