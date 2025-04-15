import axios from 'axios';

// Base URLs for different services
const CORE_API_URL = '/api/core';
const LLM_API_URL = '/api/llm';
const OPENCV_API_URL = '/api/opencv';
const OBD_API_URL = '/api/obd';

// Create axios instances for each service
const coreApi = axios.create({
  baseURL: CORE_API_URL,
  timeout: 10000,
});

const llmApi = axios.create({
  baseURL: LLM_API_URL,
  timeout: 30000, // Longer timeout for LLM operations
});

const opencvApi = axios.create({
  baseURL: OPENCV_API_URL,
  timeout: 10000,
});

const obdApi = axios.create({
  baseURL: OBD_API_URL,
  timeout: 5000,
});

// Core API functions
export const getSystemStatus = async () => {
  const response = await coreApi.get('/');
  return response.data;
};

export const getPlateRecognitions = async (skip = 0, limit = 100) => {
  const response = await coreApi.get(`/plates?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const getSecurityEvents = async (skip = 0, limit = 100) => {
  const response = await coreApi.get(`/security-events?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const resolveSecurityEvent = async (eventId) => {
  const response = await coreApi.put(`/security-events/${eventId}/resolve`);
  return response.data;
};

export const getVehicleData = async (skip = 0, limit = 100) => {
  const response = await coreApi.get(`/vehicle-data?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const getSystemConfig = async (key) => {
  const response = await coreApi.get(`/config/${key}`);
  return response.data;
};

export const updateSystemConfig = async (key, value, description) => {
  const response = await coreApi.put(`/config/${key}`, { value, description });
  return response.data;
};

export const analyzePlate = async (imagePath, location) => {
  const response = await coreApi.post('/plates/analyze', { image_path: imagePath, location });
  return response.data;
};

// LLM API functions
export const getLLMStatus = async () => {
  const response = await llmApi.get('/');
  return response.data;
};

export const generateText = async (prompt, maxTokens = 512, temperature = 0.7, modelPreference = 'auto') => {
  const response = await llmApi.post('/generate', {
    prompt,
    max_tokens: maxTokens,
    temperature,
    model_preference: modelPreference,
  });
  return response.data;
};

export const setApiKey = async (provider, apiKey) => {
  const response = await llmApi.post('/api-keys', { provider, api_key: apiKey });
  return response.data;
};

export const deleteApiKey = async (provider) => {
  const response = await llmApi.delete(`/api-keys/${provider}`);
  return response.data;
};

export const reloadModel = async () => {
  const response = await llmApi.post('/reload-model');
  return response.data;
};

// OpenCV API functions
export const getOpenCVStatus = async () => {
  const response = await opencvApi.get('/status');
  return response.data;
};

export const getCameraStatus = async () => {
  const response = await opencvApi.get('/camera/status');
  return response.data;
};

export const getCameraFrame = async () => {
  const response = await opencvApi.get('/camera/frame', { responseType: 'blob' });
  return URL.createObjectURL(response.data);
};

export const recognizePlate = async (imagePath, minConfidence = 0.7) => {
  const response = await opencvApi.post('/recognize-plate', { image_path: imagePath, min_confidence: minConfidence });
  return response.data;
};

export const processImage = async (imagePath, processType = 'plate_recognition', parameters = {}) => {
  const response = await opencvApi.post('/process-image', { image_path: imagePath, process_type: processType, parameters });
  return response.data;
};

// OBD API functions
export const getOBDStatus = async () => {
  const response = await obdApi.get('/status');
  return response.data;
};

export const getOBDData = async () => {
  const response = await obdApi.get('/data');
  return response.data;
};

export const getOBDDiagnostics = async () => {
  const response = await obdApi.get('/diagnostics');
  return response.data;
};

export default {
  getSystemStatus,
  getPlateRecognitions,
  getSecurityEvents,
  resolveSecurityEvent,
  getVehicleData,
  getSystemConfig,
  updateSystemConfig,
  analyzePlate,
  getLLMStatus,
  generateText,
  setApiKey,
  deleteApiKey,
  reloadModel,
  getOpenCVStatus,
  getCameraStatus,
  getCameraFrame,
  recognizePlate,
  processImage,
  getOBDStatus,
  getOBDData,
  getOBDDiagnostics,
};
