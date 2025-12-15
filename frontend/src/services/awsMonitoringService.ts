import { useQuery, UseQueryResult } from '@tanstack/react-query';
import apiClient from './apiClient';
import { AlertSummary, Alert, HealthStatus, MonitoringDashboard } from './monitoringService';

export interface AwsDashboardAlert {
  id: string;
  title: string;
  severity: string;
  service: string;
  resource: string;
  state: string;
  last_triggered: string;
  description: string;
  recommended_action: string;
}

export interface AwsMonitoringScope {
  id: string;
  name: string;
  code: string;
  type: string;
  lifecycle_state: string;
  description?: string;
}

export interface AwsDashboardResponse extends MonitoringDashboard {
  eks?: {
    cluster_count: number;
    active_nodes: number;
    pods_running: number;
    failing_workloads: number;
    clusters: Array<{
      name: string;
      region: string;
      status: string;
      health_score: number;
      node_groups: number;
      node_pressure: string | null;
      pod_restarts_24h: number;
    }>;
    insights: Array<{
      id: string;
      severity: string;
      summary: string;
      recommendation: string;
    }>;
  };
  alerts?: AwsDashboardAlert[];
}

const awsMonitoringQueryKeys = {
  all: ['aws-monitoring'] as const,
  scopes: () => [...awsMonitoringQueryKeys.all, 'scopes'] as const,
  summary: (scopeId: string) => [...awsMonitoringQueryKeys.all, 'summary', scopeId] as const,
  alarms: (scopeId: string) => [...awsMonitoringQueryKeys.all, 'alarms', scopeId] as const,
  history: (scopeId: string) => [...awsMonitoringQueryKeys.all, 'history', scopeId] as const,
  dashboard: (scopeId: string) => [...awsMonitoringQueryKeys.all, 'dashboard', scopeId] as const,
  health: (scopeId: string) => [...awsMonitoringQueryKeys.all, 'health', scopeId] as const,
};

class AwsMonitoringService {
  private extractResourceFromQuery(query?: string): string {
    if (!query) return 'Unknown Resource';

    const resourceMatches = query.match(/resourceDisplayName\s*=\s*"([^"]+)"/);
    if (resourceMatches) return resourceMatches[1];

    const idMatches = query.match(/resourceId\s*=\s*"([^"]+)"/);
    if (idMatches) {
      const rawId = idMatches[1];
      const parts = rawId.split('.');
      return parts[parts.length - 1] || rawId;
    }

    const metricMatches = query.match(/(\w+)\[/);
    if (metricMatches) return `${metricMatches[1]} metrics`;

    return 'Resource from query';
  }

  private deriveCategoryFromNamespace(namespace?: string): string {
    if (!namespace) return 'Infrastructure';
    const ns = namespace.toLowerCase();

    if (ns.includes('eks') || ns.includes('kubernetes') || ns.includes('containers')) return 'Kubernetes';
    if (ns.includes('database') || ns.includes('rds') || ns.includes('aurora') || ns.includes('dynamodb')) return 'Database';
    if (ns.includes('ec2') || ns.includes('compute') || ns.includes('lambda')) return 'Compute';
    if (ns.includes('network') || ns.includes('vpc') || ns.includes('elb') || ns.includes('alb') || ns.includes('nlb')) return 'Network';
    if (ns.includes('storage') || ns.includes('s3') || ns.includes('efs') || ns.includes('ebs')) return 'Storage';

    return 'Infrastructure';
  }

  async getScopes(): Promise<AwsMonitoringScope[]> {
    const response = await apiClient.get<AwsMonitoringScope[]>('/aws/monitoring/scopes');
    return response.data;
  }

  async getAlertSummary(scopeId: string): Promise<AlertSummary> {
    const response = await apiClient.get<AlertSummary>('/aws/monitoring/alerts/summary', {
      params: { scope_id: scopeId },
    });
    const summary = response.data;

    const rawScore = typeof summary.health_score === 'number' ? summary.health_score : 0.7;
    const normalized = rawScore <= 1 ? rawScore * 100 : rawScore;
    summary.health_score = Math.min(100, Math.max(0, normalized));

    return summary;
  }

  async getAlarms(scopeId: string): Promise<Alert[]> {
    const response = await apiClient.get('/aws/monitoring/alarms', {
      params: { scope_id: scopeId },
    });
    const rawAlarms = response.data as Array<Record<string, any>>;

    return rawAlarms.map((alarm) => ({
      id: alarm.id,
      name: alarm.display_name || alarm.title || 'Unnamed Alert',
      severity: alarm.severity || 'MEDIUM',
      status: alarm.lifecycle_state === 'ACTIVE' ? 'OPEN' : alarm.lifecycle_state === 'FIRING' ? 'OPEN' : 'ACKNOWLEDGED',
      description: alarm.query || alarm.description || 'No monitoring query specified',
      service: alarm.namespace || alarm.service || 'Unknown Service',
      resource:
        this.extractResourceFromQuery(alarm.query) || alarm.metric_compartment_id || alarm.resource || 'Unknown Resource',
      timestamp: alarm.time_created || alarm.last_triggered || new Date().toISOString(),
      lastUpdate: alarm.time_updated || alarm.time_created || alarm.last_triggered || new Date().toISOString(),
      category: this.deriveCategoryFromNamespace(alarm.namespace || alarm.service),
      display_name: alarm.display_name,
      namespace: alarm.namespace,
      query: alarm.query,
      lifecycle_state: alarm.lifecycle_state,
      is_enabled: alarm.is_enabled,
      metric_compartment_id: alarm.metric_compartment_id,
      time_created: alarm.time_created,
      time_updated: alarm.time_updated,
    }));
  }

  async getAlarmHistory(scopeId: string): Promise<any[]> {
    const response = await apiClient.get('/aws/monitoring/alarms/history', {
      params: { scope_id: scopeId },
    });
    return response.data as any[];
  }

  async getDashboard(scopeId: string): Promise<AwsDashboardResponse> {
    const response = await apiClient.get<AwsDashboardResponse>('/aws/monitoring/dashboard', {
      params: { scope_id: scopeId },
    });
    const dashboard = response.data;

    if (dashboard.summary) {
      const rawScore = typeof dashboard.summary.health_score === 'number' ? dashboard.summary.health_score : 0.7;
      const normalized = rawScore <= 1 ? rawScore * 100 : rawScore;
      dashboard.summary.health_score = Math.min(100, Math.max(0, normalized));
    }

    return dashboard;
  }

  async getHealthStatus(scopeId: string): Promise<HealthStatus> {
    const summary = await this.getAlertSummary(scopeId);
    const healthScore = summary.health_score;

    return {
      compartment_id: scopeId,
      overall_status:
        summary.severity_breakdown.CRITICAL > 0
          ? 'CRITICAL'
          : summary.severity_breakdown.HIGH > 0
          ? 'WARNING'
          : healthScore >= 90
          ? 'HEALTHY'
          : healthScore >= 70
          ? 'WARNING'
          : healthScore >= 50
          ? 'DEGRADED'
          : 'CRITICAL',
      status_color:
        summary.severity_breakdown.CRITICAL > 0
          ? 'red'
          : summary.severity_breakdown.HIGH > 0
          ? 'yellow'
          : healthScore >= 90
          ? 'green'
          : healthScore >= 70
          ? 'yellow'
          : healthScore >= 50
          ? 'orange'
          : 'red',
      health_score: healthScore,
      critical_alerts: summary.severity_breakdown.CRITICAL || 0,
      high_alerts: summary.severity_breakdown.HIGH || 0,
      total_active_alarms: summary.active_alarms,
      alert_rate_24h: typeof summary.recent_activity?.alert_rate === 'number' ? summary.recent_activity.alert_rate : 0,
      last_updated: summary.timestamp,
    };
  }

  async testIntegration(scopeId?: string): Promise<any> {
    const targetScopeId = scopeId || 'aws:region:us-east-1';
    const summary = await this.getAlertSummary(targetScopeId);
    return {
      status: 'success',
      monitoring_available: true,
      test_summary: summary,
      timestamp: new Date().toISOString(),
      compartment_id: targetScopeId,
    };
  }
}

