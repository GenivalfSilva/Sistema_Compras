import { useEffect, useState } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Container, 
  Stack, 
  Box, 
  Avatar, 
  Menu, 
  MenuItem, 
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  useTheme,
  useMediaQuery,
  Tooltip
} from '@mui/material';
import { Outlet, Link as RouterLink, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { logout, fetchProfile } from '../features/auth/authSlice';
import MenuIcon from '@mui/icons-material/Menu';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ListAltIcon from '@mui/icons-material/ListAlt';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import InventoryIcon from '@mui/icons-material/Inventory';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import PeopleIcon from '@mui/icons-material/People';
import SettingsIcon from '@mui/icons-material/Settings';
import HistoryIcon from '@mui/icons-material/History';
import LogoutIcon from '@mui/icons-material/Logout';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

export default function MainLayout() {
  const dispatch = useAppDispatch();
  const profile = useAppSelector((s) => s.auth.profile);
  const perms = profile?.permissions;
  const token = useAppSelector((s) => s.auth.tokens?.access) || localStorage.getItem('access');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();
  
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  
  // Carrega o perfil quando há token mas o profile ainda não foi carregado
  useEffect(() => {
    if (!profile && token) {
      dispatch(fetchProfile());
    }
  }, [profile, token, dispatch]);

  const onLogout = async () => {
    await dispatch(logout());
    window.location.href = '/login';
  };
  
  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };
  
  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };
  
  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  // Determina o caminho do dashboard com base no perfil
  const getDashboardPath = () => {
    if (profile?.perfil === 'Suprimentos' || profile?.permissions?.can_manage_procurement) {
      return '/dashboard/suprimentos';
    }
    if (profile?.perfil === 'Diretoria' || profile?.permissions?.can_approve) {
      return '/diretoria/aprovacoes';
    }
    if (profile?.perfil === 'Estoque' || profile?.permissions?.can_manage_stock) {
      return '/estoque/requisicoes';
    }
    return '/dashboard/solicitante';
  };

  // Navigation items based on permissions
  const navItems = [
    { 
      title: 'Dashboard', 
      path: getDashboardPath(), 
      icon: <DashboardIcon />, 
      visible: true 
    },
    { 
      title: 'Solicitações', 
      path: '/solicitacoes', 
      icon: <ListAltIcon />, 
      visible: true 
    },
    { 
      title: 'Nova Solicitação', 
      path: '/solicitacoes/nova', 
      icon: <AddCircleOutlineIcon />, 
      visible: perms?.can_create_solicitation || profile?.perfil === 'Solicitante' || perms?.is_admin 
    },
    { 
      title: 'Estoque', 
      path: '/estoque/requisicoes', 
      icon: <InventoryIcon />, 
      visible: perms?.can_manage_stock 
    },
    { 
      title: 'Processar', 
      path: '/suprimentos/processar', 
      icon: <ShoppingCartIcon />, 
      visible: perms?.can_manage_procurement 
    },
    { 
      title: 'Cotações', 
      path: '/suprimentos/cotacoes', 
      icon: <ShoppingCartIcon />, 
      visible: perms?.can_manage_procurement 
    },
    { 
      title: 'Pedidos', 
      path: '/suprimentos/pedidos', 
      icon: <ShoppingCartIcon />, 
      visible: perms?.can_manage_procurement 
    },
    { 
      title: 'Dashboard Diretoria', 
      path: '/diretoria/dashboard', 
      icon: <DashboardIcon />, 
      visible: perms?.can_approve 
    },
    { 
      title: 'Aprovações', 
      path: '/diretoria/aprovacoes', 
      icon: <ThumbUpIcon />, 
      visible: perms?.can_approve 
    },
    { 
      title: 'Usuários', 
      path: '/admin/usuarios', 
      icon: <PeopleIcon />, 
      visible: perms?.is_admin 
    },
    { 
      title: 'Configurações', 
      path: '/admin/configuracoes', 
      icon: <SettingsIcon />, 
      visible: perms?.is_admin 
    },
    { 
      title: 'Auditoria', 
      path: '/admin/auditoria', 
      icon: <HistoryIcon />, 
      visible: perms?.is_admin 
    },
  ];

  const drawer = (
    <Box sx={{ width: 250 }} role="presentation">
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h6">Sistema de Compras</Typography>
      </Box>
      <Divider />
      {profile && (
        <Box sx={{ p: 2, display: 'flex', alignItems: 'center', bgcolor: 'grey.100' }}>
          <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
            {profile.username?.charAt(0).toUpperCase() || 'U'}
          </Avatar>
          <Box>
            <Typography variant="subtitle2">{profile.username}</Typography>
            <Typography variant="caption" color="text.secondary">{profile.perfil || 'Usuário'}</Typography>
          </Box>
        </Box>
      )}
      <List>
        {navItems.filter(item => item.visible).map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton 
              component={RouterLink} 
              to={item.path}
              selected={isActive(item.path)}
              onClick={() => setDrawerOpen(false)}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.title} />
            </ListItemButton>
          </ListItem>
        ))}
        <Divider sx={{ my: 1 }} />
        <ListItem disablePadding>
          <ListItemButton onClick={onLogout}>
            <ListItemIcon>
              <LogoutIcon />
            </ListItemIcon>
            <ListItemText primary="Sair" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <>
      <AppBar position="sticky" elevation={1} sx={{ bgcolor: 'white', color: 'primary.main' }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            Sistema de Compras
          </Typography>
          
          {!isMobile && (
            <Stack direction="row" spacing={1}>
              {navItems.filter(item => item.visible).slice(0, 4).map((item) => (
                <Button 
                  key={item.path} 
                  color="primary" 
                  component={RouterLink} 
                  to={item.path}
                  variant={isActive(item.path) ? "contained" : "text"}
                  startIcon={item.icon}
                >
                  {item.title}
                </Button>
              ))}
            </Stack>
          )}
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title={profile?.username || 'Perfil'}>
              <IconButton
                size="large"
                edge="end"
                aria-label="account of current user"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                  {profile?.username?.charAt(0).toUpperCase() || <AccountCircleIcon />}
                </Avatar>
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>
      
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer}
      >
        {drawer}
      </Drawer>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleProfileMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem disabled>
          <Typography variant="body2">{profile?.perfil || 'Usuário'}</Typography>
        </MenuItem>
        <Divider />
        <MenuItem onClick={onLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          <Typography variant="body2">Sair</Typography>
        </MenuItem>
      </Menu>
      
      <Container 
        maxWidth={false} 
        disableGutters
        sx={{ 
          mt: 0, 
          mb: 0, 
          px: { xs: 1, sm: 2, md: 3 },
          minHeight: 'calc(100vh - 64px)',
          height: 'calc(100vh - 64px)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'auto'
        }}
      >
        <Outlet />
      </Container>
    </>
  );
}
