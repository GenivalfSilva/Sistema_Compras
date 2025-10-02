import { createTheme } from '@mui/material/styles';

// Cores da Ziran (vermelho)
const ziranRed = {
  main: '#d91a2a', // Vermelho principal da Ziran
  light: '#e14554', // Versão mais clara
  dark: '#b01522', // Versão mais escura
  contrastText: '#fff', // Texto em contraste (branco)
};

// Criando o tema personalizado
const theme = createTheme({
  palette: {
    primary: ziranRed,
    secondary: {
      main: '#424242',
      light: '#6d6d6d',
      dark: '#1b1b1b',
      contrastText: '#fff',
    },
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
    },
    info: {
      main: '#2196f3',
    },
    success: {
      main: '#4caf50',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
    subtitle1: {
      fontWeight: 400,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
        },
        containedPrimary: {
          boxShadow: '0 4px 6px rgba(217, 26, 42, 0.25)',
          '&:hover': {
            boxShadow: '0 6px 10px rgba(217, 26, 42, 0.35)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
        },
      },
    },
  },
});

export default theme;
