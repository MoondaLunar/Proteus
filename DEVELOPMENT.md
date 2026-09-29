# Maritime AI System - Development Guide

## Core Principles

### 1. Captain Authority is Non-Negotiable
- The captain ALWAYS has final say on decisions
- AI provides recommendations with full transparency
- System must track who made which decision and when
- Any AI override is logged as a captain decision

### 2. Transparency & Explainability
Every decision must include:
- **What**: Clear description of the action recommended
- **Why**: Explicit reasoning with sensor data referenced
- **Confidence**: Confidence score (0.0-1.0) of the recommendation
- **Alternatives**: Other options considered and why they were rejected
- **Impact**: Expected outcomes of the decision

### 3. Immutable Audit Trail
- All decisions are digitally signed with Ed25519
- Logs cannot be modified or deleted (retention: 10 years default)
- Both AI and human decisions are equally logged
- Tamper seals verify log integrity

### 4. Learning from Experience
The system learns captain decision patterns:
- Tracks which decisions the captain accepts/rejects
- Analyzes reasoning behind captain's choices
- Updates AI models based on feedback
- Provides confidence scores based on learned patterns

### 5. Real-Time Responsiveness
- Sensor data ingested every 5 seconds
- Decisions made within 2-3 seconds
- GPS/livestream updated in real-time
- No more than 500ms latency for critical alerts

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│         Command Center Dashboard            │
│      (React/TypeScript Frontend)            │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│      Maritime AI Central Hub (FastAPI)      │
├──────────────────────────────────────────────┤
│  Decision Engine | Learning Module          │
│  Auth Manager    | Audit Logger             │
│  Message Router  | Tamper Seal System       │
└──────┬─────────┬──────────────┬──────────────┘
       │         │              │
   ┌───▼─┐   ┌──▼──┐       ┌───▼──┐
   │Ships│   │Crews│       │Audit │
   │Agent│   │Comms│       │Logger│
   └─────┘   └─────┘       └──────┘
       │
   ┌───▼────────────────────┐
   │  Per-Ship Services     │
   ├────────────────────────┤
   │ Sensors | Radio | GPS  │
   │ Power   | Crew Comms   │
   └────────────────────────┘
