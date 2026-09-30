"""
pytest configuration and fixtures
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

# TestClient sends Host: testserver; allow it before main reads ALLOWED_HOSTS.
import config as _config
_config.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

from main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create async test client"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

class TestHealth:
    """Health endpoint tests"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
        assert "version" in response.json()

class TestShipsEndpoints:
    """Ships management endpoint tests"""
    
    def test_list_ships(self, client):
        """Test listing ships"""
        response = client.get("/api/v1/ships")
        assert response.status_code == 200
        assert "ships" in response.json() or isinstance(response.json(), dict)
    
    def test_get_ship_status(self, client):
        """Test getting ship status (real: register a ship first)"""
        sid = client.post("/api/v1/ships", json={"call_sign": "OLD1", "name": "Old Test"}).json()["ship"]["id"]
        response = client.get(f"/api/v1/ships/{sid}/status")
        assert response.status_code == 200
        data = response.json()
        assert "ship_id" in data
        assert data["ship_id"] == 1

class TestDecisionsEndpoints:
    """Decisions management endpoint tests"""
    
    def test_list_decisions(self, client):
        """Test listing decisions"""
        response = client.get("/api/v1/decisions")
        assert response.status_code == 200
        data = response.json()
        assert "decisions" in data or "message" in data

class TestTelemetryEndpoints:
    """Telemetry endpoint tests"""
    
    def test_get_gps_position(self, client):
        """Test getting GPS position (real: ship + a gps reading)"""
        sid = client.post("/api/v1/ships", json={"call_sign": "GPS1", "name": "G"}).json()["ship"]["id"]
        client.post(f"/api/v1/telemetry/{sid}/gps", json={"latitude": 1.0, "longitude": 2.0})
        response = client.get(f"/api/v1/telemetry/{sid}/gps")
        assert response.status_code == 200
        data = response.json()
        assert data["gps"]["latitude"] == 1.0
        assert "longitude" in data["gps"]
    
    def test_get_weather_data(self, client):
        """Test getting weather data (real: ship + a weather reading)"""
        sid = client.post("/api/v1/ships", json={"call_sign": "WX1", "name": "W"}).json()["ship"]["id"]
        client.post(f"/api/v1/telemetry/{sid}/weather", json={
            "wind_speed_knots": 5.0, "wind_direction_deg": 90, "wave_height_m": 1.0,
            "temperature_c": 20.0, "barometric_pressure_mb": 1013.0})
        response = client.get(f"/api/v1/telemetry/{sid}/weather")
        assert response.status_code == 200
        data = response.json()
        assert "wind_speed_knots" in data["weather"]

