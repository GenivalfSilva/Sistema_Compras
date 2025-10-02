import { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Collapse, 
  Divider,
  Chip
} from '@mui/material';
import { useAppSelector } from '../../../app/hooks';
import { authStorage } from '../authStorage';
import BugReportIcon from '@mui/icons-material/BugReport';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

/**
 * Componente para depurar o estado da sessão
 * Mostra informações sobre tokens e perfil do usuário
 * Útil para desenvolvimento e depuração
 */
export default function SessionDebugger() {
  const [open, setOpen] = useState(false);
  const { tokens, profile, loading, error } = useAppSelector((s) => s.auth);
  
  // Verifica tokens e perfil no localStorage
  const accessToken = localStorage.getItem('access');
  const refreshToken = localStorage.getItem('refresh');
  const storedTokens = authStorage.getTokens();
  const storedProfile = authStorage.getProfile();
  
  // Só exibe em ambiente de desenvolvimento
  // No Vite, usamos import.meta.env ao invés de process.env
  const isDevelopment = (import.meta as any).env?.MODE === 'development' || true;
  if (!isDevelopment) {
    return null;
  }
  
  return (
    <Box 
      sx={{ 
        position: 'fixed', 
        bottom: 16, 
        right: 16, 
        zIndex: 9999 
      }}
    >
      <Button
        variant="contained"
        color="warning"
        size="small"
        startIcon={<BugReportIcon />}
        endIcon={open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        onClick={() => setOpen(!open)}
        sx={{ mb: 1 }}
      >
        Sessão
      </Button>
      
      <Collapse in={open}>
        <Paper 
          elevation={3} 
          sx={{ 
            p: 2, 
            width: 300, 
            maxHeight: 400, 
            overflow: 'auto',
            opacity: 0.9
          }}
        >
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Estado da Sessão
          </Typography>
          
          <Divider sx={{ my: 1 }} />
          
          <Typography variant="subtitle2" gutterBottom>
            Redux Store:
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Chip 
              label={`Loading: ${loading ? 'Sim' : 'Não'}`} 
              color={loading ? 'warning' : 'success'} 
              size="small" 
              sx={{ mr: 1, mb: 1 }} 
            />
            <Chip 
              label={`Token: ${tokens?.access ? 'Presente' : 'Ausente'}`} 
              color={tokens?.access ? 'success' : 'error'} 
              size="small" 
              sx={{ mr: 1, mb: 1 }} 
            />
            <Chip 
              label={`Refresh: ${tokens?.refresh ? 'Presente' : 'Ausente'}`} 
              color={tokens?.refresh ? 'success' : 'error'} 
              size="small" 
              sx={{ mr: 1, mb: 1 }} 
            />
            <Chip 
              label={`Perfil: ${profile ? 'Carregado' : 'Ausente'}`} 
              color={profile ? 'success' : 'error'} 
              size="small" 
              sx={{ mr: 1, mb: 1 }} 
            />
          </Box>
          
          <Typography variant="subtitle2" gutterBottom>
            LocalStorage:
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Chip 
              label={`Access: ${accessToken ? 'Presente' : 'Ausente'}`} 
              color={accessToken ? 'success' : 'error'} 
              size="small" 
              sx={{ mr: 1, mb: 1 }} 
            />
            <Chip 
              label={`Refresh: ${refreshToken ? 'Presente' : 'Ausente'}`} 
              color={refreshToken ? 'success' : 'error'} 
              size="small" 
              sx={{ mr: 1, mb: 1 }} 
            />
          </Box>
          
          <Typography variant="subtitle2" gutterBottom>
            AuthStorage:
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Chip 
              label={`Tokens: ${storedTokens ? 'Presente' : 'Ausente'}`} 
              color={storedTokens ? 'success' : 'error'} 
              size="small" 
              sx={{ mr: 1, mb: 1 }} 
            />
            <Chip 
              label={`Profile: ${storedProfile ? 'Presente' : 'Ausente'}`} 
              color={storedProfile ? 'success' : 'error'} 
              size="small" 
              sx={{ mr: 1, mb: 1 }} 
            />
          </Box>
          
          {profile && (
            <>
              <Typography variant="subtitle2" gutterBottom>
                Usuário:
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Nome:</strong> {profile.username}
                </Typography>
                <Typography variant="body2">
                  <strong>Perfil:</strong> {profile.perfil || 'N/A'}
                </Typography>
              </Box>
            </>
          )}
          
          {error && (
            <>
              <Typography variant="subtitle2" color="error" gutterBottom>
                Erro:
              </Typography>
              <Typography variant="body2" color="error">
                {typeof error === 'string' ? error : JSON.stringify(error)}
              </Typography>
            </>
          )}
          
          <Divider sx={{ my: 2 }} />
          
          <Button 
            variant="outlined" 
            color="error" 
            size="small"
            onClick={() => {
              authStorage.clearAuth();
              window.location.reload();
            }}
            sx={{ width: '100%' }}
          >
            Limpar Dados de Autenticação
          </Button>
        </Paper>
      </Collapse>
    </Box>
  );
}
