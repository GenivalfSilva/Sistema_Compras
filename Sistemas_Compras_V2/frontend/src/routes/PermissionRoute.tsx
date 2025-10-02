import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { Typography, Box, CircularProgress } from '@mui/material';
import { useAppSelector } from '../app/hooks';
import { authStorage } from '../features/auth/authStorage';

interface Props {
  perm?: string; // permission key in profile.permissions
  children: ReactNode;
}

export default function PermissionRoute({ perm, children }: Props) {
  const { profile, loading } = useAppSelector((s) => s.auth);
  const token = authStorage.getTokens()?.access;
  const storedProfile = authStorage.getProfile();

  // Se não há token, redireciona para login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Se está carregando o perfil, mostra um indicador de carregamento
  if (loading) {
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
      </Box>
    );
  }

  // Se não há perfil no Redux, tenta usar o perfil do localStorage
  const currentProfile = profile || storedProfile;
  
  // Se não há perfil mesmo após verificar o localStorage, redireciona para login
  if (!currentProfile) {
    return <Navigate to="/login" replace />;
  }

  // Se não há permissão específica requerida, permite o acesso
  if (!perm) return <>{children}</>;

  // Verifica se o usuário tem a permissão necessária
  const allowed = Boolean(currentProfile?.permissions?.[perm]);
  if (!allowed) {
    return (
      <Box p={3} sx={{ textAlign: 'center', mt: 4 }}>
        <Typography variant="h5" gutterBottom color="error">
          403 - Acesso negado
        </Typography>
        <Typography variant="body1">
          Você não possui permissão para acessar esta página.
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Seu perfil: {currentProfile?.perfil || 'Usuário'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Permissão necessária: {perm}
        </Typography>
      </Box>
    );
  }

  return <>{children}</>;
}