export const awsMonitoringService = new AwsMonitoringService();

export function useAwsMonitoringScopes(): UseQueryResult<AwsMonitoringScope[], Error> {
  return useQuery({
    queryKey: awsMonitoringQueryKeys.scopes(),
    queryFn: () => awsMonitoringService.getScopes(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAwsMonitoringSummary(scopeId: string | undefined): UseQueryResult<AlertSummary, Error> {
  return useQuery({
    queryKey: scopeId ? awsMonitoringQueryKeys.summary(scopeId) : ['aws-monitoring', 'summary', 'disabled'],
    queryFn: () => awsMonitoringService.getAlertSummary(scopeId as string),
    enabled: !!scopeId,
  });
}

export function useAwsMonitoringAlarms(scopeId: string | undefined): UseQueryResult<Alert[], Error> {
  return useQuery({
    queryKey: scopeId ? awsMonitoringQueryKeys.alarms(scopeId) : ['aws-monitoring', 'alarms', 'disabled'],
    queryFn: () => awsMonitoringService.getAlarms(scopeId as string),
    enabled: !!scopeId,
  });
}

export function useAwsMonitoringHistory(scopeId: string | undefined): UseQueryResult<any[], Error> {
  return useQuery({
    queryKey: scopeId ? awsMonitoringQueryKeys.history(scopeId) : ['aws-monitoring', 'history', 'disabled'],
    queryFn: () => awsMonitoringService.getAlarmHistory(scopeId as string),
    enabled: !!scopeId,
  });
}

export function useAwsMonitoringDashboard(scopeId: string | undefined): UseQueryResult<AwsDashboardResponse, Error> {
  return useQuery({
    queryKey: scopeId ? awsMonitoringQueryKeys.dashboard(scopeId) : ['aws-monitoring', 'dashboard', 'disabled'],
    queryFn: () => awsMonitoringService.getDashboard(scopeId as string),
    enabled: !!scopeId,
  });
}

export function useAwsMonitoringHealth(scopeId: string | undefined): UseQueryResult<HealthStatus, Error> {
  return useQuery({
    queryKey: scopeId ? awsMonitoringQueryKeys.health(scopeId) : ['aws-monitoring', 'health', 'disabled'],
    queryFn: () => awsMonitoringService.getHealthStatus(scopeId as string),
    enabled: !!scopeId,
  });
}
