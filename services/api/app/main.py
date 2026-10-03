import json
import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from .config import settings
from .portal import router as portal
from .chat_routes import router as chat
from .ticket_routes import router as tickets
from .admin_routes import router as admin

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("nicecomp")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
app = FastAPI(
    title="NICE COMP Support API",
    version="0.1.0",
    docs_url="/docs" if settings().app_env != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().cors_origins.split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
for router in (portal, chat, tickets, admin):
    app.include_router(router)


@app.middleware("http")
async def safe_logging(request: Request, call_next):
    started = time.monotonic()
    request_id = uuid.uuid4().hex
    if int(request.headers.get("content-length", "0") or "0") > 21_000_000:
        return JSONResponse({"detail": "Upload too large."}, status_code=413)
    try:
        response = await call_next(request)
    except Exception:
        logger.error(json.dumps({"event": "api.error", "request_id": request_id}))
        return JSONResponse(
            {"detail": "Service unavailable. Please retry.", "request_id": request_id},
            status_code=503,
        )
    response.headers["X-Request-ID"] = request_id
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    route = request.scope.get("route")
    logger.info(
        json.dumps(
            {
                "event": "api.request",
                "route": getattr(route, "path", "unmatched"),
                "status": response.status_code,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "request_id": request_id,
            }
        )
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never return Pydantic's raw input values (which could include a password).
    return JSONResponse({"detail": "Check the required fields and try again."}, status_code=422)


@app.exception_handler(IntegrityError)
async def conflict(request, exc):
    return JSONResponse(
        {"detail": "A conflicting record already exists. Refresh and retry."}, status_code=409
    )


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings().app_env}
