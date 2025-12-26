import hmac
import hashlib
import time
import uuid
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, validator
import uvicorn

from config import settings
from storage import Database
from logging_utils import setup_logger, log_request
from metrics import MetricsCollector

logger = setup_logger()
metrics = MetricsCollector()


class WebhookMessage(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_: str = Field(..., alias="from")
    to: str
    ts: str
    text: Optional[str] = Field(None, max_length=4096)

    @validator("from_", "to")
    def validate_e164(cls, v):
        if not v.startswith("+") or not v[1:].isdigit():
            raise ValueError("must be E.164 format (+ followed by digits)")
        return v

    @validator("ts")
    def validate_timestamp(cls, v):
        if not v.endswith("Z"):
            raise ValueError("timestamp must end with Z")
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("invalid ISO-8601 timestamp")
        return v


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not settings.WEBHOOK_SECRET:
        logger.error("WEBHOOK_SECRET not set - failing startup")
        raise RuntimeError("WEBHOOK_SECRET must be set")
    
    db = Database(settings.DATABASE_URL)
    db.init_db()
    app.state.db = db
    logger.info("Application started", extra={"database": settings.DATABASE_URL})
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.start_time = time.time()
    
    response = await call_next(request)
    
    latency_ms = int((time.time() - request.state.start_time) * 1000)
    
    log_data = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": latency_ms
    }
    
    # Add webhook-specific fields if present
    if hasattr(request.state, "webhook_data"):
        log_data.update(request.state.webhook_data)
    
    log_request(logger, log_data)
    
    # Update metrics
    metrics.record_request(request.url.path, response.status_code, latency_ms)
    
    return response


def verify_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/webhook")
async def webhook(request: Request):
    # Read raw body
    body = await request.body()
    
    # Check signature
    signature = request.headers.get("X-Signature", "")
    if not verify_signature(body, signature):
        request.state.webhook_data = {
            "result": "invalid_signature",
            "dup": False
        }
        metrics.record_webhook("invalid_signature")
        logger.error("Invalid signature", extra={"request_id": request.state.request_id})
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "invalid signature"}
        )
    
    # Parse and validate
    try:
        message = WebhookMessage.parse_raw(body)
    except Exception as e:
        request.state.webhook_data = {
            "result": "validation_error",
            "dup": False
        }
        metrics.record_webhook("validation_error")
        raise
    
    # Store message
    db: Database = request.app.state.db
    is_duplicate = db.insert_message(
        message.message_id,
        message.from_,
        message.to,
        message.ts,
        message.text
    )
    
    result = "duplicate" if is_duplicate else "created"
    request.state.webhook_data = {
        "message_id": message.message_id,
        "result": result,
        "dup": is_duplicate
    }
    
    metrics.record_webhook(result)
    
    return {"status": "ok"}


@app.get("/messages")
async def get_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_: Optional[str] = Query(None, alias="from"),
    since: Optional[str] = Query(None),
    q: Optional[str] = Query(None)
):
    db: Database = app.state.db
    
    messages, total = db.get_messages(
        limit=limit,
        offset=offset,
        from_msisdn=from_,
        since=since,
        search_text=q
    )
    
    return {
        "data": messages,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/stats")
async def get_stats():
    db: Database = app.state.db
    stats = db.get_stats()
    return stats


@app.get("/health/live")
async def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready():
    if not settings.WEBHOOK_SECRET:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "reason": "WEBHOOK_SECRET not set"}
        )
    
    try:
        db: Database = app.state.db
        db.check_health()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "reason": str(e)}
        )


@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    return metrics.generate_prometheus_format()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)