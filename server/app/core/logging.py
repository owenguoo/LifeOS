import logging
import sys
from typing import Any, Dict
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, "extra_data"):
            log_entry["extra"] = record.extra_data
            
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("lifeos")
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
    
    return logger


def log_api_request(endpoint: str, method: str, user_id: str = None, **kwargs):
    logger = logging.getLogger("lifeos.api")
    extra_data = {
        "endpoint": endpoint,
        "method": method,
        "user_id": user_id,
        **kwargs
    }
    logger.info(f"API Request: {method} {endpoint}", extra={"extra_data": extra_data})


def log_video_processing(event: str, video_id: str = None, **kwargs):
    logger = logging.getLogger("lifeos.video")
    extra_data = {
        "event": event,
        "video_id": video_id,
        **kwargs
    }
    logger.info(f"Video Processing: {event}", extra={"extra_data": extra_data})


def log_error(error: Exception, context: Dict[str, Any] = None):
    logger = logging.getLogger("lifeos.error")
    extra_data = {
        "error_type": type(error).__name__,
        "context": context or {}
    }
    logger.error(f"Error occurred: {str(error)}", exc_info=True, extra={"extra_data": extra_data})