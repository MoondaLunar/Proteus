# Maritime AI System - File Index & Navigation

## 🗂️ Quick Navigation

### 📖 Start Here
- **README.md** - System overview, architecture, and design principles
- **GETTING_STARTED.md** - Quick start guide and setup instructions
- **PHASE1_SUMMARY.md** - What's been built and current status

### 🔨 Development
- **DEVELOPMENT.md** - Development guidelines, architecture details, best practices
- **Makefile** - Common development commands
- **conftest.py** - Test configuration and fixtures

### 💻 Code
- **main.py** - FastAPI application entry point
- **config.py** - Configuration management
- **database.py** - Database connection layer
- **persistence.py** - PostgreSQL write-through + hydration (asyncpg, phase 3)
- **ships.py** - Ship management routes
- **decisions.py** - Decision engine routes
- **telemetry.py** - Sensor data routes
- **crew.py** - Crew management routes

### 📦 Configuration
- **.env.example** - Environment template (copy to .env)
- **requirements.txt** - Python dependencies
- **Dockerfile** - Docker container definition
- **docker-compose.yml** - Multi-container orchestration

### 📊 Database
- **init_db.sql** - PostgreSQL schema (25+ tables)

### 📚 Examples & Utilities
- **example_usage.py** - API usage examples
- **setup_project.py** - Project initialization script

