import React from 'react';
import { HealthStatus } from '../../../services/remediationService';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

interface SystemStatusProps {
  healthStatus: HealthStatus | null;
  onRefresh: () => void;
}

export function SystemStatus({ healthStatus, onRefresh }: SystemStatusProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'available':
        return 'text-green-600 bg-green-100';
      case 'unhealthy':
      case 'not_installed':
        return 'text-red-600 bg-red-100';
      case 'unavailable':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'available':
        return 'fas fa-check-circle';
      case 'unhealthy':
      case 'not_installed':
        return 'fas fa-times-circle';
      case 'unavailable':
        return 'fas fa-exclamation-triangle';
      default:
        return 'fas fa-question-circle';
    }
  };

  if (!healthStatus) {
    return (
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading system status...</span>
        </div>
      </div>
    );
  }

  const systemChecks = [
    {
      name: 'Database',
      status: healthStatus.checks.database,
      description: 'Connection to the remediation database',
      icon: 'fas fa-database'
    },
    {
      name: 'OCI Service',
      status: healthStatus.checks.oci_service,
      description: 'Oracle Cloud Infrastructure connectivity',
      icon: 'fas fa-cloud'
    },
    {
      name: 'Terraform',
      status: healthStatus.checks.terraform,
      description: 'Terraform CLI availability',
      icon: 'fas fa-code-branch'
    }
  ];

  const overallHealthy = healthStatus.status === 'healthy';

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            <i className="fas fa-heartbeat mr-2 text-blue-500"></i>
            System Health Status
          </h2>
          <button
            onClick={onRefresh}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <i className="fas fa-sync-alt mr-1"></i>
            Refresh
          </button>
        </div>

        <div className={`flex items-center p-4 rounded-lg ${
          overallHealthy ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
            overallHealthy ? 'bg-green-500' : 'bg-red-500'
          }`}>
            <i className={`fas ${overallHealthy ? 'fa-check' : 'fa-times'} text-white text-xl`}></i>
          </div>
          <div className="ml-4">
            <h3 className={`text-lg font-medium ${
              overallHealthy ? 'text-green-900' : 'text-red-900'
            }`}>
              System Status: {(healthStatus.status ?? '').toString().toUpperCase()}
            </h3>
            <p className={`text-sm ${
              overallHealthy ? 'text-green-700' : 'text-red-700'
            }`}>
              {overallHealthy 
                ? 'All remediation services are operational'
                : 'One or more services require attention'
              }
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Last checked: {new Date(healthStatus.timestamp).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Component Status */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Component Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {systemChecks.map((check) => (
            <div key={check.name} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getStatusColor(check.status)}`}>
                  <i className={`${check.icon} text-sm`}></i>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white">{check.name}</h4>
                  <div className="flex items-center">
                    <i className={`${getStatusIcon(check.status)} text-xs mr-1`}></i>
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {(check.status ?? '').toString().replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">{check.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* System Information */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Service Details</h4>
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500 dark:text-gray-400">Service Name</dt>
                <dd className="text-sm text-gray-900 dark:text-white">{healthStatus.service}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500 dark:text-gray-400">Status</dt>
                <dd className="text-sm text-gray-900 dark:text-white">{healthStatus.status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-500 dark:text-gray-400">Last Check</dt>
                <dd className="text-sm text-gray-900 dark:text-white">
                  {new Date(healthStatus.timestamp).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Capabilities</h4>
            <div className="space-y-2">
              <div className="flex items-center">
                <i className="fas fa-cloud text-blue-500 mr-2"></i>
                <span className="text-sm text-gray-900 dark:text-white">OCI CLI Commands</span>
              </div>
              <div className="flex items-center">
                <i className="fas fa-code-branch text-purple-500 mr-2"></i>
                <span className="text-sm text-gray-900 dark:text-white">Terraform Execution</span>
              </div>
              <div className="flex items-center">
                <i className="fas fa-dharmachakra text-blue-600 mr-2"></i>
                <span className="text-sm text-gray-900 dark:text-white">Kubernetes Integration</span>
              </div>
              <div className="flex items-center">
                <i className="fas fa-terminal text-green-500 mr-2"></i>
                <span className="text-sm text-gray-900 dark:text-white">Script Execution</span>
              </div>
              <div className="flex items-center">
                <i className="fas fa-cogs text-orange-500 mr-2"></i>
                <span className="text-sm text-gray-900 dark:text-white">API Calls</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Health Tips */}
      <div className="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
          <i className="fas fa-lightbulb mr-1"></i>
          Health Tips
        </h4>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• Ensure all components show "healthy" status for optimal performance</li>
          <li>• Database connectivity is required for all remediation operations</li>
          <li>• OCI service must be available for cloud resource management</li>
          <li>• Terraform must be installed for infrastructure automation</li>
        </ul>
      </div>
    </div>
  );
} 