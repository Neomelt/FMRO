# FMRO Architecture

## Components

- Android App (Kotlin + Compose + Room)
- Backend API (Ktor + PostgreSQL)
- Crawler Worker (Kotlin coroutines)

## Data Flow

1. Crawler fetches whitelisted company careers pages
2. Parser normalizes data into `review_queue`
3. User approves entries into `job_posting`
4. Application/interview states are tracked and visualized

## Security

- Single-user auth token for API
- Rate limiting for crawler domains
- Robots.txt and terms-respecting crawl policies
