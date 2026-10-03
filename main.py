"""
Maritime AI System - Main Application
FastAPI application setup and initialization
"""
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from config import (
    DEBUG, CORS_ORIGINS, ALLOWED_HOSTS, LOG_LEVEL, ENVIRONMENT
)
from store import store

from ships import router as ships_router
from decisions import router as decisions_router
from telemetry import router as telemetry_router
from crew import router as crew_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def setup_persistence():
    """Attach PostgreSQL persistence to the store (idempotent). Used by the
    lifespan, and callable directly (tests, scripts). The pool is created
    lazily on first use, in whichever loop is running."""
    from persistence import Persistence, bootstrap, connect, hydrate, pg_url
    pool = await connect()
    if pool is None:
        logger.warning("⚠ PostgreSQL unreachable, in-memory store only")
        return None
    await bootstrap(pool)
    counts = await hydrate(pool, store)
    await pool.close()  # hydration done; Persistence opens its own pool lazily
    store.persist = Persistence(pg_url())
    logger.info(f"✓ PostgreSQL persistence on, hydrated: {counts}")
    return counts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    logger.info("🚀 Maritime AI System starting up...")
    logger.info(f"   Environment: {ENVIRONMENT}")
    logger.info(f"   Debug Mode: {DEBUG}")

    try:
        from database import init_db
        await init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        # Degraded mode: the API still serves; /status reports the truth.
        from database import mark_db_unavailable
        mark_db_unavailable(str(e))
        logger.warning(f"⚠ Database unavailable, running degraded: {e}")

    # Phase 3: PostgreSQL persistence (asyncpg write-through + hydration).
    # The API never depends on Postgres being reachable; when it is, the
    # store survives restarts.
    try:
        await setup_persistence()
    except Exception as e:
        logger.warning(f"⚠ Persistence setup failed, in-memory store only: {e}")

    yield

    # Shutdown
    logger.info("🛑 Maritime AI System shutting down...")
    try:
        from persistence import close
        if store.persist is not None:
            await close(store.persist.pool)
            store.persist = None
            logger.info("✓ PostgreSQL pool closed")
    except Exception as e:
        logger.error(f"Error closing persistence pool: {e}")
    try:
        from database import close_db
        await close_db()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Maritime AI System",
    description="Comprehensive AI system for maritime operations and vessel management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "service": "Maritime AI System",
        "version": "0.1.0",
        "environment": ENVIRONMENT
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Maritime AI System API",
        "version": "0.1.0",
        "environment": ENVIRONMENT,
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "ships": "/api/v1/ships",
            "decisions": "/api/v1/decisions",
            "telemetry": "/api/v1/telemetry",
            "crew": "/api/v1/crew",
            "livestream": "/api/v1/livestream",
            "audit": "/api/v1/audit"
        }
    }


@app.get("/status", tags=["Status"])
async def system_status():
    """Get detailed system status (truthful, reflects actual state)"""
    from database import db_state
    db = db_state()
    persistence_state = store.persist.state() if store.persist else {
        "kind": "in-memory only (PostgreSQL unreachable or not configured)"
    }
    return {
        "status": "operational" if db["connected"] else "degraded",
        "version": "0.1.0",
        "environment": ENVIRONMENT,
        "debug_mode": DEBUG,
        "database": db["status"],
        "persistence": persistence_state,
        "message_queue": store.queue.state(),
        "cache": store.cache.state(),
        "routes_mounted": sorted(
            r.path for r in app.routes if r.path.startswith("/api/v1")
        ),
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


# include route modules (wired 2026-09-28, phase 1 made real)
app.include_router(ships_router, prefix="/api/v1")
app.include_router(decisions_router, prefix="/api/v1")
app.include_router(telemetry_router, prefix="/api/v1")
app.include_router(crew_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG,
        log_level=LOG_LEVEL.lower()
    )

