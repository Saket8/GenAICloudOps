import React, { useState, useEffect } from 'react';
import { RemediationAction, ActionStatusResponse, remediationService } from '../../../services/remediationService';
import { useAuth } from '../../../contexts/AuthContext';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

interface ActionDetailsProps {
  action: RemediationAction;
  onClose: () => void;
  onActionUpdate: (action: RemediationAction) => void;
}

export function ActionDetails({ action, onClose, onActionUpdate }: ActionDetailsProps) {
  const { permissions } = useAuth();
  const [actionDetails, setActionDetails] = useState<ActionStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [approving, setApproving] = useState(false);
  const [rolling, setRolling] = useState(false);

  useEffect(() => {
    loadActionDetails();
  }, [action.id]);

  const loadActionDetails = async () => {
    setLoading(true);
    try {
      const details = await remediationService.getActionStatus(action.id);
      setActionDetails(details);
    } catch (error) {
      console.error('Failed to load action details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    setApproving(true);
    try {
      await remediationService.approveAction(action.id, 'Approved via dashboard');
      await loadActionDetails();
      onActionUpdate({ ...action, status: 'approved' });
    } catch (error: any) {
      alert(`Failed to approve action: ${error.message}`);
    } finally {
      setApproving(false);
    }
  };

  const handleExecute = async (isDryRun: boolean = false) => {
    setExecuting(true);
    try {
      await remediationService.executeAction(action.id, isDryRun);
      await loadActionDetails();
      onActionUpdate({ 
        ...action, 
        status: isDryRun ? action.status : 'in_progress' 
      });
    } catch (error: any) {
      alert(`Failed to execute action: ${error.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const handleRollback = async () => {
    setRolling(true);
    try {
      await remediationService.rollbackAction(action.id);
      await loadActionDetails();
      onActionUpdate({ ...action, status: 'rolled_back' });
    } catch (error: any) {
      alert(`Failed to rollback action: ${error.message}`);
    } finally {
      setRolling(false);
    }
  };

  const canApprove = permissions?.can_approve_remediation && action.status === 'pending';
  const canExecute = permissions?.can_execute_remediation && ['approved', 'queued'].includes(action.status);
  const canRollback = permissions?.can_execute_remediation && action.status === 'completed' && !action.rollback_executed;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white dark:bg-gray-800">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              <i className="fas fa-cogs mr-2 text-blue-500"></i>
              Action Details
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              ID: {action.id} • Created {remediationService.formatTimestamp(action.created_at)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <i className="fas fa-times text-xl"></i>
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
            <span className="ml-2 text-gray-600 dark:text-gray-400">Loading details...</span>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status and Actions */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                    remediationService.getStatusColor(action.status)
                  }`}>
                    {(action.status ?? '').toString().replace('_', ' ').toUpperCase() || 'UNKNOWN'}
                  </span>
                  
                  <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                    remediationService.getSeverityColor(action.severity)
                  }`}>
                    {(action.severity ?? 'low').toString().toUpperCase()}
                  </span>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-2">
                  {canApprove && (
                    <button
                      onClick={handleApprove}
                      disabled={approving}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                      {approving ? <LoadingSpinner size="sm" /> : <i className="fas fa-check mr-1"></i>}
                      Approve
                    </button>
                  )}
                  
                  {canExecute && (
                    <>
                      <button
                        onClick={() => handleExecute(true)}
                        disabled={executing}
                        className="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
                      >
                        {executing ? <LoadingSpinner size="sm" /> : <i className="fas fa-vial mr-1"></i>}
                        Dry Run
                      </button>
                      <button
                        onClick={() => handleExecute(false)}
                        disabled={executing}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                      >
                        {executing ? <LoadingSpinner size="sm" /> : <i className="fas fa-play mr-1"></i>}
                        Execute
                      </button>
                    </>
                  )}
                  
                  {canRollback && (
                    <button
                      onClick={handleRollback}
                      disabled={rolling}
                      className="px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
                    >
                      {rolling ? <LoadingSpinner size="sm" /> : <i className="fas fa-undo mr-1"></i>}
                      Rollback
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">Basic Information</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Title</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">{action.title}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Service</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">{action.service_name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Environment</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">{action.environment}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Action Type</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">
                      <i className={`fas ${
                        action.action_type === 'oci_cli' ? 'fa-cloud' :
                        action.action_type === 'terraform' ? 'fa-code-branch' :
                        action.action_type === 'kubernetes' ? 'fa-dharmachakra' :
                        action.action_type === 'script' ? 'fa-terminal' :
                        'fa-cogs'
                      } mr-1`}></i>
                      {(action.action_type ?? '').toString().replace('_', ' ').toUpperCase() || 'N/A'}
                    </dd>
                  </div>
                </dl>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">Execution Info</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Duration</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">
                      {remediationService.formatDuration(action.execution_duration)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Started</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">
                      {remediationService.formatTimestamp(action.started_at)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Completed</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">
                      {remediationService.formatTimestamp(action.completed_at)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Rollback</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">
                      {action.rollback_executed ? 'Yes' : 'No'}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Description */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">Description</h3>
              <p className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded">
                {action.description}
              </p>
            </div>

            {/* Command */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">Command</h3>
              <pre className="text-sm text-gray-700 dark:text-gray-300 bg-gray-900 text-green-400 p-3 rounded font-mono overflow-x-auto">
{action.action_command}
              </pre>
            </div>

            {/* Execution Output */}
            {action.execution_output && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">Execution Output</h3>
                <pre className="text-sm bg-gray-900 text-white p-3 rounded font-mono overflow-x-auto max-h-64">
{action.execution_output}
                </pre>
              </div>
            )}

            {/* Execution Error */}
            {action.execution_error && (
              <div>
                <h3 className="text-lg font-medium text-red-600 dark:text-red-400 mb-3">
                  <i className="fas fa-exclamation-triangle mr-1"></i>
                  Execution Error
                </h3>
                <pre className="text-sm bg-red-900 text-red-100 p-3 rounded font-mono overflow-x-auto max-h-64">
{action.execution_error}
                </pre>
              </div>
            )}

            {/* Audit Trail */}
            {actionDetails?.audit_logs && actionDetails.audit_logs.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">Audit Trail</h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {actionDetails.audit_logs.map((log) => (
                    <div key={log.id} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 p-2 rounded text-sm">
                      <div>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {(log.event_type ?? '').toString().replace('_', ' ')}
                        </span>
                        <span className="text-gray-600 dark:text-gray-400 ml-2">
                          {log.event_description}
                        </span>
                      </div>
                      <span className="text-gray-500 dark:text-gray-400 text-xs">
                        {remediationService.formatTimestamp(log.timestamp)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 