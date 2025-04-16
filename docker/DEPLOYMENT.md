# Deployment Guide - Tesla Model 3 Companion

This guide provides step-by-step instructions for deploying the Tesla Model 3 Companion system on a Raspberry Pi 5.

## Hardware Requirements

- Raspberry Pi 5 with 8GB RAM (4GB minimum)
- 64GB or larger microSD card (Class 10 or UHS-I/II recommended)
- Official Raspberry Pi 5V/5A power supply
- Reliable cooling solution (heatsink, fan, or case with cooling)
- USB OBD-II adapter compatible with Tesla Model 3
- USB camera or Raspberry Pi Camera Module
- Ethernet connection (recommended) or Wi-Fi adapter
- Optional: GPS module for location tracking

## Software Prerequisites

1. Install Raspberry Pi OS (64-bit) with desktop or lite version
2. Update your system:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. Install Docker:
   ```bash
   curl -sSL https://get.docker.com | sh
   ```
4. Add your user to the Docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```
5. Log out and log back in for changes to take effect
6. Install Docker Compose:
   ```bash
   sudo apt install -y python3-pip
   sudo pip3 install docker-compose
   ```
7. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

## System Configuration

1. Enable the camera interface if you're using the Raspberry Pi Camera Module:
   ```bash
   sudo raspi-config
   ```
   Navigate to "Interface Options" > "Camera" and enable it

2. Configure USB devices:
   - Connect your OBD-II adapter and camera
   - Check they are detected properly:
     ```bash
     ls -l /dev/video0
     ls -l /dev/ttyUSB0
     ```

3. Optimize your Raspberry Pi for performance:
   - Edit config.txt file:
     ```bash
     sudo nano /boot/config.txt
     ```
   - Add or modify these lines:
     ```
     # Overclock (if needed and with proper cooling)
     arm_freq=2000
     gpu_freq=750
     
     # Memory split (allocate more to CPU for LLM)
     gpu_mem=128
     
     # Disable Bluetooth if not needed
     dtoverlay=disable-bt
     ```

4. Configure swapfile for additional memory:
   ```bash
   sudo nano /etc/dphys-swapfile
   ```
   Change `CONF_SWAPSIZE=100` to `CONF_SWAPSIZE=2048`
   ```bash
   sudo systemctl restart dphys-swapfile
   ```

## Deploying the Application

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TeslaM3Comp.git
   cd TeslaM3Comp/docker
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Update all the variables with your specific values, especially:
   - `JWT_SECRET` (generate a strong random key)
   - `POSTGRES_PASSWORD`
   - `REDIS_PASSWORD`
   - `MQTT_PASSWORD`
   - `CLOUD_API_KEY` (if using cloud LLM backup)
   - `TAILSCALE_AUTH_KEY` (if using Tailscale for remote access)

3. Download LLM model:
   ```bash
   chmod +x llm/download_model.sh
   ./llm/download_model.sh
   ```
   This will download the Llama 3 model to the appropriate directory.

4. Start the services:
   ```bash
   docker-compose up -d
   ```
   The first startup may take some time as it builds all the containers and downloads necessary assets.

5. Check that all services are running:
   ```bash
   docker-compose ps
   ```
   All services should show as "Up" with their health status.

## Post-Installation Configuration

1. Access the web interface at `http://your-raspberry-pi-ip`

2. Log in with default credentials:
   - Username: `admin`
   - Password: `teslaadmin`

3. Change the default password immediately

4. Configure system settings:
   - Go to Settings > System and update your preferences
   - Configure notification settings
   - Set up vehicle profile with your Tesla Model 3 details

5. Set up SSL for secure access:
   - Generate SSL certificates or use Let's Encrypt:
     ```bash
     mkdir -p ssl
     cd ssl
     openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout privkey.pem -out fullchain.pem
     ```
   - Move certificates to the SSL volume:
     ```bash
     sudo cp *.pem /var/lib/docker/volumes/docker_ssl_data/_data/
     ```
   - Edit the nginx configuration to enable HTTPS by uncommenting the relevant sections
   - Restart the web service:
     ```bash
     docker-compose restart webui
     ```

