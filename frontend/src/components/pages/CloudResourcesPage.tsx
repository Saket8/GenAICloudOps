import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { CompartmentSelector } from '../ui/CompartmentSelector';
import { useCompartments } from '../../services/cloudService';

interface CloudInstance {
  id: string;
  display_name: string;
  lifecycle_state: string;
  availability_domain: string;
  shape: string;
  time_created: string;
  cpu_utilization?: number;
  memory_utilization?: number;
  region: string;
  fault_domain: string;
}

const InstanceCard: React.FC<{ instance: CloudInstance }> = ({ instance }) => {
  const [isLoading, setIsLoading] = useState(false);

  const getStatusColor = (state: string) => {
    switch (state.toLowerCase()) {
      case 'running': return 'green';
      case 'stopped': return 'red';
      case 'stopping': return 'yellow';
      case 'starting': return 'blue';
      default: return 'gray';
    }
  };

  const handleInstanceAction = async (action: 'start' | 'stop') => {
    setIsLoading(true);
    try {
      await apiClient.post(`/cloud/instances/${instance.id}/${action}`);
      // In a real app, we'd refetch the data here
      console.log(`${action} action initiated for ${instance.display_name}`);
    } catch (error) {
      console.error(`Failed to ${action} instance:`, error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {instance.display_name}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {instance.shape} • {instance.availability_domain}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${getStatusColor(instance.lifecycle_state)}-100 text-${getStatusColor(instance.lifecycle_state)}-800`}>
            {instance.lifecycle_state}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400">Region:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-white">{instance.region}</span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Fault Domain:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-white">{instance.fault_domain}</span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Created:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-white">
            {new Date(instance.time_created).toLocaleDateString()}
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">OCID:</span>
          <span className="ml-2 font-mono text-xs text-gray-600 dark:text-gray-300">
            {instance.id.split('.').pop()}
          </span>
        </div>
      </div>

      {/* Resource Utilization */}
      {instance.lifecycle_state === 'RUNNING' && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Resource Utilization</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">CPU</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${instance.cpu_utilization! > 70 ? 'bg-red-500' : instance.cpu_utilization! > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                    style={{ width: `${instance.cpu_utilization}%` }}
                  ></div>
                </div>
                <span className="text-sm font-medium">{instance.cpu_utilization}%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">Memory</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${instance.memory_utilization! > 70 ? 'bg-red-500' : instance.memory_utilization! > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                    style={{ width: `${instance.memory_utilization}%` }}
                  ></div>
                </div>
                <span className="text-sm font-medium">{instance.memory_utilization}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-2">
        {instance.lifecycle_state === 'RUNNING' ? (
          <button
            onClick={() => handleInstanceAction('stop')}
            disabled={isLoading}
            className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white text-sm py-2 px-4 rounded-md font-medium"
          >
            {isLoading ? (
              <>
                <i className="fas fa-spinner animate-spin mr-2"></i>
                Stopping...
              </>
            ) : (
              <>
                <i className="fas fa-stop mr-2"></i>
                Stop
              </>
            )}
          </button>
        ) : (
          <button
            onClick={() => handleInstanceAction('start')}
            disabled={isLoading}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white text-sm py-2 px-4 rounded-md font-medium"
          >
            {isLoading ? (
              <>
                <i className="fas fa-spinner animate-spin mr-2"></i>
                Starting...
              </>
            ) : (
              <>
                <i className="fas fa-play mr-2"></i>
                Start
              </>
            )}
          </button>
        )}
        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 px-4 rounded-md font-medium">
          <i className="fas fa-info-circle mr-2"></i>
          Details
        </button>
      </div>
    </div>
  );
};

export function CloudResourcesPage() {
  const { data: compartments, isLoading: compartmentsLoading } = useCompartments();
  const [selectedCompartmentId, setSelectedCompartmentId] = useState<string>('test-compartment');

  const { data: instances, isLoading: instancesLoading, error } = useQuery({
    queryKey: ['instances', selectedCompartmentId],
    queryFn: async () => {
      const response = await apiClient.get<CloudInstance[]>('/cloud/instances');
      return response.data;
    },
  });

  const runningInstances = instances?.filter(i => i.lifecycle_state === 'RUNNING') || [];
  const stoppedInstances = instances?.filter(i => i.lifecycle_state === 'STOPPED') || [];

  if (compartmentsLoading || instancesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-4">
        <div className="flex items-center">
          <i className="fas fa-exclamation-triangle text-red-500 mr-2"></i>
          <span className="text-sm text-red-700 dark:text-red-200">
            Failed to load cloud resources: {error.message}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Cloud Resources
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage your OCI compute instances and resources
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

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <i className="fas fa-server text-blue-500 text-2xl"></i>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Instances</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{instances?.length || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <i className="fas fa-play-circle text-green-500 text-2xl"></i>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Running</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{runningInstances.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <i className="fas fa-stop-circle text-red-500 text-2xl"></i>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Stopped</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stoppedInstances.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <i className="fas fa-chart-line text-purple-500 text-2xl"></i>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg CPU Usage</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {runningInstances.length > 0 
                  ? Math.round(runningInstances.reduce((acc, inst) => acc + (inst.cpu_utilization || 0), 0) / runningInstances.length) 
                  : 0}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Instances Grid */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Compute Instances ({instances?.length || 0})
        </h2>
        
        {instances && instances.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {instances.map((instance) => (
              <InstanceCard key={instance.id} instance={instance} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
            <i className="fas fa-server text-4xl text-gray-400 mb-4"></i>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No instances found</h3>
            <p className="text-gray-500 dark:text-gray-400">
              No compute instances are available in the selected compartment.
            </p>
          </div>
        )}
      </div>

      {/* Action Bar */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <i className="fas fa-info-circle mr-2"></i>
            Instance data refreshes automatically every 30 seconds
          </div>
          <div className="flex space-x-2">
            <button className="bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 px-4 rounded-md font-medium">
              <i className="fas fa-sync mr-2"></i>
              Refresh
            </button>
            <button className="bg-green-600 hover:bg-green-700 text-white text-sm py-2 px-4 rounded-md font-medium">
              <i className="fas fa-plus mr-2"></i>
              Create Instance
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 