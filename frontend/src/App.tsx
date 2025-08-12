import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryProvider } from './providers/QueryProvider';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { AppLayout } from './components/layout/AppLayout';
import { LoginForm } from './components/auth/LoginForm';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { DashboardPage } from './components/pages/DashboardPage';
import { MonitoringPage } from './components/pages/MonitoringPage';
import { AlertsPage } from './components/pages/AlertsPage';
import { RemediationPage } from './components/pages/RemediationPage';
import { AccessAnalyzerPage } from './components/pages/AccessAnalyzerPage';
import { PodHealthAnalyzerPage } from './components/pages/PodHealthAnalyzerPage';
import { CostAnalyzerPage } from './components/pages/CostAnalyzerPage';
import { SettingsPage } from './components/pages/SettingsPage';
import { CloudResourcesPage } from './components/pages/CloudResourcesPage';

// KubernetesPage is now replaced by PodHealthAnalyzerPage

// Use RemediationPage as AutomationPage
const AutomationPage = RemediationPage;

// SettingsPage now provided with dummy data UI

function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-6xl font-bold text-gray-300 dark:text-gray-600">404</h1>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">Page Not Found</h2>
          <p className="text-gray-600 dark:text-gray-400">
            The page you're looking for doesn't exist.
          </p>
        </div>
        <a
          href="/dashboard"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <i className="fas fa-home mr-2"></i>
          Go to Dashboard
        </a>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryProvider>
      <NotificationProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginForm />} />
              
              {/* Protected routes with layout */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_dashboard']}>
                    <AppLayout>
                      <DashboardPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/cloud-resources"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_dashboard']}>
                    <AppLayout>
                      <CloudResourcesPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/monitoring"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_alerts']}>
                    <AppLayout>
                      <MonitoringPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/alerts"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_alerts']}>
                    <AppLayout>
                      <AlertsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/kubernetes"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_pod_analyzer']}>
                    <AppLayout>
                      <PodHealthAnalyzerPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/access-analyzer"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_access_analyzer']}>
                    <AppLayout>
                      <AccessAnalyzerPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/cost-analysis"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_cost_analyzer']}>
                    <AppLayout>
                      <CostAnalyzerPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/automation"
                element={
                  <ProtectedRoute requiredPermissions={['can_execute_remediation']}>
                    <AppLayout>
                      <AutomationPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/settings"
                element={
                  <ProtectedRoute requiredPermissions={['can_manage_users']}>
                    <AppLayout>
                      <SettingsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              {/* Default redirect */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              
              {/* 404 page */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </NotificationProvider>
    </QueryProvider>
  );
}

export default App; 