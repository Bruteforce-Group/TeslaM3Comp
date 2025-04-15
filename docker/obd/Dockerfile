FROM python:3.10-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    bluetooth \
    libbluetooth-dev \
    rfkill \
    usbutils \
    libusb-1.0-0-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/config /app/data /app/logs

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py /app/

# Set environment variables
ENV OBD_DEVICE=/dev/ttyUSB0 \
    CORE_API_URL=http://core:8000 \
    LOG_LEVEL=info \
    PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8082

# Run the application
CMD ["python", "obd_server.py"]
