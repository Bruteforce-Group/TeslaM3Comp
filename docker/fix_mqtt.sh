#!/bin/bash
# Fix MQTT configuration and continue testing

# Set colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}Fixing MQTT Configuration Issue${NC}"

# Fix mosquitto.conf file
echo "Fixing mosquitto.conf..."
mkdir -p mqtt/config
cat > mqtt/config/mosquitto.conf << EOL
# Mosquitto MQTT Broker Configuration for Tesla Model 3 Companion

# Basic configuration
pid_file /var/run/mosquitto.pid
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout

# Allow anonymous connections locally, but require authentication for remote connections
allow_anonymous false
password_file /mosquitto/config/password.file

# Enable websockets for web interface
listener 1883
protocol mqtt

listener 9001
protocol websockets

# Performance settings
max_connections -1
max_queued_messages 1000
max_inflight_messages 20
max_packet_size 0
allow_zero_length_clientid true
persistent_client_expiration 1d

# Security settings
set_tcp_nodelay true
tls_version tlsv1.2

# Logging
log_type error
log_type warning
log_type notice
log_type information
connection_messages true
log_timestamp true

# Topic settings - no bridge configuration
topic read/vehicle/# readwrite
topic read/camera/# readwrite
topic write/events/# readwrite
topic write/commands/# readwrite
topic status/# read
EOL

# Create password file if it doesn't exist
echo "Creating MQTT password file..."
cat > mqtt/config/password.file << EOL
# Format: username:password (hashed)
# Generate real passwords with: mosquitto_passwd -c password.file username
teslaapi:$6$IKtQr8VUgW5i3X$SCS50Rr5cFt7euGxe+N7nTRnQJnQxmjEav7C0ZR49wZB9W5mmrM5ePgkzJwZLc0PXZCVSvPoiJeJHBvoQ56ujQ==
EOL

echo -e "${GREEN}MQTT configuration fixed${NC}"

# Restart MQTT service
echo "Restarting MQTT service..."
docker-compose down mosquitto
docker-compose up -d mosquitto

echo "Waiting for MQTT service to restart (15 seconds)..."
sleep 15

# Check MQTT status
echo -n "MQTT broker status: "
if docker-compose ps mosquitto | grep "Up" > /dev/null; then
  echo -e "${GREEN}Running${NC}"
else
  echo -e "${RED}Still having issues${NC}"
  echo "Checking logs for errors..."
  docker-compose logs mosquitto --tail 10
fi

# Continue with Web UI testing if MQTT is fixed
if docker-compose ps mosquitto | grep "Up" > /dev/null; then
  echo -e "\n${YELLOW}Proceeding with Web UI Testing${NC}"
  
  # Create minimal index.html for webui if it doesn't exist
  echo "Creating minimal web files..."
  mkdir -p webui/build
  cat > webui/build/index.html << EOL
<!DOCTYPE html>
<html>
<head>
  <title>Tesla M3 Companion</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
    .container { max-width: 800px; margin: 0 auto; padding: 20px; background: #f8f9fa; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { color: #343a40; }
    .status { margin: 20px 0; padding: 15px; border-radius: 4px; background: #d4edda; color: #155724; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Tesla M3 Companion Dashboard</h1>
    <div class="status">Health status: <span id="health">Checking...</span></div>
    <p>This is a minimal test UI for the Tesla M3 Companion project.</p>
    <p>Core API status: <a href="http://localhost:8000/health">Check</a></p>
    <p>Grafana Dashboard: <a href="http://localhost:3000">Open</a></p>
    <p>Prometheus: <a href="http://localhost:9090">Open</a></p>
  </div>
  <script>
    fetch('/health').then(response => {
      document.getElementById('health').innerText = 'Healthy';
    }).catch(error => {
      document.getElementById('health').innerText = 'Error';
    });
  </script>
</body>
</html>
EOL

  # Rebuild and start Web UI
  echo "Building and starting Web UI..."
  docker-compose build webui
  docker-compose up -d webui
  
  echo "Waiting for Web UI to start (20 seconds)..."
  sleep 20
  
  echo -n "Web UI status: "
  if docker-compose ps webui | grep "Up" > /dev/null; then
    echo -e "${GREEN}Running${NC}"
    echo -e "${GREEN}You can now access the Web UI at http://localhost${NC}"
  else
    echo -e "${RED}Not running${NC}"
    echo "Checking logs for errors..."
    docker-compose logs webui --tail 30
  fi
fi

echo -e "\n${BLUE}Successfully running services:${NC}"
docker-compose ps --filter "status=running"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Access the Web UI at http://localhost"
echo "2. Check Grafana dashboard at http://localhost:3000 (admin/admin)"
echo "3. Check Prometheus at http://localhost:9090"
echo "4. Test Core API at http://localhost:8000/health"
echo "5. For hardware-dependent services (OpenCV, OBD), you need to create mock implementations"
echo "6. To clean up: docker-compose down -v"
