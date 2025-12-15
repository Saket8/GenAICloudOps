import React, { useEffect, useMemo, useState } from 'react';
import { LoadingSpinner } from '../../ui/LoadingSpinner';
import { CompartmentSelector } from '../../ui/CompartmentSelector';
import { AlertSummary, Alert, HealthStatus } from '../../../services/monitoringService';
import {
  awsMonitoringService,
  useAwsMonitoringScopes,
  useAwsMonitoringSummary,
  useAwsMonitoringAlarms,
  useAwsMonitoringDashboard,
  useAwsMonitoringHealth,
  AwsDashboardResponse,
} from '../../../services/awsMonitoringService';

const BADGE_COLOR_MAP: Record<string, string> = {
  red: 'bg-red-100 text-red-800',
  orange: 'bg-orange-100 text-orange-800',
  yellow: 'bg-yellow-100 text-yellow-800',
  green: 'bg-green-100 text-green-800',
  blue: 'bg-blue-100 text-blue-800',
  gray: 'bg-gray-100 text-gray-800',
};

const TEXT_COLOR_MAP: Record<string, string> = {
  red: 'text-red-600',
  orange: 'text-orange-600',
  yellow: 'text-yellow-600',
  green: 'text-green-600',
  blue: 'text-blue-600',
  gray: 'text-gray-600',
};

const StatusBadge: React.FC<{ status: string; color: string }> = ({ status, color }) => (
  <span
    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
      BADGE_COLOR_MAP[color] || BADGE_COLOR_MAP.gray
    }`}
  >
    {status}
  </span>
);

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const colors: Record<string, string> = {
    CRITICAL: 'red',
    HIGH: 'orange',
    MEDIUM: 'yellow',
    LOW: 'blue',
    INFO: 'gray',
  };
  const color = colors[severity] || 'gray';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        BADGE_COLOR_MAP[color] || BADGE_COLOR_MAP.gray
      }`}
    >
      {severity}
    </span>
  );
};

const HealthScoreCard: React.FC<{ health: HealthStatus }> = ({ health }) => {
  const getHealthColor = (score: number) => {
    if (score >= 90) return 'green';
    if (score >= 70) return 'yellow';
    if (score >= 50) return 'orange';
    return 'red';
  };

  const color = getHealthColor(health.health_score);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Health Score</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">Overall AWS monitoring health</p>
        </div>
        <div className="text-right">
          <div className={`text-3xl font-bold ${TEXT_COLOR_MAP[color] || TEXT_COLOR_MAP.gray}`}>
            {health.health_score.toFixed(1)}
          </div>
          <StatusBadge status={health.overall_status} color={health.status_color} />
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400">Critical Alerts:</span>
          <span className="ml-2 font-medium text-red-600">{health.critical_alerts}</span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">High Alerts:</span>
          <span className="ml-2 font-medium text-orange-600">{health.high_alerts}</span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Active Alarms:</span>
          <span className="ml-2 font-medium">{health.total_active_alarms}</span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Alert Rate (24h):</span>
          <span className="ml-2 font-medium">{health.alert_rate_24h.toFixed(2)}/hr</span>
        </div>
      </div>
    </div>
  );
};

