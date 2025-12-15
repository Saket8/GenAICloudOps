import React from 'react';
import { useAwsResources } from '../../../services/awsService';
import { LoadingSpinner } from '../../ui/LoadingSpinner';

function StatCard({ label, value, icon }: { label: string; value: string | number; icon: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
          <p className="mt-2 text-xl font-semibold text-gray-900 dark:text-white">{value}</p>
        </div>
        <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-300">
          <i className={icon}></i>
        </div>
      </div>
    </div>
  );
}

export function AwsResourcesPage() {
  const { data: resources, isLoading, error } = useAwsResources();

  if (isLoading) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading AWS resource inventory..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/40 border border-red-200 dark:border-red-800 rounded-md p-6">
        <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Unable to load AWS resources</h2>
        <p className="text-sm text-red-700 dark:text-red-300">{error.message}</p>
      </div>
    );
  }

  if (!resources) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/40 border border-yellow-200 dark:border-yellow-700 rounded-md p-6">
        <h2 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Resource snapshot unavailable</h2>
        <p className="text-sm text-yellow-700 dark:text-yellow-300">Demo inventory is currently unavailable. Please try again later.</p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <header className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AWS Resource Inventory</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl">
            High-level breakdown of compute, storage, database, and networking assets sourced from the AWS demo datasets.
            Values are curated to mirror the GenAI CloudOps production layout with no live API calls.
          </p>
        </div>
        <div className="bg-slate-50 dark:bg-slate-900/30 border border-slate-200 dark:border-slate-700 rounded-lg px-5 py-4 text-sm text-slate-700 dark:text-slate-200">
          <div className="font-semibold flex items-center space-x-2">
            <i className="fas fa-database" />
            <span>Data Source</span>
          </div>
          <div className="mt-2 text-xs">
            Demo refresh cadence: <strong>weekly</strong>
          </div>
          <div className="text-xs">
            Coverage: EC2, Lambda, S3, EFS, RDS, DynamoDB, VPC, ELB
          </div>
        </div>
      </header>

      <section className="grid gap-6 md:grid-cols-4">
        <StatCard label="EC2 Instances" value={resources.compute.ec2.running_instances} icon="fas fa-server" />
        <StatCard label="EKS Clusters" value={resources.compute.ec2.eks_clusters} icon="fas fa-dharmachakra" />
        <StatCard label="Lambda Functions" value={resources.compute.lambda.active_functions} icon="fas fa-bolt" />
        <StatCard label="S3 Buckets" value={resources.storage.s3.total_buckets} icon="fas fa-box-open" />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Compute Utilization</h2>
          <div className="grid gap-4">
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300">
                <span>Average EC2 CPU</span>
                <span className="font-semibold">{resources.compute.ec2.average_cpu}%</span>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Auto Scaling Groups: {resources.compute.ec2.auto_scaling_groups}
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300">
                <span>Lambda Avg Duration</span>
                <span className="font-semibold">{resources.compute.lambda.avg_duration_ms} ms</span>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Error rate: {resources.compute.lambda.error_rate}%
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Storage Overview</h2>
          <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span>S3 Object Count</span>
                <span className="font-semibold">{(resources.storage.s3.object_count / 1_000_000).toFixed(1)}M</span>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Storage footprint: {resources.storage.s3.storage_tb} TB
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span>EFS Average Utilization</span>
                <span className="font-semibold">{resources.storage.efs.avg_utilization}%</span>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                File systems: {resources.storage.efs.file_systems}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Database Estate</h2>
          <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span>RDS Instances</span>
                <span className="font-semibold">{resources.databases.rds.instances}</span>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Aurora clusters: {resources.databases.rds.aurora_clusters}
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span>DynamoDB Tables</span>
                <span className="font-semibold">{resources.databases.dynamodb.tables}</span>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Throttle events (24h): {resources.databases.dynamodb.throttle_events}
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span>Average RDS CPU</span>
                <span className="font-semibold">{resources.databases.rds.avg_cpu}%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Networking Footprint</h2>
          <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
              <span>Total VPCs</span>
              <span className="font-semibold">{resources.networking.vpcs}</span>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
              <span>Subnets</span>
              <span className="font-semibold">{resources.networking.subnets}</span>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span>Load Balancers</span>
                <span className="font-semibold">
                  {resources.networking.load_balancers.alb + resources.networking.load_balancers.nlb}
                </span>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                ALB: {resources.networking.load_balancers.alb} • NLB: {resources.networking.load_balancers.nlb} • GW: {resources.networking.load_balancers.gateway}
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
              <span>VPN Connections</span>
              <span className="font-semibold">{resources.networking.vpn_connections}</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AwsResourcesPage;
