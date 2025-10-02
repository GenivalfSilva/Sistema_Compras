import { useState, useEffect } from 'react';
import { Alert, AlertTitle, Box, Button, Typography } from '@mui/material';
import { useAppSelector } from '../app/hooks';

interface ErrorMessageProps {
  message: string;
  onClose?: () => void;
}

export default function ErrorMessage({ message, onClose }: ErrorMessageProps) {
  const [showDetails, setShowDetails] = useState(false);
  const profile = useAppSelector((s) => s.auth.profile);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  useEffect(() => {
    // Verifica se a mensagem contém informações sobre permissão
    if (message.includes('403') || message.includes('Forbidden') || message.includes('permissão')) {
      setErrorDetails(`
        Usuário: ${profile?.username || 'Não identificado'}
        Perfil: ${profile?.perfil || 'Não identificado'}
        Permissões necessárias: can_create_solicitation
      `);
    }
  }, [message, profile]);

  return (
    <Box sx={{ mb: 2 }}>
      <Alert 
        severity="error" 
        onClose={onClose}
        sx={{ mb: 1 }}
      >
        <AlertTitle>Erro</AlertTitle>
        {message}
      </Alert>
      
      {errorDetails && (
        <Box sx={{ mt: 1 }}>
          <Button 
            size="small" 
            variant="text" 
            color="error" 
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Ocultar detalhes' : 'Ver detalhes'}
          </Button>
          
          {showDetails && (
            <Box sx={{ mt: 1, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                {errorDetails}
              </Typography>
              <Typography variant="body2" sx={{ mt: 2, fontWeight: 'bold' }}>
                Solução:
              </Typography>
              <Typography variant="body2">
                Entre em contato com o administrador do sistema para adicionar a permissão "can_create_solicitation" ao seu perfil.
              </Typography>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}
