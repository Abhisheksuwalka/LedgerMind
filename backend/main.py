import logging
import os
from dotenv import load_dotenv

# Load env variables before doing anything else
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect

from api.routes import router, limiter
from db.models import init_db
from ws.manager import ConnectionManager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ledgermind")

app = FastAPI(
    title="LedgerMind",
    description="AI-powered CFO for indie SaaS founders — free-tier LLMs, zero paid dependency.",
    version="2.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _error_response(status_code: int, code: str, message: str, detail=None):
    payload = {
        "error": {
            "code": code,
            "message": message,
            "detail": detail,
        },
        # Keep legacy shape for compatibility with existing clients.
        "detail": detail if detail is not None else message,
    }
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", "Request failed")
        code = detail.get("code", f"http_{exc.status_code}")
    else:
        message = str(detail) if detail else "Request failed"
        code = f"http_{exc.status_code}"
    return _error_response(exc.status_code, code, message, detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    errors = exc.errors()
    return _error_response(422, "validation_error", "Request validation failed", errors)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled server error: %s", exc)
    return _error_response(500, "internal_server_error", "Unexpected server error")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.on_event("startup")
async def on_startup():
    await init_db()
    from tools.llm_router import log_provider_status
    log_provider_status()
    app.state.ws_manager = manager
    logger.info("LedgerMind started — database ready")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "LedgerMind"}
