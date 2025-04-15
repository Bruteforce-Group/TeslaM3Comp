import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  CardHeader, 
  Button,
  CircularProgress,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  BatteryChargingFull as BatteryIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Camera as CameraIcon,
  Psychology as LLMIcon,
  DirectionsCar as CarIcon
} from '@mui/icons-material';
import { getCameraFrame, getSystemStatus, getLLMStatus, getOBDStatus } from '../services/api';

const Dashboard = ({ systemStatus }) => {
  const [cameraImage, setCameraImage] = useState(null);
  const [loadingCamera, setLoadingCamera] = useState(false);
  const [llmStatus, setLlmStatus] = useState(null);
  const [obdStatus, setObdStatus] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    // Load camera image
    const loadCameraImage = async () => {
      try {
        setLoadingCamera(true);
        const imageUrl = await getCameraFrame();
        setCameraImage(imageUrl);
      } catch (err) {
        console.error('Error loading camera image:', err);
      } finally {
        setLoadingCamera(false);
      }
    };

    // Load LLM status
    const loadLlmStatus = async () => {
      try {
        const status = await getLLMStatus();
        setLlmStatus(status);
      } catch (err) {
        console.error('Error loading LLM status:', err);
      }
    };

    // Load OBD status
    const loadObdStatus = async () => {
      try {
        const status = await getOBDStatus();
        setObdStatus(status);
      } catch (err) {
        console.error('Error loading OBD status:', err);
      }
    };

    loadCameraImage();
    loadLlmStatus();
    loadObdStatus();

    // Refresh camera image every 5 seconds
    const cameraInterval = setInterval(loadCameraImage, 5000);
    
    return () => {
      clearInterval(cameraInterval);
      // Revoke object URL to avoid memory leaks
      if (cameraImage) {
        URL.revokeObjectURL(cameraImage);
      }
    };
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      // Refresh all data
      const imageUrl = await getCameraFrame();
      setCameraImage(imageUrl);
      
      const llmStatusData = await getLLMStatus();
      setLlmStatus(llmStatusData);
      
      const obdStatusData = await getOBDStatus();
      setObdStatus(obdStatusData);
    } catch (err) {
      console.error('Error refreshing data:', err);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Button 
          variant="contained" 
          onClick={handleRefresh}
          disabled={refreshing}
          startIcon={refreshing ? <CircularProgress size={20} /> : null}
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* System Status Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="System Status" />
            <CardContent>
              {systemStatus ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Memory Usage
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <MemoryIcon sx={{ mr: 1 }} />
                        <Typography>
                          {systemStatus.memory_usage.rss.toFixed(2)} MB ({systemStatus.memory_usage.percent.toFixed(1)}%)
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Storage
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <StorageIcon sx={{ mr: 1 }} />
                        <Typography>
                          {systemStatus.storage_usage.used.toFixed(1)} GB / {systemStatus.storage_usage.total.toFixed(1)} GB ({systemStatus.storage_usage.percent}%)
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12}>
                    <Divider />
                    <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                      Services
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemIcon>
                          {systemStatus.database_connected ? <CheckIcon color="success" /> : <ErrorIcon color="error" />}
                        </ListItemIcon>
                        <ListItemText primary="Database" secondary={systemStatus.database_connected ? "Connected" : "Disconnected"} />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          {systemStatus.llm_service_connected ? <CheckIcon color="success" /> : <ErrorIcon color="error" />}
                        </ListItemIcon>
                        <ListItemText primary="LLM Service" secondary={systemStatus.llm_service_connected ? "Connected" : "Disconnected"} />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          {systemStatus.opencv_service_connected ? <CheckIcon color="success" /> : <ErrorIcon color="error" />}
                        </ListItemIcon>
                        <ListItemText primary="OpenCV Service" secondary={systemStatus.opencv_service_connected ? "Connected" : "Disconnected"} />
                      </ListItem>
                    </List>
                  </Grid>
                </Grid>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Camera Preview Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="Camera Preview" 
              action={
                <Chip 
                  icon={<CameraIcon />} 
                  label={loadingCamera ? "Loading..." : "Live"} 
                  color={loadingCamera ? "default" : "success"} 
                  variant="outlined" 
                />
              }
            />
            <CardContent>
              <Box 
                sx={{ 
                  height: 300, 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center',
                  bgcolor: 'background.default',
                  borderRadius: 1
                }}
              >
                {loadingCamera ? (
                  <CircularProgress />
                ) : cameraImage ? (
                  <img 
                    src={cameraImage} 
                    alt="Camera feed" 
                    style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} 
                  />
                ) : (
                  <Typography color="text.secondary">
                    Camera feed not available
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* LLM Status Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="LLM Status" 
              action={
                <Chip 
                  icon={<LLMIcon />} 
                  label={llmStatus?.model_loaded ? "Ready" : "Not Ready"} 
                  color={llmStatus?.model_loaded ? "success" : "error"} 
                  variant="outlined" 
                />
              }
            />
            <CardContent>
              {llmStatus ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Model
                      </Typography>
                      <Typography>
                        Llama 3 ({llmStatus.model_loaded ? "Loaded" : "Not Loaded"})
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Path: {llmStatus.model_path}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Memory Usage
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <MemoryIcon sx={{ mr: 1 }} />
                        <Typography>
                          {llmStatus.memory_usage.rss.toFixed(2)} MB ({llmStatus.memory_usage.percent.toFixed(1)}%)
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12}>
                    <Divider />
                    <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                      Available Providers
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {llmStatus.available_providers.map((provider) => (
                        <Chip key={provider} label={provider} />
                      ))}
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      Cloud Fallback: {llmStatus.cloud_fallback_enabled ? "Enabled" : "Disabled"}
                    </Typography>
                  </Grid>
                </Grid>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Vehicle Status Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="Vehicle Status" 
              action={
                <Chip 
                  icon={<CarIcon />} 
                  label={obdStatus?.connected ? "Connected" : "Disconnected"} 
                  color={obdStatus?.connected ? "success" : "error"} 
                  variant="outlined" 
                />
              }
            />
            <CardContent>
              {obdStatus ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Speed
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <SpeedIcon sx={{ mr: 1 }} />
                        <Typography>
                          {obdStatus.speed || 0} km/h
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Battery
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <BatteryIcon sx={{ mr: 1 }} />
                        <Typography>
                          {obdStatus.battery_level || 0}%
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12}>
                    <Divider />
                    <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                      Connection Details
                    </Typography>
                    <Typography variant="body2">
                      Device: {obdStatus.device || "Not connected"}
                    </Typography>
                    <Typography variant="body2">
                      Protocol: {obdStatus.protocol || "Unknown"}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Last Updated: {obdStatus.last_updated || "Never"}
                    </Typography>
                  </Grid>
                </Grid>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
