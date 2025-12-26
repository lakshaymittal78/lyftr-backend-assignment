import logging
import json
import sys
from datetime import datetime
from config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms
        if hasattr(record, "message_id"):
            log_data["message_id"] = record.message_id
        if hasattr(record, "dup"):
            log_data["dup"] = record.dup
        if hasattr(record, "result"):
            log_data["result"] = record.result
        
        return json.dumps(log_data)


def setup_logger():
    logger = logging.getLogger("webhook_api")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    logger.handlers.clear()
    logger.addHandler(handler)
    
    return logger


def log_request(logger, data: dict):
    """Log a request with structured data"""
    extra = {k: v for k, v in data.items() if k != "message"}
    message = f"{data.get('method', 'UNKNOWN')} {data.get('path', 'UNKNOWN')} - {data.get('status', 0)}"
    logger.info(message, extra=extra)