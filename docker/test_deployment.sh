#!/bin/bash
# Comprehensive Fix Script for Tesla M3 Companion

# Set colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Tesla M3 Companion - Complete Fix Script${NC}"
echo "This script will fix all issues and set up a working test environment."

# 1. Fix version attribute in docker-compose.yml
echo -e "\n${YELLOW}1. Fixing docker-compose.yml${NC}"
# Remove version if it's at the top
if grep -q "^version:" docker-compose.yml; then
  sed -i.bak '1d' docker-compose.yml
  echo -e "  ${GREEN}Removed obsolete version attribute${NC}"
fi

# 2. Create necessary directories
echo -e "\n${YELLOW}2. Creating necessary directories and files${NC}"
mkdir -p core/scripts opencv/models llm/models obd/scripts webui/build mqtt/config
echo -e "  ${GREEN}Created directory structure${NC}"

# 3. Fix Core API
echo -e "\n${YELLOW}3. Setting up Core API${NC}"

# Create minimal requirements.txt
cat > core/requirements.txt << 'EOL'
fastapi>=0.68.0,<0.69.0
uvicorn>=0.15.0,<0.16.0
pydantic>=1.8.0,<2.0.0
python-dotenv==1.0.0
requests>=2.26.0,<3.0.0
numpy>=1.21.0,<2.0.0
psycopg2-binary>=2.9.0,<3.0.0
sqlalchemy>=1.4.0,<1.5.0
alembic==1.12.1
python-multipart>=0.0.5,<0.1.0
aiohttp==3.8.6
prometheus-client>=0.14.1,<0.15.0
pillow>=9.0.0,<10.0.0
loguru>=0.5.3,<0.6.0
pyjwt>=2.4.0,<3.0.0
redis>=4.3.4,<5.0.0
pytest>=6.2.5,<7.0.0
pytest-asyncio==0.15.1
httpx>=0.23.0,<0.24.0
aiofiles>=0.7.0,<0.8.0
psutil>=5.8.0,<6.0.0
python-jose[cryptography]>=3.3.0,<4.0.0
passlib[bcrypt]>=1.7.4,<2.0.0
paho-mqtt>=2.0.0,<3.0.0
email-validator>=1.1.3,<2.0.0
tenacity>=8.0.1,<9.0.0
EOL

# Create minimal app.py
cat > core/app.py << 'EOL'
#!/usr/bin/env python3
from fastapi import FastAPI
import uvicorn
import os
import json
from datetime import datetime

app = FastAPI(
    title="Tesla Model 3 Companion API",
    description="Core API for Tesla Model 3 Integration",
    version="1.0.0",
)

@app.get("/health")
async def health_check():
    """Health check endpoint for the service"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Get system status"""
    return {
        "status": "running",
        "version": "1.0.0",
        "services": ["database", "redis", "core_api", "mqtt"],
        "api_docs": "/docs"
    }

@app.get("/vehicle-data/mock")
async def mock_vehicle_data():
    """Get mock vehicle data for testing"""
    return {
        "speed": 65.5,
        "battery_level": 78.3,
        "temperature": 72.1,
        "location": "37.7749,-122.4194",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "odometer": 12345.6,
            "battery_voltage": 380.5,
            "tire_pressure": {
                "front_left": 36.0,
                "front_right": 35.8,
                "rear_left": 36.2,
                "rear_right": 36.0
            }
        }
    }

@app.get("/plates/mock")
async def mock_plate_recognition():
    """Get mock plate recognition data for testing"""
    return {
        "plate_number": "ABC123",
        "confidence": 0.92,
        "timestamp": datetime.now().isoformat(),
        "vehicle_make": "Tesla",
        "vehicle_model": "Model 3",
        "vehicle_color": "Red"
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
EOL

# Create Dockerfile for core
cat > core/Dockerfile << 'EOL'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/data /app/logs /app/scripts

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "app.py"]
EOL

echo -e "  ${GREEN}Core API setup complete${NC}"

# 4. Fix MQTT configuration
echo -e "\n${YELLOW}4. Setting up MQTT broker${NC}"

# Create mosquitto.conf with fixed max_packet_size
cat > mqtt/config/mosquitto.conf << 'EOL'
# Mosquitto MQTT Broker Configuration for Tesla Model 3 Companion

# Basic configuration
pid_file /var/run/mosquitto.pid
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout

# Allow anonymous connections for testing
allow_anonymous true
# For production, uncomment these and comment out allow_anonymous true
#allow_anonymous false
#password_file /mosquitto/config/password.file

# Enable websockets
listener 1883
protocol mqtt

listener 9001
protocol websockets

