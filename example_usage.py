"""
Example Usage of Maritime AI System API
Demonstrates how to interact with the system
"""

import asyncio
import requests
from datetime import datetime
from typing import Dict, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "http://localhost:8000"
API_VERSION = "v1"
API_BASE = f"{BASE_URL}/api/{API_VERSION}"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_response(title: str, response: requests.Response):
    """Log API response"""
    print(f"\n{'='*60}")
    print(f"📍 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    try:
        import json
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)


# ============================================================================
# HEALTH CHECKS
# ============================================================================

def check_system_health():
    """Check system health"""
    print("\n🏥 Checking system health...")
    
    response = requests.get(f"{BASE_URL}/health")
    log_response("System Health", response)
    
    response = requests.get(f"{BASE_URL}/status")
    log_response("System Status", response)


# ============================================================================
# SHIP MANAGEMENT EXAMPLES
# ============================================================================

def get_all_ships():
    """Get list of all registered ships"""
    print("\n🚢 Fetching all ships...")
    
    response = requests.get(f"{API_BASE}/ships")
    log_response("List Ships", response)
    return response.json()


def get_ship_details(ship_id: int):
    """Get details of a specific ship"""
    print(f"\n🚢 Getting ship {ship_id} details...")
    
    response = requests.get(f"{API_BASE}/ships/{ship_id}")
    log_response(f"Ship {ship_id} Details", response)
    return response.json()


def get_ship_status(ship_id: int):
    """Get real-time status of a ship"""
    print(f"\n🚢 Getting ship {ship_id} real-time status...")
    
    response = requests.get(f"{API_BASE}/ships/{ship_id}/status")
    log_response(f"Ship {ship_id} Status", response)
    return response.json()


def get_power_status(ship_id: int):
    """Get power system status"""
    print(f"\n⚡ Getting power system status for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/ships/{ship_id}/power")
    log_response(f"Ship {ship_id} Power Status", response)
    return response.json()


def register_new_ship(call_sign: str, name: str, ship_type: str):
    """Register a new ship"""
    print(f"\n🚢 Registering new ship: {name} ({call_sign})...")
    
    ship_data = {
        "call_sign": call_sign,
        "name": name,
        "ship_type": ship_type,
        "gross_tonnage": 5000,
        "crew_count": 25,
        "home_port": "San Francisco"
    }
    
    response = requests.post(f"{API_BASE}/ships", json=ship_data)
    log_response("Register Ship", response)
    return response.json()


# ============================================================================
# DECISION MANAGEMENT EXAMPLES
# ============================================================================

def get_pending_decisions(ship_id: int):
    """Get pending decisions awaiting captain approval"""
    print(f"\n⚖️ Getting pending decisions for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/decisions/{ship_id}/pending")
    log_response(f"Pending Decisions - Ship {ship_id}", response)
    return response.json()


def get_decision_history(ship_id: int, days: int = 7):
    """Get decision history"""
    print(f"\n📋 Getting {days}-day decision history for ship {ship_id}...")
    
    response = requests.get(
        f"{API_BASE}/decisions/{ship_id}/history",
        params={"days": days}
    )
    log_response(f"Decision History - Ship {ship_id}", response)
    return response.json()


def create_decision(ship_id: int):
    """Log an AI recommendation"""
    print(f"\n🤖 Creating AI recommendation for ship {ship_id}...")
    
    decision_data = {
        "decision_type": "heading_change",
        "decision_maker": "ai_system",
        "recommended_action": "Change heading to 180 degrees to avoid storm system",
        "reasoning": {
            "weather_threat": "Strong storm 50nm northeast",
            "current_heading": 90,
            "recommended_heading": 180,
            "confidence_factors": {
                "wind_speed": 0.9,
                "wave_height": 0.85,
                "pressure_trend": 0.8
            }
        },
        "confidence_score": 0.87
    }
    
    response = requests.post(f"{API_BASE}/decisions", json=decision_data)
    log_response("Create Decision", response)
    return response.json()


def get_decision_reasoning(decision_id: int):
    """Get AI reasoning for a decision"""
    print(f"\n💭 Getting reasoning for decision {decision_id}...")
    
    response = requests.get(f"{API_BASE}/decisions/{decision_id}/reasoning")
    log_response("Decision Reasoning", response)
    return response.json()


def approve_decision(decision_id: int, approved: bool = True):
    """Approve or reject a decision"""
    print(f"\n✅ Approving decision {decision_id}...")
    
    approval_data = {
        "approved": approved,
        "approver_id": 1,
        "notes": "Captain approved - course change will improve passenger comfort"
    }
    
    response = requests.post(
        f"{API_BASE}/decisions/{decision_id}/approve",
        json=approval_data
    )
    log_response("Approve Decision", response)
    return response.json()


# ============================================================================
# TELEMETRY & SENSOR DATA EXAMPLES
# ============================================================================

def get_gps_position(ship_id: int):
    """Get current GPS position"""
    print(f"\n📍 Getting GPS position for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/telemetry/{ship_id}/gps")
    log_response("GPS Position", response)
    return response.json()


