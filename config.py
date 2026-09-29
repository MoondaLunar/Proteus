"""Maritime AI System - Configuration Module"""
import os
from typing import List

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://maritime_user:maritime_secure_pass_dev@postgres:5432/maritime_ai"
)

# RabbitMQ
RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://maritime_user:maritime_secure_pass_dev@rabbitmq:5672/"
)

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Application
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "maritime-ai-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

# CORS
CORS_ORIGINS = ["http://localhost", "http://localhost:3000", "http://localhost:8000"]
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Maritime specific
MAX_SHIPS = 100
SENSOR_SYNC_INTERVAL_SECONDS = 5
DECISION_LOG_RETENTION_DAYS = 3650

# Satellite
SATELLITE_PROVIDER = os.getenv("SATELLITE_PROVIDER", "starlink")
STREAM_BITRATE_KBPS = 2500
STREAM_RESOLUTION = "720p"
