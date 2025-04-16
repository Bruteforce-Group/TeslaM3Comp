FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

# Create necessary directories
RUN mkdir -p /app/models /app/logs /app/config

COPY . .

EXPOSE 8080

CMD ["python", "-c", "import uvicorn; import json; from fastapi import FastAPI; app = FastAPI(); @app.get('/health'); async def health(): return {'status': 'healthy'}; @app.post('/generate'); async def generate(request: dict): return {'text': 'This is a mock response from the LLM service.', 'model_used': 'mock-llama3', 'tokens_used': 42, 'processing_time': 0.1}; uvicorn.run(app, host='0.0.0.0', port=8080)"]
