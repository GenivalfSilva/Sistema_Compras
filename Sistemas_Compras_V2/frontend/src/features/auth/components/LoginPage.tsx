import { useState, useEffect } from 'react';
import { Typography, Box, Button, CircularProgress, IconButton, Fade } from '@mui/material';
import { useAppDispatch, useAppSelector } from '../../../app/hooks';
import { login } from '../authSlice';
import { useNavigate } from 'react-router-dom';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import VisibilityOffOutlinedIcon from '@mui/icons-material/VisibilityOffOutlined';
import BusinessIcon from '@mui/icons-material/Business';
import SecurityIcon from '@mui/icons-material/Security';
import SpeedIcon from '@mui/icons-material/Speed';
import './LoginPage.css';

export default function LoginPage() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const loading = useAppSelector((s: any) => s.auth?.loading || false);
  const errorState = useAppSelector((s: any) => s.auth?.error || null);
  
  // Formatar mensagem de erro para exibição
  const formatError = (error: any): string => {
    if (!error) return '';
    
    // Se for um objeto com non_field_errors
    if (typeof error === 'object' && error.non_field_errors) {
      return Array.isArray(error.non_field_errors) 
        ? error.non_field_errors.join(', ')
        : String(error.non_field_errors);
    }
    
    // Se for um objeto genérico
    if (typeof error === 'object') {
      return Object.entries(error)
        .map(([key, value]) => `${key}: ${value}`)
        .join(', ');
    }
    
    // Se for uma string
    return String(error);
  };
  
  const errorMessage = formatError(errorState);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) return;
    
    const res = await dispatch(login({ username, password }));
    if (login.fulfilled.match(res)) {
      navigate('/');
    }
  };

  return (
    <div className="login-container">
      <div className="login-content">
        {/* Painel esquerdo com fundo translúcido */}
        <div className="login-left-panel">
          <div className="login-brand">
            <div className="login-logo-container">
              <img src="/assets/img/logo_ziran.jpg" alt="Logo Ziran" className="login-logo" />
            </div>
            <Typography variant="h4" className="login-welcome">
              Bem-vindo ao<br />
              <span className="highlight">Sistema de Compras</span>
            </Typography>
            <Typography variant="body1" className="login-description">
              Gerencie suas solicitações, requisições e aprovações<br />em um só lugar.
            </Typography>
            
            {/* Recursos destacados */}
            <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', gap: 2, opacity: 0.9 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <BusinessIcon sx={{ color: 'rgba(255,255,255,0.8)', fontSize: '1.2rem' }} />
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.85rem' }}>
                  Gestão Empresarial Completa
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <SecurityIcon sx={{ color: 'rgba(255,255,255,0.8)', fontSize: '1.2rem' }} />
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.85rem' }}>
                  Segurança e Auditoria Avançada
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <SpeedIcon sx={{ color: 'rgba(255,255,255,0.8)', fontSize: '1.2rem' }} />
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.85rem' }}>
                  Fluxo de Trabalho Otimizado
                </Typography>
              </Box>
            </Box>
          </div>
        </div>
        
        {/* Formulário de login */}
        <div className="login-paper">
          <div className="login-header">
            <Typography variant="h5" className="login-title">
              Acesse sua conta
            </Typography>
            <Typography variant="body2" className="login-subtitle">
              Entre com suas credenciais para continuar
            </Typography>
          </div>
          
          <Box component="form" onSubmit={onSubmit} className="login-form">
            {/* Campo de usuário */}
            <Fade in={isLoaded} timeout={800} style={{ transitionDelay: '0.8s' }}>
              <div className="input-container">
                <label htmlFor="username">Usuário</label>
                <div className="input-field">
                  <PersonIcon className="input-icon" />
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoComplete="username"
                    placeholder="Digite seu usuário"
                  />
                </div>
              </div>
            </Fade>
            
            {/* Campo de senha */}
            <Fade in={isLoaded} timeout={800} style={{ transitionDelay: '0.9s' }}>
              <div className="input-container">
                <label htmlFor="password">Senha</label>
                <div className="input-field">
                  <LockIcon className="input-icon" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    placeholder="Digite sua senha"
                  />
                  <IconButton
                    className="visibility-toggle"
                    aria-label="toggle password visibility"
                    onClick={togglePasswordVisibility}
                    edge="end"
                    size="small"
                  >
                    {showPassword ? <VisibilityOffOutlinedIcon /> : <VisibilityOutlinedIcon />}
                  </IconButton>
                </div>
              </div>
            </Fade>
            
            {/* Mensagem de erro */}
            <Fade in={!!errorMessage} timeout={400}>
              <div>
                {errorMessage && (
                  <div className="login-error">
                    ⚠️ {errorMessage}
                  </div>
                )}
              </div>
            </Fade>
            
            {/* Botão de login */}
            <Fade in={isLoaded} timeout={800} style={{ transitionDelay: '1.2s' }}>
              <div>
                <Button 
                  type="submit" 
                  variant="contained" 
                  fullWidth 
                  disabled={loading || !username || !password} 
                  className="login-button"
                >
                  {loading ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CircularProgress size={20} color="inherit" />
                      <span>Entrando...</span>
                    </Box>
                  ) : (
                    '🚀 Entrar no Sistema'
                  )}
                </Button>
              </div>
            </Fade>
            
            {/* Mensagem de suporte */}
            <Fade in={isLoaded} timeout={800} style={{ transitionDelay: '1.4s' }}>
              <div className="login-help">
                <Typography variant="body2">
                  💬 Problemas para acessar? Entre em contato com o suporte
                </Typography>
              </div>
            </Fade>
          </Box>
        </div>
      </div>
      
      {/* Rodapé */}
      <div className="login-footer">
        <Typography variant="caption">
          Sistema de Compras Ziran © {new Date().getFullYear()} | v2.0.0
        </Typography>
      </div>
    </div>
  );
}
