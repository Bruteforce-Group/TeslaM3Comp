#!/usr/bin/env python3
# Core Application for Tesla Model 3 Raspberry Pi 5 Integration
# This is the main application that coordinates all components

import os
import sys
import time
import json
import logging
from typing import Dict, List, Optional, Union, Any
import threading
import asyncio

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel, Field
from loguru import logger
import requests
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stderr, level=log_level)
logger.add("/app/logs/core_app.log", rotation="10 MB", level=log_level)

# Load environment variables
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@database:5432/tesla")
LLM_SERVICE_URL = os.environ.get("LLM_SERVICE_URL", "http://llm:8080")
OPENCV_SERVICE_URL = os.environ.get("OPENCV_SERVICE_URL", "http://opencv:8081")

# Initialize FastAPI app
app = FastAPI(
    title="Tesla Model 3 Integration API",
    description="Core API for Tesla Model 3 Raspberry Pi 5 Integration",
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

# Database setup
Base = declarative_base()
engine = sa.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database models
class PlateRecognition(Base):
    __tablename__ = "plate_recognitions"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    plate_number = sa.Column(sa.String, index=True)
    confidence = sa.Column(sa.Float)
    timestamp = sa.Column(sa.DateTime, server_default=sa.func.now())
    image_path = sa.Column(sa.String, nullable=True)
    location = sa.Column(sa.String, nullable=True)
    vehicle_data = sa.Column(sa.JSON, nullable=True)

class SecurityEvent(Base):
    __tablename__ = "security_events"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    event_type = sa.Column(sa.String, index=True)
    severity = sa.Column(sa.String)
    timestamp = sa.Column(sa.DateTime, server_default=sa.func.now())
    description = sa.Column(sa.String)
    image_path = sa.Column(sa.String, nullable=True)
    location = sa.Column(sa.String, nullable=True)
    is_resolved = sa.Column(sa.Boolean, default=False)

class VehicleData(Base):
    __tablename__ = "vehicle_data"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    timestamp = sa.Column(sa.DateTime, server_default=sa.func.now())
    speed = sa.Column(sa.Float, nullable=True)
    battery_level = sa.Column(sa.Float, nullable=True)
    temperature = sa.Column(sa.Float, nullable=True)
    location = sa.Column(sa.String, nullable=True)
    data = sa.Column(sa.JSON)

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    key = sa.Column(sa.String, unique=True, index=True)
    value = sa.Column(sa.String)
    description = sa.Column(sa.String, nullable=True)
    updated_at = sa.Column(sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for API
class PlateRecognitionCreate(BaseModel):
    plate_number: str
    confidence: float
    image_path: Optional[str] = None
    location: Optional[str] = None
    vehicle_data: Optional[Dict[str, Any]] = None

class PlateRecognitionResponse(BaseModel):
    id: int
    plate_number: str
    confidence: float
    timestamp: str
    image_path: Optional[str] = None
    location: Optional[str] = None
    vehicle_data: Optional[Dict[str, Any]] = None

class SecurityEventCreate(BaseModel):
    event_type: str
    severity: str
    description: str
    image_path: Optional[str] = None
    location: Optional[str] = None

class SecurityEventResponse(BaseModel):
    id: int
    event_type: str
    severity: str
    timestamp: str
    description: str
    image_path: Optional[str] = None
    location: Optional[str] = None
    is_resolved: bool

class VehicleDataCreate(BaseModel):
    speed: Optional[float] = None
    battery_level: Optional[float] = None
    temperature: Optional[float] = None
    location: Optional[str] = None
    data: Dict[str, Any]

class VehicleDataResponse(BaseModel):
    id: int
    timestamp: str
    speed: Optional[float] = None
    battery_level: Optional[float] = None
    temperature: Optional[float] = None
    location: Optional[str] = None
    data: Dict[str, Any]

class SystemConfigUpdate(BaseModel):
    value: str
    description: Optional[str] = None

class SystemConfigResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    updated_at: str

class SystemStatusResponse(BaseModel):
    status: str
    version: str
    database_connected: bool
    llm_service_connected: bool
    opencv_service_connected: bool
    uptime: float
    memory_usage: Dict[str, Any]
    storage_usage: Dict[str, Any]

class LLMRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    model_preference: Optional[str] = "auto"

class LLMResponse(BaseModel):
    text: str
    model_used: str
    tokens_used: int
    processing_time: float

class PlateAnalysisRequest(BaseModel):
    image_path: str
    location: Optional[str] = None

class PlateAnalysisResponse(BaseModel):
    plate_number: str
    confidence: float
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_color: Optional[str] = None
    timestamp: str
    analysis: Optional[str] = None

# API endpoints
@app.get("/", response_model=SystemStatusResponse)
async def root():
    """Get the status of the core system"""
    # Get memory usage
    import psutil
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Get storage usage
    storage = psutil.disk_usage("/")
    
    # Check database connection
    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
            db_connected = True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
    
    # Check LLM service connection
    llm_connected = False
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/", timeout=2)
        llm_connected = response.status_code == 200
    except Exception as e:
        logger.error(f"LLM service connection error: {e}")
    
    # Check OpenCV service connection
    opencv_connected = False
    try:
        response = requests.get(f"{OPENCV_SERVICE_URL}/status", timeout=2)
        opencv_connected = response.status_code == 200
    except Exception as e:
        logger.error(f"OpenCV service connection error: {e}")
    
    return {
        "status": "running",
        "version": "1.0.0",
        "database_connected": db_connected,
        "llm_service_connected": llm_connected,
        "opencv_service_connected": opencv_connected,
        "uptime": time.time() - process.create_time(),
        "memory_usage": {
            "rss": memory_info.rss / (1024 * 1024),  # MB
            "vms": memory_info.vms / (1024 * 1024),  # MB
            "percent": process.memory_percent()
        },
        "storage_usage": {
            "total": storage.total / (1024 * 1024 * 1024),  # GB
            "used": storage.used / (1024 * 1024 * 1024),  # GB
            "free": storage.free / (1024 * 1024 * 1024),  # GB
            "percent": storage.percent
        }
    }

# Plate recognition endpoints
@app.post("/plates", response_model=PlateRecognitionResponse)
async def create_plate_recognition(plate: PlateRecognitionCreate, db: sa.orm.Session = Depends(get_db)):
    """Create a new plate recognition record"""
    db_plate = PlateRecognition(
        plate_number=plate.plate_number,
        confidence=plate.confidence,
        image_path=plate.image_path,
        location=plate.location,
        vehicle_data=plate.vehicle_data
    )
    db.add(db_plate)
    db.commit()
    db.refresh(db_plate)
    
    return {
        "id": db_plate.id,
        "plate_number": db_plate.plate_number,
        "confidence": db_plate.confidence,
        "timestamp": db_plate.timestamp.isoformat(),
        "image_path": db_plate.image_path,
        "location": db_plate.location,
        "vehicle_data": db_plate.vehicle_data
    }

@app.get("/plates", response_model=List[PlateRecognitionResponse])
async def get_plate_recognitions(skip: int = 0, limit: int = 100, db: sa.orm.Session = Depends(get_db)):
    """Get all plate recognition records"""
    plates = db.query(PlateRecognition).order_by(PlateRecognition.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": plate.id,
        "plate_number": plate.plate_number,
        "confidence": plate.confidence,
        "timestamp": plate.timestamp.isoformat(),
        "image_path": plate.image_path,
        "location": plate.location,
        "vehicle_data": plate.vehicle_data
    } for plate in plates]

@app.get("/plates/{plate_id}", response_model=PlateRecognitionResponse)
async def get_plate_recognition(plate_id: int, db: sa.orm.Session = Depends(get_db)):
    """Get a specific plate recognition record"""
    plate = db.query(PlateRecognition).filter(PlateRecognition.id == plate_id).first()
    if plate is None:
        raise HTTPException(status_code=404, detail="Plate recognition not found")
    
    return {
        "id": plate.id,
        "plate_number": plate.plate_number,
        "confidence": plate.confidence,
        "timestamp": plate.timestamp.isoformat(),
        "image_path": plate.image_path,
        "location": plate.location,
        "vehicle_data": plate.vehicle_data
    }

# Security event endpoints
@app.post("/security-events", response_model=SecurityEventResponse)
async def create_security_event(event: SecurityEventCreate, db: sa.orm.Session = Depends(get_db)):
    """Create a new security event"""
    db_event = SecurityEvent(
        event_type=event.event_type,
        severity=event.severity,
        description=event.description,
        image_path=event.image_path,
        location=event.location
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return {
        "id": db_event.id,
        "event_type": db_event.event_type,
        "severity": db_event.severity,
        "timestamp": db_event.timestamp.isoformat(),
        "description": db_event.description,
        "image_path": db_event.image_path,
        "location": db_event.location,
        "is_resolved": db_event.is_resolved
    }

@app.get("/security-events", response_model=List[SecurityEventResponse])
async def get_security_events(skip: int = 0, limit: int = 100, db: sa.orm.Session = Depends(get_db)):
    """Get all security events"""
    events = db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": event.id,
        "event_type": event.event_type,
        "severity": event.severity,
        "timestamp": event.timestamp.isoformat(),
        "description": event.description,
        "image_path": event.image_path,
        "location": event.location,
        "is_resolved": event.is_resolved
    } for event in events]

