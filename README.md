Webhook API – Lyftr AI Backend Assignment

A production-ready FastAPI service for ingesting WhatsApp-like messages with HMAC-SHA256 signature verification, idempotent storage, and comprehensive observability.

The service is fully containerized using Docker Compose, follows 12-factor app principles, and is designed to pass the Lyftr evaluation script exactly as specified.

🚀 Features Implemented

✅ HMAC-SHA256 Signature Verification
Secure webhook endpoint validating cryptographic signatures over raw request bytes

✅ Idempotent Message Ingestion
Duplicate messages prevented using SQLite PRIMARY KEY (message_id)

✅ Pagination & Filtering
Advanced querying on /messages with limit, offset, sender, timestamp, and text search

✅ Analytics Dashboard
Message-level statistics via /stats endpoint

✅ Prometheus Metrics
Production-grade metrics exposed via /metrics

✅ Health Probes
Kubernetes-ready /health/live and /health/ready endpoints

✅ Structured JSON Logging
One JSON log per request with request tracking and webhook outcomes

✅ Docker Compose Setup
One-command deployment with persistent SQLite storage

✅ 12-Factor Configuration
All configuration via environment variables (no hard-coded secrets or paths)

📁 Project Structure
.
├── app/
│   ├── main.py          # FastAPI app, routes, middleware
│   ├── storage.py       # SQLite DB operations
│   ├── models.py        # DB schema initialization
│   ├── logging_utils.py # Structured JSON logger
│   ├── metrics.py       # Prometheus metrics helpers
│   └── config.py        # Environment configuration
├── tests/
│   ├── test_webhook.py
│   ├── test_messages.py
│   └── test_stats.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md

⚙️ Configuration (Environment Variables)
Variable	Description
WEBHOOK_SECRET	Secret key used for HMAC-SHA256 signature verification (required)
DATABASE_URL	SQLite database path (default: sqlite:////data/app.db)
LOG_LEVEL	Logging level (INFO, DEBUG)

The application will fail readiness checks if WEBHOOK_SECRET is not set.

🏃 Quick Start
1️⃣ Clone the Repository
git clone <your-repo-url>
cd webhook-api

2️⃣ Set Environment Variables
export WEBHOOK_SECRET="testsecret"
export DATABASE_URL="sqlite:////data/app.db"

3️⃣ Start the Service
make up


Wait for startup:

sleep 10

4️⃣ Run Tests
chmod +x test_webhook.sh
./test_webhook.sh


The test script validates:

Invalid signature rejection

Valid message insertion

Idempotent duplicate handling

5️⃣ View Logs
make logs

6️⃣ Stop the Service
make down

📡 API Endpoints
POST /webhook

Ingests WhatsApp-like messages exactly once.

Headers

Content-Type: application/json

X-Signature: <hex HMAC-SHA256>

Success Response

{ "status": "ok" }


Failure Cases

401 → Invalid or missing signature

422 → Payload validation error

GET /messages

Returns stored messages with pagination and filters.

Query Parameters

limit (default: 50, min: 1, max: 100)

offset (default: 0)

from (exact sender match)

since (ISO-8601 UTC timestamp)

q (case-insensitive text search)

Ordering

ts ASC, message_id ASC

Response

{
  "data": [...],
  "total": 42,
  "limit": 10,
  "offset": 0
}

GET /stats

Provides message-level analytics.

Returns:

total_messages

senders_count

messages_per_sender (top 10 senders)

first_message_ts

last_message_ts

Health & Ops Endpoints

GET /health/live → Always returns 200 if app is running

GET /health/ready → Returns 200 only if DB is reachable and WEBHOOK_SECRET is set

GET /metrics → Prometheus-compatible metrics

📊 Metrics

Exposed at /metrics using Prometheus exposition format.

Includes:

http_requests_total{path,status}

webhook_requests_total{result}

Request latency histogram (request_latency_ms_bucket)

Metric names are stable and documented.

🧠 Design Decisions
HMAC Verification

Signature computed using HMAC-SHA256

Computed over raw request body bytes

Secret sourced from WEBHOOK_SECRET

Invalid signatures return 401 with no DB insert

Idempotency

Enforced via SQLite PRIMARY KEY (message_id)

Duplicate inserts handled gracefully and still return 200 {"status": "ok"}

Pagination Contract

total reflects the total number of matching records before pagination

Filters applied consistently across count and data queries

Stats Computation

Aggregations implemented using SQL queries for efficiency

Handles empty database cases gracefully

Observability

Structured JSON logs emitted per request

/webhook logs include message_id, dup, and result

Metrics and logs are exception-safe

🛠️ Setup Used

VS Code

Python + FastAPI

Docker & Docker Compose

Occasional ChatGPT assistance for validation logic and edge cases

✅ Evaluation Readiness

This service has been tested against the Lyftr evaluation flow, including:

Health checks

HMAC signature validation

Idempotent webhook ingestion

Pagination and filtering

Stats correctness

Metrics exposure

Structured JSON loggin
