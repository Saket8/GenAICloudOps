import React, { useState, useEffect } from 'react';
import { CreateActionRequest, ActionType, Severity, remediationService, RemediationAction } from '../../../services/remediationService';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

interface CreateActionFormProps {
  onActionCreated: (action: RemediationAction) => void;
  onCancel: () => void;
}

export function CreateActionForm({ onActionCreated, onCancel }: CreateActionFormProps) {
  const [formData, setFormData] = useState<CreateActionRequest>({
    title: '',
    description: '',
    action_type: 'oci_cli',
    action_command: '',
    issue_details: '',
    environment: '',
    service_name: '',
    severity: 'medium',
    action_parameters: {},
    resource_info: {},
    requires_approval: true,
    rollback_command: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [actionTypes, setActionTypes] = useState<{ type: string; description: string }[]>([]);

  useEffect(() => {
    loadActionTypes();
  }, []);

  const loadActionTypes = async () => {
    try {
      const types = await remediationService.getActionTypes();
      setActionTypes(types);
    } catch (error) {
      console.error('Failed to load action types:', error);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (!formData.action_command.trim()) {
      newErrors.action_command = 'Action command is required';
    }

    if (!formData.issue_details.trim()) {
      newErrors.issue_details = 'Issue details are required';
    }

    if (!formData.environment.trim()) {
      newErrors.environment = 'Environment is required';
    }

    if (!formData.service_name.trim()) {
      newErrors.service_name = 'Service name is required';
    }

    // Validate command based on action type
    if (formData.action_type === 'oci_cli' && !formData.action_command.trim().startsWith('oci ')) {
      newErrors.action_command = 'OCI CLI commands must start with "oci "';
    }

    if (formData.action_type === 'terraform' && !formData.action_command.trim().startsWith('terraform ')) {
      newErrors.action_command = 'Terraform commands must start with "terraform "';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    
    try {
      const newAction = await remediationService.createAction(formData);
      onActionCreated(newAction);
    } catch (error: any) {
      console.error('Failed to create action:', error);
      setErrors({ submit: error.message || 'Failed to create action' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof CreateActionRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const actionTypeOptions = [
    { value: 'oci_cli', label: 'OCI CLI', icon: 'fas fa-cloud' },
    { value: 'terraform', label: 'Terraform', icon: 'fas fa-code-branch' },
    { value: 'kubernetes', label: 'Kubernetes', icon: 'fas fa-dharmachakra' },
    { value: 'script', label: 'Script', icon: 'fas fa-terminal' },
    { value: 'api_call', label: 'API Call', icon: 'fas fa-cogs' }
  ];

  const severityOptions = [
    { value: 'low', label: 'Low', color: 'text-blue-600' },
    { value: 'medium', label: 'Medium', color: 'text-yellow-600' },
    { value: 'high', label: 'High', color: 'text-orange-600' },
    { value: 'critical', label: 'Critical', color: 'text-red-600' }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          <i className="fas fa-plus mr-2 text-blue-500"></i>
          Create Remediation Action
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Create a new automated remediation action for infrastructure issues
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Title and Description */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              placeholder="e.g., Restart unresponsive OCI instance"
              className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white ${
                errors.title ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.title && <p className="mt-1 text-sm text-red-500">{errors.title}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Service Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.service_name}
              onChange={(e) => handleInputChange('service_name', e.target.value)}
              placeholder="e.g., web-app-01"
              className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white ${
                errors.service_name ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.service_name && <p className="mt-1 text-sm text-red-500">{errors.service_name}</p>}
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Description <span className="text-red-500">*</span>
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            placeholder="Detailed description of what this action does..."
            rows={3}
            className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white ${
              errors.description ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.description && <p className="mt-1 text-sm text-red-500">{errors.description}</p>}
        </div>

        {/* Action Type and Severity */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Action Type <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.action_type}
              onChange={(e) => handleInputChange('action_type', e.target.value as ActionType)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white"
            >
              {actionTypeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Severity <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.severity}
              onChange={(e) => handleInputChange('severity', e.target.value as Severity)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white"
            >
              {severityOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Environment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Environment <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.environment}
            onChange={(e) => handleInputChange('environment', e.target.value)}
            placeholder="e.g., production, staging, development"
            className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white ${
              errors.environment ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.environment && <p className="mt-1 text-sm text-red-500">{errors.environment}</p>}
        </div>

        {/* Action Command */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Action Command <span className="text-red-500">*</span>
          </label>
          <textarea
            value={formData.action_command}
            onChange={(e) => handleInputChange('action_command', e.target.value)}
            placeholder={
              formData.action_type === 'oci_cli' ? 'oci compute instance action --instance-id <INSTANCE_ID> --action SOFTRESET' :
              formData.action_type === 'terraform' ? 'terraform apply -var="instance_id=<INSTANCE_ID>" -auto-approve' :
              formData.action_type === 'kubernetes' ? 'kubectl restart deployment/<DEPLOYMENT_NAME>' :
              'Enter the command to execute...'
            }
            rows={3}
            className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white font-mono text-sm ${
              errors.action_command ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.action_command && <p className="mt-1 text-sm text-red-500">{errors.action_command}</p>}
        </div>

        {/* Issue Details */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Issue Details <span className="text-red-500">*</span>
          </label>
          <textarea
            value={formData.issue_details}
            onChange={(e) => handleInputChange('issue_details', e.target.value)}
            placeholder="Describe the issue this action will resolve..."
            rows={3}
            className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white ${
              errors.issue_details ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.issue_details && <p className="mt-1 text-sm text-red-500">{errors.issue_details}</p>}
        </div>

        {/* Rollback Command */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Rollback Command (Optional)
          </label>
          <textarea
            value={formData.rollback_command}
            onChange={(e) => handleInputChange('rollback_command', e.target.value)}
            placeholder="Command to rollback this action if needed..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:text-white font-mono text-sm"
          />
        </div>

        {/* Options */}
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Options</h3>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.requires_approval}
                onChange={(e) => handleInputChange('requires_approval', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Requires approval before execution
              </span>
            </label>
          </div>
        </div>

        {/* Submit Error */}
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            <i className="fas fa-exclamation-triangle mr-2"></i>
            {errors.submit}
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-500 dark:hover:bg-gray-600"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" />
                <span className="ml-2">Creating...</span>
              </>
            ) : (
              <>
                <i className="fas fa-plus mr-2"></i>
                Create Action
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
} 