@app.put("/security-events/{event_id}/resolve", response_model=SecurityEventResponse)
async def resolve_security_event(event_id: int, db: sa.orm.Session = Depends(get_db)):
    """Mark a security event as resolved"""
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Security event not found")
    
    event.is_resolved = True
    db.commit()
    db.refresh(event)
    
    return {
        "id": event.id,
        "event_type": event.event_type,
        "severity": event.severity,
        "timestamp": event.timestamp.isoformat(),
        "description": event.description,
        "image_path": event.image_path,
        "location": event.location,
        "is_resolved": event.is_resolved
    }

# Vehicle data endpoints
@app.post("/vehicle-data", response_model=VehicleDataResponse)
async def create_vehicle_data(data: VehicleDataCreate, db: sa.orm.Session = Depends(get_db)):
    """Create a new vehicle data record"""
    db_data = VehicleData(
        speed=data.speed,
        battery_level=data.battery_level,
        temperature=data.temperature,
        location=data.location,
        data=data.data
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    
    return {
        "id": db_data.id,
        "timestamp": db_data.timestamp.isoformat(),
        "speed": db_data.speed,
        "battery_level": db_data.battery_level,
        "temperature": db_data.temperature,
        "location": db_data.location,
        "data": db_data.data
    }

@app.get("/vehicle-data", response_model=List[VehicleDataResponse])
async def get_vehicle_data(skip: int = 0, limit: int = 100, db: sa.orm.Session = Depends(get_db)):
    """Get all vehicle data records"""
    data = db.query(VehicleData).order_by(VehicleData.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": item.id,
        "timestamp": item.timestamp.isoformat(),
        "speed": item.speed,
        "battery_level": item.battery_level,
        "temperature": item.temperature,
        "location": item.location,
        "data": item.data
    } for item in data]