class TestCrewEndpoints:
    """Crew management endpoint tests"""
    
    def test_list_crew(self, client):
        """Test listing crew members (real: ship + crew)"""
        sid = client.post("/api/v1/ships", json={"call_sign": "CRW0", "name": "Old Crew"}).json()["ship"]["id"]
        client.post(f"/api/v1/crew/{sid}", json={"name": "Eve", "role": "Engineer", "employee_id": "E0"})
        response = client.get(f"/api/v1/crew/{sid}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1


class TestPhase2Ships:
    """Phase 2: ships backed by the in-memory store"""

    def test_register_and_get_ship(self, client):
        r = client.post("/api/v1/ships", json={"call_sign": "TEST1", "name": "Test Vessel"})
        assert r.status_code == 201
        ship_id = r.json()["ship"]["id"]
        r = client.get(f"/api/v1/ships/{ship_id}")
        assert r.status_code == 200
        assert r.json()["call_sign"] == "TEST1"

    def test_register_duplicate_call_sign_409(self, client):
        client.post("/api/v1/ships", json={"call_sign": "DUP1", "name": "A"})
        r = client.post("/api/v1/ships", json={"call_sign": "DUP1", "name": "B"})
        assert r.status_code == 409

    def test_get_missing_ship_404(self, client):
        r = client.get("/api/v1/ships/99999")
        assert r.status_code == 404

    def test_ship_status_derives_from_telemetry(self, client):
        sid = client.post("/api/v1/ships", json={"call_sign": "STAT1", "name": "S"}).json()["ship"]["id"]
        client.post(f"/api/v1/telemetry/{sid}/gps", json={"latitude": 12.5, "longitude": -45.0})
        r = client.get(f"/api/v1/ships/{sid}/status")
        assert r.status_code == 200
        assert r.json()["gps"]["latitude"] == 12.5

class TestPhase2Telemetry:
    """Phase 2: telemetry ingestion stores and queues"""

    def test_ingest_then_read(self, client):
        sid = client.post("/api/v1/ships", json={"call_sign": "TEL1", "name": "T"}).json()["ship"]["id"]
        r = client.post(f"/api/v1/telemetry/{sid}", json={"sensor_type": "battery", "data_point": {"battery_percent": 77}})
        assert r.status_code == 202
        assert r.json()["queued"] is True
        r = client.get(f"/api/v1/telemetry/{sid}")
        assert r.json()["count"] == 1
        r = client.get(f"/api/v1/telemetry/{sid}/power")
        assert r.json()["battery"]["charge_percent"] == 77

    def test_ingest_to_missing_ship_404(self, client):
        r = client.post("/api/v1/telemetry/99999", json={"sensor_type": "gps", "data_point": {}})
        assert r.status_code == 404

class TestPhase2Decisions:
    """Phase 2: full decision lifecycle"""

    def test_create_approve_execute(self, client):
        r = client.post("/api/v1/decisions", json={
            "ship_id": 1, "decision_type": "heading_change", "decision_maker": "ai_system",
            "recommended_action": "turn to 090", "reasoning": {"factor": "wind"}, "confidence_score": 0.9})
        assert r.status_code == 201
        did = r.json()["decision"]["id"]
        assert r.json()["decision"]["status"] == "pending_approval"
        r = client.post(f"/api/v1/decisions/{did}/execute")
        assert r.status_code == 409  # must approve first
        r = client.post(f"/api/v1/decisions/{did}/approve", json={"approved": True, "approver_id": 1})
        assert r.status_code == 200 and r.json()["decision"]["status"] == "approved"
        r = client.post(f"/api/v1/decisions/{did}/execute")
        assert r.status_code == 200 and r.json()["decision"]["status"] == "executed"

    def test_reject(self, client):
        did = client.post("/api/v1/decisions", json={
            "decision_type": "emergency", "decision_maker": "ai_system",
            "recommended_action": "all stop"}).json()["decision"]["id"]
        r = client.post(f"/api/v1/decisions/{did}/approve", json={"approved": False, "approver_id": 2, "notes": "no"})
        assert r.json()["decision"]["status"] == "rejected"

    def test_pending_filter(self, client):
        client.post("/api/v1/decisions", json={
            "decision_type": "speed_adjustment", "decision_maker": "ai_system", "recommended_action": "slow"})
        r = client.get("/api/v1/decisions/pending")
        assert "pending_decisions" in r.json() and r.json()["count"] >= 1

    def test_history(self, client):
        r = client.get("/api/v1/decisions/history?ship_id=1&days=7")
        assert r.status_code == 200
        assert "ai_acceptance_rate" in r.json()

class TestPhase2Crew:
    """Phase 2: crew records, auth, comms, notifications"""

    def test_add_crew_and_list(self, client):
        sid = client.post("/api/v1/ships", json={"call_sign": "CRW1", "name": "C"}).json()["ship"]["id"]
        r = client.post(f"/api/v1/crew/{sid}", json={"name": "Ada", "role": "Captain", "employee_id": "E1"})
        assert r.status_code == 201
        cid = r.json()["crew_member"]["id"]
        r = client.get(f"/api/v1/crew/{sid}")
        assert r.json()["total_count"] == 1
        r = client.get(f"/api/v1/crew/{sid}/captain")
        assert r.json()["captain"]["name"] == "Ada"
        r = client.get(f"/api/v1/crew/member/{cid}")
        assert r.status_code == 200 and r.json()["name"] == "Ada"

    def test_authenticate_issued_token(self, client):
        sid = client.post("/api/v1/ships", json={"call_sign": "AUT1", "name": "A"}).json()["ship"]["id"]
        cid = client.post(f"/api/v1/crew/{sid}", json={"name": "Bo", "role": "Engineer", "employee_id": "E2"}).json()["crew_member"]["id"]
        r = client.post(f"/api/v1/crew/{cid}/authenticate", json={"username": "bo", "password": "x"})
        assert r.status_code == 200
        tok = r.json()["token"]
        assert len(tok) > 20 and tok != "jwt_token_here"
        r = client.post(f"/api/v1/crew/99999/authenticate", json={"username": "x", "password": "y"})
        assert r.status_code == 404

    def test_comms_and_notifications(self, client):
        sid = client.post("/api/v1/ships", json={"call_sign": "MSG1", "name": "M"}).json()["ship"]["id"]
        cid = client.post(f"/api/v1/crew/{sid}", json={"name": "Cy", "role": "Deckhand", "employee_id": "E3"}).json()["crew_member"]["id"]
        r = client.post(f"/api/v1/crew/{cid}/comms", json={"message_type": "alert", "content": "check lines"})
        assert r.json()["status"] == "sent"
        r = client.get(f"/api/v1/crew/{cid}/notifications")
        assert r.json()["unread_count"] == 1 and r.json()["total_count"] == 1

    def test_preferences_put_then_get(self, client):
        sid = client.post("/api/v1/ships", json={"call_sign": "PREF1", "name": "P"}).json()["ship"]["id"]
        cid = client.post(f"/api/v1/crew/{sid}", json={"name": "Di", "role": "Support", "employee_id": "E4"}).json()["crew_member"]["id"]
        r = client.put(f"/api/v1/crew/{cid}/preferences", json={"language": "es", "bogus": "drop me"})
        assert r.status_code == 200 and r.json()["preferences"]["language"] == "es"
        assert "bogus" not in r.json()["preferences"]
        r = client.get(f"/api/v1/crew/{cid}/preferences")
        assert r.json()["language"] == "es"

    def test_acknowledge(self, client):
        did = client.post("/api/v1/decisions", json={
            "decision_type": "route_change", "decision_maker": "captain", "recommended_action": "port"}).json()["decision"]["id"]
        r = client.post(f"/api/v1/crew/1/acknowledge?decision_id={did}")
        assert r.json()["acknowledged"] is True

class TestPhase2Status:
    """Phase 2: /status reports queue and cache truthfully"""

    def test_status_reports_queue_and_cache(self, client):
        r = client.get("/status")
        data = r.json()
        assert isinstance(data["message_queue"], dict) and "depth" in data["message_queue"]
        assert isinstance(data["cache"], dict) and "entries" in data["cache"]

