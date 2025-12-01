"""FastAPI main application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import Database
from api.routes import (
    auth_router,
    events_router,
    fights_router,
    predictions_router,
    scorecards_router,
    users_router,
)

# Global database instance (singleton)
_db: Optional[Database] = None

# Path to frontend build
FRONTEND_BUILD_PATH = Path(__file__).parent.parent / "frontend" / "dist"


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        db_path = os.getenv("DATABASE_PATH", "mma_data.db")
        _db = Database(db_path)
    return _db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs on startup and shutdown."""
    # Startup: ensure database tables exist
    db = get_database()
    db.create_tables()
    yield
    # Shutdown: nothing to clean up for SQLite


app = FastAPI(
    title="MMA Scoring API",
    description="""
    MMA Fight Scoring Application API
    
    Features:
    - Browse upcoming MMA events and fight cards
    - Submit pre-fight predictions (winner + method)
    - Submit round-by-round scorecards (10-point must system)
    - View crowd wisdom aggregations and statistics
    - Telegram authentication for user identification
    
    All picks are immutable once submitted - you cannot change them!
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
# In production, frontend is served from same origin, so CORS is less critical
# But we keep it for development and potential API access from other origins
allow_all_origins = os.getenv("CORS_ALLOW_ALL", "false").lower() == "true"

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Add custom origins from environment (comma-separated)
custom_origins = os.getenv("CORS_ORIGINS", "")
if custom_origins:
    origins.extend([o.strip() for o in custom_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(fights_router, prefix="/api")
app.include_router(predictions_router, prefix="/api")
app.include_router(scorecards_router, prefix="/api")
app.include_router(users_router, prefix="/api")


@app.get("/")
async def root():
    """API root endpoint with basic info."""
    return {
        "name": "MMA Scoring API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health_check():
    """API health check endpoint (for Railway)."""
    return {"status": "healthy"}


# Serve frontend static files in production
if FRONTEND_BUILD_PATH.exists():
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=FRONTEND_BUILD_PATH / "assets"), name="assets")
    
    # Serve index.html for all non-API routes (SPA fallback)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the SPA for all non-API routes."""
        # Don't serve index.html for API routes
        if full_path.startswith("api/") or full_path in ["docs", "openapi.json", "redoc"]:
            return {"detail": "Not found"}
        
        # Check if it's a static file
        file_path = FRONTEND_BUILD_PATH / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # Return index.html for SPA routing
        return FileResponse(FRONTEND_BUILD_PATH / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

