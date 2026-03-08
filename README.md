# Comotion Web App

Coach analytics dashboard for [Comotion](https://github.com/louisza/comotion) wearable tracker data. Upload match CSVs, view player performance, track season workload.

## Documentation

- **[Product Specification](docs/PRODUCT_SPEC.md)** — Full product spec (screens, metrics, data model, pipeline, build order)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React / Next.js |
| Backend API | Python / FastAPI |
| Database | PostgreSQL |
| Raw storage | S3-compatible object store |
| Analytics | Embedded Superset |
| Async processing | Worker queue |

## Related Repos

- [comotion](https://github.com/louisza/comotion) — Monorepo (mobile/backend/web/shared)
- [comotion-firmware](https://github.com/louisza/comotion-firmware) — Wearable firmware (NRF52840 / Zephyr)
- [comotion-mobile](https://github.com/louisza/comotion-mobile) — Flutter mobile app
- [comotion-hardware](https://github.com/louisza/comotion-hardware) — 3D printed case designs

## Status

📋 **Specification phase** — product spec complete, implementation not yet started.
