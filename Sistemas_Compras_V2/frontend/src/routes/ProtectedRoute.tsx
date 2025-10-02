import { Navigate } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';
import { Box, CircularProgress } from '@mui/material';
import type { ReactNode } from 'react';
import { authStorage } from '../features/auth/authStorage';

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { loading } = useAppSelector((s) => s.auth);
  const isAuthenticated = authStorage.isAuthenticated();
  
  // Se não há token, redireciona para login
  if (!isAuthenticated) {
    console.log('Não autenticado, redirecionando para login');
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
  
  // Se há token mas não há perfil, pode ser que o token seja inválido
  // Neste caso, o AuthInitializer já está tentando carregar o perfil
  // Então podemos renderizar o conteúdo normalmente
  
  return children;
}
