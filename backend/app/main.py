"""
Main FastAPI Application Entrypoint for KiranaVaani.
"""
from contextlib import asynccontextmanager
import logging
import os
import re
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

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

# Enable spec-compliant CORS (wildcard cannot be paired with allow_credentials=True)
cors_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if cors_origins_env:
    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Standard HTTP security headers and cache invalidation
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:;"
    if request.url.path == "/" or request.url.path.endswith((".html", ".htm")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount all API endpoints at root, and secondary mirror at /api prefix (excluded from schema to avoid duplicate operation IDs)
app.include_router(api_router)
app.include_router(api_router, prefix="/api", include_in_schema=False)

# Static frontend mounting (supports unified full-stack serving on Render, Docker, and local; disabled on Vercel where CDN serves frontend/dist)
is_vercel = bool(os.getenv("VERCEL"))
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if not is_vercel and frontend_dist.exists() and (frontend_dist / "index.html").exists():
    try:
        from fastapi.staticfiles import StaticFiles
        from starlette.exceptions import HTTPException as StarletteHTTPException

        @app.exception_handler(StarletteHTTPException)
        async def spa_404_handler(request, exc: StarletteHTTPException):
            if exc.status_code == 404 and request.method == "GET":
                path = request.url.path
                is_system_path = path.startswith(("/etc", "/var", "/bin", "/usr", "/proc", "/sys", "/windows", "/..", ".."))
                has_extension = bool(re.search(r"\.[a-zA-Z0-9]+$", path))
                api_prefixes = (
                    "/api", "/docs", "/redoc", "/openapi.json", "/health", "/catalogue",
                    "/khata", "/ondc", "/audio-samples", "/transcribe", "/parse-order",
                    "/match-products", "/cart", "/synthesize", "/process-order",
                    "/price-check", "/budget-order", "/soundbox-chime", "/receipt",
                    "/voiceprint", "/inventory", "/mandi", "/telemetry", "/judge",
                    "/benchmark", "/judge-arena", "/negotiate-bhav", "/delivery", "/recipe-to-cart"
                )
                if not path.startswith(api_prefixes) and not is_system_path and not has_extension:
                    return FileResponse(frontend_dist / "index.html")
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    except Exception as e:
        logger.warning(f"Could not mount static frontend: {e}")
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
