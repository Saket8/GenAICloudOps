import React, { useEffect } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCloudProvider } from '../../contexts/CloudProviderContext';

interface NavigationItem {
  id: string;
  name: string;
  path: string;
  icon: string;
  requiredPermissions?: string[];
  description: string;
}

const ociNavigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    path: '/dashboard',
    icon: 'fas fa-tachometer-alt',
    description: 'Overview and key metrics',
  },
  {
    id: 'cloud-resources',
    name: 'Cloud Resources',
    path: '/cloud-resources',
    icon: 'fas fa-cloud',
    requiredPermissions: ['can_view_resources'],
    description: 'OCI resources and services',
  },
  {
    id: 'monitoring',
    name: 'Monitoring',
    path: '/monitoring',
    icon: 'fas fa-chart-line',
    requiredPermissions: ['can_view_monitoring'],
    description: 'Real-time metrics and alerts',
  },
  {
    id: 'alerts',
    name: 'Alerts & Insights',
    path: '/alerts',
    icon: 'fas fa-exclamation-triangle',
    requiredPermissions: ['can_view_alerts'],
    description: 'Alert management with AI insights',
  },

  {
    id: 'cost-analysis',
    name: 'Cost Analysis',
    path: '/cost-analysis',
    icon: 'fas fa-dollar-sign',
    requiredPermissions: ['can_view_cost_analyzer'],
    description: 'Resource costs and optimization',
  },
  {
    id: 'intelligence',
    name: 'Intelligence Hub',
    path: '/intelligence',
    icon: 'fas fa-brain',
    requiredPermissions: ['can_view_dashboard'],
    description: 'Multi-dimensional analytics & insights',
  },
  {
    id: 'automation',
    name: 'Automation',
    path: '/automation',
    icon: 'fas fa-cogs',
    requiredPermissions: ['can_manage_automation'],
    description: 'Automated workflows and remediation',
  },
  {
    id: 'settings',
    name: 'Settings',
    path: '/settings',
    icon: 'fas fa-cog',
    requiredPermissions: ['can_view_settings'],
    description: 'Application configuration',
  },
];

const awsNavigationItems: NavigationItem[] = [
  {
    id: 'aws-dashboard',
    name: 'Dashboard',
    path: '/aws/dashboard',
    icon: 'fab fa-aws',
    description: 'AWS overview and key metrics',
  },
  {
    id: 'aws-cloud-resources',
    name: 'Cloud Resources',
    path: '/aws/resources',
    icon: 'fas fa-cloud',
    requiredPermissions: ['can_view_resources'],
    description: 'AWS resource summaries',
  },
  {
    id: 'aws-monitoring',
    name: 'Monitoring',
    path: '/aws/monitoring',
    icon: 'fas fa-chart-line',
    requiredPermissions: ['can_view_monitoring'],
    description: 'CloudWatch health, alerts, and dashboards',
  },
  {
    id: 'aws-alerts',
    name: 'Alerts & Insights',
    path: '/alerts',
    icon: 'fas fa-exclamation-triangle',
    requiredPermissions: ['can_view_alerts'],
    description: 'Unified alert triage with AI insights',
  },

  {
    id: 'aws-cost',
    name: 'Cost Analysis',
    path: '/aws/cost',
    icon: 'fas fa-dollar-sign',
    requiredPermissions: ['can_view_cost_analyzer'],
    description: 'Cost Explorer snapshots',
  },
  {
    id: 'aws-automation',
    name: 'Automation',
    path: '/aws/automation',
    icon: 'fas fa-cogs',
    requiredPermissions: ['can_manage_automation'],
    description: 'Runbooks and remediation playbooks',
  },
  {
    id: 'aws-settings',
    name: 'Settings',
    path: '/settings',
    icon: 'fas fa-cog',
    requiredPermissions: ['can_view_settings'],
    description: 'Application configuration',
  },
];

const applicationNavigationItems: NavigationItem[] = [
  {
    id: 'operational-dashboard',
    name: 'Operational Dashboard',
    path: '/operational-insights',
    icon: 'fas fa-tachometer-alt',
    description: 'Application performance and health overview',
  },
  {
    id: 'pod-health',
    name: 'Pod Health',
    path: '/kubernetes',
    icon: 'fas fa-dharmachakra',
    requiredPermissions: ['can_view_pod_analyzer'],
    description: 'Pod health monitoring and log analysis',
  },
];