```

## Implementation Phases

### Phase 1: Foundation (Current) ✓
- [x] Project structure
- [x] Docker setup
- [x] Core FastAPI application
- [x] Database schema
- [x] Message queue setup
- [x] Environment configuration
- [ ] Database migrations
- [ ] API authentication

**Phase 1 Status**: 80% - Core infrastructure ready, authentication pending

### Phase 2: Sensor Systems (Next)
- Sensor adapter interface
- Radar data integration
- Weather sensor aggregation
- Power monitoring (hydro/solar)
- Radio communications monitoring

**Estimated Duration**: 2-3 weeks

### Phase 3: Livestream & GPS
- GPS positioning service
- Satellite livestream manager
- Video encoding with GPS overlay

**Estimated Duration**: 1-2 weeks

### Phase 4: Intelligence
- Decision engine core
- Captain learning module
- Explainability layer

**Estimated Duration**: 3-4 weeks

### Phase 5: Security & Logging
- Digital tamper seals (Ed25519)
- Audit logging system
- Command authority enforcement

**Estimated Duration**: 2-3 weeks

### Phase 6: Integration & Optimization
- Ship agent factory
- Crew communication interface
- Command center dashboard

**Estimated Duration**: 3-4 weeks

## Database Design

### Core Entities

#### Ships
```sql
ships
├── id
├── call_sign (unique)
├── name
├── ship_type
└── crew_members → crew_members
```

#### Crew Members
```sql
crew_members
├── id
├── ship_id → ships
├── name
├── role
└── authentication → crew_authentication
```

#### Decisions (Core System)
```sql
decisions
├── id
├── ship_id → ships
├── decision_type
├── decision_maker (ai_system, captain, first_mate)
├── reasoning (JSONB)
├── confidence_score
├── approved_by → crew_members
└── digital_signature
```

#### Audit Logs (Immutable)
```sql
audit_logs
├── id
├── ship_id → ships
├── event_type
├── actor_type
├── details (JSONB)
└── digital_signature
```

#### Telemetry Data
```sql
telemetry_data
├── id
├── ship_id → ships
├── sensor_type
├── data_point (JSONB)
└── timestamp
```

#### Captain Decision Patterns (ML Training Data)
```sql
captain_decision_patterns
├── id
├── ship_id → ships
├── captain_id → crew_members
├── decision_type
├── parameters (JSONB)
├── pattern_confidence
└── decision_count
```

### Key Indexes
All data is indexed for performance:
- `ship_id + timestamp` for time-series queries
- `decision_maker` for decision history
- `created_at DESC` for recent activity
- `status` for filtering

## API Design Principles

### Request/Response Format

All responses follow a consistent structure:
```json
{
  "success": true,
  "data": { /* actual data */ },
  "message": "Optional success message",
  "error": null,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "data": null,
  "message": "Human-readable error message",
  "error": {
    "code": "ERROR_CODE",
    "details": {}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Authorization failed
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Pagination
```
GET /api/v1/resource?skip=0&limit=20&sort=created_at&order=desc
```

## Security Implementation

### Authentication
- JWT tokens with 7-day expiration for crew
- Refresh token mechanism for long sessions
- Rate limiting on auth endpoints

### Authorization
- Role-based access control (RBAC)
- Captain > First Mate > Crew hierarchy for decisions
- Ship-based isolation (crew can only see their ship)

### Data Protection
- Passwords hashed with bcrypt (12 rounds)
- API tokens hashed with SHA-256
- TLS/SSL for all API communication
- Database connections encrypted

### Audit & Compliance
- All decisions logged with actor information
- Digital signatures on critical records
- Tamper seal verification on log access
- Immutable audit trail

## Adding New Features

### 1. Adding a New Sensor Type

**Step 1**: Create sensor adapter in `app/services/sensors/`
```python
class RadarSensorAdapter:
    async def read_data(self) -> dict:
        # Read radar data
        pass
    
    async def validate_data(self, data: dict) -> bool:
        # Validate sensor reading
        pass
```

**Step 2**: Create route in `app/routes/telemetry.py`
```python
@router.get("/telemetry/{ship_id}/radar")
async def get_radar_data(ship_id: int):
    # Return radar contacts
    pass
```

**Step 3**: Add database table if needed in `init_db.sql`

**Step 4**: Add tests in `tests/integration/test_radar.py`

### 2. Adding a New Decision Type

**Step 1**: Create decision handler in `app/services/decisions/`
```python
class CourseChangeDecisionHandler:
    async def recommend(self, ship_id: int) -> Decision:
        # Analyze conditions
        # Return recommendation
        pass
```

**Step 2**: Register in decision engine
**Step 3**: Create tests
**Step 4**: Document decision reasoning

### 3. Adding a New API Endpoint

**Step 1**: Create route file
```python
# app/routes/new_feature.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "Hello"}
```

**Step 2**: Include in `main.py`
```python
from app.routes import new_feature
app.include_router(new_feature.router, prefix="/api/v1", tags=["NewFeature"])
```

**Step 3**: Add tests
**Step 4**: Document in API docs

## Testing Strategy

### Unit Tests
- Test individual functions
- Mock external dependencies
- Located in `tests/unit/`
- Run with `pytest tests/unit/`

### Integration Tests
- Test API endpoints
- Test database interactions
- Located in `tests/integration/`
- Run with `pytest tests/integration/`

### Test Coverage Targets
- Core business logic: 90%+
- API endpoints: 85%+
- Utilities: 80%+

```bash
# Run tests with coverage report
pytest --cov=app --cov-report=html
```

## Performance Optimization

### Caching Strategy
- Cache ship status (5 seconds)
- Cache captain patterns (1 hour)
- Cache system config (24 hours)
- Use Redis for all caching

### Database Optimization
- Use indexes on frequently queried fields
- Implement pagination (20-100 items)
- Archive old telemetry data
- Use connection pooling

### API Optimization
- Return only required fields
- Implement request compression
- Use async/await throughout
- Implement request timeouts

## Deployment

### Development
```bash
docker-compose up -d
# Services available immediately
```

### Staging
```bash
export ENVIRONMENT=staging
docker-compose -f docker-compose.staging.yml up -d
```

### Production
```bash
export ENVIRONMENT=production
docker-compose -f docker-compose.prod.yml up -d
# With SSL/TLS certificates
```

## Monitoring & Logging

### Log Levels
- `DEBUG` - Detailed diagnostic information
- `INFO` - Confirmation that things are working
- `WARNING` - Something unexpected happened
- `ERROR` - A serious problem occurred
- `CRITICAL` - A very serious problem

### Key Metrics to Monitor
- API response times (< 200ms target)
- Database query times (< 100ms target)
- Message queue depth (< 1000 messages)
- Decision execution time (< 5 seconds)
- GPS update frequency (> 1 Hz)

## Contributing

### Code Style
- Follow PEP 8
- Use type hints throughout
- Maximum line length: 100 characters
- Document public functions
- Write descriptive commit messages

### Workflow
1. Create feature branch: `git checkout -b feature/name`
2. Make changes and test
3. Format and lint: `make quality`
4. Commit: `git commit -m "Description"`
5. Push: `git push origin feature/name`
6. Create pull request

### Pre-commit Checklist
- [ ] Code is formatted with Black
- [ ] All tests pass
- [ ] Type checking passes
- [ ] No linting errors
- [ ] Documentation updated
- [ ] Commit message is descriptive

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **RabbitMQ Docs**: https://www.rabbitmq.com/documentation.html
- **PyTorch Docs**: https://pytorch.org/docs/stable/index.html

---

**Last Updated**: 2024
**Version**: 0.1.0
