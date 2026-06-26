import logging, json, sys
from datetime import datetime, timezone
from app.config import settings

class JSONFormatter(logging.Formatter):
    def format(self, record):
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname.lower(), "service": "notification-service", "message": record.getMessage()}
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)

def get_logger(name):
    log = logging.getLogger(name)
    log.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(JSONFormatter())
        log.addHandler(h)
    log.propagate = False
    return log

logger = get_logger("notification-service")
