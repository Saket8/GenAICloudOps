import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  fallbackPath?: string;
}

export function ProtectedRoute({ 
  children, 
  requiredPermissions = [], 
  fallbackPath = '/login' 
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, permissions } = useAuth();
  const location = useLocation();

  // Show loading spinner while authentication state is being determined
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
          <p className="mt-2 text-gray-300">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  // Check permissions if required
  if (requiredPermissions.length > 0 && permissions) {
    const hasRequiredPermissions = requiredPermissions.every(permission => 
      permissions[permission as keyof typeof permissions]
    );

    if (!hasRequiredPermissions) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900">
          <div className="text-center">
            <div className="text-red-400 text-6xl mb-4">
              <i className="fas fa-lock"></i>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Access Denied</h2>
            <p className="text-gray-300 mb-4">
              You don't have permission to access this page.
            </p>
            <button
              onClick={() => window.history.back()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}

// Specific permission-based protected routes
export function RequireDashboardAccess({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredPermissions={['can_view_dashboard']}>
      {children}
    </ProtectedRoute>
  );
}

export function RequireAlertsAccess({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredPermissions={['can_view_alerts']}>
      {children}
    </ProtectedRoute>
  );
}

export function RequireRemediationAccess({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredPermissions={['can_approve_remediation']}>
      {children}
    </ProtectedRoute>
  );
}

export function RequireUserManagement({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredPermissions={['can_manage_users']}>
      {children}
    </ProtectedRoute>
  );
}

export function RequireAccessAnalyzer({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredPermissions={['can_view_access_analyzer']}>
      {children}
    </ProtectedRoute>
  );
}

export function RequirePodAnalyzer({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredPermissions={['can_view_pod_analyzer']}>
      {children}
    </ProtectedRoute>
  );
}

export function RequireCostAnalyzer({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredPermissions={['can_view_cost_analyzer']}>
      {children}
    </ProtectedRoute>
  );
}

export function RequireChatbotAccess({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredPermissions={['can_use_chatbot']}>
      {children}
    </ProtectedRoute>
  );
} 