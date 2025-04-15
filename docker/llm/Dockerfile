FROM python:3.10-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    libopenblas-dev \
    libblas-dev \
    liblapack-dev \
    libopencv-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/models /app/config /app/logs

# Copy application files
COPY *.py /app/
COPY scripts/ /app/scripts/

# Set up model download script
COPY download_model.sh /app/
RUN chmod +x /app/download_model.sh

# Set environment variables
ENV MODEL_PATH=/app/models/llama3 \
    QUANTIZATION=none \
    MAX_TOKENS=2048 \
    CONTEXT_SIZE=4096 \
    LOG_LEVEL=info \
    ENABLE_CLOUD_FALLBACK=true \
    PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8080

# Run the application
CMD ["python", "server.py"]
