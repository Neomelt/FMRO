# FMRO Setup Guide

## 1) Start PostgreSQL (Docker)

```bash
cd infra
docker compose up -d
```

This starts Postgres at `127.0.0.1:5432` with:
- db: `fmro`
- user: `postgres`
- password: `postgres`

## 2) Configure backend env

```bash
cd backend
cp .env.example .env
# edit if needed
```

Then export env for current shell:

```bash
set -a
source .env
set +a
```

## 3) Run backend

From project root:

```bash
./scripts/run_backend.sh
```

## 4) Smoke test API

```bash
./scripts/smoke_api.sh
```

## 5) Android emulator + hot iteration

See `docs/ANDROID_DEV.md`.
