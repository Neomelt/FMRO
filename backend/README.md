# FMRO Backend

Kotlin + Ktor backend for FMRO.

## Run

```bash
gradle run
```

If you use Gradle wrapper later, switch to:

```bash
./gradlew run
```

Or run from project root:

```bash
./scripts/run_backend.sh
```

## Storage Mode

Default is in-memory store.

To enable PostgreSQL:

```bash
export FMRO_STORE=postgres
export FMRO_DB_URL='jdbc:postgresql://127.0.0.1:5432/fmro'
export FMRO_DB_USER='postgres'
export FMRO_DB_PASSWORD='postgres'
gradle run
```

## Endpoint Smoke Check

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8080/api/v1/overview
```

From project root you can run end-to-end API smoke:

```bash
./scripts/smoke_api.sh
```