const AlertSummaryCard: React.FC<{ summary: AlertSummary }> = ({ summary }) => {
  const recentActivity = summary.recent_activity ?? {};

  const getNumber = (value: unknown, fallback = 0): number => (typeof value === 'number' ? value : fallback);

  const newAlerts = getNumber(
    (recentActivity as Record<string, unknown>).last_24h_alerts ??
      (recentActivity as Record<string, unknown>).new_alerts ??
      (recentActivity as Record<string, unknown>).oci_alarms,
    0,
  );
  const resolvedAlerts = getNumber(
    (recentActivity as Record<string, unknown>).resolved_alerts ??
      (recentActivity as Record<string, unknown>).resource_alerts,
    0,
  );
  const alertRate = (recentActivity as Record<string, unknown>).alert_rate;
  const alertRateDisplay = typeof alertRate === 'number' ? `${alertRate.toFixed(1)}/hr` : 'n/a';
  const activitySummary =
    typeof (recentActivity as Record<string, unknown>).summary === 'string'
      ? ((recentActivity as Record<string, unknown>).summary as string)
      : undefined;
  const lastUpdated =
    (recentActivity as Record<string, unknown>).last_updated ?? summary.timestamp;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Alert Summary</h3>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{summary.total_alarms}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Total Alarms</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{summary.active_alarms}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Active</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{summary.severity_breakdown.CRITICAL}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Critical</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">{summary.severity_breakdown.HIGH}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">High</div>
        </div>
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Recent Activity</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">New Alerts:</span>
            <span className="ml-2 font-medium">{newAlerts}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Resolved:</span>
            <span className="ml-2 font-medium text-green-600">{resolvedAlerts}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Rate:</span>
            <span className="ml-2 font-medium">{alertRateDisplay}</span>
          </div>
        </div>

        {activitySummary && (
          <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">{activitySummary}</div>
        )}
        <div className="mt-2 text-xs text-gray-400 dark:text-gray-500">Last updated: {lastUpdated as string}</div>
      </div>
    </div>
  );
};

