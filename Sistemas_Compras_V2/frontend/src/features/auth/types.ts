export interface Tokens {
  access: string;
  refresh?: string;
}

export interface UserProfile {
  id: number;
  username: string;
  nome?: string;
  perfil?: string;
  departamento?: string;
  permissions?: any;
}
