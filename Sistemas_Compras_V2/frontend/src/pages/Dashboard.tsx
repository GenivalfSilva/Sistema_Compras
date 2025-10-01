import { useEffect } from 'react';
import { Container, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';

export default function Dashboard() {
  const navigate = useNavigate();
  const perms = useAppSelector((s) => s.auth.profile?.permissions);

  useEffect(() => {
    // Redireciona automaticamente para a página principal de cada perfil
    if (perms?.is_admin) {
      navigate('/admin/usuarios', { replace: true });
      return;
    }
    if (perms?.can_manage_stock) {
      navigate('/estoque/requisicoes', { replace: true });
      return;
    }
    if (perms?.can_manage_procurement) {
      navigate('/suprimentos/processar', { replace: true });
      return;
    }
    if (perms?.can_approve) {
      navigate('/diretoria/aprovacoes', { replace: true });
      return;
    }
    if (perms?.can_create_solicitation) {
      navigate('/dashboard/solicitante', { replace: true });
      return;
    }
  }, [perms, navigate]);

  return (
    <Container sx={{ mt: 4 }}>
      <Typography variant="h4">Dashboard</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        Bem-vindo ao Sistema de Compras.
      </Typography>
    </Container>
  );
}
