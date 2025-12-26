# Webhook API - Lyftr AI Backend Assignment

A production-ready FastAPI service for ingesting WhatsApp-like messages with HMAC signature verification, idempotency, and comprehensive observability.

## 🚀 Features

- ✅ **HMAC-SHA256 Signature Verification** - Secure webhook endpoint with cryptographic validation
- ✅ **Idempotent Message Ingestion** - Duplicate detection using SQLite PRIMARY KEY constraint
- ✅ **Pagination & Filtering** - Advanced query capabilities on `/messages` endpoint
- ✅ **Analytics Dashboard** - Real-time statistics via `/stats` endpoint
- ✅ **Prometheus Metrics** - Production-grade observability with `/metrics` endpoint
- ✅ **Health Probes** - Kubernetes-ready liveness and readiness checks
- ✅ **Structured JSON Logging** - Machine-readable logs with request tracking
- ✅ **Docker Compose Setup** - One-command deployment with persistent storage
- ✅ **12-Factor Configuration** - Environment-based configuration

## 📋 Prerequisites

- Docker & Docker Compose
- Make (optional, for convenience commands)
- Git

## 🏃 Quick Start

### 1. Clone the Repository
```bash
# Navigate to project directory
cd webhook-api

# Set environment variable
export WEBHOOK_SECRET="testsecret"

# Start the service
make up

# Wait for startup (10 seconds)
sleep 10

# Run tests
chmod +x test_webhook.sh
./test_webhook.sh

# View logs
make logs

# Stop the service
make down