export function Navigation() {
  const { permissions } = useAuth();
  const { provider, setProvider } = useCloudProvider();
  const location = useLocation();
  const navigate = useNavigate();

  const isAdminSubpage = [
    '/user-management',
    '/settings',
    '/administration'
  ].some(path => location.pathname.startsWith(path));

  const isSecuritySubpage = [
    '/access-analyzer',
    '/aws/security'
  ].some(path => location.pathname.startsWith(path));

  const isApplicationSubpage = [
    '/operational-insights',
    '/kubernetes'
  ].some(path => location.pathname.startsWith(path));

  const isBusinessOpsSubpage = [
    '/business/providers'
  ].some(path => location.pathname.startsWith(path));

  useEffect(() => {
    const path = location.pathname;
    if (path.startsWith('/aws')) {
      if (provider !== 'aws') {
        setProvider('aws');
      }
    } else if (!path.startsWith('/cloud-selection') && provider !== 'oci') {
      setProvider('oci');
    }
  }, [location.pathname, provider, setProvider]);

  const hasPermission = (requiredPermissions?: string[]): boolean => {
    if (!requiredPermissions || requiredPermissions.length === 0) {
      return true;
    }

    if (!permissions) {
      return false;
    }

    const permissionMap: Record<string, boolean> = {
      'can_view_dashboard': permissions.can_view_dashboard,
      'can_view_resources': permissions.can_view_dashboard, // For now, map to dashboard
      'can_view_monitoring': permissions.can_view_alerts,
      'can_view_alerts': permissions.can_view_alerts, // Add mapping for alerts & insights
      'can_view_kubernetes': permissions.can_view_pod_analyzer,
      'can_view_pod_analyzer': permissions.can_view_pod_analyzer, // Fix: Add mapping for Pod Health Analyzer
      'can_view_costs': permissions.can_view_cost_analyzer,
      'can_view_cost_analyzer': permissions.can_view_cost_analyzer, // Add correct mapping for Cost Analysis
      'can_manage_automation': permissions.can_execute_remediation,
      'can_view_settings': permissions.can_manage_users || permissions.can_manage_roles,
    };

    return requiredPermissions.some(permission =>
      permissionMap[permission] === true
    );
  };

  const navigationItems = isApplicationSubpage
    ? applicationNavigationItems
    : provider === 'aws' ? awsNavigationItems : ociNavigationItems;
  const visibleItems = navigationItems.filter(item => hasPermission(item.requiredPermissions));

  return (
    <nav className="bg-gradient-to-r from-[#0d1b4c] via-[#0f2060] to-[#0d1b4c] border-b border-blue-900/30 shadow-lg">
      <div className="px-4 sm:px-6 lg:px-8">

        {/* Desktop Navigation */}
        <div className="hidden md:block">
          <div className="hidden md:flex items-center justify-between">
            {!isAdminSubpage && !isSecuritySubpage && !isApplicationSubpage && !isBusinessOpsSubpage && (
              <div className="flex space-x-1">
                {visibleItems.map((item) => (
                  <NavLink
                    key={item.id}
                    to={item.path}
                    className={({ isActive }) =>
                      `group flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${isActive
                        ? 'bg-blue-600/20 text-blue-300 border-b-2 border-blue-400'
                        : 'text-slate-300 hover:text-white hover:bg-white/10'
                      }`
                    }
                  >
                    <i className={`${item.icon} mr-2 text-sm`} />
                    <span>{item.name}</span>

                    {/* Tooltip */}
                    <div className="absolute invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-gray-900 text-white text-xs rounded-lg py-2 px-3 mt-16 ml-4 whitespace-nowrap z-50 shadow-xl border border-gray-700">
                      {item.description}
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-b-gray-900" />
                    </div>
                  </NavLink>
                ))}
              </div>
            )}
            {isAdminSubpage ? (
              <button
                onClick={() => navigate('/administration')}
                className="ml-auto inline-flex items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left mr-2" />
                Back to Admin
              </button>
            ) : isSecuritySubpage ? (
              <button
                onClick={() => navigate('/security/providers')}
                className="ml-auto inline-flex items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left mr-2" />
                Back to Security Providers
              </button>
            ) : isApplicationSubpage ? (
              <button
                onClick={() => navigate('/application/providers')}
                className="ml-auto inline-flex items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left mr-2" />
                Back to Application Providers
              </button>
            ) : isBusinessOpsSubpage ? (
              <button
                onClick={() => navigate('/layers')}
                className="ml-auto inline-flex items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left mr-2" />
                Back to Layers
              </button>
            ) : (
              <button
                onClick={() => navigate('/infrastructure/providers')}
                className="ml-auto inline-flex items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left mr-2" />
                Back to Infrastructure Providers
              </button>
            )}
          </div>
        </div>


        {/* Mobile Navigation */}
        <div className="md:hidden">
          <div className="flex items-center overflow-x-auto py-2 space-x-4">
            {!isAdminSubpage && !isSecuritySubpage && !isApplicationSubpage && !isBusinessOpsSubpage && visibleItems.map((item) => (
              <NavLink
                key={item.id}
                to={item.path}
                className={({ isActive }) =>
                  `flex-shrink-0 flex flex-col items-center px-3 py-2 text-xs font-medium rounded-md transition-colors duration-200 ${isActive
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`
                }
              >
                <i className={`${item.icon} text-lg mb-1`}></i>
                <span className="whitespace-nowrap">{item.name}</span>
              </NavLink>
            ))}
            {isAdminSubpage ? (
              <button
                onClick={() => navigate('/administration')}
                className="flex-shrink-0 flex flex-col items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left text-lg mb-1"></i>
                <span className="whitespace-nowrap">Back</span>
              </button>
            ) : isSecuritySubpage ? (
              <button
                onClick={() => navigate('/security/providers')}
                className="flex-shrink-0 flex flex-col items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left text-lg mb-1"></i>
                <span className="whitespace-nowrap">Back</span>
              </button>
            ) : isApplicationSubpage ? (
              <button
                onClick={() => navigate('/application/providers')}
                className="flex-shrink-0 flex flex-col items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left text-lg mb-1"></i>
                <span className="whitespace-nowrap">Back</span>
              </button>
            ) : isBusinessOpsSubpage ? (
              <button
                onClick={() => navigate('/layers')}
                className="flex-shrink-0 flex flex-col items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left text-lg mb-1"></i>
                <span className="whitespace-nowrap">Back</span>
              </button>
            ) : isBusinessOpsSubpage ? (
              <button
                onClick={() => navigate('/layers')}
                className="flex-shrink-0 flex flex-col items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left text-lg mb-1"></i>
                <span className="whitespace-nowrap">Back</span>
              </button>
            ) : (
              <button
                onClick={() => navigate('/infrastructure/providers')}
                className="flex-shrink-0 flex flex-col items-center px-3 py-2 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60"
              >
                <i className="fas fa-arrow-left text-lg mb-1"></i>
                <span className="whitespace-nowrap">Back</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}