import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  Drawer, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  IconButton, 
  Container, 
  CircularProgress,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Camera as CameraIcon,
  DirectionsCar as CarIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Psychology as LLMIcon,
  Storage as DatabaseIcon,
  Monitoring as MonitoringIcon
} from '@mui/icons-material';

// Import pages
import Dashboard from './pages/Dashboard';
import CameraView from './pages/CameraView';
import PlateRecognition from './pages/PlateRecognition';
import SecurityAnalysis from './pages/SecurityAnalysis';
import VehicleData from './pages/VehicleData';
import LLMSettings from './pages/LLMSettings';
import SystemSettings from './pages/SystemSettings';
import Monitoring from './pages/Monitoring';

// Import API service
import { getSystemStatus } from './services/api';

const drawerWidth = 240;

function App() {
  const [open, setOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check system status on load
    const checkStatus = async () => {
      try {
        setLoading(true);
        const status = await getSystemStatus();
        setSystemStatus(status);
        setError(null);
      } catch (err) {
        console.error('Error fetching system status:', err);
        setError('Failed to connect to the system. Please check if all services are running.');
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
    // Set up interval to check status every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleDrawerToggle = () => {
    setOpen(!open);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Camera View', icon: <CameraIcon />, path: '/camera' },
    { text: 'Plate Recognition', icon: <CameraIcon />, path: '/plates' },
    { text: 'Security Analysis', icon: <SecurityIcon />, path: '/security' },
    { text: 'Vehicle Data', icon: <CarIcon />, path: '/vehicle' },
    { text: 'LLM Settings', icon: <LLMIcon />, path: '/llm' },
    { text: 'System Settings', icon: <SettingsIcon />, path: '/settings' },
    { text: 'Monitoring', icon: <MonitoringIcon />, path: '/monitoring' },
  ];

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Tesla Model 3
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem 
            button 
            key={item.text} 
            onClick={() => navigate(item.path)}
            selected={location.pathname === item.path}
          >
            <ListItemIcon>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </div>
  );

  if (loading && !systemStatus) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh' 
        }}
      >
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading system...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: 'white',
          color: 'text.primary'
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            Tesla Model 3 Raspberry Pi 5 Integration
          </Typography>
          {systemStatus && (
            <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
              <Typography variant="body2" sx={{ mr: 2 }}>
                Status: {systemStatus.status}
              </Typography>
              {systemStatus.llm_service_connected ? (
                <Typography variant="body2" color="success.main" sx={{ mr: 2 }}>
                  LLM: Connected
                </Typography>
              ) : (
                <Typography variant="body2" color="error.main" sx={{ mr: 2 }}>
                  LLM: Disconnected
                </Typography>
              )}
              {systemStatus.opencv_service_connected ? (
                <Typography variant="body2" color="success.main">
                  OpenCV: Connected
                </Typography>
              ) : (
                <Typography variant="body2" color="error.main">
                  OpenCV: Disconnected
                </Typography>
              )}
            </Box>
          )}
        </Toolbar>
      </AppBar>
      <Drawer
        variant="persistent"
        open={open}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        {drawer}
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${open ? drawerWidth : 0}px)` },
          ml: { sm: `${open ? drawerWidth : 0}px` },
          transition: (theme) => theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar />
        <Container maxWidth="xl">
          <Routes>
            <Route path="/" element={<Dashboard systemStatus={systemStatus} />} />
            <Route path="/camera" element={<CameraView />} />
            <Route path="/plates" element={<PlateRecognition />} />
            <Route path="/security" element={<SecurityAnalysis />} />
            <Route path="/vehicle" element={<VehicleData />} />
            <Route path="/llm" element={<LLMSettings />} />
            <Route path="/settings" element={<SystemSettings />} />
            <Route path="/monitoring" element={<Monitoring />} />
          </Routes>
        </Container>
      </Box>
      
      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;