# System configuration endpoints
@app.get("/config/{key}", response_model=SystemConfigResponse)
async def get_system_config(key: str, db: sa.orm.Session = Depends(get_db)):
    """Get a system configuration value"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration key not found")
    
    return {
        "key": config.key,
        "value": config.value,
        "description": config.description,
        "updated_at": config.updated_at.isoformat()
    }

@app.put("/config/{key}", response_model=SystemConfigResponse)
async def update_system_config(key: str, config_update: SystemConfigUpdate, db: sa.orm.Session = Depends(get_db)):
    """Update a system configuration value"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config is None:
        # Create new config if it doesn't exist
        config = SystemConfig(key=key, value=config_update.value, description=config_update.description)
        db.add(config)
    else:
        # Update existing config
        config.value = config_update.value
        if config_update.description is not None:
            config.description = config_update.description
    
    db.commit()
    db.refresh(config)
    
    return {
        "key": config.key,
        "value": config.value,
        "description": config.description,
        "updated_at": config.updated_at.isoformat()
    }

# LLM integration endpoints
@app.post("/llm/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    """Generate text using the LLM service"""
    try:
        response = requests.post(
            f"{LLM_SERVICE_URL}/generate",
            json={
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "model_preference": request.model_preference
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"LLM service error: {response.text}"
            )
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"LLM service connection error: {str(e)}")

# Plate analysis endpoints
@app.post("/plates/analyze", response_model=PlateAnalysisResponse)
async def analyze_plate(request: PlateAnalysisRequest):
    """Analyze a license plate image"""
    try:
        # First, use OpenCV service to recognize the plate
        opencv_response = requests.post(
            f"{OPENCV_SERVICE_URL}/recognize-plate",
            json={"image_path": request.image_path},
            timeout=10
        )
        
        if opencv_response.status_code != 200:
            raise HTTPException(
                status_code=opencv_response.status_code,
                detail=f"OpenCV service error: {opencv_response.text}"
            )
        
        plate_data = opencv_response.json()
        
        # Then, use LLM to analyze the plate data
        prompt = f"""
        Analyze this license plate information:
        - Plate Number: {plate_data['plate_number']}
        - Confidence: {plate_data['confidence']}
        - Location: {request.location or 'Unknown'}
        
        Provide information about the vehicle if possible, and any relevant analysis.
        """
        
        llm_response = requests.post(
            f"{LLM_SERVICE_URL}/generate",
            json={
                "prompt": prompt,
                "max_tokens": 256,
                "temperature": 0.7,
                "model_preference": "auto"
            },
            timeout=30
        )
        
        if llm_response.status_code != 200:
            raise HTTPException(
                status_code=llm_response.status_code,
                detail=f"LLM service error: {llm_response.text}"
            )
        
        llm_data = llm_response.json()
        
        # Save the plate recognition to the database
        db = SessionLocal()
        try:
            db_plate = PlateRecognition(
                plate_number=plate_data['plate_number'],
                confidence=plate_data['confidence'],
                image_path=request.image_path,
                location=request.location
            )
            db.add(db_plate)
            db.commit()
            db.refresh(db_plate)
        finally:
            db.close()
        
        # Extract vehicle information from LLM response
        analysis_text = llm_data['text']
        
        # Simple extraction of vehicle make/model/color from analysis text
        vehicle_make = None
        vehicle_model = None
        vehicle_color = None
        
        if "make:" in analysis_text.lower():
            make_parts = analysis_text.lower().split("make:")
            if len(make_parts) > 1:
                vehicle_make = make_parts[1].split("\n")[0].strip()
        
        if "model:" in analysis_text.lower():
            model_parts = analysis_text.lower().split("model:")
            if len(model_parts) > 1:
                vehicle_model = model_parts[1].split("\n")[0].strip()
        
        if "color:" in analysis_text.lower():
            color_parts = analysis_text.lower().split("color:")
            if len(color_parts) > 1:
                vehicle_color = color_parts[1].split("\n")[0].strip()
        
        return {
            "plate_number": plate_data['plate_number'],
            "confidence": plate_data['confidence'],
            "vehicle_make": vehicle_make,
            "vehicle_model": vehicle_model,
            "vehicle_color": vehicle_color,
            "timestamp": db_plate.timestamp.isoformat(),
            "analysis": analysis_text
        }
    
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Service connection error: {str(e)}")

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
    uvicorn.run("app:app", host="0.0.0.0", port=8000, log_level=log_level.lower())
