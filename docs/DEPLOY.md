# Comotion Web — Railway Deployment

## Services

This project deploys as **3 Railway services** from one repo:

| Service | Directory | Port | Description |
|---------|-----------|------|-------------|
| **api** | `/api` | 8000 | FastAPI backend |
| **web** | `/web` | 3000 | Next.js frontend |
| **postgres** | (Railway plugin) | 5432 | PostgreSQL database |

## Quick Deploy

### 1. Create Railway Project

```bash
# Install Railway CLI
npm i -g @railway/cli
railway login
railway init    # creates project
```

### 2. Add PostgreSQL

```bash
railway add --plugin postgresql
```

### 3. Deploy API

```bash
railway service create api
railway link api
railway up --service api
```

### 4. Deploy Web

```bash
railway service create web
railway link web
railway up --service web
```

### 5. Environment Variables

**API service:**
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
S3_BUCKET=comotion-uploads
S3_ENDPOINT=https://...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
CORS_ORIGINS=${{web.RAILWAY_PUBLIC_DOMAIN}}
```

**Web service:**
```
NEXT_PUBLIC_API_URL=${{api.RAILWAY_PUBLIC_DOMAIN}}
```

Railway auto-injects `PORT` and `RAILWAY_PUBLIC_DOMAIN`.

## Local Development

```bash
docker compose up -d    # Postgres + MinIO
cd api && pip install -r requirements.txt && uvicorn main:app --reload
cd web && npm install && npm run dev
```
