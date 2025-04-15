# Docker Compose Deployment Guide for Tesla Model 3 Raspberry Pi 5 Integration

This guide provides step-by-step instructions for deploying the containerized Tesla Model 3 Raspberry Pi 5 integration system.

## Prerequisites

- Raspberry Pi 5 with 8GB RAM
- 64GB or larger microSD card (Class 10 or UHS-I/II recommended)
- Official Raspberry Pi 5V/5A power supply
- Raspberry Pi OS 64-bit (Bullseye or newer) installed
- Docker and Docker Compose installed
- Internet connection for initial setup
- USB OBD-II adapter compatible with Tesla Model 3
- USB camera or Raspberry Pi Camera Module
- Optional: USB SSD for improved performance and reliability

## Installation Steps

### 1. Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -sSL https://get.docker.com | sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

# Install additional dependencies
sudo apt install -y git python3-pip libffi-dev libssl-dev
```

Log out and log back in for group changes to take effect.

### 2. Clone the Repository

```bash
# Create project directory
mkdir -p ~/tesla_model3_rpi_project

# Clone the repository (if using Git) or copy files
git clone https://github.com/yourusername/tesla_model3_rpi_project.git ~/tesla_model3_rpi_project

# Navigate to the docker directory
cd ~/tesla_model3_rpi_project/docker
```

### 3. Configure Environment

Review and modify the following files as needed:

- `docker-compose.yml`: Adjust resource limits if necessary
- `llm/config/api_keys.json`: Add your OpenAI and Anthropic API keys if you want to use cloud fallback
- `obd/obd_server.py`: Verify the OBD device path matches your setup

### 4. Prepare Volumes

```bash
# Create directories for persistent storage
mkdir -p ~/tesla_model3_rpi_project/data/{llm_models,images,database}

# Download Llama 3 model (this may take some time)
cd ~/tesla_model3_rpi_project/docker
./llm/download_model.sh
```

### 5. Start the Services

```bash
# Start all services in detached mode
docker-compose up -d

# Check if all services are running
docker-compose ps
```

### 6. Access the Web Interface

Open a web browser and navigate to:

```
http://localhost
```

Or if accessing from another device on the same network:

```
http://<raspberry-pi-ip-address>
```

### 7. Configure System Settings

1. Navigate to the "System Settings" page in the web interface
2. Configure the following:
   - Camera settings
   - OBD connection parameters
   - LLM preferences
   - Storage locations
   - Security analysis sensitivity

### 8. Test the System

1. Navigate to the "Camera View" page to verify camera feed
2. Check "Vehicle Data" page to confirm OBD connection
3. Test plate recognition with a sample image
4. Verify LLM functionality in the "LLM Settings" page

## Updating the System

To update the system with new container versions:

```bash
# Pull the latest changes
git pull

# Rebuild and restart containers
docker-compose down
docker-compose build
docker-compose up -d
```

## Monitoring

The system includes Prometheus and Grafana for monitoring:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (default login: admin/admin)

## Troubleshooting

### Service Not Starting

Check the logs for the specific service:

```bash
docker-compose logs <service_name>
```

### Camera Not Detected

Verify the camera device is properly connected and the path in docker-compose.yml is correct:

```bash
ls -la /dev/video*
```

### OBD Connection Issues

Check if the OBD adapter is recognized:

```bash
ls -la /dev/ttyUSB*
```

Try reconnecting the adapter or restarting the OBD service:

```bash
docker-compose restart obd
```

### Memory Issues

If the system is running out of memory, adjust the resource limits in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      memory: 4G  # Reduce from 6G to 4G for LLM service
```

### Disk Space Issues

Check available disk space:

```bash
df -h
```

Consider moving the database and image storage to an external USB drive.

## Backup and Restore

### Backup

```bash
# Stop the services
docker-compose down

# Backup volumes
tar -czvf tesla_backup.tar.gz ~/tesla_model3_rpi_project/data

# Restart services
docker-compose up -d
```

### Restore

```bash
# Stop the services
docker-compose down

# Restore volumes
tar -xzvf tesla_backup.tar.gz -C /

# Restart services
docker-compose up -d
```

## Security Considerations

- Change default Grafana password immediately
- Consider setting up a VPN for remote access
- Regularly update the system and containers
- Use encrypted volumes for sensitive data
- Limit physical access to the Raspberry Pi

## Power Management

The system is configured to operate efficiently on the Raspberry Pi 5. For optimal performance:

- Use the official 5V/5A power supply
- Consider adding a UPS for power stability
- Mount in a location with good airflow in the vehicle
- Monitor system temperature through the web interface

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [Llama 3 Documentation](https://ai.meta.com/llama/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [OBD-II Documentation](https://en.wikipedia.org/wiki/On-board_diagnostics)
