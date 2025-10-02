import { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../../app/hooks';
import { fetchProfile, setTokens, setProfile } from '../authSlice';
import { useLocation } from 'react-router-dom';
import { authStorage } from '../authStorage';

/**
 * Componente que inicializa a autenticação ao carregar a aplicação
 * Verifica se há um token no localStorage e carrega o perfil do usuário se necessário
 * Também sincroniza os tokens do localStorage com o Redux store
 */
export default function AuthInitializer() {
  const dispatch = useAppDispatch();
  const { profile, tokens } = useAppSelector((s) => s.auth);
  const location = useLocation();
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Efeito para sincronizar dados de autenticação do localStorage com o Redux store
  useEffect(() => {
    const storedTokens = authStorage.getTokens();
    const storedProfile = authStorage.getProfile();
    
    // Verifica se os tokens são válidos
    const isTokenValid = storedTokens?.access && storedTokens.access.length > 20;
    
    // Se temos tokens válidos no localStorage mas não no Redux, sincroniza
    if (isTokenValid && (!tokens || tokens.access !== storedTokens.access)) {
      console.log('Sincronizando tokens do localStorage com o Redux store');
      dispatch(setTokens(storedTokens));
    } else if (!isTokenValid && storedTokens) {
      // Se os tokens não são válidos, limpa tudo
      console.log('Tokens inválidos encontrados, limpando dados de autenticação');
      authStorage.clearAuth();
    }
    
    // Se temos perfil no localStorage mas não no Redux, sincroniza
    if (storedProfile && !profile && isTokenValid) {
      console.log('Sincronizando perfil do localStorage com o Redux store');
      dispatch(setProfile(storedProfile));
    }
    
    setIsInitialized(true);
  }, [dispatch, tokens, profile]);
  
  // Efeito para carregar o perfil do usuário se necessário
  useEffect(() => {
    if (!isInitialized) return;
    
    const hasToken = Boolean(tokens?.access) || Boolean(authStorage.getTokens()?.access);
    
    // Se temos um token mas não temos o perfil, carrega o perfil
    if (hasToken && !profile) {
      console.log('Carregando perfil do usuário...');
      dispatch(fetchProfile());
    }
  }, [dispatch, profile, tokens, isInitialized, location.pathname]);

  return null; // Componente não renderiza nada
}
