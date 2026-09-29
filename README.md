# Maritime AI System

A comprehensive AI-powered maritime operations management system designed to monitor sensor data, learn from captain decisions, make intelligent recommendations, and maintain tamper-sealed audit logs.

## Features

### Core Capabilities
- 🚢 **Multi-Ship Fleet Management** - Support for 1-100+ vessels with centralized monitoring
- 🤖 **Intelligent Decision Engine** - AI recommends actions based on sensor data and learned captain patterns
- 📊 **Real-Time Sensor Integration** - Radar, weather, GPS, power systems, radio communications
- ⚡ **Renewable Energy Monitoring** - Hydro and solar power tracking with efficiency metrics
- 🎥 **24/7 Satellite Livestream** - GPS-overlaid video feed via satellite internet
- 📡 **Radio Communications** - Monitor local radio channels with logging
- 🧠 **Captain Learning System** - ML models learn from captain decision patterns
- 🔐 **Digital Tamper Seals** - Cryptographically signed audit logs (Ed25519)
- ✅ **Captain Authority** - Human-in-the-loop control; captain override ALWAYS takes precedence
- 📋 **Complete Decision Logging** - Immutable record of all decisions (AI, Captain, First Mate)
- 💬 **Individual Crew Communication** - Per-vessel messaging and notifications

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Center Dashboard                 │
│                   (Fleet Monitoring & Control)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Maritime AI Central Hub                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Decision Engine | Learning Module | Auth Manager     │ │
│  │  Audit Logger    | Tamper Seals    | Message Queue    │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Ship Agent #1   │ │  Ship Agent #2   │ │  Ship Agent #N   │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ Sensor Ingestion │ │ Sensor Ingestion │ │ Sensor Ingestion │
│ Radio Monitor    │ │ Radio Monitor    │ │ Radio Monitor    │
│ Livestream Mgr   │ │ Livestream Mgr   │ │ Livestream Mgr   │
│ Crew Comms       │ │ Crew Comms       │ │ Crew Comms       │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │   Sensors    │    │   Sensors    │    │   Sensors    │
   │   Captain    │    │   Captain    │    │   Captain    │
   │   Crew       │    │   Crew       │    │   Crew       │
   └──────────────┘    └──────────────┘    └──────────────┘
```

## Technology Stack

- **Backend**: Python 3.12 + FastAPI
- **Database**: PostgreSQL (structured data) + Redis (caching)
- **Message Queue**: RabbitMQ
- **ML/AI**: PyTorch + scikit-learn
- **Security**: Ed25519 cryptography
- **Containerization**: Docker + Docker Compose
- **Frontend**: React/TypeScript (future)

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)
- PostgreSQL 16+ (will be run in Docker)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd maritime-ai
   ```

2. **Initialize project structure**
   ```bash
   python init_project.py
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL database
   - RabbitMQ message queue
   - Redis cache
   - Maritime AI API (FastAPI)

4. **Access the system**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - RabbitMQ Admin: http://localhost:15672 (guest/guest)

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black app/ tests/

# Type checking
mypy app/
```

## API Endpoints (v1)

### Health & Status
- `GET /health` - System health check
- `GET /` - API info

### Ships
- `GET /api/v1/ships` - List all ships
- `GET /api/v1/ships/{ship_id}` - Get ship details
- `POST /api/v1/ships` - Register new ship
- `GET /api/v1/ships/{ship_id}/status` - Real-time ship status

### Decisions
- `GET /api/v1/decisions` - List decisions (filter by ship)
- `POST /api/v1/decisions` - Log new decision
- `GET /api/v1/decisions/{decision_id}` - Get decision details
- `POST /api/v1/decisions/{decision_id}/approve` - Approve/override decision

### Telemetry
- `GET /api/v1/telemetry/{ship_id}` - Get sensor data
- `POST /api/v1/telemetry/{ship_id}` - Ingest sensor reading
- `GET /api/v1/telemetry/{ship_id}/gps` - GPS coordinates
- `GET /api/v1/telemetry/{ship_id}/power` - Power system status

