-- Maritime AI System - Database Schema Initialization
-- PostgreSQL 16+ Compatible
-- This script creates all necessary tables and indexes

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- SHIP & VESSEL CONFIGURATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS ships (
    id SERIAL PRIMARY KEY,
    call_sign VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    iccn VARCHAR(7) UNIQUE,
    ship_type VARCHAR(50),
    gross_tonnage DECIMAL(10, 2),
    length_m DECIMAL(8, 2),
    beam_m DECIMAL(8, 2),
    max_speed_knots DECIMAL(6, 2),
    crew_count INT,
    home_port VARCHAR(255),
    registration_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ship_power_systems (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL UNIQUE REFERENCES ships(id) ON DELETE CASCADE,
    solar_capacity_kw DECIMAL(10, 2),
    hydro_capacity_kw DECIMAL(10, 2),
    battery_capacity_kwh DECIMAL(10, 2),
    battery_current_kwh DECIMAL(10, 2),
    total_power_generated_kwh DECIMAL(15, 2) DEFAULT 0,
    efficiency_percent DECIMAL(5, 2),
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ship_sensors (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    sensor_type VARCHAR(50) NOT NULL,
    sensor_name VARCHAR(255),
    last_reading JSONB,
    last_sync TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    error_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CREW & PERSONNEL
-- ============================================================================

CREATE TABLE IF NOT EXISTS crew_members (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    employee_id VARCHAR(50),
    contact_info VARCHAR(255),
    certification_level VARCHAR(50),
    years_experience INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crew_authentication (
    id SERIAL PRIMARY KEY,
    crew_member_id INT NOT NULL UNIQUE REFERENCES crew_members(id) ON DELETE CASCADE,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_token_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DECISION LOGGING & AUDIT TRAIL (CORE SYSTEM)
-- ============================================================================

CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    decision_type VARCHAR(100),
    decision_maker VARCHAR(50),
    decision_maker_id INT REFERENCES crew_members(id),
    recommended_action TEXT NOT NULL,
    reasoning JSONB,
    confidence_score DECIMAL(5, 4),
    is_approved BOOLEAN,
    approved_by INT REFERENCES crew_members(id),
    approval_timestamp TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE,
    execution_timestamp TIMESTAMP,
    result_notes TEXT,
    outcome_status VARCHAR(50),
    digital_signature VARCHAR(512),
    signature_algorithm VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decisions_ship_timestamp ON decisions(ship_id, timestamp DESC);
CREATE INDEX idx_decisions_maker ON decisions(decision_maker, created_at DESC);
CREATE INDEX idx_decisions_status ON decisions(executed, approval_timestamp);

-- ============================================================================
-- AUDIT LOGS (IMMUTABLE)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    event_type VARCHAR(100),
    actor_type VARCHAR(50),
    actor_id INT REFERENCES crew_members(id),
    action_description TEXT,
    details JSONB,
    digital_signature VARCHAR(512),
    signature_algorithm VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_ship_timestamp ON audit_logs(ship_id, timestamp DESC);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_type, actor_id, created_at DESC);

-- ============================================================================
-- SENSOR DATA & TELEMETRY
-- ============================================================================

CREATE TABLE IF NOT EXISTS telemetry_data (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    sensor_type VARCHAR(50),
    data_point JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telemetry_ship_timestamp ON telemetry_data(ship_id, timestamp DESC);
CREATE INDEX idx_telemetry_sensor_type ON telemetry_data(ship_id, sensor_type, timestamp DESC);

CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    wind_speed_knots DECIMAL(6, 2),
    wind_direction_deg DECIMAL(6, 2),
    wind_gust_knots DECIMAL(6, 2),
    wave_height_m DECIMAL(6, 2),
    temperature_c DECIMAL(6, 2),
    barometric_pressure_mb DECIMAL(8, 2),
    visibility_nm DECIMAL(6, 2),
    sea_state VARCHAR(20),
    raw_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weather_ship_timestamp ON weather_data(ship_id, timestamp DESC);

-- ============================================================================
-- RADIO COMMUNICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS radio_communications (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    frequency_mhz DECIMAL(8, 3),
    channel_name VARCHAR(100),
    message_type VARCHAR(50),
    sender VARCHAR(100),
    receiver VARCHAR(100),
    message_content TEXT,
    signal_strength DECIMAL(5, 2),
    is_logged BOOLEAN DEFAULT TRUE,
    digital_signature VARCHAR(512),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_radio_ship_timestamp ON radio_communications(ship_id, timestamp DESC);
CREATE INDEX idx_radio_frequency ON radio_communications(frequency_mhz, timestamp DESC);

-- ============================================================================
-- LIVESTREAM & GPS (REAL-TIME POSITIONING)
-- ============================================================================

CREATE TABLE IF NOT EXISTS livestream_sessions (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    stream_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'inactive',
    bitrate_kbps INT,
    resolution VARCHAR(20),
    satellite_provider VARCHAR(100),
    signal_strength DECIMAL(5, 2),
    uptime_seconds INT,
    viewers_count INT DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gps_positions (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    accuracy_m DECIMAL(8, 2),
    heading_deg DECIMAL(6, 2),
    speed_knots DECIMAL(6, 2),
    altitude_m DECIMAL(8, 2),
    satellite_count INT,
    hdop DECIMAL(5, 2),
    gps_status VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gps_ship_timestamp ON gps_positions(ship_id, timestamp DESC);

-- ============================================================================
-- AI LEARNING & CAPTAIN PATTERN ANALYSIS
-- ============================================================================

CREATE TABLE IF NOT EXISTS captain_decision_patterns (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    captain_id INT NOT NULL REFERENCES crew_members(id),
    decision_type VARCHAR(100),
    parameters JSONB,
    pattern_confidence DECIMAL(5, 4),
    pattern_frequency INT DEFAULT 0,
    last_observed TIMESTAMP,
    total_decisions_analyzed INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_recommendations_feedback (
    id SERIAL PRIMARY KEY,
    decision_id INT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    was_accepted BOOLEAN,
    feedback_type VARCHAR(50),
    captain_reasoning TEXT,
    outcome_notes TEXT,
    outcome_score DECIMAL(5, 4),
    learning_applied BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DIGITAL TAMPER SEALS & CRYPTOGRAPHY
-- ============================================================================

CREATE TABLE IF NOT EXISTS tamper_seals (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_id INT NOT NULL,
    seal_type VARCHAR(50),
    public_key VARCHAR(1024),
    signature VARCHAR(512),
    sealed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE,
    verification_timestamp TIMESTAMP,
    verification_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tamper_seals_entity ON tamper_seals(entity_type, entity_id);

-- ============================================================================
-- SYSTEM CONFIGURATION & PREFERENCES
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    is_secret BOOLEAN DEFAULT FALSE,
    updated_by INT REFERENCES crew_members(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crew_communication_preferences (
    id SERIAL PRIMARY KEY,
    crew_member_id INT NOT NULL UNIQUE REFERENCES crew_members(id) ON DELETE CASCADE,
    notification_method VARCHAR(50),
    alert_level VARCHAR(20),
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    language VARCHAR(10) DEFAULT 'en',
    enable_ai_recommendations BOOLEAN DEFAULT TRUE,
    enable_critical_alerts BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DECISION OVERRIDE LOG (CAPTAIN AUTHORITY TRACKING)
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_overrides (
    id SERIAL PRIMARY KEY,
    original_decision_id INT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    overriding_crew_id INT NOT NULL REFERENCES crew_members(id),
    override_reason TEXT,
    override_action TEXT,
    outcome JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_overrides_timestamp ON decision_overrides(timestamp DESC);

-- ============================================================================
-- PERFORMANCE METRICS & ANALYTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_performance_metrics (
    id SERIAL PRIMARY KEY,
    ship_id INT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    total_decisions_made INT DEFAULT 0,
    accepted_decisions INT DEFAULT 0,
    overridden_decisions INT DEFAULT 0,
    successful_outcomes INT DEFAULT 0,
    average_confidence DECIMAL(5, 4),
    model_accuracy DECIMAL(5, 4),
    learning_improvement DECIMAL(5, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

CREATE OR REPLACE VIEW v_ship_status AS
SELECT 
    s.id,
    s.call_sign,
    s.name,
    s.ship_type,
    (SELECT gp.latitude FROM gps_positions gp WHERE gp.ship_id = s.id ORDER BY gp.timestamp DESC LIMIT 1) as current_latitude,
    (SELECT gp.longitude FROM gps_positions gp WHERE gp.ship_id = s.id ORDER BY gp.timestamp DESC LIMIT 1) as current_longitude,
    (SELECT COUNT(*) FROM decisions d WHERE d.ship_id = s.id AND d.timestamp > NOW() - INTERVAL '24 hours') as decisions_24h,
    (SELECT COUNT(*) FROM crew_members cm WHERE cm.ship_id = s.id AND cm.is_active) as active_crew,
    s.updated_at
FROM ships s
WHERE s.is_active = TRUE;

CREATE OR REPLACE VIEW v_pending_decisions AS
SELECT 
    d.id,
    d.ship_id,
    s.call_sign,
    d.decision_type,
    d.recommended_action,
    d.confidence_score,
    d.timestamp
FROM decisions d
JOIN ships s ON d.ship_id = s.id
WHERE d.is_approved IS NULL
ORDER BY d.timestamp DESC;

-- ============================================================================
-- INITIAL CONFIGURATION
-- ============================================================================

INSERT INTO system_config (config_key, config_value, description, is_secret)
VALUES 
    ('SYSTEM_VERSION', '0.1.0', 'Maritime AI System Version', FALSE),
    ('DATABASE_INITIALIZED', NOW()::TEXT, 'Database Initialization Timestamp', FALSE),
    ('DECISION_LOG_RETENTION_DAYS', '3650', 'Number of days to retain decision logs', FALSE),
    ('SENSOR_SYNC_INTERVAL_SECONDS', '5', 'Sensor data sync interval in seconds', FALSE),
    ('AI_LEARNING_ENABLED', 'true', 'Enable AI captain learning system', FALSE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ships_active ON ships(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_crew_active ON crew_members(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_telemetry_recent ON telemetry_data(ship_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_recent ON audit_logs(created_at DESC);

-- ============================================================================
-- AUDIT FUNCTION (TRACK ALL CHANGES)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_ships_updated_at BEFORE UPDATE ON ships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ship_power_systems_updated_at BEFORE UPDATE ON ship_power_systems
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crew_members_updated_at BEFORE UPDATE ON crew_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_captain_decision_patterns_updated_at BEFORE UPDATE ON captain_decision_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FINAL VERIFICATION
-- ============================================================================

SELECT COUNT(*) as total_tables FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
