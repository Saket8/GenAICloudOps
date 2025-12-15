import React, { useEffect, useMemo, useState } from 'react';
import { useAwsOverview, useAwsResources, useAwsCost } from '../../../services/awsService';
import {
  useAwsMonitoringScopes,
  useAwsMonitoringDashboard,
  AwsDashboardResponse,
} from '../../../services/awsMonitoringService';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

function StatCard({ title, value, icon, accent }: { title: string; value: string | number; icon: string; accent: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="mt-2 text-2xl font-semibold text-gray-900 dark:text-white">{value}</p>
        </div>
        <div className={`h-12 w-12 rounded-full flex items-center justify-center text-white ${accent}`}>
          <i className={`${icon} text-lg`}></i>
        </div>
      </div>
    </div>
  );
}

export function AwsDashboardPage() {
  const { data: overview, isLoading: overviewLoading } = useAwsOverview();
  const { data: resources, isLoading: resourcesLoading } = useAwsResources();
  const { data: cost, isLoading: costLoading } = useAwsCost();
  const { data: scopes, isLoading: scopesLoading } = useAwsMonitoringScopes();
  const [selectedScopeId, setSelectedScopeId] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!selectedScopeId && scopes && scopes.length > 0) {
      setSelectedScopeId(scopes[0].id);
    }
  }, [scopes, selectedScopeId]);

  const { data: monitoringDashboard, isLoading: dashboardLoading } = useAwsMonitoringDashboard(selectedScopeId);

  const alerts = useMemo(() => {
    if (!monitoringDashboard) {
      return [] as Array<NonNullable<AwsDashboardResponse['alerts']>[number]>;
    }
    return (monitoringDashboard.alerts ?? []) as Array<NonNullable<AwsDashboardResponse['alerts']>[number]>;
  }, [monitoringDashboard]);

  const loading =
    overviewLoading ||
    resourcesLoading ||
    scopesLoading ||
    dashboardLoading ||
    costLoading ||
    !selectedScopeId;

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading AWS overview..." />
      </div>
    );
  }

  if (!overview || !resources || !monitoringDashboard || !cost) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/40 border border-yellow-200 dark:border-yellow-800 rounded-md p-6">
        <h2 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">AWS demo data unavailable</h2>
        <p className="text-sm text-yellow-700 dark:text-yellow-300">
          We could not retrieve the AWS demo snapshot. Please retry later or contact the platform administrator.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AWS Operations Command Center</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl">
            Unified visibility into your AWS environments with GenAI-assisted insights spanning performance, cost, security,
            and automation readiness. Data is sourced from curated demo telemetry.
          </p>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg px-5 py-4 text-sm text-blue-700 dark:text-blue-200">
          <div className="font-semibold flex items-center space-x-2">
            <i className="fab fa-aws"></i>
            <span>{overview.account.alias}</span>
          </div>
          <div className="mt-2 text-xs">
            Region: <strong>{overview.account.region}</strong> • Active environments: {overview.account.environments.length}
          </div>
        </div>
      </header>

      <section>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Platform KPIs</h2>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Services Monitored"
            value={overview.summary.total_services}
            icon="fas fa-layer-group"
            accent="bg-blue-500"
          />
          <StatCard
            title="Resources Discovered"
            value={overview.summary.resources_discovered}
            icon="fas fa-cubes"
            accent="bg-indigo-500"
          />
          <StatCard
            title="Active Alerts"
            value={overview.summary.active_alerts}
            icon="fas fa-exclamation-triangle"
            accent="bg-red-500"
          />
          <StatCard
            title="Monthly Spend ($)"
            value={cost.summary.month_to_date_spend.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            icon="fas fa-dollar-sign"
            accent="bg-emerald-500"
          />
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Operational Highlights</h3>
            <span className="text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-200">
              GenAI summarized
            </span>
          </div>
          <div className="space-y-4">
            {overview.highlights.map((item) => (
              <div key={item.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">{item.title}</span>
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 uppercase">
                        {item.severity}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{item.summary}</p>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">Impact: {item.impact}</span>
                </div>
                <div className="mt-3 text-sm text-blue-600 dark:text-blue-300">
                  <i className="fas fa-lightbulb mr-2"></i>
                  {item.recommendation}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Environment Status</h3>
          <ul className="space-y-3">
            {overview.account.environments.map((env) => (
              <li key={env.name} className="flex items-center justify-between text-sm">
                <span className="text-gray-700 dark:text-gray-300">{env.name}</span>
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    env.status === 'healthy'
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200'
                      : 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-200'
                  }`}
                >
                  <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                  {env.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Cost Breakdown</h3>
          <div className="space-y-3">
            {cost.service_breakdown.map((service) => (
              <div key={service.service} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span className="text-gray-700 dark:text-gray-300">{service.service}</span>
                </div>
                <div className="text-gray-600 dark:text-gray-400">
                  ${service.spend.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  <span
                    className={`ml-2 text-xs ${
                      service.change_percent >= 0 ? 'text-emerald-500' : 'text-red-500'
                    }`}
                  >
                    {service.change_percent >= 0 ? '+' : ''}
                    {service.change_percent}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Resource Inventory</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Compute</h4>
              <ul className="mt-2 space-y-1 text-gray-700 dark:text-gray-300">
                <li>EC2 Instances: {resources.compute.ec2.running_instances}</li>
                <li>EKS Clusters: {resources.compute.ec2.eks_clusters}</li>
                <li>Active Lambdas: {resources.compute.lambda.active_functions}</li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Storage</h4>
              <ul className="mt-2 space-y-1 text-gray-700 dark:text-gray-300">
                <li>S3 Buckets: {resources.storage.s3.total_buckets}</li>
                <li>Object Count: {(resources.storage.s3.object_count / 1_000_000).toFixed(1)}M</li>
                <li>EFS Utilization: {resources.storage.efs.avg_utilization}%</li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Databases</h4>
              <ul className="mt-2 space-y-1 text-gray-700 dark:text-gray-300">
                <li>RDS Instances: {resources.databases.rds.instances}</li>
                <li>Aurora Clusters: {resources.databases.rds.aurora_clusters}</li>
                <li>DynamoDB Tables: {resources.databases.dynamodb.tables}</li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Networking</h4>
              <ul className="mt-2 space-y-1 text-gray-700 dark:text-gray-300">
                <li>VPCs: {resources.networking.vpcs}</li>
                <li>Subnets: {resources.networking.subnets}</li>
                <li>Load Balancers: {resources.networking.load_balancers.alb + resources.networking.load_balancers.nlb}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Latest Alert Activity</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th className="px-4 py-2 text-left font-semibold text-gray-600 dark:text-gray-300">Alert</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-600 dark:text-gray-300">Service</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-600 dark:text-gray-300">Resource</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-600 dark:text-gray-300">State</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-600 dark:text-gray-300">Last Triggered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {alerts.slice(0, 5).map((alert) => (
                <tr key={alert.id}>
                  <td className="px-4 py-2 text-gray-900 dark:text-gray-100">{alert.title}</td>
                  <td className="px-4 py-2 text-gray-600 dark:text-gray-300">{alert.service}</td>
                  <td className="px-4 py-2 text-gray-600 dark:text-gray-300">{alert.resource}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        alert.state === 'ALARM'
                          ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-200'
                          : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200'
                      }`}
                    >
                      {alert.state}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-500 dark:text-gray-400">{new Date(alert.last_triggered).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default AwsDashboardPage;
