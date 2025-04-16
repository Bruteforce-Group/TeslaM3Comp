-- Tesla Model 3 Companion Database Initialization Script
-- This script runs when the database container is first created

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for user accounts
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

-- Create indexes for plate recognitions
CREATE INDEX IF NOT EXISTS idx_plate_recognitions_plate_number ON plate_recognitions (plate_number);
CREATE INDEX IF NOT EXISTS idx_plate_recognitions_timestamp ON plate_recognitions (timestamp);

-- Create indexes for security events
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events (event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events (timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events (severity);

-- Create indexes for vehicle data
CREATE INDEX IF NOT EXISTS idx_vehicle_data_timestamp ON vehicle_data (timestamp);

-- Create indexes for system config
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config (key);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_system_config_updated_at
BEFORE UPDATE ON system_config
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- Create additional tables for enhanced functionality

-- Create a table for storing notification preferences
CREATE TABLE IF NOT EXISTS notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(255) NOT NULL,
    email_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT FALSE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences (user_id);

-- Create a table for storing user sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions (session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions (expires_at);

-- Create a table for storing vehicle profiles
CREATE TABLE IF NOT EXISTS vehicle_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    make VARCHAR(100) DEFAULT 'Tesla',
    model VARCHAR(100) DEFAULT 'Model 3',
    year INTEGER,
    color VARCHAR(100),
    vin VARCHAR(17),
    license_plate VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create a table for tracking firmware updates
CREATE TABLE IF NOT EXISTS firmware_updates (
    id SERIAL PRIMARY KEY,
    version VARCHAR(100) NOT NULL,
    release_notes TEXT,
    status VARCHAR(50) DEFAULT 'available',
    update_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create a table for location data
CREATE TABLE IF NOT EXISTS location_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy DECIMAL(10, 2),
    altitude DECIMAL(10, 2),
    speed DECIMAL(10, 2),
    heading DECIMAL(5, 2)
);

CREATE INDEX IF NOT EXISTS idx_location_history_timestamp ON location_history (timestamp);

-- Create an audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER,
    ip_address VARCHAR(45),
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log (action);

-- Create initial admin user (if not exists)
-- Username: admin, Password: teslaadmin (must be changed after first login)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin') THEN
        INSERT INTO users (email, username, hashed_password, is_active, is_admin, created_at)
        VALUES ('admin@example.com', 'admin', 
                '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 
                TRUE, TRUE, NOW());
    END IF;
END
$$; 