### ✅ Testing
- **tests/** - Test suite directory (structure ready)
- **conftest.py** - Pytest fixtures

## 📋 File Details

### Core Application Files

#### main.py
```
Purpose: FastAPI application entry point
Size: ~4.4 KB
Features:
  - Application initialization with lifespan management
  - CORS and security middleware
  - Health check endpoints
  - Global exception handler
  - Route router inclusion points
```

#### config.py
```
Purpose: Configuration management
Size: ~1.2 KB
Features:
  - Database connection URL
  - Message queue configuration
  - Cache (Redis) configuration
  - Application settings (debug, log level, etc.)
  - Security settings (JWT, SECRET_KEY)
  - Maritime-specific configuration
  - Satellite/livestream settings
```

#### database.py
```
Purpose: Database connection and session management
Size: ~2.5 KB
Features:
  - Async database engine initialization
  - SQLAlchemy AsyncSessionLocal setup
  - Connection health checks
  - Session dependency for FastAPI
  - Connection cleanup on shutdown
```

### API Route Files

#### ships.py (~2.4 KB)
- GET /api/v1/ships - List all ships
- POST /api/v1/ships - Register new ship
- GET /api/v1/ships/{ship_id} - Get ship details
- GET /api/v1/ships/{ship_id}/status - Real-time status
- GET /api/v1/ships/{ship_id}/power - Power system status
- GET /api/v1/ships/{ship_id}/sensors - List sensors

#### decisions.py (~3.9 KB)
- GET /api/v1/decisions - List decisions (with filtering)
- POST /api/v1/decisions - Create decision
- GET /api/v1/decisions/{decision_id} - Get details
- POST /api/v1/decisions/{decision_id}/approve - Approve/override
- POST /api/v1/decisions/{decision_id}/execute - Execute
- GET /api/v1/decisions/{decision_id}/reasoning - Get reasoning
- GET /api/v1/decisions/{ship_id}/pending - Pending decisions
- GET /api/v1/decisions/{ship_id}/history - Decision history

#### telemetry.py (~4.2 KB)
- GET /api/v1/telemetry/{ship_id} - Generic telemetry
- POST /api/v1/telemetry/{ship_id} - Ingest telemetry
- GET /api/v1/telemetry/{ship_id}/gps - GPS position
- POST /api/v1/telemetry/{ship_id}/gps - Update GPS
- GET /api/v1/telemetry/{ship_id}/weather - Weather data
- POST /api/v1/telemetry/{ship_id}/weather - Ingest weather
- GET /api/v1/telemetry/{ship_id}/radar - Radar contacts
- GET /api/v1/telemetry/{ship_id}/power - Power telemetry
- GET /api/v1/telemetry/{ship_id}/radio - Radio monitoring

#### crew.py (~4.6 KB)
- GET /api/v1/crew/{ship_id} - List crew
- POST /api/v1/crew/{ship_id} - Add crew member
- GET /api/v1/crew/{crew_id} - Get profile
- POST /api/v1/crew/{crew_id}/authenticate - Authenticate
- POST /api/v1/crew/{crew_id}/comms - Send communication
- GET /api/v1/crew/{crew_id}/notifications - Get notifications
- GET /api/v1/crew/{crew_id}/preferences - Get preferences
- PUT /api/v1/crew/{crew_id}/preferences - Update preferences
- GET /api/v1/crew/{ship_id}/captain - Get captain
- GET /api/v1/crew/{ship_id}/decision-log - Get crew decisions
- POST /api/v1/crew/{crew_id}/acknowledge - Acknowledge decision

### Configuration Files

#### .env.example (~3.5 KB)
Environment configuration template covering:
- Database, message queue, cache settings
- Application settings
- Security configuration
- CORS and hosts
- Maritime operations
- Satellite/livestream
- AI & learning
- Radio communications
- Notifications & alerts
- Development/testing flags

#### requirements.txt (~0.4 KB)
Python dependencies including:
- FastAPI, Uvicorn, Pydantic
- SQLAlchemy, Alembic, psycopg2
- RabbitMQ (pika), Redis
- PyTorch, scikit-learn, numpy, pandas
- Cryptography, PyJWT
- Testing (pytest, httpx)
- Code quality (black, flake8, mypy)

#### Dockerfile (~0.5 KB)
- Python 3.12 slim base image
- System dependency installation
- Non-root user for security
- Port 8000 exposure
- Hot-reload development mode

#### docker-compose.yml (~2 KB)
Services:
- PostgreSQL 16 (port 5432)
- RabbitMQ 3.12 (ports 5672, 15672)
- Redis 7 (port 6379)
- FastAPI app (port 8000)

All services include:
- Health checks
- Environment configuration
- Volume persistence
- Networking setup
- Dependency management

### Database Schema (init_db.sql)

**Size**: ~17 KB | **Tables**: 25+ | **Indexes**: 20+

Tables by Category:

**Ship Management**
- ships
- ship_power_systems
- ship_sensors

**Crew Management**
- crew_members
- crew_authentication
- crew_communication_preferences

**Decision System** (Core)
- decisions (immutable, tamper-sealed)
- decision_overrides

**Audit & Logging** (Immutable)
- audit_logs (tamper-sealed)
- tamper_seals

**Telemetry & Data**
- telemetry_data
- weather_data
- radio_communications
- gps_positions
- livestream_sessions

**Intelligence & Learning**
- captain_decision_patterns
- ai_recommendations_feedback
- ai_performance_metrics

**Configuration**
- system_config

**Key Features**
- Automatic updated_at triggers
- Performance-optimized indexes
- Foreign key integrity
- JSONB for flexible data
- Retention policies
- Views for common queries

### Documentation Files

#### README.md (~9.4 KB)
- System overview
- Feature descriptions
- Technology stack
- Architecture diagram
- Design principles
- Database schema highlights
- Configuration guide
- Contributing guidelines
- License and support

#### GETTING_STARTED.md (~10.4 KB)
- Prerequisites
- Quick start (5 minutes)
- Project structure
- Configuration details
- Running the system
- API overview (32 endpoints documented)
- Development workflow
- Code quality tools
- Testing procedures
- Troubleshooting guide
- Quick reference table

#### DEVELOPMENT.md (~10.9 KB)
- Core principles (5 key principles)
- Architecture overview
- Implementation phases (6 phases)
- Database design
- API design principles
- Security implementation
- Adding new features (step-by-step)
- Testing strategy
- Performance optimization
- Deployment strategies
- Monitoring and logging
- Contributing guidelines

#### PHASE1_SUMMARY.md (~12.2 KB)
- What's been built
- Project structure overview
- Database schema highlights
- FastAPI application details
- API routes (26 endpoints)
- Docker infrastructure
- Documentation overview
- Configuration details
- Testing framework
- Development tools
- Current system capabilities
- Project status by phase
- Security features
- Key design decisions
- How to proceed
- Team coordination

### Testing & Development

#### conftest.py (~3.3 KB)
- Event loop fixture for async tests
- Test client (sync and async)
- TestHealth class (2 tests)
- TestShipsEndpoints class (2 tests)
- TestDecisionsEndpoints class (1 test)
- TestTelemetryEndpoints class (2 tests)
- TestCrewEndpoints class (1 test)
- Total: 8 basic tests (expandable)

#### example_usage.py (~12.8 KB)
- Complete API usage examples
- 30+ example functions
- Health checks
- Ship management
- Decision management
- Telemetry collection
- Crew communication
- Full workflow example
- Error handling
- JSON pretty-printing

#### Makefile (~3.5 KB)
20+ commands:
- Setup: install, dev-setup
- Docker: up, down, docker-build, docker-logs, logs
- Development: format, lint, type-check, quality
- Testing: test, test-cov
- Database: db-init, db-shell, db-backup
- Utilities: clean, status, run, health-check, api-docs
- Meta: all-checks, help

### Project Setup

#### setup_project.py (~3.9 KB)
- Creates project directory structure
- Generates Python package __init__ files
- Database initialization script setup
- Helpful startup messages
- Summary of next steps

#### .gitignore (~0.4 KB)
- Python: __pycache__, .pyc, .egg-info
- Virtual environments
- IDEs: .vscode, .idea
- Testing: .pytest_cache, .coverage
- Cache: .mypy_cache, .cache
- Docker: logs

## 📊 Statistics

- **Total Files**: 20+
- **Total Documentation**: ~50 KB
- **Total Code**: ~30 KB
- **Database Schema**: ~17 KB
- **Configuration**: ~5 KB
- **API Endpoints**: 26 (all routes defined)
- **Database Tables**: 25+
- **Indexes**: 20+
- **Development Commands**: 20+
- **Lines of Code**: ~2,500 (foundation)

## 🔄 File Relationships

```
main.py (Entry Point)
├── config.py (Configuration)
├── database.py (Database Connection)
└── Route Files
    ├── ships.py
    ├── decisions.py
    ├── telemetry.py
    └── crew.py

Docker Infrastructure
├── Dockerfile (Container)
├── docker-compose.yml (Orchestration)
└── init_db.sql (Database Schema)

Configuration
├── .env.example (Template)
├── requirements.txt (Dependencies)
└── .gitignore (VCS Rules)

Development
├── Makefile (Commands)
├── conftest.py (Tests)
├── example_usage.py (Examples)
└── setup_project.py (Init)

Documentation
├── README.md (Overview)
├── GETTING_STARTED.md (Setup)
├── DEVELOPMENT.md (Guidelines)
└── PHASE1_SUMMARY.md (Status)
```

## 🎯 How to Use This Index

1. **Getting Started?** → Read README.md then GETTING_STARTED.md
2. **Want to Develop?** → Read DEVELOPMENT.md then reference code files
3. **Need Quick Commands?** → Check Makefile
4. **Want to Run Examples?** → Use example_usage.py
5. **Database Questions?** → Review init_db.sql
6. **API Integration?** → Use example_usage.py and conftest.py
7. **Current Status?** → Read PHASE1_SUMMARY.md

## 📱 File Sizes Summary

| Category | Files | Size |
|----------|-------|------|
| Documentation | 4 | ~50 KB |
| Core Application | 4 | ~10 KB |
| Routes | 4 | ~15 KB |
| Configuration | 5 | ~7 KB |
| Database | 1 | ~17 KB |
| Testing & Examples | 4 | ~20 KB |
| **TOTAL** | **22** | **~120 KB** |

## ✨ Next Steps for Each File

### Before Next Phase
- [ ] Copy .env.example to .env
- [ ] Run docker-compose up -d
- [ ] Verify all services with Makefile commands
- [ ] Review example_usage.py
- [ ] Run pytest to verify tests

### During Phase 2
- [ ] Expand route implementations in ships.py, decisions.py, telemetry.py, crew.py
- [ ] Add new sensor adapters in app/services/
- [ ] Update example_usage.py with real examples
- [ ] Add integration tests in tests/integration/

### Documentation Maintenance
- [ ] Keep README.md updated with new features
- [ ] Update DEVELOPMENT.md with new patterns
- [ ] Add examples to example_usage.py
- [ ] Keep PHASE_X_SUMMARY.md current

---

**This index was generated for the Maritime AI System v0.1.0**
**Last Updated**: 2024
**Total Project Investment**: ~8-10 hours (foundation complete)
