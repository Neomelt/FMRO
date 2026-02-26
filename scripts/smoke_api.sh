#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${FMRO_BASE_URL:-http://127.0.0.1:8080}"
API="$BASE_URL/api/v1"

echo "[1/6] health"
curl -fsS "$BASE_URL/health"
echo -e "\n"

echo "[2/6] create company"
COMPANY_RESP=$(curl -fsS -X POST "$API/companies" \
  -H 'content-type: application/json' \
  -d '{"name":"FMRO Demo Robotics","careersUrl":"https://example.com/careers"}')
echo "$COMPANY_RESP"
COMPANY_ID=$(python3 - <<'PY' "$COMPANY_RESP"
import json,sys
print(json.loads(sys.argv[1])["id"])
PY
)

echo "[3/6] run crawler"
curl -fsS -X POST "$API/crawler/run"
echo -e "\n"

echo "[4/6] list pending review queue"
QUEUE_RESP=$(curl -fsS "$API/review-queue?status=pending")
echo "$QUEUE_RESP"
REVIEW_ID=$(python3 - <<'PY' "$QUEUE_RESP"
import json,sys
arr=json.loads(sys.argv[1])
print(arr[0]["id"] if arr else "")
PY
)

if [ -z "$REVIEW_ID" ]; then
  echo "No pending review found; smoke test failed"
  exit 1
fi

echo "[5/6] approve review -> create job"
JOB_RESP=$(curl -fsS -X POST "$API/review-queue/$REVIEW_ID/approve")
echo "$JOB_RESP"
JOB_ID=$(python3 - <<'PY' "$JOB_RESP"
import json,sys
print(json.loads(sys.argv[1])["id"])
PY
)

echo "[6/6] create application + round"
APP_RESP=$(curl -fsS -X POST "$API/applications" \
  -H 'content-type: application/json' \
  -d "{\"jobPostingId\":$JOB_ID,\"companyName\":\"FMRO Demo Robotics\",\"role\":\"Robotics Intern\",\"stage\":\"applied\"}")
echo "$APP_RESP"
APP_ID=$(python3 - <<'PY' "$APP_RESP"
import json,sys
print(json.loads(sys.argv[1])["id"])
PY
)

curl -fsS -X POST "$API/applications/$APP_ID/rounds" \
  -H 'content-type: application/json' \
  -d '{"roundNo":1,"outcome":"pending","note":"smoke test round"}'
echo -e "\n\nSmoke test done."
