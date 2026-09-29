# Maritime AI System - Getting Started Guide

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [API Overview](#api-overview)
6. [Development Workflow](#development-workflow)

## Quick Start

### Prerequisites
- Docker & Docker Compose (latest version)
- Python 3.12+ (for local development without Docker)
- Git (for version control)
- 8GB RAM minimum for full stack

### Initial Setup (5 minutes)

```bash
# 1. Navigate to project directory
cd maritime-ai

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Verify services are running
docker-compose ps

# 5. Access the API
# - API: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
# - RabbitMQ Admin: http://localhost:15672
```

## Project Structure

```
maritime-ai/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── routes/                   # API endpoint modules
│   │   ├── ships.py              # Ship management endpoints
│   │   ├── decisions.py          # Decision engine endpoints
│   │   ├── telemetry.py          # Sensor data endpoints
│   │   └── crew.py               # Crew management endpoints
│   ├── models/                   # Pydantic/SQLAlchemy models
│   ├── services/                 # Business logic layer
│   ├── utils/                    # Utility functions
│   └── integrations/             # Third-party integrations
├── tests/                        # Test suites
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── docker/                       # Docker configuration
│   └── init-db.sql              # Database initialization script
├── docs/                         # Documentation
├── logs/                         # Application logs
├── main.py                       # FastAPI application entry point
├── config.py                     # Configuration management
├── database.py                   # Database connection management
├── Dockerfile                    # Docker container definition
├── docker-compose.yml            # Multi-container orchestration
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
└── README.md                     # Main documentation
```

## Configuration

### Environment Variables

Edit `.env` file to configure:

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Message Queue (RabbitMQ)
RABBITMQ_URL=amqp://user:pass@host:5672/

# Cache (Redis)
REDIS_URL=redis://host:6379

# Application
ENVIRONMENT=development          # development, staging, production
DEBUG=true                       # Enable debug mode
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Security
SECRET_KEY=your-secret-key       # Change in production!
ALGORITHM=HS256                  # JWT algorithm

# Maritime Configuration
MAX_SHIPS=100                    # Maximum number of ships
SENSOR_SYNC_INTERVAL_SECONDS=5   # How often to sync sensor data
DECISION_LOG_RETENTION_DAYS=3650 # Retain logs for 10 years

# Satellite/Livestream
SATELLITE_PROVIDER=starlink      # starlink, viasat, inmarsat
STREAM_BITRATE_KBPS=2500        # Video bitrate
STREAM_RESOLUTION=720p          # Video resolution
```

## Running the System

### Using Docker Compose (Recommended)

```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Remove volumes (WARNING: Deletes data!)
docker-compose down -v
```

### Local Development

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py

# Application will be available at http://localhost:8000
```

### Database Management

```bash
# Initialize database schema
docker-compose exec api python -c "from database import init_db; import asyncio; asyncio.run(init_db())"

# View database
docker-compose exec postgres psql -U maritime_user -d maritime_ai

# Backup database
docker-compose exec postgres pg_dump -U maritime_user maritime_ai > backup.sql

# Restore database
docker-compose exec -T postgres psql -U maritime_user maritime_ai < backup.sql
```

## API Overview

### Health & Status Endpoints
```
GET  /health              - System health check
GET  /                    - API information
GET  /status              - Detailed system status
```

### Ships Management
```
GET    /api/v1/ships              - List all ships
POST   /api/v1/ships              - Register new ship
GET    /api/v1/ships/{id}         - Get ship details
GET    /api/v1/ships/{id}/status  - Get real-time status
GET    /api/v1/ships/{id}/power   - Get power system status
GET    /api/v1/ships/{id}/sensors - List ship sensors
```

### Decisions & AI
```
GET    /api/v1/decisions                - List decisions
POST   /api/v1/decisions                - Log new decision
GET    /api/v1/decisions/{id}           - Get decision details
GET    /api/v1/decisions/{id}/reasoning - Get AI reasoning
POST   /api/v1/decisions/{id}/approve   - Approve/override decision
GET    /api/v1/decisions/{ship_id}/pending  - Get pending decisions
GET    /api/v1/decisions/{ship_id}/history - Get decision history
```

### Telemetry & Sensors
```
GET    /api/v1/telemetry/{ship_id}        - Get sensor data
POST   /api/v1/telemetry/{ship_id}        - Ingest sensor reading
GET    /api/v1/telemetry/{ship_id}/gps    - Get GPS position
POST   /api/v1/telemetry/{ship_id}/gps    - Update GPS
GET    /api/v1/telemetry/{ship_id}/weather - Get weather data
POST   /api/v1/telemetry/{ship_id}/weather - Ingest weather
GET    /api/v1/telemetry/{ship_id}/radar  - Get radar contacts
GET    /api/v1/telemetry/{ship_id}/power  - Get power telemetry
GET    /api/v1/telemetry/{ship_id}/radio  - Get radio monitoring
```

### Crew Management
```
GET    /api/v1/crew/{ship_id}              - List crew
POST   /api/v1/crew/{ship_id}              - Add crew member
GET    /api/v1/crew/{crew_id}              - Get crew profile
POST   /api/v1/crew/{crew_id}/authenticate - Authenticate crew
POST   /api/v1/crew/{crew_id}/comms        - Send communication
GET    /api/v1/crew/{crew_id}/notifications - Get notifications
GET    /api/v1/crew/{crew_id}/preferences   - Get preferences
PUT    /api/v1/crew/{crew_id}/preferences   - Update preferences
GET    /api/v1/crew/{ship_id}/captain       - Get ship captain
GET    /api/v1/crew/{ship_id}/decision-log  - Get crew decisions
```

## Development Workflow

### Code Quality

```bash
# Format code with Black
black app/ tests/

# Check types with mypy
mypy app/

# Lint with flake8
flake8 app/ tests/

# Run all checks
black app/ tests/ && mypy app/ && flake8 app/ tests/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_ships.py

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s
```

### Creating New Routes

1. Create new file in `app/routes/` directory
2. Define Pydantic models
3. Create endpoint functions with FastAPI decorators
4. Import router in `main.py`
5. Include router with `app.include_router()`

Example:
```python
# app/routes/new_feature.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class NewModel(BaseModel):
    field: str

@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "Hello"}

# In main.py:
from app.routes import new_feature
app.include_router(new_feature.router, prefix="/api/v1", tags=["NewFeature"])
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Attach debugger with pdb
import pdb; pdb.set_trace()

# View Docker logs
docker-compose logs -f api

# Execute commands in running container
docker-compose exec api python -c "..."
```

## Troubleshooting

### Services Won't Start
```bash
# Check Docker is running
docker --version

# Verify ports are available
netstat -an | grep 5432  # PostgreSQL
netstat -an | grep 5672  # RabbitMQ
netstat -an | grep 6379  # Redis
```

### Database Connection Issues
```bash
# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U maritime_user -c "SELECT 1"
```

### API Not Responding
```bash
# Check API logs
docker-compose logs api

# Verify API is running
curl http://localhost:8000/health

# Restart API service
docker-compose restart api
```

### Port Conflicts
```bash
# Change ports in docker-compose.yml
# Example: Change API port from 8000 to 8080
ports:
  - "8080:8000"  # Host:Container
```

## Next Steps

1. **Review Database Schema** - See `init_db.sql` for complete schema
2. **Explore API Documentation** - Visit http://localhost:8000/docs
3. **Run Tests** - Execute `pytest` to verify setup
4. **Read Main README** - See `README.md` for architecture details
5. **Start Development** - Begin implementing Phase 2 sensors

## Quick Reference

| Task | Command |
|------|---------|
| Start services | `docker-compose up -d` |
| Stop services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Access database | `docker-compose exec postgres psql -U maritime_user -d maritime_ai` |
| Run tests | `pytest` |
| Format code | `black app/` |
| Check types | `mypy app/` |
| API docs | `http://localhost:8000/docs` |

## Support & Resources

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Code Examples**: See `example_usage.py` (when created)
- **Database Schema**: Review `docker/init-db.sql`
- **Configuration**: Check `.env.example` for all options
- **Logs**: View in `logs/` directory

---

**For detailed system architecture and design principles, see README.md**
