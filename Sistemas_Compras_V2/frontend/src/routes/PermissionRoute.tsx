import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { Typography, Box } from '@mui/material';
import { useAppSelector } from '../app/hooks';

interface Props {
  perm?: string; // permission key in profile.permissions
  children: ReactNode;
}

export default function PermissionRoute({ perm, children }: Props) {
  const profile = useAppSelector((s) => s.auth.profile);

  if (!profile) return <Navigate to="/login" replace />;

  if (!perm) return <>{children}</>; // if no perm required, just allow

  const allowed = Boolean(profile?.permissions?.[perm]);
  if (!allowed) {
    return (
      <Box p={3}>
        <Typography variant="h5" gutterBottom>
          403 - Acesso negado
        </Typography>
        <Typography variant="body1">
          Você não possui permissão para acessar esta página.
        </Typography>
      </Box>
    );
  }

  return <>{children}</>;
}
