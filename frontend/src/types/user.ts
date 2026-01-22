export interface User {
  id: number;
  email: string;
  name: string;
  avatar_url?: string;
  auth_provider: 'email' | 'google' | 'github';
  is_superuser: boolean;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