def update_gps_position(ship_id: int, latitude: float, longitude: float):
    """Update GPS position"""
    print(f"\n📍 Updating GPS position for ship {ship_id}...")
    
    gps_data = {
        "latitude": latitude,
        "longitude": longitude,
        "heading": 180.0,
        "speed_knots": 15.5,
        "accuracy_m": 5.0
    }
    
    response = requests.post(f"{API_BASE}/telemetry/{ship_id}/gps", json=gps_data)
    log_response("Update GPS Position", response)
    return response.json()


def get_weather_data(ship_id: int):
    """Get current weather conditions"""
    print(f"\n🌊 Getting weather data for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/telemetry/{ship_id}/weather")
    log_response("Weather Data", response)
    return response.json()


def ingest_weather_reading(ship_id: int):
    """Ingest weather sensor data"""
    print(f"\n🌊 Ingesting weather reading for ship {ship_id}...")
    
    weather_data = {
        "wind_speed_knots": 22.5,
        "wind_direction_deg": 180,
        "wave_height_m": 3.5,
        "temperature_c": 14.2,
        "barometric_pressure_mb": 1010.5,
        "visibility_nm": 18
    }
    
    response = requests.post(
        f"{API_BASE}/telemetry/{ship_id}/weather",
        json=weather_data
    )
    log_response("Ingest Weather Data", response)
    return response.json()


def get_power_telemetry(ship_id: int):
    """Get renewable power system telemetry"""
    print(f"\n⚡ Getting power telemetry for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/telemetry/{ship_id}/power")
    log_response("Power Telemetry", response)
    return response.json()


def get_radar_data(ship_id: int):
    """Get radar contacts"""
    print(f"\n📡 Getting radar data for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/telemetry/{ship_id}/radar")
    log_response("Radar Data", response)
    return response.json()


def get_radio_communications(ship_id: int):
    """Get monitored radio communications"""
    print(f"\n📻 Getting radio communications for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/telemetry/{ship_id}/radio")
    log_response("Radio Communications", response)
    return response.json()


# ============================================================================
# CREW MANAGEMENT EXAMPLES
# ============================================================================

def list_crew(ship_id: int):
    """Get list of crew members on a ship"""
    print(f"\n👥 Getting crew list for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/crew/{ship_id}")
    log_response("Crew List", response)
    return response.json()


def get_crew_profile(crew_id: int):
    """Get crew member profile"""
    print(f"\n👤 Getting profile for crew member {crew_id}...")
    
    response = requests.get(f"{API_BASE}/crew/{crew_id}")
    log_response("Crew Profile", response)
    return response.json()


def send_crew_communication(crew_id: int, message: str):
    """Send communication to crew member"""
    print(f"\n💬 Sending communication to crew member {crew_id}...")
    
    comms_data = {
        "message_type": "alert",
        "content": message,
        "priority": "high"
    }
    
    response = requests.post(
        f"{API_BASE}/crew/{crew_id}/comms",
        json=comms_data
    )
    log_response("Send Communication", response)
    return response.json()


def get_crew_notifications(crew_id: int):
    """Get notifications for crew member"""
    print(f"\n🔔 Getting notifications for crew member {crew_id}...")
    
    response = requests.get(f"{API_BASE}/crew/{crew_id}/notifications")
    log_response("Crew Notifications", response)
    return response.json()


def get_ship_captain(ship_id: int):
    """Get the captain of a ship"""
    print(f"\n👨‍✈️ Getting captain for ship {ship_id}...")
    
    response = requests.get(f"{API_BASE}/crew/{ship_id}/captain")
    log_response("Ship Captain", response)
    return response.json()


# ============================================================================
# MAIN EXAMPLE WORKFLOW
# ============================================================================

def main():
    """Run example workflow"""
    print("\n" + "="*60)
    print("🚢 Maritime AI System - API Usage Examples")
    print("="*60)
    
    try:
        # Health Checks
        print("\n[1/7] System Health Checks")
        check_system_health()
        
        # Ship Management
        print("\n[2/7] Ship Management")
        ships = get_all_ships()
        if ships and isinstance(ships, dict) and 'ships' in ships:
            if ships['ships']:
                ship_id = ships['ships'][0].get('id', 1)
                get_ship_details(ship_id)
                get_ship_status(ship_id)
                get_power_status(ship_id)
        
        # Decision Management
        print("\n[3/7] Decision Management")
        get_pending_decisions(1)
        create_decision(1)
        get_decision_history(1, days=7)
        
        # Telemetry
        print("\n[4/7] Telemetry & Sensors")
        get_gps_position(1)
        get_weather_data(1)
        get_power_telemetry(1)
        get_radar_data(1)
        get_radio_communications(1)
        
        # Crew Management
        print("\n[5/7] Crew Management")
        list_crew(1)
        get_ship_captain(1)
        
        # Communication
        print("\n[6/7] Crew Communication")
        send_crew_communication(1, "Alert: Course change recommended due to weather")
        get_crew_notifications(1)
        
        # Summary
        print("\n[7/7] Workflow Complete")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API")
        print("   Make sure the server is running: docker-compose up -d")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    
    print("\n" + "="*60)
    print("✅ Example workflow completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