6. Set up Tailscale for secure remote access:
   - The Tailscale service should automatically connect using your auth key
   - Verify connection status:
     ```bash
     docker-compose exec tailscale tailscale status
     ```
   - You can now securely access your system remotely via Tailscale

## Monitoring and Maintenance

1. Access Grafana at `http://your-raspberry-pi-ip:3000`
   - Username: `admin`
   - Password: `admin` (change this immediately)

2. Explore the pre-configured dashboards:
   - System Overview
   - Vehicle Data
   - Security Events
   - Service Health

3. Regular maintenance:
   - Check system logs:
     ```bash
     docker-compose logs -f
     ```
   - Monitor disk space:
     ```bash
     df -h
     ```
   - Check backup status:
     ```bash
     ls -l /var/lib/docker/volumes/docker_backup_data/_data/
     ```
   - Update the system:
     ```bash
     git pull
     docker-compose pull
     docker-compose up -d
     ```

## Setting Up Automatic Startup

To ensure your Tesla Model 3 Companion starts automatically at boot:

1. Copy the systemd service file to the systemd directory:
   ```bash
   sudo cp teslam3companion.service /etc/systemd/system/
   ```

2. Edit the service file to match your username and installation path:
   ```bash
   sudo nano /etc/systemd/system/teslam3companion.service
   ```
   Update the `WorkingDirectory`, `User`, and `Group` fields as needed.

3. Reload systemd to recognize the new service:
   ```bash
   sudo systemctl daemon-reload
   ```

4. Enable the service to start at boot:
   ```bash
   sudo systemctl enable teslam3companion.service
   ```

5. Start the service:
   ```bash
   sudo systemctl start teslam3companion.service
   ```

6. Check the status:
   ```bash
   sudo systemctl status teslam3companion.service
   ```

To manage the service:
- Stop: `sudo systemctl stop teslam3companion.service`
- Restart: `sudo systemctl restart teslam3companion.service`
- View logs: `sudo journalctl -u teslam3companion.service -f`

## Connecting to Your Tesla

1. Start your Tesla Model 3
2. Locate the OBD-II port (check Tesla forums for the exact location in your model year)
3. Connect the OBD-II adapter to the port
4. Within the web interface, navigate to OBD > Connection and verify the connection status
5. You should start seeing vehicle data coming in after a few seconds

## Troubleshooting

### Common Issues and Solutions

1. **Services failing to start**
   - Check logs: `docker-compose logs [service_name]`
   - Verify environment variables in `.env` file
   - Ensure you have sufficient disk space: `df -h`

2. **Camera not detected**
   - Check connection: `ls -l /dev/video0`
   - Verify permissions: `sudo chmod 666 /dev/video0`
   - Try a different USB port

3. **OBD-II adapter not connecting**
   - Check physical connection
   - Verify device path: `ls -l /dev/ttyUSB0`
   - Try different baud rates in the web interface settings

4. **High CPU/memory usage**
   - Disable GPU acceleration if not working well
   - Reduce LLM model size in the settings
   - Adjust PostgreSQL and Redis memory limits in docker-compose.yml

5. **Web interface not accessible**
   - Check if services are running: `docker-compose ps`
   - Verify network settings: `ip addr show`
   - Check nginx logs: `docker-compose logs webui`

### Getting Support

If you encounter issues not covered in this guide:
1. Check the project GitHub issues page
2. Search the community forums
3. Submit a detailed bug report with logs and system information

## Security Recommendations

1. Change all default passwords
2. Keep your system updated regularly
3. Use strong, unique secrets in your `.env` file
4. Enable Two-Factor Authentication for the admin interface
5. Use Tailscale instead of exposing ports to the internet
6. Set up SSL/TLS for all web interfaces
7. Regularly backup your data and configurations
8. Monitor system logs for suspicious activity

## Advanced Configuration

For advanced configuration options, refer to the specific documentation for each component:
- [Core API Documentation](./core/README.md)
- [LLM Service Documentation](./llm/README.md)
- [OpenCV Service Documentation](./opencv/README.md)
- [OBD Service Documentation](./obd/README.md)
- [Monitoring Stack Documentation](./monitoring/README.md)
