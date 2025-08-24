import logging
import time
import re
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from jose import jwt
from workflow.auth.security import SECRET_KEY, ALGORITHM
from workflow.logging_db import setup_db_logging
from workflow.db.database import SessionLocal, engine
from workflow.routers import (
    auth,
    cases,
    processes,
    tasks,
    process_definitions,
    process_types,
    process_data_types,
    task_rules,
    steps,
    statuses,
    process_data,
)

# Initialize DB logging early
setup_db_logging(SessionLocal, engine)

app = FastAPI()

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")

# HTTP logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("app")

    def _sanitize_body(body_text: str, content_type: str, path: str) -> str:
        # Mask common sensitive fields
        try:
            t = body_text
            # JSON-style password
            t = re.sub(r'("password"\s*:\s*")[^"]*(")', r'\1***\2', t, flags=re.IGNORECASE)
            # form/urlencoded password
            t = re.sub(r'(password=)[^&]+', r'\1***', t, flags=re.IGNORECASE)
            # Basic trimming
            return t[:2000]  # limit size to avoid huge logs
        except Exception:
            return body_text[:1000]

    def _user_from_auth_header() -> str:
        auth = request.headers.get("authorization") or request.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                sub = payload.get("sub")
                if isinstance(sub, str) and sub:
                    return sub
            except Exception:
                return "system"
        return "system"

    start = time.time()
    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else "-"
    qs = request.url.query or ""
    ct = request.headers.get("content-type", "") or ""
    user_id = _user_from_auth_header()
    # Read body once; Starlette caches it so handlers can still access it
    try:
        body_bytes = await request.body()
        body_text = body_bytes.decode("utf-8", errors="replace")
    except Exception:
        body_text = "<unreadable>"
    safe_body = _sanitize_body(body_text, ct, request.url.path)

    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000.0)

        if response.status_code >= 400:
            # Log errors with request snapshot
            logger.error(
                "HTTP error %s %s status=%s duration_ms=%s qs=\"%s\" body=\"%s\"",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                qs,
                safe_body,
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_agent": ua,
                    "client_ip": ip,
                    "user_id": user_id,
                },
            )
        else:
            # Normal info log
            logger.info(
                "HTTP request handled",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_agent": ua,
                    "client_ip": ip,
                    "user_id": user_id,
                },
            )
        return response
    except Exception:
        duration_ms = int((time.time() - start) * 1000.0)
        logger.exception(
            "Unhandled exception %s %s duration_ms=%s qs=\"%s\" body=\"%s\"",
            request.method,
            request.url.path,
            duration_ms,
            qs,
            safe_body,
            extra={
                "http_method": request.method,
                "http_path": request.url.path,
                "duration_ms": duration_ms,
                "user_agent": ua,
                "client_ip": ip,
                "user_id": user_id,
            },
        )
        raise

@app.on_event("startup")
async def on_startup():
    logging.getLogger("app").info("Application startup")

@app.on_event("shutdown")
async def on_shutdown():
    logging.getLogger("app").info("Application shutdown")

# Register routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(processes.router)
app.include_router(tasks.router)
app.include_router(process_definitions.router)
app.include_router(process_types.router)
app.include_router(process_data_types.router)
app.include_router(task_rules.router)
app.include_router(steps.router)
app.include_router(statuses.router)
app.include_router(process_data.router)


