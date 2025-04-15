FROM python:3.10-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    wget \
    curl \
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
COPY scripts/ /app/scripts/

# Set environment variables
ENV DATABASE_URL=postgresql://postgres:postgres@database:5432/tesla \
    LLM_SERVICE_URL=http://llm:8080 \
    OPENCV_SERVICE_URL=http://opencv:8081 \
    LOG_LEVEL=info \
    PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8000

# Run the application
CMD ["python", "app.py"]
