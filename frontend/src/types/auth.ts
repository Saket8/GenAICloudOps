export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface Role {
  id: number;
  name: 'admin' | 'viewer' | 'operator' | 'cloud_admin' | 'app_admin' | 'security_admin' | 'sys_admin';
  display_name: string;
  description?: string;
  can_view_dashboard: boolean;
  can_view_alerts: boolean;
  can_approve_remediation: boolean;
  can_execute_remediation: boolean;
  can_manage_users: boolean;
  can_manage_roles: boolean;
  can_view_access_analyzer: boolean;
  can_view_pod_analyzer: boolean;
  can_view_cost_analyzer: boolean;
  can_use_chatbot: boolean;
}

export interface UserWithRoles extends User {
  roles: Role[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface UserPermissions {
  can_view_dashboard: boolean;
  can_view_alerts: boolean;
  can_approve_remediation: boolean;
  can_execute_remediation: boolean;
  can_manage_users: boolean;
  can_manage_roles: boolean;
  can_view_access_analyzer: boolean;
  can_view_pod_analyzer: boolean;
  can_view_cost_analyzer: boolean;
  can_use_chatbot: boolean;
}

export interface AuthState {
  user: User | null;
  permissions: UserPermissions | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  clearError: () => void;
} 