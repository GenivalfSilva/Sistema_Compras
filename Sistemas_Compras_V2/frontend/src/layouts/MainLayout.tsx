import { AppBar, Toolbar, Typography, Button, Container, Stack } from '@mui/material';
import { Outlet, Link as RouterLink } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { logout } from '../features/auth/authSlice';

export default function MainLayout() {
  const dispatch = useAppDispatch();
  const profile = useAppSelector((s) => s.auth.profile);
  const perms = profile?.permissions;
  const onLogout = async () => {
    await dispatch(logout());
    window.location.href = '/login';
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Sistema de Compras
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button color="inherit" component={RouterLink} to="/">
              Dashboard
            </Button>
            {perms?.can_create_solicitation && (
              <Button color="inherit" component={RouterLink} to="/dashboard/solicitante">
                Meu Painel
              </Button>
            )}
            <Button color="inherit" component={RouterLink} to="/solicitacoes">
              Solicitações
            </Button>
            {perms?.can_create_solicitation && (
              <Button color="inherit" component={RouterLink} to="/solicitacoes/nova">
                Nova Solicitação
              </Button>
            )}
            {perms?.can_manage_stock && (
              <Button color="inherit" component={RouterLink} to="/estoque/requisicoes">
                Estoque
              </Button>
            )}
            {perms?.can_manage_procurement && (
              <>
                <Button color="inherit" component={RouterLink} to="/suprimentos/processar">
                  Processar
                </Button>
                <Button color="inherit" component={RouterLink} to="/suprimentos/cotacoes">
                  Cotações
                </Button>
                <Button color="inherit" component={RouterLink} to="/suprimentos/pedidos">
                  Pedidos
                </Button>
              </>
            )}
            {perms?.can_approve && (
              <Button color="inherit" component={RouterLink} to="/diretoria/aprovacoes">
                Aprovações
              </Button>
            )}
            {perms?.is_admin && (
              <>
                <Button color="inherit" component={RouterLink} to="/admin/usuarios">
                  Usuários
                </Button>
                <Button color="inherit" component={RouterLink} to="/admin/configuracoes">
                  Configurações
                </Button>
                <Button color="inherit" component={RouterLink} to="/admin/auditoria">
                  Auditoria
                </Button>
              </>
            )}
          </Stack>
          <Button color="inherit" onClick={onLogout}>
            Sair
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 3 }}>
        <Outlet />
      </Container>
    </>
  );
}
