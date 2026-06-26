import logging
import json
import sys
from datetime import datetime, timezone
from app.config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level":     record.levelname.lower(),
            "service":   "auth-service",
            "message":   record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, 'extra'):
            entry.update(record.extra)
        return json.dumps(entry)


def get_logger(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        log.addHandler(handler)
    log.propagate = False
    return log


logger = get_logger("auth-service")
