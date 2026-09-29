"""
Database initialization and connection management for Maritime AI System
"""
import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# Import from config
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATABASE_URL

# Use async version of PostgreSQL URL
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = None
AsyncSessionLocal = None
_db_error = None


def mark_db_unavailable(error: str):
    """Record why the database is unavailable (degraded mode)"""
    global _db_error
    _db_error = error


def db_state() -> dict:
    """Actual database state for /status (no hardcoded claims)"""
    if engine is not None:
        return {"connected": True, "status": "connected"}
    if _db_error is not None:
        return {"connected": False, "status": f"unavailable: {_db_error}"}
    return {"connected": False, "status": "not initialized"}


async def init_db():
    """Initialize database engine and create tables"""
    global engine, AsyncSessionLocal
    
    try:
        # Create async engine
        engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=False,
            poolclass=NullPool,
            connect_args={
                "timeout": 10,
                "command_timeout": 10,
                "server_settings": {
                    "application_name": "maritime-ai",
                    "jit": "off",
                }
            }
        )
        
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database engine initialized")
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info(f"Database connection successful: {result.fetchone()}")
        
        return engine
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db():
    """Dependency for getting database session"""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def close_db():
    """Close database connections"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")
