import type { UserProfile, Tokens } from './types';

// Chaves para armazenamento no localStorage
const STORAGE_KEYS = {
  TOKENS: 'auth_tokens',
  PROFILE: 'auth_profile',
};

/**
 * Funções para persistir e recuperar o estado de autenticação do localStorage
 */
export const authStorage = {
  /**
   * Salva os tokens no localStorage
   */
  saveTokens(tokens: Tokens | null): void {
    if (tokens) {
      localStorage.setItem(STORAGE_KEYS.TOKENS, JSON.stringify(tokens));
      // Mantém os tokens individuais para compatibilidade com o código existente
      localStorage.setItem('access', tokens.access);
      if (tokens.refresh) localStorage.setItem('refresh', tokens.refresh);
    } else {
      localStorage.removeItem(STORAGE_KEYS.TOKENS);
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
    }
  },

  /**
   * Recupera os tokens do localStorage
   */
  getTokens(): Tokens | null {
    const tokensStr = localStorage.getItem(STORAGE_KEYS.TOKENS);
    if (!tokensStr) {
      // Tenta recuperar dos tokens individuais para compatibilidade
      const access = localStorage.getItem('access');
      const refresh = localStorage.getItem('refresh');
      
      if (access) {
        const tokens = { access, refresh: refresh || undefined };
        // Salva no formato novo para próximas requisições
        this.saveTokens(tokens);
        return tokens;
      }
      
      return null;
    }
    
    try {
      return JSON.parse(tokensStr) as Tokens;
    } catch (e) {
      console.error('Erro ao recuperar tokens do localStorage:', e);
      return null;
    }
  },

  /**
   * Salva o perfil do usuário no localStorage
   */
  saveProfile(profile: UserProfile | null): void {
    if (profile) {
      localStorage.setItem(STORAGE_KEYS.PROFILE, JSON.stringify(profile));
    } else {
      localStorage.removeItem(STORAGE_KEYS.PROFILE);
    }
  },

  /**
   * Recupera o perfil do usuário do localStorage
   */
  getProfile(): UserProfile | null {
    const profileStr = localStorage.getItem(STORAGE_KEYS.PROFILE);
    if (!profileStr) return null;
    
    try {
      return JSON.parse(profileStr) as UserProfile;
    } catch (e) {
      console.error('Erro ao recuperar perfil do localStorage:', e);
      return null;
    }
  },

  /**
   * Limpa todos os dados de autenticação do localStorage
   */
  clearAuth(): void {
    localStorage.removeItem(STORAGE_KEYS.TOKENS);
    localStorage.removeItem(STORAGE_KEYS.PROFILE);
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
  },

  /**
   * Verifica se o usuário está autenticado
   */
  isAuthenticated(): boolean {
    return !!this.getTokens()?.access;
  }
};
