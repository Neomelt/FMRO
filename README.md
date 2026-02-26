# FMRO

Find Much Robot Offer.

FMRO is a personal job-ops system for robotics internship hunting:
- Track company opportunities and deadlines
- Manage interview stages and results
- Visualize progress (kanban + timeline)
- Ingest company career pages with human-in-the-loop review

## Monorepo Layout

- `backend/` Ktor API + crawler scheduler
- `infra/` PostgreSQL schema and migration seed
- `docs/` product and engineering docs (`PRD.md`, `ARCHITECTURE.md`, `API.md`, `SETUP.md`)
- `android/` Android app plan and module notes

## Quick Start (Backend)

```bash
cd backend
./gradlew run
```

Then open `http://localhost:8080/health`.

## Local Setup

See `docs/SETUP.md` for PostgreSQL + backend startup.

## API Smoke Test

```bash
./scripts/smoke_api.sh
```

## Android Dev Loop (Ubuntu/Windows/macOS)

```bash
./scripts/dev_android_loop.sh up emulator
```

See `docs/ANDROID_DEV.md` for emulator setup and USB-device workflow.

## CI/CD

- CI: `FMRO/.github/workflows/ci.yml`
- Release: tag `v*` triggers `FMRO/.github/workflows/release.yml`

## Publish to GitHub

```bash
./scripts/publish_to_github.sh Neomelt FMRO
```

If the repository does not exist yet, create it first in GitHub (or set `GITHUB_TOKEN` before running the script).
