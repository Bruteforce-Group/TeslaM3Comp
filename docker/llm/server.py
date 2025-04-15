#!/usr/bin/env python3
# LLM Server for Tesla Model 3 Raspberry Pi 5 Integration
# This server provides a FastAPI interface to the Llama 3 model with cloud fallback options

import os
import sys
import time
import json
import logging
from typing import Dict, List, Optional, Union, Any
import threading
import queue

import numpy as np
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field
from loguru import logger
import requests

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stderr, level=log_level)
logger.add("/app/logs/llm_server.log", rotation="10 MB", level=log_level)

# Load environment variables
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/models/llama3")
QUANTIZATION = os.environ.get("QUANTIZATION", "none")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "2048"))
CONTEXT_SIZE = int(os.environ.get("CONTEXT_SIZE", "4096"))
ENABLE_CLOUD_FALLBACK = os.environ.get("ENABLE_CLOUD_FALLBACK", "true").lower() == "true"

# Initialize FastAPI app
app = FastAPI(
    title="Tesla Model 3 LLM API",
    description="API for Llama 3 model with cloud fallback options",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys from config
api_keys = {}
try:
    if os.path.exists("/app/config/api_keys.json"):
        with open("/app/config/api_keys.json", "r") as f:
            api_keys = json.load(f)
            logger.info("Loaded API keys from config file")
except Exception as e:
    logger.error(f"Error loading API keys: {e}")

# Model loading
llm = None
model_loading = False
model_load_error = None
model_load_queue = queue.Queue()

# Pydantic models for API
class LLMRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = Field(default=512)
    temperature: Optional[float] = Field(default=0.7)
    top_p: Optional[float] = Field(default=0.95)
    top_k: Optional[int] = Field(default=40)
    stop_sequences: Optional[List[str]] = Field(default=None)
    model_preference: Optional[str] = Field(default="local")  # local, openai, anthropic, auto

class LLMResponse(BaseModel):
    text: str
    model_used: str
    tokens_used: int
    processing_time: float

class APIKeyRequest(BaseModel):
    provider: str  # openai, anthropic
    api_key: str

class StatusResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
    cloud_fallback_enabled: bool
    available_providers: List[str]
    memory_usage: Dict[str, Any]
    uptime: float

# Startup event
@app.on_event("startup")
async def startup_event():
    global model_loading
    # Start model loading in background
    model_loading = True
    threading.Thread(target=load_model, daemon=True).start()

# Load the model in a separate thread
def load_model():
    global llm, model_loading, model_load_error
    try:
        logger.info(f"Loading Llama 3 model from {MODEL_PATH}")
        start_time = time.time()
        
        # Check if model exists
        model_file = None
        if QUANTIZATION == "none":
            model_file = os.path.join(MODEL_PATH, "ggml-model-f16.gguf")
        else:
            model_file = os.path.join(MODEL_PATH, f"ggml-model-{QUANTIZATION}.gguf")
        
        if not os.path.exists(model_file):
            logger.warning(f"Model file {model_file} not found, attempting to download")
            # Run the download script
            import subprocess
            result = subprocess.run(["/app/download_model.sh"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Failed to download model: {result.stderr}")
        
        # Import here to avoid loading the module before we need it
        from llama_cpp import Llama
        
        # Load the model
        llm = Llama(
            model_path=model_file,
            n_ctx=CONTEXT_SIZE,
            n_threads=os.cpu_count(),
            n_batch=512,
            verbose=False
        )
        
        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
        model_loading = False
        model_load_error = None
        model_load_queue.put(True)
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        model_loading = False
        model_load_error = str(e)
        model_load_queue.put(False)

# Wait for model to load
async def wait_for_model():
    if llm is not None:
        return True
    
    if not model_loading and model_load_error is not None:
        raise HTTPException(status_code=500, detail=f"Model failed to load: {model_load_error}")
    
    try:
        # Wait for up to 30 seconds for model to load
        result = model_load_queue.get(timeout=30)
        return result
    except queue.Empty:
        raise HTTPException(status_code=503, detail="Model is still loading, please try again later")

# Generate text with local model
def generate_with_local_model(prompt, max_tokens, temperature, top_p, top_k, stop_sequences):
    start_time = time.time()
    
    # Generate text
    output = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        stop=stop_sequences,
        echo=False
    )
    
    processing_time = time.time() - start_time
    
    return {
        "text": output["choices"][0]["text"],
        "model_used": "llama3-local",
        "tokens_used": output["usage"]["total_tokens"],
        "processing_time": processing_time
    }

# Generate text with OpenAI API
def generate_with_openai(prompt, max_tokens, temperature, top_p, stop_sequences):
    if "openai" not in api_keys or not api_keys["openai"]:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    
    start_time = time.time()
    
    try:
        import openai
        openai.api_key = api_keys["openai"]
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop_sequences
        )
        
        processing_time = time.time() - start_time
        
        return {
            "text": response.choices[0].message.content,
            "model_used": "openai-gpt-3.5-turbo",
            "tokens_used": response.usage.total_tokens,
            "processing_time": processing_time
        }
    except Exception as e:
        logger.error(f"Error using OpenAI API: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

# Generate text with Anthropic API
def generate_with_anthropic(prompt, max_tokens, temperature, top_p, stop_sequences):
    if "anthropic" not in api_keys or not api_keys["anthropic"]:
        raise HTTPException(status_code=400, detail="Anthropic API key not configured")
    
    start_time = time.time()
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_keys["anthropic"])
        
        response = client.completions.create(
            prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
            model="claude-instant-1",
            max_tokens_to_sample=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences or ["\n\nHuman:"]
        )
        
        processing_time = time.time() - start_time
        
        return {
            "text": response.completion,
            "model_used": "anthropic-claude-instant",
            "tokens_used": len(response.completion.split()) * 1.3,  # Rough estimate
            "processing_time": processing_time
        }
    except Exception as e:
        logger.error(f"Error using Anthropic API: {e}")
        raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")

# API endpoints
@app.get("/", response_model=StatusResponse)
async def root():
    """Get the status of the LLM server"""
    # Get memory usage
    import psutil
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Get available providers
    providers = ["local"]
    if "openai" in api_keys and api_keys["openai"]:
        providers.append("openai")
    if "anthropic" in api_keys and api_keys["anthropic"]:
        providers.append("anthropic")
    
    return {
        "status": "loading" if model_loading else "ready" if llm is not None else "error",
        "model_loaded": llm is not None,
        "model_path": MODEL_PATH,
        "cloud_fallback_enabled": ENABLE_CLOUD_FALLBACK,
        "available_providers": providers,
        "memory_usage": {
            "rss": memory_info.rss / (1024 * 1024),  # MB
            "vms": memory_info.vms / (1024 * 1024),  # MB
            "percent": process.memory_percent()
        },
        "uptime": time.time() - process.create_time()
    }

@app.post("/generate", response_model=LLMResponse)
async def generate(request: LLMRequest):
    """Generate text using the LLM model"""
    logger.info(f"Received generation request with preference: {request.model_preference}")
    
    # Determine which model to use
    model_preference = request.model_preference.lower()
    
    if model_preference == "local":
        # Use local model
        await wait_for_model()
        if llm is None:
            raise HTTPException(status_code=500, detail="Local model is not available")
        
        return generate_with_local_model(
            request.prompt,
            request.max_tokens,
            request.temperature,
            request.top_p,
            request.top_k,
            request.stop_sequences
        )
    
    elif model_preference == "openai":
        # Use OpenAI
        return generate_with_openai(
            request.prompt,
            request.max_tokens,
            request.temperature,
            request.top_p,
            request.stop_sequences
        )
    
    elif model_preference == "anthropic":
        # Use Anthropic
        return generate_with_anthropic(
            request.prompt,
            request.max_tokens,
            request.temperature,
            request.top_p,
            request.stop_sequences
        )
    
    elif model_preference == "auto":
        # Try local first, then fall back to cloud if enabled
        try:
            # Check if local model is available
            model_ready = await wait_for_model()
            if model_ready and llm is not None:
                return generate_with_local_model(
                    request.prompt,
                    request.max_tokens,
                    request.temperature,
                    request.top_p,
                    request.top_k,
                    request.stop_sequences
                )
        except Exception as e:
            logger.warning(f"Local model generation failed, falling back to cloud: {e}")
        
        # If we get here, try cloud providers if enabled
        if not ENABLE_CLOUD_FALLBACK:
            raise HTTPException(status_code=503, detail="Local model unavailable and cloud fallback is disabled")
        
        # Try OpenAI first
        if "openai" in api_keys and api_keys["openai"]:
            try:
                return generate_with_openai(
                    request.prompt,
                    request.max_tokens,
                    request.temperature,
                    request.top_p,
                    request.stop_sequences
                )
            except Exception as e:
                logger.warning(f"OpenAI generation failed, trying Anthropic: {e}")
        
        # Then try Anthropic
        if "anthropic" in api_keys and api_keys["anthropic"]:
            try:
                return generate_with_anthropic(
                    request.prompt,
                    request.max_tokens,
                    request.temperature,
                    request.top_p,
                    request.stop_sequences
                )
            except Exception as e:
                logger.error(f"Anthropic generation failed: {e}")
        
        # If we get here, all providers failed
        raise HTTPException(status_code=503, detail="All LLM providers failed to generate text")
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid model preference: {request.model_preference}")

@app.post("/api-keys")
async def set_api_key(request: APIKeyRequest):
    """Set an API key for a cloud provider"""
    global api_keys
    
    if request.provider not in ["openai", "anthropic"]:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
    
    # Update the API key
    api_keys[request.provider] = request.api_key
    
    # Save to config file
    try:
        os.makedirs("/app/config", exist_ok=True)
        with open("/app/config/api_keys.json", "w") as f:
            json.dump(api_keys, f)
        logger.info(f"Saved {request.provider} API key to config file")
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving API key: {str(e)}")
    
    return {"status": "success", "message": f"{request.provider} API key updated successfully"}

@app.delete("/api-keys/{provider}")
async def delete_api_key(provider: str):
    """Delete an API key for a cloud provider"""
    global api_keys
    
    if provider not in ["openai", "anthropic"]:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    
    # Remove the API key
    if provider in api_keys:
        del api_keys[provider]
    
    # Save to config file
    try:
        with open("/app/config/api_keys.json", "w") as f:
            json.dump(api_keys, f)
        logger.info(f"Removed {provider} API key from config file")
    except Exception as e:
        logger.error(f"Error saving API key changes: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving API key changes: {str(e)}")
    
    return {"status": "success", "message": f"{provider} API key removed successfully"}

@app.post("/reload-model")
async def reload_model():
    """Reload the local LLM model"""
    global llm, model_loading
    
    if model_loading:
        raise HTTPException(status_code=400, detail="Model is already loading")
    
    # Unload current model
    llm = None
    
    # Start loading in background
    model_loading = True
    threading.Thread(target=load_model, daemon=True).start()
    
    return {"status": "success", "message": "Model reload initiated"}

# Error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Main entry point
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8080, log_level=log_level.lower())
