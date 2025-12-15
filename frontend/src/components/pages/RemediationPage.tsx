import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { remediationService, RemediationAction, HealthStatus } from '../../services/remediationService';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { ErrorBoundary } from '../ui/ErrorBoundary';
import { ActionsList } from './remediation/ActionsList';
import { CreateActionForm } from './remediation/CreateActionForm';
import { ActionDetails } from './remediation/ActionDetails';
import { SystemStatus } from './remediation/SystemStatus';

type ActiveTab = 'actions' | 'create' | 'status';

export function RemediationPage() {
  const { user, permissions } = useAuth();
  const [activeTab, setActiveTab] = useState<ActiveTab>('actions');
  const [actions, setActions] = useState<RemediationAction[]>([]);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [selectedAction, setSelectedAction] = useState<RemediationAction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCleaningUp, setIsCleaningUp] = useState(false);

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load health status and actions in parallel
      const [health, actionsData] = await Promise.all([
        remediationService.getHealth().catch(() => null),
        remediationService.getActions().catch(() => [])
      ]);
      
      setHealthStatus(health);
      setActions(actionsData);
    } catch (err: any) {
      setError('Failed to load remediation data');
      console.error('Error loading remediation data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanupTestData = async () => {
    if (!confirm('⚠️ This will permanently delete all test/mock remediation data. Are you sure?')) {
      return;
    }
    
    setIsCleaningUp(true);
    setError(null);
    
    try {
      const result = await remediationService.cleanupTestData();
      if (result.success) {
        await loadData(); // Reload to reflect changes
        alert(`✅ ${result.message}\nDeleted ${result.deleted_count} test actions.`);
      }
    } catch (err: any) {
      const errorMsg = 'Failed to cleanup test data';
      setError(errorMsg);
      console.error('Error cleaning up test data:', err);
      alert(`❌ ${errorMsg}: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsCleaningUp(false);
    }
  };

  const handleActionCreated = (newAction: RemediationAction) => {
    setActions(prev => [newAction, ...prev]);
    setActiveTab('actions');
  };

  const handleActionUpdated = (updatedAction: RemediationAction) => {
    setActions(prev => prev.map(action => 
      action.id === updatedAction.id ? updatedAction : action
    ));
    if (selectedAction?.id === updatedAction.id) {
      setSelectedAction(updatedAction);
    }
  };

  const handleActionDeleted = (deletedActionId: number) => {
    setActions(prev => prev.filter(action => action.id !== deletedActionId));
    if (selectedAction?.id === deletedActionId) {
      setSelectedAction(null);
    }
  };

  const tabs = [
    {
      id: 'actions' as const,
      name: 'Actions',
      icon: 'fas fa-list',
      count: actions.length,
      description: 'View and manage remediation actions'
    },
    {
      id: 'create' as const,
      name: 'Create Action',
      icon: 'fas fa-plus',
      description: 'Create new remediation action',
      requiresPermission: 'can_execute_remediation'
    },
    {
      id: 'status' as const,
      name: 'System Status',
      icon: 'fas fa-heartbeat',
      description: 'View remediation system health'
    }
  ];

  // Filter tabs based on permissions
  const visibleTabs = tabs.filter(tab => {
    if (!tab.requiresPermission) return true;
    return permissions?.[tab.requiresPermission as keyof typeof permissions];
  });

  if (loading && !actions.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
        <span className="ml-2 text-gray-600 dark:text-gray-400">Loading remediation panel...</span>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                <i className="fas fa-cogs mr-3 text-blue-500"></i>
                Automated Remediation
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Manage infrastructure remediation actions with AI-powered automation
              </p>
            </div>
            
            {/* Action buttons and health indicator */}
            <div className="flex items-center space-x-4">
              {/* Cleanup Test Data Button */}
              {permissions?.can_execute_remediation && (
                <button
                  onClick={handleCleanupTestData}
                  disabled={isCleaningUp}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600"
                >
                  {isCleaningUp ? (
                    <>
                      <i className="fas fa-spinner fa-spin mr-2"></i>
                      Cleaning...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-trash-alt mr-2"></i>
                      Cleanup Test Data
                    </>
                  )}
                </button>
              )}
              
              {/* Refresh Button */}
              <button
                onClick={loadData}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-2"></i>
                    Loading...
                  </>
                ) : (
                  <>
                    <i className="fas fa-sync-alt mr-2"></i>
                    Refresh
                  </>
                )}
              </button>
              
              {/* Health indicator */}
              {healthStatus && (
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    healthStatus.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    System {healthStatus.status}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex space-x-8 px-6">
              {visibleTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`group flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <i className={`${tab.icon} mr-2`}></i>
                  {tab.name}
                  {tab.count !== undefined && (
                    <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {tab.count}
                    </span>
                  )}
                  
                  {/* Tooltip */}
                  <div className="absolute invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-gray-900 text-white text-xs rounded py-1 px-2 mt-12 ml-4 whitespace-nowrap z-50">
                    {tab.description}
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
                  </div>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                <div className="flex items-center">
                  <i className="fas fa-exclamation-triangle mr-2"></i>
                  {error}
                  <button
                    onClick={loadData}
                    className="ml-auto text-red-600 hover:text-red-800"
                  >
                    <i className="fas fa-redo"></i> Retry
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'actions' && (
              <ActionsList
                actions={actions}
                onActionSelect={setSelectedAction}
                onActionUpdate={handleActionUpdated}
                onActionDelete={handleActionDeleted}
                onRefresh={loadData}
              />
            )}

            {activeTab === 'create' && (
              <CreateActionForm
                onActionCreated={handleActionCreated}
                onCancel={() => setActiveTab('actions')}
              />
            )}

            {activeTab === 'status' && (
              <SystemStatus
                healthStatus={healthStatus}
                onRefresh={loadData}
              />
            )}
          </div>
        </div>

        {/* Action Details Modal */}
        {selectedAction && (
          <ActionDetails
            action={selectedAction}
            onClose={() => setSelectedAction(null)}
            onActionUpdate={handleActionUpdated}
          />
        )}
      </div>
    </ErrorBoundary>
  );
} 