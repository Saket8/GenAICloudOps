import { api } from './apiClient';

// Types for Remediation Data
export interface RemediationAction {
  id: number;
  title: string;
  description: string;
  status: ActionStatus;
  action_type: ActionType;
  severity: Severity;
  environment: string;
  service_name: string;
  created_at?: string;
  requires_approval: boolean;
  rollback_executed: boolean;
  action_command?: string;
  execution_result?: string;
  execution_output?: string;
  execution_error?: string;
  execution_duration?: number;
  created_by?: number;
  approved_by?: number;
  executed_by?: number;
  approved_at?: string;
  started_at?: string;
  completed_at?: string;
}

export interface CreateActionRequest {
  title: string;
  description: string;
  action_type: ActionType;
  action_command: string;
  issue_details: string;
  environment: string;
  service_name: string;
  severity: Severity;
  action_parameters?: Record<string, any>;
  resource_info?: Record<string, any>;
  requires_approval?: boolean;
  rollback_command?: string;
}

export interface ExecutionResult {
  status: string;
  output: string;
  error?: string;
  duration: number;
}

export interface ActionStatusResponse {
  action: RemediationAction;
  audit_logs: AuditLog[];
  workflow?: ApprovalWorkflow;
}

export interface AuditLog {
  id: number;
  event_type: string;
  event_description: string;
  timestamp: string;
  user_id?: number;
}

export interface ApprovalWorkflow {
  id: number;
  status: string;
  current_step: number;
  total_steps: number;
}

export type ActionStatus = 
  | 'pending' 
  | 'approved' 
  | 'rejected' 
  | 'queued' 
  | 'in_progress' 
  | 'completed' 
  | 'failed' 
  | 'rolled_back' 
  | 'cancelled';

export type ActionType = 
  | 'oci_cli' 
  | 'terraform' 
  | 'script' 
  | 'api_call' 
  | 'kubernetes';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface ActionTypeInfo {
  type: string;
  description: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  timestamp: string;
  checks: {
    database: string;
    oci_service: string;
    terraform: string;
  };
}

class RemediationService {
  // Health check
  async getHealth(): Promise<HealthStatus> {
    const response = await api.get<HealthStatus>('/remediation/health');
    return response.data;
  }

  // Get all actions with optional filtering
  async getActions(params?: {
    status_filter?: string;
    environment_filter?: string;
    severity_filter?: string;
    limit?: number;
    offset?: number;
  }): Promise<RemediationAction[]> {
    const response = await api.get<RemediationAction[]>('/remediation/actions', { params });
    return response.data;
  }

  // Create new remediation action
  async createAction(actionData: CreateActionRequest): Promise<RemediationAction> {
    const response = await api.post<RemediationAction>('/remediation/actions', actionData);
    return response.data;
  }

  // Get detailed action status
  async getActionStatus(actionId: number): Promise<ActionStatusResponse> {
    const response = await api.get<ActionStatusResponse>(`/remediation/actions/${actionId}/status`);
    return response.data;
  }

  // Approve an action
  async approveAction(actionId: number, comment?: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/remediation/actions/${actionId}/approve`, {
      approval_comment: comment
    });
    return response.data;
  }

  // Execute an action
  async executeAction(actionId: number, isDryRun: boolean = false): Promise<ExecutionResult> {
    const response = await api.post<ExecutionResult>(`/remediation/actions/${actionId}/execute`, {
      is_dry_run: isDryRun
    });
    return response.data;
  }

  // Rollback an action
  async rollbackAction(actionId: number): Promise<ExecutionResult> {
    const response = await api.post<ExecutionResult>(`/remediation/actions/${actionId}/rollback`);
    return response.data;
  }

  // Cancel a pending action
  async cancelAction(actionId: number): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/remediation/actions/${actionId}`);
    return response.data;
  }

  // Get available action types
  async getActionTypes(): Promise<ActionTypeInfo[]> {
    const response = await api.get<{ action_types: ActionTypeInfo[] }>('/remediation/actions/types');
    return response.data.action_types;
  }

  // Get available action statuses
  async getActionStatuses(): Promise<{ status: string; description: string }[]> {
    const response = await api.get<{ statuses: { status: string; description: string }[] }>('/remediation/actions/statuses');
    return response.data.statuses;
  }

  // Get available severity levels
  async getSeverities(): Promise<{ severity: string; description: string }[]> {
    const response = await api.get<{ severities: { severity: string; description: string }[] }>('/remediation/actions/severities');
    return response.data.severities;
  }

  // Helper method to get status badge color
  getStatusColor(status: ActionStatus): string {
    const colorMap: Record<ActionStatus, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      rejected: 'bg-red-100 text-red-800',
      queued: 'bg-indigo-100 text-indigo-800',
      in_progress: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      rolled_back: 'bg-orange-100 text-orange-800',
      cancelled: 'bg-gray-100 text-gray-800'
    };
    return colorMap[status] || 'bg-gray-100 text-gray-800';
  }

  // Helper method to get severity color
  getSeverityColor(severity: Severity): string {
    const colorMap: Record<Severity, string> = {
      low: 'bg-blue-100 text-blue-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return colorMap[severity] || 'bg-gray-100 text-gray-800';
  }

  // Helper method to format duration
  formatDuration(seconds?: number): string {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  }

  // Helper method to format timestamp
  formatTimestamp(timestamp?: string): string {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  }

  // Generate remediation actions from real OCI data
  async generateFromOCI(environment: string = 'production'): Promise<{
    success: boolean;
    message: string;
    actions_created: number;
    actions: Array<{
      id: number;
      title: string;
      severity: string;
      environment: string;
      service_name: string;
    }>;
  }> {
    const response = await api.post('/remediation/actions/generate-from-oci', null, {
      params: { environment }
    });
    return response.data;
  }

  // Clean up test/mock data
  async cleanupTestData(): Promise<{
    success: boolean;
    message: string;
    deleted_count: number;
  }> {
    const response = await api.delete('/remediation/actions/cleanup-test-data');
    return response.data;
  }
}

export const remediationService = new RemediationService(); 