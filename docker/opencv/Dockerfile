FROM python:3.10-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    libopencv-dev \
    python3-opencv \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/models /app/data /app/logs

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py /app/
COPY models/ /app/models/

# Set environment variables
ENV CAMERA_SOURCE=/dev/video0 \
    ENABLE_GPU=false \
    LOG_LEVEL=info \
    PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8081

# Run the application
CMD ["python", "opencv_server.py"]
