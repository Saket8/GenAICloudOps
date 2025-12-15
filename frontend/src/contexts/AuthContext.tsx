import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { 
  AuthState, 
  AuthContextType, 
  LoginCredentials, 
  RegisterData, 
  User, 
  UserPermissions 
} from '../types/auth';
import { authService, tokenManager } from '../services/authService';

// Initial state
const initialState: AuthState = {
  user: null,
  permissions: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Auth actions
type AuthAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User }
  | { type: 'SET_PERMISSIONS'; payload: UserPermissions }
  | { type: 'SET_AUTHENTICATED'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_AUTH' }
  | { type: 'CLEAR_ERROR' };

// Auth reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_USER':
      return { ...state, user: action.payload, isAuthenticated: true, error: null };
    case 'SET_PERMISSIONS':
      return { ...state, permissions: action.payload };
    case 'SET_AUTHENTICATED':
      return { ...state, isAuthenticated: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    case 'CLEAR_AUTH':
      return { 
        ...initialState, 
        isLoading: false, 
        isAuthenticated: false 
      };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize authentication state
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      // Check if user has valid tokens
      if (!authService.hasValidTokens()) {
        dispatch({ type: 'SET_LOADING', payload: false });
        return;
      }

      // Verify token and get user data
      await verifyAndLoadUser();
    } catch (error) {
      console.error('Auth initialization error:', error);
      tokenManager.clearTokens();
      dispatch({ type: 'CLEAR_AUTH' });
    }
  };

  const verifyAndLoadUser = async () => {
    // Verify token is still valid
    await authService.verifyToken();
    
    // Load user data and permissions
    const [user, permissionData] = await Promise.all([
      authService.getCurrentUser(),
      authService.getUserPermissions()
    ]);

    dispatch({ type: 'SET_USER', payload: user });
    dispatch({ type: 'SET_PERMISSIONS', payload: permissionData.permissions });
    dispatch({ type: 'SET_LOADING', payload: false });
  };

  const login = async (credentials: LoginCredentials) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });

      // Authenticate user
      await authService.login(credentials);
      
      // Load user data and permissions
      await verifyAndLoadUser();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });

      // Register user
      await authService.register(data);
      
      // Auto-login after successful registration
      await login({ username: data.username, password: data.password });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'CLEAR_AUTH' });
    }
  };

  const refreshToken = async () => {
    try {
      await authService.refreshToken();
      // Reload user data after token refresh
      await verifyAndLoadUser();
    } catch (error) {
      console.error('Token refresh error:', error);
      // If refresh fails, clear auth state
      tokenManager.clearTokens();
      dispatch({ type: 'CLEAR_AUTH' });
      throw error;
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshToken,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext; 