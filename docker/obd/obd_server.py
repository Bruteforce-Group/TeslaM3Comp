#!/usr/bin/env python3
# OBD Server for Tesla Model 3 Raspberry Pi 5 Integration
# This server provides vehicle data collection via OBD-II interface

import os
import sys
import time
import json
import logging
from typing import Dict, List, Optional, Union, Any
import threading
import queue
import datetime

import obd
from obd import OBDStatus
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field
from loguru import logger
import requests
import psutil

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stderr, level=log_level)
logger.add("/app/logs/obd_server.log", rotation="10 MB", level=log_level)

# Load environment variables
OBD_DEVICE = os.environ.get("OBD_DEVICE", "/dev/ttyUSB0")
CORE_API_URL = os.environ.get("CORE_API_URL", "http://core:8000")

# Initialize FastAPI app
app = FastAPI(
    title="Tesla Model 3 OBD API",
    description="API for vehicle data collection via OBD-II interface",
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

# OBD connection
obd_connection = None
obd_lock = threading.Lock()
obd_data_cache = {}
obd_data_cache_lock = threading.Lock()
obd_data_thread = None
obd_data_thread_running = False

# Pydantic models for API
class OBDStatusResponse(BaseModel):
    connected: bool
    status: str
    device: str
    protocol: Optional[str] = None
    port_name: Optional[str] = None
    baudrate: Optional[int] = None
    speed: Optional[float] = None
    battery_level: Optional[float] = None
    temperature: Optional[float] = None
    last_updated: Optional[str] = None

class OBDDataResponse(BaseModel):
    timestamp: str
    speed: Optional[float] = None
    rpm: Optional[float] = None
    coolant_temp: Optional[float] = None
    intake_temp: Optional[float] = None
    throttle_pos: Optional[float] = None
    engine_load: Optional[float] = None
    fuel_level: Optional[float] = None
    battery_voltage: Optional[float] = None
    ambient_air_temp: Optional[float] = None
    oil_temp: Optional[float] = None
    fuel_rate: Optional[float] = None
    fuel_pressure: Optional[float] = None
    timing_advance: Optional[float] = None
    dtc_count: Optional[int] = None
    maf: Optional[float] = None
    barometric_pressure: Optional[float] = None
    control_module_voltage: Optional[float] = None
    relative_throttle_pos: Optional[float] = None
    ambient_air_temp: Optional[float] = None
    commanded_equiv_ratio: Optional[float] = None
    relative_accel_pos: Optional[float] = None

class OBDDiagnosticsResponse(BaseModel):
    dtc_codes: List[str]
    mil_status: bool
    freeze_frame: Optional[Dict[str, Any]] = None
    timestamp: str

class SystemStatusResponse(BaseModel):
    status: str
    obd_connected: bool
    obd_status: str
    memory_usage: Dict[str, Any]
    uptime: float

# Initialize OBD connection
def init_obd_connection():
    global obd_connection
    try:
        with obd_lock:
            if obd_connection is not None:
                # Close existing connection
                obd_connection.close()
                obd_connection = None
            
            # Initialize connection
            logger.info(f"Connecting to OBD device: {OBD_DEVICE}")
            obd_connection = obd.OBD(OBD_DEVICE, fast=False)
            
            # Check connection status
            if obd_connection.status() == OBDStatus.CAR_CONNECTED:
                logger.info(f"Successfully connected to vehicle via OBD: {OBD_DEVICE}")
                logger.info(f"Protocol: {obd_connection.protocol_name()}")
                
                # Start data collection thread if not already running
                start_data_collection_thread()
                
                return True
            else:
                logger.warning(f"Failed to connect to vehicle via OBD: {OBD_DEVICE}, status: {obd_connection.status()}")
                obd_connection = None
                return False
    except Exception as e:
        logger.error(f"Error initializing OBD connection: {e}")
        obd_connection = None
        return False

# Get OBD connection status
def get_obd_status():
    global obd_connection
    with obd_lock:
        if obd_connection is None:
            return {
                "connected": False,
                "status": "Not connected",
                "device": OBD_DEVICE,
                "protocol": None,
                "port_name": None,
                "baudrate": None,
                "speed": None,
                "battery_level": None,
                "temperature": None,
                "last_updated": None
            }
        
        status_str = str(obd_connection.status())
        protocol = obd_connection.protocol_name() if obd_connection.status() == OBDStatus.CAR_CONNECTED else None
        port_name = obd_connection.port_name() if hasattr(obd_connection, 'port_name') else None
        baudrate = obd_connection.baudrate if hasattr(obd_connection, 'baudrate') else None
        
        # Get cached data
        with obd_data_cache_lock:
            speed = obd_data_cache.get('speed', None)
            battery_level = obd_data_cache.get('battery_level', None)
            temperature = obd_data_cache.get('coolant_temp', None)
            last_updated = obd_data_cache.get('timestamp', None)
        
        return {
            "connected": obd_connection.status() == OBDStatus.CAR_CONNECTED,
            "status": status_str,
            "device": OBD_DEVICE,
            "protocol": protocol,
            "port_name": port_name,
            "baudrate": baudrate,
            "speed": speed,
            "battery_level": battery_level,
            "temperature": temperature,
            "last_updated": last_updated
        }

# Data collection thread
def obd_data_collection_thread():
    global obd_connection, obd_data_thread_running
    logger.info("Starting OBD data collection thread")
    
    # Define commands to query
    commands = [
        obd.commands.SPEED,
        obd.commands.RPM,
        obd.commands.COOLANT_TEMP,
        obd.commands.INTAKE_TEMP,
        obd.commands.THROTTLE_POS,
        obd.commands.ENGINE_LOAD,
        obd.commands.FUEL_LEVEL,
        obd.commands.CONTROL_MODULE_VOLTAGE,
        obd.commands.AMBIANT_AIR_TEMP,
        obd.commands.OIL_TEMP,
        obd.commands.FUEL_RATE,
        obd.commands.FUEL_PRESSURE,
        obd.commands.TIMING_ADVANCE,
        obd.commands.GET_DTC,
        obd.commands.MAF,
        obd.commands.BAROMETRIC_PRESSURE,
        obd.commands.RELATIVE_THROTTLE_POS,
        obd.commands.COMMANDED_EQUIV_RATIO,
        obd.commands.RELATIVE_ACCEL_POS
    ]
    
    while obd_data_thread_running:
        try:
            with obd_lock:
                if obd_connection is None or obd_connection.status() != OBDStatus.CAR_CONNECTED:
                    # Try to reconnect
                    if not init_obd_connection():
                        time.sleep(5)
                        continue
            
            # Query each command and update cache
            data = {}
            data['timestamp'] = datetime.datetime.now().isoformat()
            
            with obd_lock:
                for command in commands:
                    try:
                        response = obd_connection.query(command)
                        if response.is_null():
                            continue
                        
                        # Extract value based on command
                        if command == obd.commands.SPEED:
                            # Convert to km/h if needed
                            data['speed'] = response.value.magnitude
                        elif command == obd.commands.RPM:
                            data['rpm'] = response.value.magnitude
                        elif command == obd.commands.COOLANT_TEMP:
                            data['coolant_temp'] = response.value.magnitude
                        elif command == obd.commands.INTAKE_TEMP:
                            data['intake_temp'] = response.value.magnitude
                        elif command == obd.commands.THROTTLE_POS:
                            data['throttle_pos'] = response.value.magnitude
                        elif command == obd.commands.ENGINE_LOAD:
                            data['engine_load'] = response.value.magnitude
                        elif command == obd.commands.FUEL_LEVEL:
                            data['fuel_level'] = response.value.magnitude
                        elif command == obd.commands.CONTROL_MODULE_VOLTAGE:
                            data['battery_voltage'] = response.value.magnitude
                            # Estimate battery level (very rough approximation)
                            if response.value.magnitude > 0:
                                # For Tesla, this might be different, but for demonstration
                                battery_min = 10.5  # Volts
                                battery_max = 14.4  # Volts
                                battery_range = battery_max - battery_min
                                battery_level = min(100, max(0, (response.value.magnitude - battery_min) / battery_range * 100))
                                data['battery_level'] = battery_level
                        elif command == obd.commands.AMBIANT_AIR_TEMP:
                            data['ambient_air_temp'] = response.value.magnitude
                        elif command == obd.commands.OIL_TEMP:
                            data['oil_temp'] = response.value.magnitude
                        elif command == obd.commands.FUEL_RATE:
                            data['fuel_rate'] = response.value.magnitude
                        elif command == obd.commands.FUEL_PRESSURE:
                            data['fuel_pressure'] = response.value.magnitude
                        elif command == obd.commands.TIMING_ADVANCE:
                            data['timing_advance'] = response.value.magnitude
                        elif command == obd.commands.GET_DTC:
                            data['dtc_codes'] = response.value
                            data['dtc_count'] = len(response.value) if response.value else 0
                        elif command == obd.commands.MAF:
                            data['maf'] = response.value.magnitude
                        elif command == obd.commands.BAROMETRIC_PRESSURE:
                            data['barometric_pressure'] = response.value.magnitude
                        elif command == obd.commands.RELATIVE_THROTTLE_POS:
                            data['relative_throttle_pos'] = response.value.magnitude
                        elif command == obd.commands.COMMANDED_EQUIV_RATIO:
                            data['commanded_equiv_ratio'] = response.value.magnitude
                        elif command == obd.commands.RELATIVE_ACCEL_POS:
                            data['relative_accel_pos'] = response.value.magnitude
                    except Exception as e:
                        logger.debug(f"Error querying {command}: {e}")
            
            # Update cache
            with obd_data_cache_lock:
                obd_data_cache.update(data)
            
            # Send data to core API
            try:
                requests.post(
                    f"{CORE_API_URL}/vehicle-data",
                    json={
                        "speed": data.get('speed'),
                        "battery_level": data.get('battery_level'),
                        "temperature": data.get('coolant_temp'),
                        "data": data
                    },
                    timeout=5
                )
            except Exception as e:
                logger.warning(f"Error sending data to core API: {e}")
            
            # Sleep for a bit
            time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error in OBD data collection thread: {e}")
            time.sleep(5)

# Start data collection thread
def start_data_collection_thread():
    global obd_data_thread, obd_data_thread_running
    if obd_data_thread is None or not obd_data_thread.is_alive():
        obd_data_thread_running = True
        obd_data_thread = threading.Thread(target=obd_data_collection_thread, daemon=True)
        obd_data_thread.start()

# Stop data collection thread
def stop_data_collection_thread():
    global obd_data_thread_running
    obd_data_thread_running = False
    if obd_data_thread is not None:
        obd_data_thread.join(timeout=5)

# API endpoints
@app.get("/status", response_model=SystemStatusResponse)
async def get_status():
    """Get the status of the OBD server"""
    # Get memory usage
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Get OBD status
    obd_status = get_obd_status()
    
    return {
        "status": "running",
        "obd_connected": obd_status["connected"],
        "obd_status": obd_status["status"],
        "memory_usage": {
            "rss": memory_info.rss / (1024 * 1024),  # MB
            "vms": memory_info.vms / (1024 * 1024),  # MB
            "percent": process.memory_percent()
        },
        "uptime": time.time() - process.create_time()
    }

@app.get("/connection", response_model=OBDStatusResponse)
async def get_connection_status():
    """Get the status of the OBD connection"""
    return get_obd_status()

@app.post("/connection/reconnect", response_model=OBDStatusResponse)
async def reconnect_obd():
    """Reconnect to the OBD device"""
    success = init_obd_connection()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to connect to OBD device")
    
    return get_obd_status()

@app.get("/data", response_model=OBDDataResponse)
async def get_obd_data():
    """Get the latest OBD data"""
    with obd_data_cache_lock:
        if not obd_data_cache:
            raise HTTPException(status_code=404, detail="No OBD data available")
        
        return {
            "timestamp": obd_data_cache.get('timestamp', datetime.datetime.now().isoformat()),
            "speed": obd_data_cache.get('speed'),
            "rpm": obd_data_cache.get('rpm'),
            "coolant_temp": obd_data_cache.get('coolant_temp'),
            "intake_temp": obd_data_cache.get('intake_temp'),
            "throttle_pos": obd_data_cache.get('throttle_pos'),
            "engine_load": obd_data_cache.get('engine_load'),
            "fuel_level": obd_data_cache.get('fuel_level'),
            "battery_voltage": obd_data_cache.get('battery_voltage'),
            "ambient_air_temp": obd_data_cache.get('ambient_air_temp'),
            "oil_temp": obd_data_cache.get('oil_temp'),
            "fuel_rate": obd_data_cache.get('fuel_rate'),
            "fuel_pressure": obd_data_cache.get('fuel_pressure'),
            "timing_advance": obd_data_cache.get('timing_advance'),
            "dtc_count": obd_data_cache.get('dtc_count'),
            "maf": obd_data_cache.get('maf'),
            "barometric_pressure": obd_data_cache.get('barometric_pressure'),
            "control_module_voltage": obd_data_cache.get('battery_voltage'),
            "relative_throttle_pos": obd_data_cache.get('relative_throttle_pos'),
            "ambient_air_temp": obd_data_cache.get('ambient_air_temp'),
            "commanded_equiv_ratio": obd_data_cache.get('commanded_equiv_ratio'),
            "relative_accel_pos": obd_data_cache.get('relative_accel_pos')
        }

@app.get("/diagnostics", response_model=OBDDiagnosticsResponse)
async def get_diagnostics():
    """Get diagnostic trouble codes and related information"""
    global obd_connection
    
    with obd_lock:
        if obd_connection is None or obd_connection.status() != OBDStatus.CAR_CONNECTED:
            raise HTTPException(status_code=503, detail="OBD not connected")
        
        try:
            # Get DTCs
            dtc_response = obd_connection.query(obd.commands.GET_DTC)
            dtc_codes = dtc_response.value if not dtc_response.is_null() else []
            
            # Get MIL status
            mil_response = obd_connection.query(obd.commands.STATUS)
            mil_status = mil_response.value.MIL if not mil_response.is_null() else False
            
            # Get freeze frame data (if available)
            freeze_frame = {}
            try:
                for command in obd.commands.FREEZE_FRAME:
                    response = obd_connection.query(command)
                    if not response.is_null():
                        freeze_frame[command.name] = response.value.magnitude
            except Exception as e:
                logger.warning(f"Error getting freeze frame data: {e}")
            
            return {
                "dtc_codes": dtc_codes,
                "mil_status": mil_status,
                "freeze_frame": freeze_frame if freeze_frame else None,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting diagnostics: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting diagnostics: {str(e)}")

# Error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    # Initialize OBD connection
    init_obd_connection()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # Stop data collection thread
    stop_data_collection_thread()
    
    # Close OBD connection
    global obd_connection
    with obd_lock:
        if obd_connection is not None:
            obd_connection.close()
            obd_connection = None

# Main entry point
if __name__ == "__main__":
    uvicorn.run("obd_server:app", host="0.0.0.0", port=8082, log_level=log_level.lower())
