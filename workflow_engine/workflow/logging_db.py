import logging
from typing import Optional
from sqlalchemy.orm import Session
from workflow.db.models import Base, LogEntry
from sqlalchemy.exc import SQLAlchemyError

class DBLogHandler(logging.Handler):
    """
    Logging handler that writes log records into the database.
    Accepts a session factory (e.g., SessionLocal), opening a short session per record.
    """

    def __init__(self, session_factory, level=logging.INFO):
        super().__init__(level)
        self._session_factory = session_factory

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
            entry = LogEntry(
                level=record.levelname,
                logger_name=record.name,
                message=msg,
                pathname=getattr(record, "pathname", None),
                lineno=getattr(record, "lineno", None),
                func=getattr(record, "funcName", None),

                # HTTP context, populated via logger.extra in middleware
                http_method=getattr(record, "http_method", None),
                http_path=getattr(record, "http_path", None),
                status_code=getattr(record, "status_code", None),
                duration_ms=int(getattr(record, "duration_ms", 0)) if getattr(record, "duration_ms", None) is not None else None,
                user_agent=getattr(record, "user_agent", None),
                client_ip=getattr(record, "client_ip", None),
                user_id=getattr(record, "user_id", None),
            )
            session: Optional[Session] = None
            try:
                session = self._session_factory()
                session.add(entry)
                session.commit()
            finally:
                if session is not None:
                    session.close()
        except Exception:
            # Never raise from logging; swallow errors quietly
            self.handleError(record)

def setup_db_logging(session_factory, engine, level=logging.INFO) -> None:
    """
    Attach DBLogHandler to root logger and ensure the logs table exists.
    """
    # Ensure the logs table exists
    try:
        Base.metadata.create_all(bind=engine, tables=[LogEntry.__table__])
    except SQLAlchemyError:
        # If table creation fails, we still proceed to not break the app
        pass

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing DBLogHandler instances to avoid duplicates (hot reload scenarios)
    for h in list(root.handlers):
        if isinstance(h, DBLogHandler):
            root.removeHandler(h)

    db_handler = DBLogHandler(session_factory, level=level)
    # Keep message formatting minimal; we store structured fields separately
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    db_handler.setFormatter(formatter)
    root.addHandler(db_handler)

    # Propagate library loggers
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        l = logging.getLogger(name)
        l.setLevel(level)
        l.propagate = True

    logging.getLogger("app").info("DB logging initialized")
