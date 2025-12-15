import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryProvider } from './providers/QueryProvider';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
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
import { CloudSelectionPage } from './components/pages/CloudSelectionPage';
import { UserManagementPage } from './components/pages/UserManagementPage';
import { OperationalInsightsPage } from './components/pages/OperationalInsightsPage';
import { AwsDashboardPage } from './components/pages/aws/AwsDashboardPage';
import { AwsMonitoringPage } from './components/pages/aws/AwsMonitoringPage';
import { AwsCostPage } from './components/pages/aws/AwsCostPage';
import { AwsSecurityPage } from './components/pages/aws/AwsSecurityPage';
import { AwsAutomationPage } from './components/pages/aws/AwsAutomationPage';
import { AwsResourcesPage } from './components/pages/aws/AwsResourcesPage';
import { LayersSelectionPage } from './components/pages/LayersSelectionPage';
import { InfrastructureProvidersPage } from './components/pages/InfrastructureProvidersPage';
import { SecurityProvidersPage } from './components/pages/SecurityProvidersPage';
import { ApplicationProvidersPage } from './components/pages/ApplicationProvidersPage';
import { BusinessOpsPage } from './components/pages/BusinessOpsPage';
import { AdministrationPage } from './components/pages/AdministrationPage';
import { IntelligenceHubPage } from './components/pages/IntelligenceHubPage';


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
      <AuthProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginForm />} />

              {/* Layers selection landing */}
              <Route
                path="/layers"
                element={
                  <ProtectedRoute>
                    <LayersSelectionPage />
                  </ProtectedRoute>
                }
              />

              {/* Infrastructure providers selection */}
              <Route
                path="/infrastructure/providers"
                element={
                  <ProtectedRoute>
                    <InfrastructureProvidersPage />
                  </ProtectedRoute>
                }
              />

              {/* Security providers selection */}
              <Route
                path="/security/providers"
                element={
                  <ProtectedRoute>
                    <SecurityProvidersPage />
                  </ProtectedRoute>
                }
              />

              {/* Application providers selection */}
              <Route
                path="/application/providers"
                element={
                  <ProtectedRoute>
                    <ApplicationProvidersPage />
                  </ProtectedRoute>
                }
              />

              {/* Business Ops Dashboard */}
              <Route
                path="/business/providers"
                element={
                  <ProtectedRoute>
                    <BusinessOpsPage />
                  </ProtectedRoute>
                }
              />

              {/* Administration landing */}
              <Route
                path="/administration"
                element={
                  <ProtectedRoute requiredPermissions={['can_manage_users']}>
                    <AdministrationPage />
                  </ProtectedRoute>
                }
              />

              {/* Cloud selection landing (kept for backward compatibility) */}
              <Route
                path="/cloud-selection"
                element={
                  <ProtectedRoute>
                    <CloudSelectionPage />
                  </ProtectedRoute>
                }
              />

              {/* OCI routes */}
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
                path="/intelligence"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_dashboard']}>
                    <AppLayout>
                      <IntelligenceHubPage />
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

              <Route
                path="/user-management"
                element={
                  <ProtectedRoute requiredPermissions={['can_manage_users']}>
                    <AppLayout>
                      <UserManagementPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/operational-insights"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_dashboard']}>
                    <AppLayout>
                      <OperationalInsightsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              {/* AWS routes */}
              <Route
                path="/aws/dashboard"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_dashboard']}>
                    <AppLayout>
                      <AwsDashboardPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/aws/monitoring"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_alerts']}>
                    <AppLayout>
                      <AwsMonitoringPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/aws/cost"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_cost_analyzer']}>
                    <AppLayout>
                      <AwsCostPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/aws/security"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_access_analyzer']}>
                    <AppLayout>
                      <AwsSecurityPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/aws/automation"
                element={
                  <ProtectedRoute requiredPermissions={['can_execute_remediation']}>
                    <AppLayout>
                      <AwsAutomationPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/aws/resources"
                element={
                  <ProtectedRoute requiredPermissions={['can_view_dashboard']}>
                    <AppLayout>
                      <AwsResourcesPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              {/* Default redirect */}
              <Route path="/" element={<Navigate to="/layers" replace />} />

              {/* 404 page */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </QueryProvider>
  );
}

export default App;