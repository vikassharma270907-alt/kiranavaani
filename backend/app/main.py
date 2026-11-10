"""
Main FastAPI Application Entrypoint for KiranaVaani.
"""
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.config import HOST, PORT, is_live_gnani_configured
from backend.app.api.routes import api_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kiranavaani")


@asynccontextmanager
async def lifespan(app: FastAPI):
    live_status = "ENABLED (Live Cloud API)" if is_live_gnani_configured() else "DEMO/MOCK (No API Key configured)"
    logger.info("==================================================================")
    logger.info("KiranaVaani Backend Initialized Successfully")
    logger.info(f"Gnani AI Service Status: {live_status}")
    logger.info("Endpoints: /health, /catalogue, /transcribe, /parse-order, /match-products, /cart, /synthesize, /process-order")
    logger.info("==================================================================")
    yield


app = FastAPI(
    title="KiranaVaani API",
    version="2.0.0",
    description=(
        "Noise-Robust Hinglish Voice Assistant for Neighbourhood Kirana Stores. "
        "Powered by Gnani AI Prisma STT, Timbre TTS, RapidFuzz Catalogue Matching, "
        "and Conversational Clarification Gates."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API endpoints at both root and /api prefix for seamless local and Vercel routing
app.include_router(api_router)
app.include_router(api_router, prefix="/api")

# Static frontend mounting (supports unified full-stack serving on Render, Docker, and local)
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    @app.exception_handler(StarletteHTTPException)
    async def spa_404_handler(request, exc: StarletteHTTPException):
        if exc.status_code == 404 and request.method == "GET":
            if not request.url.path.startswith(("/api", "/docs", "/redoc", "/openapi.json")):
                return FileResponse(frontend_dist / "index.html")
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return JSONResponse(
            content={
                "app": "KiranaVaani",
                "version": "2.0.0",
                "description": "Noise-Robust Hinglish Voice Assistant for Kirana Stores",
                "docs": "/docs",
                "health": "/health"
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=True)
