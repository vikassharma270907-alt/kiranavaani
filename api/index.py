"""
Vercel Serverless Function Handler for KiranaVaani FastAPI Backend.
Exposes the FastAPI app for Vercel Serverless execution.
"""
from backend.app.main import app

# Vercel's Python runtime recognizes 'app' directly as ASGI handler
