import React from 'react';
import { createTheme } from '@mui/material/styles';

// Create a theme instance matching Tesla's design aesthetic
const theme = createTheme({
  palette: {
    primary: {
      main: '#e82127', // Tesla red
      light: '#ff5f52',
      dark: '#af0000',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#393c41', // Tesla dark gray
      light: '#646669',
      dark: '#121517',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: '#171a20',
      secondary: '#5c5e62',
    },
  },
  typography: {
    fontFamily: '"Gotham SSm", "Helvetica Neue", Arial, sans-serif',
    h1: {
      fontWeight: 500,
      fontSize: '2.5rem',
    },
    h2: {
      fontWeight: 500,
      fontSize: '2rem',
    },
    h3: {
      fontWeight: 500,
      fontSize: '1.75rem',
    },
    h4: {
      fontWeight: 500,
      fontSize: '1.5rem',
    },
    h5: {
      fontWeight: 500,
      fontSize: '1.25rem',
    },
    h6: {
      fontWeight: 500,
      fontSize: '1rem',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          padding: '10px 24px',
          fontWeight: 500,
        },
        containedPrimary: {
          backgroundColor: '#e82127',
          '&:hover': {
            backgroundColor: '#d32f2f',
          },
        },
        outlinedPrimary: {
          borderColor: '#e82127',
          color: '#e82127',
          '&:hover': {
            backgroundColor: 'rgba(232, 33, 39, 0.04)',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
          borderRadius: 12,
        },
      },
    },
  },
});

export default theme;
