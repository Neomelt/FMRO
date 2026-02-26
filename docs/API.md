# FMRO Backend API (v0.1)

Base URL: `http://localhost:8080/api/v1`

## Health

- `GET /health`

## Overview

- `GET /overview`

## Company

- `GET /companies`
- `POST /companies`
- `PUT /companies/{id}`
- `DELETE /companies/{id}`

Create payload:

```json
{
  "name": "DJI",
  "officialSite": "https://www.dji.com",
  "careersUrl": "https://www.dji.com/careers",
  "active": true
}
```

## Job Posting

- `GET /jobs?companyId=1`
- `POST /jobs`
- `PUT /jobs/{id}`
- `DELETE /jobs/{id}`

Create payload:

```json
{
  "companyId": 1,
  "title": "Robotics Intern",
  "location": "Shenzhen",
  "sourceUrl": "https://www.dji.com/careers",
  "applyUrl": "https://careers.example/apply/123",
  "deadlineAt": "2026-03-31T00:00:00Z",
  "status": "open"
}
```

## Application

- `GET /applications?stage=applied`
- `POST /applications`
- `PUT /applications/{id}`
- `DELETE /applications/{id}`

Create payload:

```json
{
  "jobPostingId": 1,
  "companyName": "DJI",
  "role": "Robotics Intern",
  "appliedAt": "2026-02-25T10:00:00Z",
  "deadlineAt": "2026-03-31T00:00:00Z",
  "stage": "applied",
  "notes": "Resume v3"
}
```

## Interview Round

- `GET /applications/{id}/rounds`
- `POST /applications/{id}/rounds`
- `PUT /rounds/{id}`
- `DELETE /rounds/{id}`

Create payload:

```json
{
  "roundNo": 1,
  "scheduledAt": "2026-03-03T06:00:00Z",
  "outcome": "pending",
  "note": "online interview"
}
```

## Review Queue (Crawler Pipeline)

- `GET /review-queue?status=pending`
- `POST /review-queue`
- `POST /review-queue/{id}/approve`
- `POST /review-queue/{id}/reject`

Manual queue payload:

```json
{
  "sourceType": "manual",
  "payload": {
    "companyId": "1",
    "companyName": "DJI",
    "title": "SLAM Intern",
    "location": "Shenzhen",
    "sourceUrl": "https://www.dji.com/careers",
    "applyUrl": "https://apply.example/123",
    "status": "open"
  },
  "confidence": 0.9
}
```

## Crawler

- `POST /crawler/run`

Behavior:
- scans active companies with non-empty `careersUrl`
- adds candidate postings to `review_queue`
- deduplicates existing open jobs and pending queue entries
- waits for manual approve/reject

## Quick Demo Flow

```bash
# 1) create company
curl -s -X POST http://localhost:8080/api/v1/companies \
  -H 'content-type: application/json' \
  -d '{"name":"DJI","careersUrl":"https://www.dji.com/careers"}'

# 2) run crawler
curl -s -X POST http://localhost:8080/api/v1/crawler/run

# 3) check pending queue
curl -s 'http://localhost:8080/api/v1/review-queue?status=pending'

# 4) approve id=1 -> creates job_posting
curl -s -X POST http://localhost:8080/api/v1/review-queue/1/approve
```