### Crew
- `GET /api/v1/crew/{ship_id}` - List crew members
- `POST /api/v1/crew/{ship_id}` - Add crew member
- `POST /api/v1/crew/{crew_id}/authenticate` - Crew authentication
- `POST /api/v1/crew/{crew_id}/comms` - Send crew communication

## Key Design Principles

### 1. **Captain Authority is Absolute**
The AI makes recommendations and explains its reasoning, but the captain always has the final say. System enforces this hierarchy:
- AI suggests action with reasoning
- Captain reviews and decides
- Captain's decision is always executed
- Decision is logged with captain override notation

### 2. **Transparency & Explainability**
Every AI decision includes:
- Decision reasoning (parameters, sensor data used)
- Confidence score
- Alternative options considered
- Estimated outcome

### 3. **Immutable Audit Trail**
All decisions are:
- Digitally signed with Ed25519
- Timestamped
- Include actor information (AI, Captain, First Mate)
- Cannot be modified (tamper-sealed)
- Retained for 10 years by default

### 4. **Learning from Experience**
The system:
- Tracks captain decision patterns
- Learns preferred decision styles
- Adapts recommendations over time
- Maintains pattern confidence scores
- Provides explainability for pattern-based decisions

### 5. **Real-Time Monitoring**
- Sensor data ingested every 5 seconds
- Decisions made within 2-3 seconds
- GPS/livestream updated in real-time
- Radio communications logged immediately

## Database Schema Highlights

- **ships** - Vessel configuration and metadata
- **ship_power_systems** - Renewable energy tracking
- **ship_sensors** - Sensor configuration and status
- **crew_members** - Personnel information
- **decisions** - AI/Human decision log (immutable)
- **audit_logs** - System event log (tamper-sealed)
- **telemetry_data** - Sensor readings (time-series)
- **weather_data** - Weather observations
- **radio_communications** - Radio traffic log
- **livestream_sessions** - Video stream management
- **gps_positions** - Position history
- **captain_decision_patterns** - ML training data

## Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://maritime_user:password@localhost:5432/maritime_ai

# Message Queue
RABBITMQ_URL=amqp://maritime_user:password@localhost:5672/

# Cache
REDIS_URL=redis://localhost:6379

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Satellite
SATELLITE_PROVIDER=starlink
STREAM_BITRATE_KBPS=2500
STREAM_RESOLUTION=720p
```

## Project Phases

### Phase 1: Foundation ✓
- Project structure, Docker setup
- Core FastAPI application
- Database schema
- Message queue integration

### Phase 2: Sensor Systems (In Progress)
- Sensor adapter interface
- Radar data integration
- Weather sensor aggregation
- Power monitoring (hydro/solar)
- Radio communications monitoring

### Phase 3: Livestream & GPS
- GPS positioning service
- Satellite livestream manager
- Video encoding with GPS overlay

### Phase 4: Intelligence
- Decision engine core
- Captain learning module
- Explainability layer

### Phase 5: Security & Logging
- Digital tamper seals
- Audit logging system
- Command authority enforcement

### Phase 6: Integration
- Ship agent factory
- Crew communication interface
- Command center dashboard

## Security Considerations

- All crew communications are encrypted
- API authentication via JWT tokens
- Database connections use SSL
- Audit logs are cryptographically signed
- Non-root Docker container execution
- Sensitive configuration in environment variables
- Regular security audits of decision logs

## Contributing

This system is designed for maritime operations. Contributions should focus on:
- Sensor integration improvements
- Decision engine enhancements
- Learning model optimizations
- Safety and reliability

## License

[Specify your license]

## Support

For issues, questions, or feature requests, please contact the Maritime AI team.

---

**Last Updated**: 2024
**Version**: 0.1.0
**Status**: Active Development
