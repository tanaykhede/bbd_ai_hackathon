import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

def setup_logging(log_file_path: str = "logs/app.log", level: int = logging.INFO) -> None:
    """
    Configure application-wide logging:
      - TimedRotatingFileHandler writing to logs/app.log (rotates at midnight, keeps 7 days)
      - StreamHandler to stdout (useful for local/dev)
      - Captures warnings into logging
      - Ensures uvicorn/fastapi loggers propagate to root
    """
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    # Avoid duplicate handlers on reload
    for h in list(root.handlers):
        root.removeHandler(h)

    # File handler (rotated daily)
    file_handler = TimedRotatingFileHandler(
        log_file_path, when="midnight", backupCount=7, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # Capture warnings (warnings.warn) into logging
    logging.captureWarnings(True)

    # Let common libraries propagate into root
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        l = logging.getLogger(name)
        l.setLevel(level)
        l.propagate = True

    logging.getLogger("app").info("Logging initialized")
