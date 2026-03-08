# Comotion Web App

Coach analytics dashboard for [Comotion](https://github.com/louisza/comotion) wearable tracker data. Upload match CSVs, view player performance, track season workload.

## Documentation

- **[Product Specification](docs/PRODUCT_SPEC.md)** — Full product spec (screens, metrics, data model, pipeline, build order)
- **[Deployment Guide](docs/DEPLOY.md)** — Railway deployment instructions

## Architecture

```
Browser → Next.js (React) → FastAPI (Python) → PostgreSQL
                                    ↓
                              CSV Processing Pipeline
                              (validate → clean → metrics)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 + React 19 + Tailwind CSS 4 |
| Backend API | Python 3.12 + FastAPI + SQLAlchemy (async) |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Raw storage | Local filesystem (S3 in production) |

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard — KPI cards, recent matches |
| `/matches` | Match list with status badges |
| `/matches/new` | Create new match |
| `/matches/:id` | Match detail — upload CSVs, player table |
| `/matches/:id/players/:pid` | Player card — 14 metrics, load bar |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (includes DB status) |
| POST | `/api/v1/organizations` | Create organization |
| GET | `/api/v1/organizations` | List organizations |
| POST | `/api/v1/organizations/:id/teams` | Create team |
| POST | `/api/v1/teams/:id/players` | Create player |
| POST | `/api/v1/matches` | Create match |
| GET | `/api/v1/matches` | List matches |
| GET | `/api/v1/matches/:id` | Get match details |
| DELETE | `/api/v1/matches/:id` | Delete match |
| POST | `/api/v1/matches/:id/upload` | Upload CSV |
| GET | `/api/v1/matches/:id/uploads` | List uploads |
| GET | `/api/v1/matches/:id/players` | Player summaries |

## CSV Processing Pipeline

1. **Ingest** — Upload CSV, validate schema/headers
2. **Clean** — Flag missing timestamps, low satellites, impossible speeds
3. **Derive** — Distance, speed zones, sprints, acceleration events, IMU load
4. **Publish** — Write PlayerMatchSummary to database

Quality flags returned: GPS quality %, missing timestamps, speed spikes, satellite issues.

## Quick Start

```bash
# Clone
git clone https://github.com/louisza/comotion-web.git
cd comotion-web

# Copy env
cp .env.example .env

# Start with Docker
docker compose up -d

# API: http://localhost:8000/docs (Swagger UI)
# Web: http://localhost:3000
```

## Deploy to Railway

See [docs/DEPLOY.md](docs/DEPLOY.md) for full instructions.

```bash
railway login && railway init
railway add --plugin postgresql
# Deploy api + web as separate services
```

## Tests

```bash
cd api
pip install pytest pytest-asyncio httpx
pytest tests/
```

## Related Repos

- [comotion](https://github.com/louisza/comotion) — Monorepo
- [comotion-firmware](https://github.com/louisza/comotion-firmware) — Wearable firmware (NRF52840 / Zephyr)
- [comotion-mobile](https://github.com/louisza/comotion-mobile) — Flutter mobile app
- [comotion-hardware](https://github.com/louisza/comotion-hardware) — 3D printed case designs
