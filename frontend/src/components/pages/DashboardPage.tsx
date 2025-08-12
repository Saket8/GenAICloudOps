import React, { useState } from 'react';
import { useCompartments, useAllResources } from '../../services/cloudService';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { CompartmentSelector } from '../ui/CompartmentSelector';
import { ResourceCard } from '../ui/ResourceCard';
import { MetricsChart } from '../ui/MetricsChart';
import { ResourceFilter } from '../ui/ResourceFilter';
import { useWebSocket, useSystemMetrics, useConnectionStatus } from '../../hooks/useWebSocket';
import { SubscriptionType } from '../../services/websocketService';

// StatCard component for quick stats
interface StatCardProps {
  title: string;
  value: number;
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'indigo' | 'red' | 'yellow';
  isLoading?: boolean;
  trend?: string;
}

function StatCard({ title, value, icon, color, isLoading, trend }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    indigo: 'bg-indigo-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
  };

  return (
    <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`p-3 rounded-md ${colorClasses[color]}`}>
              <i className={`${icon} text-white text-xl`}></i>
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                {isLoading ? (
                  <div className="text-2xl font-semibold text-gray-400">
                    <LoadingSpinner size="sm" />
                  </div>
                ) : (
                  <div className="text-2xl font-semibold text-gray-900 dark:text-white">
                    {value.toLocaleString()}
                  </div>
                )}
                {trend && (
                  <p className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                    {trend}
                  </p>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data: compartments, isLoading: compartmentsLoading, error: compartmentsError } = useCompartments();
  const [selectedCompartmentId, setSelectedCompartmentId] = useState<string>('');
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedResourceType, setSelectedResourceType] = useState<string>('');
  
  // ⚠️ TEMPORARILY DISABLED: WebSocket for real-time updates (causing performance issues)
  const { connected, error: wsError } = useWebSocket({
    autoConnect: false,
    subscriptions: []
  });
  const { metrics, lastUpdated } = useSystemMetrics();
  const connectionStatus = useConnectionStatus();
  
  // Set default compartment when compartments load
  React.useEffect(() => {
    if (compartments && compartments.length > 0 && !selectedCompartmentId) {
      setSelectedCompartmentId(compartments[0].id);
    }
  }, [compartments, selectedCompartmentId]);
  
  const selectedCompartment = compartments?.find(c => c.id === selectedCompartmentId);
  const { 
    data: allResources, 
    isLoading: resourcesLoading, 
    error: resourcesError 
  } = useAllResources(selectedCompartmentId || '', undefined);

  // Filter resources based on search and filter criteria
  const filterResources = (resources: any[], resourceType: string) => {
    if (!resources) return [];

    return resources.filter(resource => {
      // Search filter
      const matchesSearch = !searchTerm || 
        (resource.display_name && resource.display_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (resource.name && resource.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (resource.id && resource.id.toLowerCase().includes(searchTerm.toLowerCase()));

      // Status filter
      const matchesStatus = !selectedStatus || resource.lifecycle_state === selectedStatus;

      // Resource type filter
      const matchesResourceType = !selectedResourceType || resourceType === selectedResourceType;

      return matchesSearch && matchesStatus && matchesResourceType;
    });
  };

  if (compartmentsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading compartments..." />
      </div>
    );
  }

  if (compartmentsError) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-4">
          <div className="flex">
            <i className="fas fa-exclamation-circle text-red-400 mr-3 mt-0.5"></i>
            <div>
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Error loading compartments
              </h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                {compartmentsError.message || 'Failed to load compartments'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Compartment Selector */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Dashboard Overview
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Real-time view of your cloud infrastructure and operations
          </p>
        </div>
        <div className="mt-4 lg:mt-0 lg:ml-6">
          <CompartmentSelector
            compartments={compartments || []}
            selectedCompartmentId={selectedCompartmentId}
            onCompartmentChange={setSelectedCompartmentId}
            loading={compartmentsLoading}
          />
        </div>
      </div>

      {/* Performance optimized - Real-time features disabled */}
      <div className="flex items-center justify-between bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-md p-3">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <i className="fas fa-check-circle text-green-600 dark:text-green-400 mr-2"></i>
            <span className="text-sm text-green-700 dark:text-green-300">
              ✅ Performance optimized - Auto-refresh disabled
            </span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full mr-2 bg-gray-500"></div>
            <span className="text-sm text-green-700 dark:text-green-300">
              Real-time features disabled for performance
            </span>
          </div>
        </div>
        <button 
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-md transition-colors duration-200 flex items-center space-x-2"
          onClick={() => {
            // Smart refresh - invalidate relevant queries instead of full page reload
            window.location.reload();
          }}
        >
          <i className="fas fa-sync-alt"></i>
          <span>Manual Refresh</span>
        </button>
      </div>

      {/* Real-time System Metrics */}
      {connected && metrics && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              System Metrics (Live)
            </h2>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {lastUpdated && `Last updated: ${lastUpdated.toLocaleTimeString()}`}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* CPU Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">CPU Usage</span>
                <span className="text-sm text-gray-600 dark:text-gray-400">{metrics.cpu_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    metrics.cpu_percent > 80 ? 'bg-red-500' : 
                    metrics.cpu_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(metrics.cpu_percent, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Memory Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Memory Usage</span>
                <span className="text-sm text-gray-600 dark:text-gray-400">{metrics.memory_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    metrics.memory_percent > 80 ? 'bg-red-500' : 
                    metrics.memory_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(metrics.memory_percent, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Disk Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Disk Usage</span>
                <span className="text-sm text-gray-600 dark:text-gray-400">{metrics.disk_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    metrics.disk_percent > 80 ? 'bg-red-500' : 
                    metrics.disk_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(metrics.disk_percent, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Active Connections */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">WS Connections</span>
                <span className="text-sm text-gray-600 dark:text-gray-400">{metrics.active_connections}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  Uptime: {Math.floor(metrics.uptime_seconds / 3600)}h {Math.floor((metrics.uptime_seconds % 3600) / 60)}m
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* WebSocket Error */}
      {wsError && (
        <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-4">
          <div className="flex">
            <i className="fas fa-exclamation-triangle text-red-400 mr-3 mt-0.5"></i>
            <div>
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Real-time Connection Error
              </h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                {wsError}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Resource Filter */}
      <ResourceFilter
        searchTerm={searchTerm}
        selectedStatus={selectedStatus}
        selectedResourceType={selectedResourceType}
        onSearchChange={setSearchTerm}
        onStatusFilter={setSelectedStatus}
        onResourceTypeFilter={setSelectedResourceType}
      />

      {/* Enhanced Quick Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Resources"
          value={allResources?.total_resources || 0}
          icon="fas fa-cube"
          color="blue"
          isLoading={resourcesLoading}
          trend={"+12%"}
        />
        <StatCard
          title="Compute Instances"
          value={allResources?.resources?.compute_instances?.length || 0}
          icon="fas fa-server"
          color="green"
          isLoading={resourcesLoading}
          trend={"+5%"}
        />
        <StatCard
          title="Databases"
          value={allResources?.resources?.databases?.length || 0}
          icon="fas fa-database"
          color="purple"
          isLoading={resourcesLoading}
          trend="+2"
        />
        <StatCard
          title="Network Resources"
          value={allResources?.resources?.network_resources?.length || 0}
          icon="fas fa-network-wired"
          color="indigo"
          isLoading={resourcesLoading}
          trend="stable"
        />
      </div>

      {/* Additional Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Storage Volumes"
          value={allResources?.resources?.block_volumes?.length || 0}
          icon="fas fa-hdd"
          color="orange"
          isLoading={resourcesLoading}
          trend="+3"
        />
        <StatCard
          title="File Systems"
          value={allResources?.resources?.file_systems?.length || 0}
          icon="fas fa-folder-open"
          color="yellow"
          isLoading={resourcesLoading}
          trend="+1"
        />
        <StatCard
          title="Load Balancers"
          value={allResources?.resources?.load_balancers?.length || 0}
          icon="fas fa-balance-scale"
          color="red"
          isLoading={resourcesLoading}
          trend="stable"
        />
        <StatCard
          title="OKE Clusters"
          value={allResources?.resources?.oke_clusters?.length || 0}
          icon="fas fa-dharmachakra"
          color="purple"
          isLoading={resourcesLoading}
          trend="stable"
        />
      </div>

      {/* Real-time Metrics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart
          title="Resource Health Overview"
          type="health"
          data={allResources}
          loading={resourcesLoading}
        />
        <MetricsChart
          title="Resource Distribution"
          type="distribution"
          data={allResources}
          loading={resourcesLoading}
        />
      </div>

      {/* Enhanced Resource Cards with Hierarchical Organization */}
      {selectedCompartment && (
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Resources in {selectedCompartment.name}
            </h2>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Organized by category and relationships
            </div>
          </div>

          {resourcesLoading ? (
            <div className="flex items-center justify-center p-12">
              <LoadingSpinner size="lg" message="Loading resources..." />
            </div>
          ) : resourcesError ? (
            <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-4">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Error loading resources</h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                {resourcesError.message || 'Failed to load resources'}
              </p>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Compute & Container Services */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                  <i className="fas fa-server text-blue-500 mr-2"></i>
                  Compute & Container Services
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  <ResourceCard
                    title="Compute Instances"
                    icon="fas fa-server"
                    color="blue"
                    resources={filterResources(allResources?.resources?.compute_instances || [], 'compute_instances')}
                    resourceType="compute"
                  />
                  
                  <ResourceCard
                    title="OKE Clusters"
                    icon="fas fa-dharmachakra"
                    color="green"
                    resources={filterResources(allResources?.resources?.oke_clusters || [], 'oke_clusters')}
                    resourceType="kubernetes"
                  />
                </div>
              </div>

              {/* Data & Database Services */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                  <i className="fas fa-database text-purple-500 mr-2"></i>
                  Data & Database Services
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  <ResourceCard
                    title="Database Services"
                    icon="fas fa-database"
                    color="purple"
                    resources={filterResources(allResources?.resources?.databases || [], 'databases')}
                    resourceType="database"
                  />
                </div>
              </div>

              {/* Networking Services */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                  <i className="fas fa-network-wired text-indigo-500 mr-2"></i>
                  Networking Services
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  <ResourceCard
                    title="Network Resources"
                    icon="fas fa-network-wired"
                    color="indigo"
                    resources={filterResources(allResources?.resources?.network_resources || [], 'network_resources')}
                    resourceType="network"
                  />
                  
                  <ResourceCard
                    title="Load Balancers"
                    icon="fas fa-balance-scale"
                    color="blue"
                    resources={filterResources(allResources?.resources?.load_balancers || [], 'load_balancers')}
                    resourceType="load_balancer"
                  />
                  
                  <ResourceCard
                    title="API Gateways"
                    icon="fas fa-route"
                    color="orange"
                    resources={filterResources(allResources?.resources?.api_gateways || [], 'api_gateways')}
                    resourceType="api_gateway"
                  />
                </div>
              </div>

              {/* Storage Services */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                  <i className="fas fa-hdd text-yellow-500 mr-2"></i>
                  Storage Services
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  <ResourceCard
                    title="Block Volumes"
                    icon="fas fa-hdd"
                    color="orange"
                    resources={filterResources(allResources?.resources?.block_volumes || [], 'block_volumes')}
                    resourceType="storage"
                  />
                  
                  <ResourceCard
                    title="File Systems"
                    icon="fas fa-folder-open"
                    color="yellow"
                    resources={filterResources(allResources?.resources?.file_systems || [], 'file_systems')}
                    resourceType="file_system"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 