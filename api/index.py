"""
Vercel Serverless Function Handler for KiranaVaani FastAPI Backend.
Handles path normalization for Vercel's ASGI bridge.
"""
from backend.app.main import app as fastapi_app


async def app(scope, receive, send):
    if scope["type"] == "http":
        path = scope.get("path", "")
        # Normalize Vercel internal function path rewrites
        for prefix in ("/api/index.py", "/api/index"):
            if path.startswith(prefix):
                new_path = path[len(prefix):] or "/"
                scope["path"] = new_path
                scope["raw_path"] = new_path.encode("utf-8")
                break
    await fastapi_app(scope, receive, send)
