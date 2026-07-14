import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
import logging

from app.api.research import router as research_router
from app.api.models import router as models_router
from app.api.ws import router as ws_router
from app.core.checkpointer import checkpoint_db_path
from app.orchestrator.graph import build_graph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Establish connection lifecycle for AsyncSqliteSaver
    async with AsyncSqliteSaver.from_conn_string(checkpoint_db_path) as saver:
        app.state.graph = build_graph(saver)
        yield

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local Research Backend",
    version="0.1.0",
    lifespan=lifespan
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=getattr(exc, "headers", None)
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "stage": "request",
            "message": str(exc.detail),
            "details": ""
        },
        headers=getattr(exc, "headers", None)
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error occurred in request pipeline")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "stage": "backend",
            "message": "Internal server error.",
            "details": str(exc)
        }
    )

# Include API and WS routers
app.include_router(research_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(ws_router, prefix="/api")

# Serve UI static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def get_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Local Research Backend is running. Frontend static/index.html not found.</h1>")