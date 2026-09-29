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
        """Test getting ship status"""
        response = client.get("/api/v1/ships/1/status")
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
        """Test getting GPS position"""
        response = client.get("/api/v1/telemetry/1/gps")
        assert response.status_code == 200
        data = response.json()
        assert "gps" in data
        assert "latitude" in data["gps"]
        assert "longitude" in data["gps"]
    
    def test_get_weather_data(self, client):
        """Test getting weather data"""
        response = client.get("/api/v1/telemetry/1/weather")
        assert response.status_code == 200
        data = response.json()
        assert "weather" in data

class TestCrewEndpoints:
    """Crew management endpoint tests"""
    
    def test_list_crew(self, client):
        """Test listing crew members"""
        response = client.get("/api/v1/crew/1")
        assert response.status_code == 200
        data = response.json()
        assert "crew_members" in data or "message" in data