# Performance settings
max_connections -1
max_queued_messages 1000
max_inflight_messages 20
# Fixed to use valid size (1MB)
max_packet_size 1048576
allow_zero_length_clientid true
persistent_client_expiration 1d

# Security settings
set_tcp_nodelay true

# Logging
log_type error
log_type warning
log_type notice
log_type information
connection_messages true
log_timestamp true

# Topic settings
topic read/vehicle/# readwrite
topic read/camera/# readwrite
topic write/events/# readwrite
topic write/commands/# readwrite
topic status/# read
EOL

# Create password.file
cat > mqtt/config/password.file << 'EOL'
# Format: username:password (hashed)
# Generate real passwords with: mosquitto_passwd -c password.file username
teslaapi:$6$IKtQr8VUgW5i3X$SCS50Rr5cFt7euGxe+N7nTRnQJnQxmjEav7C0ZR49wZB9W5mmrM5ePgkzJwZLc0PXZCVSvPoiJeJHBvoQ56ujQ==
EOL

echo -e "  ${GREEN}MQTT configuration complete${NC}"

# 5. Set up WebUI
echo -e "\n${YELLOW}5. Setting up Web UI${NC}"

# Create minimal index.html
cat > webui/build/index.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tesla M3 Companion</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      margin: 0;
      padding: 0;
      background-color: #f5f5f5;
      color: #333;
    }
    header {
      background-color: #222;
      color: white;
      padding: 1rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 1rem;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }
    .card {
      background-color: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      padding: 1rem;
      transition: transform 0.3s ease;
    }
    .card:hover {
      transform: translateY(-5px);
    }
    .status {
      display: inline-block;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-size: 0.875rem;
      font-weight: 500;
    }
    .healthy {
      background-color: #d1e7dd;
      color: #0f5132;
    }
    .error {
      background-color: #f8d7da;
      color: #842029;
    }
    .pending {
      background-color: #fff3cd;
      color: #664d03;
    }
    h1, h2, h3 {
      margin-top: 0;
    }
    a {
      color: #0d6efd;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
    button {
      background-color: #0d6efd;
      color: white;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      font-size: 1rem;
    }
    button:hover {
      background-color: #0b5ed7;
    }
    .data-panel {
      margin-top: 1rem;
      background-color: #f8f9fa;
      border-radius: 8px;
      padding: 1rem;
      font-family: monospace;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <header>
    <div class="container">
      <h1>Tesla Model 3 Companion Dashboard</h1>
      <p>Test Environment</p>
    </div>
  </header>
  
  <div class="container">
    <h2>Service Status</h2>
    <div class="grid">
      <div class="card">
        <h3>Core API</h3>
        <p>Status: <span class="status pending" id="core-status">Checking...</span></p>
        <p><a href="http://localhost:8000/docs" target="_blank">API Documentation</a></p>
        <button onclick="checkService('core')">Check Status</button>
      </div>
      
      <div class="card">
        <h3>Database</h3>
        <p>Status: <span class="status pending" id="db-status">Checking...</span></p>
        <p>PostgreSQL: localhost:5432</p>
        <p>Credentials: postgres/postgres</p>
      </div>
      
      <div class="card">
        <h3>Redis</h3>
        <p>Status: <span class="status pending" id="redis-status">Checking...</span></p>
        <p>Port: 6379</p>
      </div>
      
      <div class="card">
        <h3>MQTT Broker</h3>
        <p>Status: <span class="status pending" id="mqtt-status">Checking...</span></p>
        <p>MQTT: 1883, WebSockets: 9001</p>
      </div>
    </div>
    
    <h2>Monitoring</h2>
    <div class="grid">
      <div class="card">
        <h3>Prometheus</h3>
        <p><a href="http://localhost:9090" target="_blank">Open Prometheus</a></p>
      </div>
      
      <div class="card">
        <h3>Grafana</h3>
        <p><a href="http://localhost:3000" target="_blank">Open Grafana Dashboard</a></p>
        <p>Default login: admin/admin</p>
      </div>
    </div>
    
    <h2>Test Data</h2>
    <div class="grid">
      <div class="card">
        <h3>Vehicle Data</h3>
        <button onclick="fetchVehicleData()">Load Mock Data</button>
        <div class="data-panel" id="vehicle-data">Click button to load mock data</div>
      </div>
      
      <div class="card">
        <h3>License Plate Detection</h3>
        <button onclick="fetchPlateData()">Load Mock Data</button>
        <div class="data-panel" id="plate-data">Click button to load mock data</div>
      </div>
    </div>
  </div>
  
  <script>
    // Function to check service status
    async function checkService(service) {
      const statusElement = document.getElementById(`${service}-status`);
      statusElement.textContent = 'Checking...';
      statusElement.className = 'status pending';
      
      try {
        let response;
        switch(service) {
          case 'core':
            response = await fetch('http://localhost:8000/health');
            break;
          default:
            // For services without direct health endpoints
            statusElement.textContent = 'Unknown';
            statusElement.className = 'status pending';
            return;
        }
        
        if (response.ok) {
          statusElement.textContent = 'Healthy';
          statusElement.className = 'status healthy';
        } else {
          statusElement.textContent = 'Error';
          statusElement.className = 'status error';
        }
      } catch (error) {
        statusElement.textContent = 'Unavailable';
        statusElement.className = 'status error';
      }
    }
    
    // Function to fetch mock vehicle data
    async function fetchVehicleData() {
      const dataPanel = document.getElementById('vehicle-data');
      dataPanel.textContent = 'Loading...';
      
      try {
        const response = await fetch('http://localhost:8000/vehicle-data/mock');
        if (response.ok) {
          const data = await response.json();
          dataPanel.textContent = JSON.stringify(data, null, 2);
        } else {
          dataPanel.textContent = 'Error fetching data';
        }
      } catch (error) {
        dataPanel.textContent = 'Service unavailable. Make sure the Core API is running.';
      }
    }
    
    // Function to fetch mock plate data
    async function fetchPlateData() {
      const dataPanel = document.getElementById('plate-data');
      dataPanel.textContent = 'Loading...';
      
      try {
        const response = await fetch('http://localhost:8000/plates/mock');
        if (response.ok) {
          const data = await response.json();
          dataPanel.textContent = JSON.stringify(data, null, 2);
        } else {
          dataPanel.textContent = 'Error fetching data';
        }
      } catch (error) {
        dataPanel.textContent = 'Service unavailable. Make sure the Core API is running.';
      }
    }
    
    // Check core service status on page load
    window.addEventListener('load', () => {
      checkService('core');
      
      // Mark other services as unknown initially
      document.getElementById('db-status').textContent = 'Unknown';
      document.getElementById('redis-status').textContent = 'Unknown';
      document.getElementById('mqtt-status').textContent = 'Unknown';
    });
  </script>
</body>
</html>
EOL

# Create nginx.conf
cat > webui/nginx.conf << 'EOL'
server {
    listen 80;
    server_name _;
    
    # Health check endpoint
    location /health {
        access_log off;
        add_header Content-Type text/plain;
        return 200 'healthy';
    }
    
    # Main application
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options SAMEORIGIN;
        add_header X-XSS-Protection "1; mode=block";
    }
    
    # API proxy to Core service
    location /api/ {
        proxy_pass http://core:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Error handling
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOL

# Create Dockerfile for webui
cat > webui/Dockerfile << 'EOL'
FROM nginx:alpine

# Copy built files
COPY build/ /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose ports
EXPOSE 80
EXPOSE 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOL

echo -e "  ${GREEN}Web UI setup complete${NC}"

# 6. Create mock services
echo -e "\n${YELLOW}6. Setting up mock services${NC}"

# Create basic OpenCV mock service
mkdir -p opencv
cat > opencv/Dockerfile << 'EOL'
FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

# Create necessary directories
RUN mkdir -p /app/models /app/logs /app/data/images

COPY . .

EXPOSE 8081

CMD ["python", "-c", "import uvicorn; from fastapi import FastAPI; app = FastAPI(); @app.get('/health'); async def health(): return {'status': 'healthy'}; @app.get('/status'); async def status(): return {'status': 'ok', 'camera': 'mock'}; uvicorn.run(app, host='0.0.0.0', port=8081)"]
EOL

# Create basic OBD mock service
mkdir -p obd
cat > obd/Dockerfile << 'EOL'
FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

# Create necessary directories
RUN mkdir -p /app/logs /app/data

COPY . .

EXPOSE 8082

CMD ["python", "-c", "import uvicorn; from fastapi import FastAPI; app = FastAPI(); @app.get('/health'); async def health(): return {'status': 'healthy'}; @app.get('/status'); async def status(): return {'status': 'ok', 'obd': 'mock'}; uvicorn.run(app, host='0.0.0.0', port=8082)"]
EOL

# Create basic LLM mock service
mkdir -p llm
cat > llm/Dockerfile << 'EOL'
FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

# Create necessary directories
RUN mkdir -p /app/models /app/logs /app/config

COPY . .

EXPOSE 8080

CMD ["python", "-c", "import uvicorn; import json; from fastapi import FastAPI; app = FastAPI(); @app.get('/health'); async def health(): return {'status': 'healthy'}; @app.post('/generate'); async def generate(request: dict): return {'text': 'This is a mock response from the LLM service.', 'model_used': 'mock-llama3', 'tokens_used': 42, 'processing_time': 0.1}; uvicorn.run(app, host='0.0.0.0', port=8080)"]
EOL

echo -e "  ${GREEN}Mock services setup complete${NC}"

# 7. Create .env file
echo -e "\n${YELLOW}7. Creating .env file${NC}"
cat > .env << 'EOL'
# Test environment values
CLOUD_API_KEY=test_key
TAILSCALE_AUTH_KEY=test_key
JWT_SECRET=test_secret_key_replace_in_production
JWT_EXPIRATION=3600
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tesla
REDIS_PASSWORD=redis
MQTT_USERNAME=teslaapi
MQTT_PASSWORD=teslaapi
LOG_LEVEL=info
CAMERA_SOURCE=/dev/null
OBD_DEVICE=/dev/null
ENABLE_GPU=false
EOL
echo -e "  ${GREEN}.env file created${NC}"

# 8. Fix docker-compose.yml device mounts
echo -e "\n${YELLOW}8. Adjusting device mounts for testing${NC}"
# Remove device mounts for camera and OBD
sed -i.device.bak 's/      - \/dev\/video0:\/dev\/video0/      # - \/dev\/video0:\/dev\/video0  # Commented for testing/' docker-compose.yml
sed -i 's/      - \/dev\/ttyUSB0:\/dev\/ttyUSB0/      # - \/dev\/ttyUSB0:\/dev\/ttyUSB0  # Commented for testing/' docker-compose.yml
echo -e "  ${GREEN}Device mounts adjusted for testing${NC}"

# 9. Create a minimal prometheus.yml file if needed
echo -e "\n${YELLOW}9. Setting up Prometheus configuration${NC}"
mkdir -p monitoring
cat > monitoring/prometheus.yml << 'EOL'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'core'
    static_configs:
      - targets: ['core:8000']

  - job_name: 'llm'
    static_configs:
      - targets: ['llm:8080']

  - job_name: 'opencv'
    static_configs:
      - targets: ['opencv:8081']

  - job_name: 'obd'
    static_configs:
      - targets: ['obd:8082']

  - job_name: 'database'
    static_configs:
      - targets: ['database:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOL
echo -e "  ${GREEN}Prometheus configuration created${NC}"

# 10. Start services incrementally
echo -e "\n${YELLOW}10. Starting services incrementally${NC}"

echo -e "\n${BLUE}Starting database and Redis...${NC}"
docker-compose up -d database redis

echo "Waiting 15 seconds for database and Redis to initialize..."
sleep 15

echo -e "\n${BLUE}Starting MQTT broker...${NC}"
docker-compose up -d mosquitto

echo "Waiting 10 seconds for MQTT to initialize..."
sleep 10

echo -e "\n${BLUE}Building and starting Core API...${NC}"
docker-compose build core
docker-compose up -d core

echo "Waiting 15 seconds for Core API to initialize..."
sleep 15

# Check if core is running
if docker-compose ps core | grep "Up" > /dev/null; then
  echo -e "  ${GREEN}Core API is running${NC}"
  
  echo -e "\n${BLUE}Starting Web UI...${NC}"
  docker-compose build webui
  docker-compose up -d webui
  
  echo "Waiting 10 seconds for Web UI to initialize..."
  sleep 10
  
  if docker-compose ps webui | grep "Up" > /dev/null; then
    echo -e "  ${GREEN}Web UI is running${NC}"
  else
    echo -e "  ${RED}Web UI failed to start${NC}"
    docker-compose logs webui --tail 20
  fi
else
  echo -e "  ${RED}Core API failed to start${NC}"
  docker-compose logs core --tail 20
fi

# 11. Print status and next steps
echo -e "\n${GREEN}Successfully running services:${NC}"
docker-compose ps --filter "status=running"

echo -e "\n${BLUE}Test Environment Setup Complete!${NC}"
echo -e "\n${YELLOW}How to use your test environment:${NC}"
echo "1. Access Web Dashboard: http://localhost"
echo "2. Core API Documentation: http://localhost:8000/docs"
echo "3. Grafana (when started): http://localhost:3000 (admin/admin)"
echo "4. Prometheus (when started): http://localhost:9090"
echo ""
echo "To start all services: docker-compose up -d"
echo "To check logs: docker-compose logs -f [service_name]"
echo "To stop all services: docker-compose down"
echo "To clean up completely: docker-compose down -v"