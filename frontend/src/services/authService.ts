import { AxiosResponse } from 'axios';
import { 
  AuthTokens, 
  LoginCredentials, 
  RegisterData, 
  User, 
  UserPermissions 
} from '../types/auth';
import { api } from './apiClient';

// Token management
const TOKEN_KEY = 'genai_access_token';
const REFRESH_TOKEN_KEY = 'genai_refresh_token';

export const tokenManager = {
  getToken: (): string | null => localStorage.getItem(TOKEN_KEY),
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (tokens: AuthTokens): void => {
    localStorage.setItem(TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  },
  clearTokens: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

// Auth service methods
export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    try {
      const response = await api.post<AuthTokens>('/auth/login', credentials);
      const tokens = response.data;
      tokenManager.setTokens(tokens);
      return tokens;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  register: async (userData: RegisterData): Promise<User> => {
    try {
      const response = await api.post<User>('/auth/register', userData);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      tokenManager.clearTokens();
    }
  },

  refreshToken: async (): Promise<AuthTokens> => {
    const refreshToken = tokenManager.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await api.post<AuthTokens>('/auth/refresh', {
        refresh_token: refreshToken,
      });
      const tokens = response.data;
      tokenManager.setTokens(tokens);
      return tokens;
    } catch (error) {
      console.error('Token refresh error:', error);
      tokenManager.clearTokens();
      throw error;
    }
  },

  verifyToken: async (): Promise<boolean> => {
    try {
      await api.get('/auth/verify-token');
      return true;
    } catch (error) {
      console.error('Token verification failed:', error);
      return false;
    }
  },

  getCurrentUser: async (): Promise<User> => {
    try {
      const response = await api.get<User>('/auth/me');
      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  },

  getUserPermissions: async (): Promise<{ permissions: UserPermissions }> => {
    try {
      const response = await api.get<{ permissions: UserPermissions }>('/auth/me/permissions');
      return response.data;
    } catch (error) {
      console.error('Get user permissions error:', error);
      throw error;
    }
  },

  hasValidTokens: (): boolean => {
    const token = tokenManager.getToken();
    const refreshToken = tokenManager.getRefreshToken();
    return !!(token && refreshToken);
  },

  // Helper method to check if we need to refresh tokens
  isTokenExpired: (token: string): boolean => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch {
      return true;
    }
  }
};

export default authService; 