const ActiveAlarmsCard: React.FC<{ alarms: Alert[] }> = ({ alarms }) => (
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Active Alarms</h3>

    {alarms.length === 0 ? (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <i className="fas fa-check-circle text-4xl mb-2 text-green-500" />
        <p>No active alarms</p>
      </div>
    ) : (
      <div className="space-y-3">
        {alarms.slice(0, 5).map((alarm: Alert) => (
          <div key={alarm.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">{alarm.name}</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {alarm.service} • {alarm.resource}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <SeverityBadge severity={alarm.severity} />
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                    alarm.status === 'OPEN'
                      ? 'bg-red-100 text-red-800'
                      : alarm.status === 'ACKNOWLEDGED'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }`}
                >
                  {alarm.status}
                </span>
              </div>
            </div>
          </div>
        ))}
        {alarms.length > 5 && (
          <div className="text-center py-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">+ {alarms.length - 5} more alarms</span>
          </div>
        )}
      </div>
    )}
  </div>
);

const TestIntegrationCard: React.FC<{ scopeId?: string }> = ({ scopeId }) => {
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const runTest = async () => {
    setTesting(true);
    try {
      const result = await awsMonitoringService.testIntegration(scopeId);
      setTestResult(result);
    } catch (error) {
      setTestResult({ status: 'error', error: error instanceof Error ? error.message : String(error) });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Integration Test</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Testing scope: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">{scopeId || 'aws:region:us-east-1'}</code>
      </p>

      <div className="flex items-center space-x-4 mb-4">
        <button
          onClick={runTest}
          disabled={testing}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          {testing ? (
            <>
              <i className="fas fa-spinner animate-spin mr-2" />
              Testing...
            </>
          ) : (
            <>
              <i className="fas fa-flask mr-2" />
              Run Test
            </>
          )}
        </button>
      </div>

      {testResult && (
        <div className={`p-4 rounded-md ${testResult.status === 'success' ? 'bg-green-50 dark:bg-green-900' : 'bg-red-50 dark:bg-red-900'}`}>
          <div className="flex items-center">
            <i
              className={`fas ${
                testResult.status === 'success' ? 'fa-check-circle text-green-500' : 'fa-exclamation-circle text-red-500'
              } mr-2`}
            />
            <span
              className={`text-sm font-medium ${
                testResult.status === 'success' ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'
              }`}
            >
              {testResult.status === 'success' ? 'Test Passed' : 'Test Failed'}
            </span>
          </div>

          {testResult.test_summary && (
            <div className="mt-3 space-y-2">
              <div className="text-sm">
                <span className="font-medium">Health Score:</span>
                <span className="ml-2 font-bold text-lg">{testResult.test_summary.health_score}</span>
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                <div>Total Alarms: {testResult.test_summary.total_alarms}</div>
                <div>Active Alarms: {testResult.test_summary.active_alarms}</div>
                <div>Critical: {testResult.test_summary.severity_breakdown?.CRITICAL || 0}</div>
                <div>High: {testResult.test_summary.severity_breakdown?.HIGH || 0}</div>
              </div>
            </div>
          )}

          {testResult.error && (
            <div className="mt-2 text-xs text-red-600 dark:text-red-400">Error: {testResult.error}</div>
          )}
        </div>
      )}
    </div>
  );
};

const EksOverviewCard: React.FC<{ eks: NonNullable<AwsDashboardResponse['eks']> }> = ({ eks }) => {
  const criticalClusters = eks.clusters.filter((cluster) => cluster.status.toLowerCase() === 'degraded');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Amazon EKS Signals</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{eks.cluster_count}</div>
          <div className="text-gray-500 dark:text-gray-400">Clusters</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-300">{eks.active_nodes}</div>
          <div className="text-gray-500 dark:text-gray-400">Active Nodes</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">{eks.pods_running}</div>
          <div className="text-gray-500 dark:text-gray-400">Pods Running</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-red-600">{eks.failing_workloads}</div>
          <div className="text-gray-500 dark:text-gray-400">Failing Workloads</div>
        </div>
      </div>

      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Cluster Health</h4>
        <div className="space-y-3 text-sm">
          {eks.clusters.map((cluster) => (
            <div key={cluster.name} className="border border-gray-200 dark:border-gray-700 rounded-md p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-gray-900 dark:text-white">{cluster.name}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{cluster.region}</div>
                </div>
                <div className="text-right">
                  <span className="text-xs uppercase text-gray-500 dark:text-gray-400">Health</span>
                  <div className="text-lg font-bold">{cluster.health_score}</div>
                </div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-500 dark:text-gray-400">
                <div>
                  Node groups: <span className="font-medium text-gray-700 dark:text-gray-200">{cluster.node_groups}</span>
                </div>
                <div>
                  Pod restarts (24h):{' '}
                  <span className="font-medium text-gray-700 dark:text-gray-200">{cluster.pod_restarts_24h}</span>
                </div>
                <div>
                  Status: <span className="font-medium text-gray-700 dark:text-gray-200">{cluster.status}</span>
                </div>
                <div>
                  Pressure: <span className="font-medium text-gray-700 dark:text-gray-200">{cluster.node_pressure || 'None'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {eks.insights.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Actionable Insights</h4>
          <ul className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
            {eks.insights.map((insight) => (
              <li key={insight.id} className="border border-gray-200 dark:border-gray-700 rounded-md p-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-gray-900 dark:text-gray-100">{insight.summary}</span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      insight.severity === 'HIGH'
                        ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-200'
                        : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-200'
                    }`}
                  >
                    {insight.severity}
                  </span>
                </div>
                <div>{insight.recommendation}</div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {criticalClusters.length > 0 && (
        <div className="mt-4 text-xs text-red-600 dark:text-red-300">
          <i className="fas fa-exclamation-triangle mr-2" />
          {criticalClusters.length} cluster(s) require immediate attention.
        </div>
      )}
    </div>
  );
};

export function AwsMonitoringPage() {
  const { data: scopes, isLoading: scopesLoading } = useAwsMonitoringScopes();
  const [selectedScopeId, setSelectedScopeId] = useState<string | undefined>(undefined);

  const scopeOptions = useMemo(() => {
    return (scopes || []).map((scope) => ({
      id: scope.id,
      name: scope.name,
      description: scope.description || scope.code,
      lifecycle_state: scope.lifecycle_state,
    }));
  }, [scopes]);

  useEffect(() => {
    if (!selectedScopeId && scopeOptions.length > 0) {
      setSelectedScopeId(scopeOptions[0].id);
    }
  }, [scopeOptions, selectedScopeId]);

  if (scopesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (!scopeOptions.length) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-md p-6">
        <h2 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">AWS monitoring scopes unavailable</h2>
        <p className="text-sm text-yellow-700 dark:text-yellow-300">
          Demo monitoring scopes could not be retrieved. Please verify backend configuration.
        </p>
      </div>
    );
  }

  const effectiveScopeId = selectedScopeId || scopeOptions[0].id;

  const {
    data: health,
    isLoading: healthLoading,
    error: healthError,
  } = useAwsMonitoringHealth(effectiveScopeId);
  const { data: summary, isLoading: summaryLoading } = useAwsMonitoringSummary(effectiveScopeId);
  const { data: alarms, isLoading: alarmsLoading } = useAwsMonitoringAlarms(effectiveScopeId);
  const { data: dashboard, isLoading: dashboardLoading } = useAwsMonitoringDashboard(effectiveScopeId);

  const isLoading = healthLoading || summaryLoading || alarmsLoading || dashboardLoading;

  return (
    <div className="space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AWS Monitoring & Alerts</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Real-time monitoring data mirrored from AWS CloudWatch, CloudTrail, and EKS insights
          </p>
        </div>
        <div className="mt-4 lg:mt-0 lg:ml-6">
          <CompartmentSelector
            compartments={scopeOptions}
            selectedCompartmentId={effectiveScopeId}
            onCompartmentChange={setSelectedScopeId}
            loading={scopesLoading}
            label="Select AWS Scope"
          />
        </div>
      </div>

      <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-md p-3">
        <div className="flex items-center">
          <i className="fas fa-sync-alt text-blue-600 dark:text-blue-400 mr-2 animate-spin" />
          <span className="text-sm text-blue-700 dark:text-blue-300">Auto-refreshing AWS monitoring data every 30 seconds</span>
        </div>
        <span className="text-xs text-blue-600 dark:text-blue-400">Last updated: {new Date().toLocaleTimeString()}</span>
      </div>

      {healthError && (
        <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-4">
          <div className="flex items-center">
            <i className="fas fa-exclamation-triangle text-red-500 mr-2" />
            <span className="text-sm text-red-700 dark:text-red-200">
              Failed to load AWS monitoring data: {healthError.message}
            </span>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <LoadingSpinner />
          <span className="ml-3 text-gray-600 dark:text-gray-400">Loading AWS monitoring data...</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {health && <HealthScoreCard health={health} />}
        {summary && <AlertSummaryCard summary={summary} />}
        {alarms && <ActiveAlarmsCard alarms={alarms} />}
        <TestIntegrationCard scopeId={effectiveScopeId} />
        {dashboard?.eks && <EksOverviewCard eks={dashboard.eks} />}
      </div>

      {dashboard && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Dashboard Overview</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 dark:bg-blue-900 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {dashboard.quick_stats.uptime_score.toFixed(1)}%
              </div>
              <div className="text-sm text-blue-700 dark:text-blue-300">Uptime Score</div>
            </div>
            <div className="bg-green-50 dark:bg-green-900 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {dashboard.quick_stats.performance_score.toFixed(1)}%
              </div>
              <div className="text-sm text-green-700 dark:text-green-300">Performance Score</div>
            </div>
            <div className="bg-red-50 dark:bg-red-900 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-600 dark:text-red-400">{dashboard.quick_stats.security_alerts}</div>
              <div className="text-sm text-red-700 dark:text-red-300">Security Alerts</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Recent Alarm History</h4>
              <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
                {dashboard.recent_history.map((entry) => (
                  <div key={entry.alarm_id + entry.timestamp} className="border border-gray-200 dark:border-gray-700 rounded-md p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-gray-900 dark:text-white">{entry.alarm_name}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">{new Date(entry.timestamp).toLocaleString()}</div>
                      </div>
                      <SeverityBadge severity={entry.severity || 'INFO'} />
                    </div>
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{entry.summary}</p>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Trends</h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                <li>Alarms trend: {dashboard.trends.total_alarms_trend >= 0 ? '+' : ''}{dashboard.trends.total_alarms_trend}</li>
                <li>Critical alerts trend: {dashboard.trends.critical_alerts_trend >= 0 ? '+' : ''}{dashboard.trends.critical_alerts_trend}</li>
                <li>Health score delta: {dashboard.trends.health_score_trend >= 0 ? '+' : ''}{dashboard.trends.health_score_trend}</li>
                <li>Last updated: {dashboard.last_updated}</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AwsMonitoringPage;
