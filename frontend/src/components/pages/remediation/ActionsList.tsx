import React, { useState } from 'react';
import { RemediationAction, ActionStatus, Severity, remediationService } from '../../../services/remediationService';
import { useAuth } from '../../../contexts/AuthContext';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

interface ActionsListProps {
  actions: RemediationAction[];
  onActionSelect: (action: RemediationAction) => void;
  onActionUpdate: (action: RemediationAction) => void;
  onActionDelete: (actionId: number) => void;
  onRefresh: () => void;
}

export function ActionsList({ 
  actions, 
  onActionSelect, 
  onActionUpdate, 
  onActionDelete, 
  onRefresh 
}: ActionsListProps) {
  const { permissions } = useAuth();
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    environment: '',
    search: ''
  });
  const [loadingActions, setLoadingActions] = useState<Set<number>>(new Set());

  // Filter actions based on current filters
  const filteredActions = actions.filter(action => {
    const matchesStatus = !filters.status || action.status === filters.status;
    const matchesSeverity = !filters.severity || action.severity === filters.severity;
    const matchesEnvironment = !filters.environment || action.environment === filters.environment;
    const matchesSearch = !filters.search || 
      action.title.toLowerCase().includes(filters.search.toLowerCase()) ||
      action.description.toLowerCase().includes(filters.search.toLowerCase()) ||
      action.service_name.toLowerCase().includes(filters.search.toLowerCase());

    return matchesStatus && matchesSeverity && matchesEnvironment && matchesSearch;
  });

  const handleQuickAction = async (actionId: number, actionType: 'approve' | 'execute' | 'cancel') => {
    setLoadingActions(prev => new Set(prev).add(actionId));
    
    try {
      let result;
      switch (actionType) {
        case 'approve':
          result = await remediationService.approveAction(actionId);
          break;
        case 'execute':
          await remediationService.executeAction(actionId, true); // Dry run first
          break;
        case 'cancel':
          result = await remediationService.cancelAction(actionId);
          if (result.success) {
            onActionDelete(actionId);
          }
          break;
      }
      
      // Refresh the action data
      onRefresh();
    } catch (error: any) {
      console.error(`Failed to ${actionType} action:`, error);
      alert(`Failed to ${actionType} action: ${error.message}`);
    } finally {
      setLoadingActions(prev => {
        const newSet = new Set(prev);
        newSet.delete(actionId);
        return newSet;
      });
    }
  };

  const getUniqueValues = (key: keyof RemediationAction): string[] => {
    return Array.from(new Set(
      actions
        .map(action => action[key])
        .filter(value => value !== null && value !== undefined && value !== '')
        .map(value => String(value))
    ));
  };

  const canApprove = permissions?.can_approve_remediation;
  const canExecute = permissions?.can_execute_remediation;

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Search
            </label>
            <div className="relative">
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                placeholder="Search actions..."
                className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white"
              />
              <i className="fas fa-search absolute left-2.5 top-2.5 text-gray-400"></i>
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white"
            >
              <option value="">All Statuses</option>
              {getUniqueValues('status').map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          {/* Severity Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Severity
            </label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white"
            >
              <option value="">All Severities</option>
              {getUniqueValues('severity').map(severity => (
                <option key={severity} value={severity}>{severity}</option>
              ))}
            </select>
          </div>

          {/* Environment Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Environment
            </label>
            <select
              value={filters.environment}
              onChange={(e) => setFilters(prev => ({ ...prev, environment: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white"
            >
              <option value="">All Environments</option>
              {getUniqueValues('environment').map(env => (
                <option key={env} value={env}>{env}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Results count */}
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Showing {filteredActions.length} of {actions.length} actions
        </div>
      </div>

      {/* Actions Table */}
      {filteredActions.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <i className="fas fa-tasks text-4xl text-gray-400 mb-4"></i>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No actions found
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {actions.length === 0 
              ? "No remediation actions have been created yet."
              : "No actions match your current filters."
            }
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Environment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredActions.map((action) => (
                  <tr 
                    key={action.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                    onClick={() => onActionSelect(action)}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <i className={`fas ${
                            action.action_type === 'oci_cli' ? 'fa-cloud' :
                            action.action_type === 'terraform' ? 'fa-code-branch' :
                            action.action_type === 'kubernetes' ? 'fa-dharmachakra' :
                            action.action_type === 'script' ? 'fa-terminal' :
                            'fa-cogs'
                          } text-gray-400`}></i>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {action.title}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {action.service_name} • {(action.action_type ?? '').toString().replace('_', ' ').toUpperCase()}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        remediationService.getStatusColor(action.status)
                      }`}>
                        {(action.status ?? '').toString().replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        remediationService.getSeverityColor(action.severity)
                      }`}>
                        {(action.severity ?? 'low').toString().toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {action.environment}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {remediationService.formatTimestamp(action.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      {/* Quick action buttons */}
                      {action.status === 'pending' && canApprove && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleQuickAction(action.id, 'approve');
                          }}
                          disabled={loadingActions.has(action.id)}
                          className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                          title="Approve Action"
                        >
                          {loadingActions.has(action.id) ? (
                            <LoadingSpinner size="sm" />
                          ) : (
                            <i className="fas fa-check"></i>
                          )}
                        </button>
                      )}
                      
                      {action.status === 'approved' && canExecute && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleQuickAction(action.id, 'execute');
                          }}
                          disabled={loadingActions.has(action.id)}
                          className="text-green-600 hover:text-green-900 disabled:opacity-50"
                          title="Execute (Dry Run)"
                        >
                          {loadingActions.has(action.id) ? (
                            <LoadingSpinner size="sm" />
                          ) : (
                            <i className="fas fa-play"></i>
                          )}
                        </button>
                      )}
                      
                      {['pending', 'queued'].includes(action.status) && canExecute && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleQuickAction(action.id, 'cancel');
                          }}
                          disabled={loadingActions.has(action.id)}
                          className="text-red-600 hover:text-red-900 disabled:opacity-50"
                          title="Cancel Action"
                        >
                          {loadingActions.has(action.id) ? (
                            <LoadingSpinner size="sm" />
                          ) : (
                            <i className="fas fa-times"></i>
                          )}
                        </button>
                      )}
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onActionSelect(action);
                        }}
                        className="text-gray-600 hover:text-gray-900"
                        title="View Details"
                      >
                        <i className="fas fa-eye"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
} 