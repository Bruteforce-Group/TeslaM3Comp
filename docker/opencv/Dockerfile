FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

# Create necessary directories
RUN mkdir -p /app/models /app/logs /app/data/images

COPY . .

EXPOSE 8081

CMD ["python", "-c", "import uvicorn; from fastapi import FastAPI; app = FastAPI(); @app.get('/health'); async def health(): return {'status': 'healthy'}; @app.get('/status'); async def status(): return {'status': 'ok', 'camera': 'mock'}; uvicorn.run(app, host='0.0.0.0', port=8081)"]
