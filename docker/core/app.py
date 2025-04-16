#!/usr/bin/env python3
from fastapi import FastAPI
import uvicorn
import os
import json
from datetime import datetime

app = FastAPI(
    title="Tesla Model 3 Companion API",
    description="Core API for Tesla Model 3 Integration",
    version="1.0.0",
)

@app.get("/health")
async def health_check():
    """Health check endpoint for the service"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Get system status"""
    return {
        "status": "running",
        "version": "1.0.0",
        "services": ["database", "redis", "core_api", "mqtt"],
        "api_docs": "/docs"
    }

@app.get("/vehicle-data/mock")
async def mock_vehicle_data():
    """Get mock vehicle data for testing"""
    return {
        "speed": 65.5,
        "battery_level": 78.3,
        "temperature": 72.1,
        "location": "37.7749,-122.4194",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "odometer": 12345.6,
            "battery_voltage": 380.5,
            "tire_pressure": {
                "front_left": 36.0,
                "front_right": 35.8,
                "rear_left": 36.2,
                "rear_right": 36.0
            }
        }
    }

@app.get("/plates/mock")
async def mock_plate_recognition():
    """Get mock plate recognition data for testing"""
    return {
        "plate_number": "ABC123",
        "confidence": 0.92,
        "timestamp": datetime.now().isoformat(),
        "vehicle_make": "Tesla",
        "vehicle_model": "Model 3",
        "vehicle_color": "Red"
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
