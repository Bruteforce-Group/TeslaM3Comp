#!/usr/bin/env python3
# OpenCV Server for Tesla Model 3 Raspberry Pi 5 Integration
# This server provides image processing and license plate recognition capabilities

import os
import sys
import time
import json
import logging
from typing import Dict, List, Optional, Union, Any
import threading
import queue
import base64
from io import BytesIO

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
from pydantic import BaseModel, Field
from loguru import logger
import requests
from PIL import Image
import easyocr

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stderr, level=log_level)
logger.add("/app/logs/opencv_server.log", rotation="10 MB", level=log_level)

# Load environment variables
CAMERA_SOURCE = os.environ.get("CAMERA_SOURCE", "/dev/video0")
ENABLE_GPU = os.environ.get("ENABLE_GPU", "false").lower() == "true"

# Initialize FastAPI app
app = FastAPI(
    title="Tesla Model 3 OpenCV API",
    description="API for image processing and license plate recognition",
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

# Initialize EasyOCR reader
reader = None
reader_loading = False
reader_load_error = None
reader_load_queue = queue.Queue()

# Camera capture
camera = None
camera_lock = threading.Lock()

# Pydantic models for API
class ImageProcessRequest(BaseModel):
    image_path: str
    process_type: str = "plate_recognition"  # plate_recognition, object_detection, etc.
    parameters: Optional[Dict[str, Any]] = None

class ImageProcessResponse(BaseModel):
    success: bool
    message: str
    results: Dict[str, Any]
    processing_time: float

class PlateRecognitionRequest(BaseModel):
    image_path: str
    min_confidence: Optional[float] = 0.7

class PlateRecognitionResponse(BaseModel):
    plate_number: str
    confidence: float
    bounding_box: Optional[List[List[int]]] = None
    processing_time: float

class CameraStatusResponse(BaseModel):
    camera_connected: bool
    camera_source: str
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    fps: Optional[float] = None

class SystemStatusResponse(BaseModel):
    status: str
    ocr_loaded: bool
    camera_connected: bool
    gpu_enabled: bool
    memory_usage: Dict[str, Any]
    uptime: float

# Startup event
@app.on_event("startup")
async def startup_event():
    global reader_loading
    # Start OCR loading in background
    reader_loading = True
    threading.Thread(target=load_ocr, daemon=True).start()

# Load OCR in a separate thread
def load_ocr():
    global reader, reader_loading, reader_load_error
    try:
        logger.info("Loading EasyOCR reader")
        start_time = time.time()
        
        # Initialize EasyOCR with GPU if enabled
        reader = easyocr.Reader(['en'], gpu=ENABLE_GPU)
        
        load_time = time.time() - start_time
        logger.info(f"EasyOCR reader loaded successfully in {load_time:.2f} seconds")
        reader_loading = False
        reader_load_error = None
        reader_load_queue.put(True)
    except Exception as e:
        logger.error(f"Error loading EasyOCR reader: {e}")
        reader_loading = False
        reader_load_error = str(e)
        reader_load_queue.put(False)

# Wait for OCR to load
async def wait_for_ocr():
    if reader is not None:
        return True
    
    if not reader_loading and reader_load_error is not None:
        raise HTTPException(status_code=500, detail=f"OCR failed to load: {reader_load_error}")
    
    try:
        # Wait for up to 30 seconds for OCR to load
        result = reader_load_queue.get(timeout=30)
        return result
    except queue.Empty:
        raise HTTPException(status_code=503, detail="OCR is still loading, please try again later")

# Initialize camera
def init_camera():
    global camera
    try:
        with camera_lock:
            if camera is not None:
                # Release existing camera
                camera.release()
            
            # Initialize camera
            if CAMERA_SOURCE.isdigit():
                camera = cv2.VideoCapture(int(CAMERA_SOURCE))
            else:
                camera = cv2.VideoCapture(CAMERA_SOURCE)
            
            # Check if camera opened successfully
            if not camera.isOpened():
                logger.error(f"Failed to open camera: {CAMERA_SOURCE}")
                camera = None
                return False
            
            # Set camera properties
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            camera.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info(f"Camera initialized successfully: {CAMERA_SOURCE}")
            return True
    except Exception as e:
        logger.error(f"Error initializing camera: {e}")
        camera = None
        return False

# Get camera frame
def get_camera_frame():
    global camera
    try:
        with camera_lock:
            if camera is None or not camera.isOpened():
                if not init_camera():
                    return None
            
            ret, frame = camera.read()
            if not ret:
                logger.warning("Failed to read frame from camera")
                return None
            
            return frame
    except Exception as e:
        logger.error(f"Error getting camera frame: {e}")
        return None

# Process image for license plate recognition
def process_image_for_plate(image_path, min_confidence=0.7):
    start_time = time.time()
    
    try:
        # Load image
        if image_path.startswith("http"):
            # Download image from URL
            response = requests.get(image_path)
            img = Image.open(BytesIO(response.content))
            img = np.array(img)
        else:
            # Load image from file
            img = cv2.imread(image_path)
        
        if img is None:
            raise Exception(f"Failed to load image from {image_path}")
        
        # Convert to RGB if needed
        if len(img.shape) == 3 and img.shape[2] == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = img
        
        # Use EasyOCR to detect text
        results = reader.readtext(img_rgb)
        
        # Filter results for license plates
        plates = []
        for (bbox, text, prob) in results:
            if prob >= min_confidence:
                # Check if text matches license plate pattern (alphanumeric, typically 5-8 chars)
                if len(text) >= 5 and len(text) <= 8 and any(c.isalpha() for c in text) and any(c.isdigit() for c in text):
                    plates.append((bbox, text, prob))
        
        # If no plates found, return the highest confidence text
        if not plates and results:
            plates = [max(results, key=lambda x: x[2])]
        
        processing_time = time.time() - start_time
        
        if not plates:
            return {
                "plate_number": "",
                "confidence": 0.0,
                "bounding_box": None,
                "processing_time": processing_time
            }
        
        # Return the highest confidence plate
        best_plate = max(plates, key=lambda x: x[2])
        bbox, text, prob = best_plate
        
        return {
            "plate_number": text,
            "confidence": prob,
            "bounding_box": bbox,
            "processing_time": processing_time
        }
    
    except Exception as e:
        logger.error(f"Error processing image for plate recognition: {e}")
        processing_time = time.time() - start_time
        
        return {
            "plate_number": "",
            "confidence": 0.0,
            "bounding_box": None,
            "processing_time": processing_time,
            "error": str(e)
        }

# API endpoints
@app.get("/status", response_model=SystemStatusResponse)
async def get_status():
    """Get the status of the OpenCV server"""
    # Get memory usage
    import psutil
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Check camera connection
    camera_connected = False
    with camera_lock:
        if camera is not None and camera.isOpened():
            camera_connected = True
        elif init_camera():
            camera_connected = True
    
    return {
        "status": "loading" if reader_loading else "ready" if reader is not None else "error",
        "ocr_loaded": reader is not None,
        "camera_connected": camera_connected,
        "gpu_enabled": ENABLE_GPU,
        "memory_usage": {
            "rss": memory_info.rss / (1024 * 1024),  # MB
            "vms": memory_info.vms / (1024 * 1024),  # MB
            "percent": process.memory_percent()
        },
        "uptime": time.time() - process.create_time()
    }

@app.get("/camera/status", response_model=CameraStatusResponse)
async def get_camera_status():
    """Get the status of the camera"""
    with camera_lock:
        if camera is None or not camera.isOpened():
            if not init_camera():
                return {
                    "camera_connected": False,
                    "camera_source": CAMERA_SOURCE,
                    "frame_width": None,
                    "frame_height": None,
                    "fps": None
                }
        
        frame_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = camera.get(cv2.CAP_PROP_FPS)
        
        return {
            "camera_connected": True,
            "camera_source": CAMERA_SOURCE,
            "frame_width": frame_width,
            "frame_height": frame_height,
            "fps": fps
        }

@app.post("/recognize-plate", response_model=PlateRecognitionResponse)
async def recognize_plate(request: PlateRecognitionRequest):
    """Recognize license plate in an image"""
    # Wait for OCR to load
    await wait_for_ocr()
    
    # Process image for plate recognition
    result = process_image_for_plate(request.image_path, request.min_confidence)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.get("/camera/frame")
async def get_frame():
    """Get a single frame from the camera"""
    frame = get_camera_frame()
    if frame is None:
        raise HTTPException(status_code=500, detail="Failed to get camera frame")
    
    # Encode frame as JPEG
    _, buffer = cv2.imencode(".jpg", frame)
    io_buf = BytesIO(buffer)
    
    return StreamingResponse(io_buf, media_type="image/jpeg")

@app.post("/process-image", response_model=ImageProcessResponse)
async def process_image(request: ImageProcessRequest):
    """Process an image with various computer vision techniques"""
    # Wait for OCR to load
    await wait_for_ocr()
    
    start_time = time.time()
    
    try:
        if request.process_type == "plate_recognition":
            # Process image for plate recognition
            plate_result = process_image_for_plate(
                request.image_path,
                request.parameters.get("min_confidence", 0.7) if request.parameters else 0.7
            )
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "message": "Image processed successfully",
                "results": plate_result,
                "processing_time": processing_time
            }
        
        elif request.process_type == "object_detection":
            # Not implemented yet
            raise HTTPException(status_code=501, detail="Object detection not implemented yet")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown process type: {request.process_type}")
    
    except Exception as e:
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "message": f"Error processing image: {str(e)}",
            "results": {},
            "processing_time": processing_time
        }

# Error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    global camera
    # Release camera
    with camera_lock:
        if camera is not None:
            camera.release()
            camera = None

# Main entry point
if __name__ == "__main__":
    uvicorn.run("opencv_server:app", host="0.0.0.0", port=8081, log_level=log_level.lower())
