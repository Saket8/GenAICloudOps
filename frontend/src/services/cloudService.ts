import { useQuery, useMutation, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { api } from './apiClient';

// Type definitions for cloud resources
export interface Compartment {
  id: string;
  name: string;
  description: string;
  lifecycle_state: string;
}

export interface CloudResource {
  id: string;
  display_name?: string;
  name?: string;
  lifecycle_state: string;
  resource_type: string;
  compartment_id: string;
  availability_domain?: string;
  shape?: string;
  time_created?: string;
  region?: string;
}

export interface ResourceMetrics {
  resource_id: string;
  metrics: {
    cpu_utilization: number;
    memory_utilization: number;
    network_bytes_in: number;
    network_bytes_out: number;
  };
  timestamp: string;
  health_status: string;
}

export interface AllResourcesResponse {
  compartment_id: string;
  resources: {
    compute_instances: CloudResource[];
    databases: CloudResource[];
    oke_clusters: CloudResource[];
    api_gateways: CloudResource[];
    load_balancers: CloudResource[];
    network_resources: CloudResource[];
    storage_resources: CloudResource[];
    block_volumes: CloudResource[];
    file_systems: CloudResource[];
  };
  total_resources: number;
  last_updated: string;
}

// Query Keys
export const cloudQueryKeys = {
  all: ['cloud'] as const,
  compartments: () => [...cloudQueryKeys.all, 'compartments'] as const,
  compartment: (id: string) => [...cloudQueryKeys.all, 'compartment', id] as const,
  resources: (compartmentId: string) => [...cloudQueryKeys.compartment(compartmentId), 'resources'] as const,
  computeInstances: (compartmentId: string) => [...cloudQueryKeys.compartment(compartmentId), 'compute'] as const,
  databases: (compartmentId: string) => [...cloudQueryKeys.compartment(compartmentId), 'databases'] as const,
  okeClusters: (compartmentId: string) => [...cloudQueryKeys.compartment(compartmentId), 'oke'] as const,
  apiGateways: (compartmentId: string) => [...cloudQueryKeys.compartment(compartmentId), 'api-gateways'] as const,
  loadBalancers: (compartmentId: string) => [...cloudQueryKeys.compartment(compartmentId), 'load-balancers'] as const,
  metrics: (resourceId: string) => [...cloudQueryKeys.all, 'metrics', resourceId] as const,
};

// API Functions
const cloudApi = {
  // Get all compartments
  getCompartments: async (): Promise<Compartment[]> => {
    const response = await api.get<Compartment[]>('/cloud/compartments');
    return response.data;
  },

  // Get all resources in a compartment
  getAllResources: async (compartmentId: string, resourceFilter?: string[]): Promise<AllResourcesResponse> => {
    const params = resourceFilter ? { resource_filter: resourceFilter.join(',') } : {};
    try {
      const response = await api.get<AllResourcesResponse>(`/cloud/compartments/${compartmentId}/resources`, { params });
      return response.data;
    } catch (error: any) {
      // Development fallback to prevent dashboard from breaking on 401 or missing mocks
      if (import.meta && (import.meta as any).env && (import.meta as any).env.DEV) {
        const now = new Date().toISOString();
        const dummy: AllResourcesResponse = {
          compartment_id: compartmentId,
          resources: {
            compute_instances: [
              { id: 'ocid1.instance.oc1..r1', display_name: 'web-server-1', lifecycle_state: 'RUNNING', resource_type: 'compute', compartment_id: compartmentId, time_created: now },
              { id: 'ocid1.instance.oc1..r2', display_name: 'db-worker', lifecycle_state: 'STOPPED', resource_type: 'compute', compartment_id: compartmentId, time_created: now }
            ],
            databases: [
              { id: 'ocid1.database.oc1..db1', display_name: 'orders-db', lifecycle_state: 'AVAILABLE', resource_type: 'database', compartment_id: compartmentId, time_created: now }
            ],
            oke_clusters: [
              { id: 'ocid1.cluster.oc1..c1', display_name: 'production-cluster', lifecycle_state: 'ACTIVE', resource_type: 'oke_cluster', compartment_id: compartmentId, time_created: now }
            ],
            api_gateways: [],
            load_balancers: [
              { id: 'ocid1.loadbalancer.oc1..lb1', display_name: 'public-lb', lifecycle_state: 'ACTIVE', resource_type: 'load_balancer', compartment_id: compartmentId, time_created: now }
            ],
            network_resources: [
              { id: 'ocid1.vcn.oc1..v1', display_name: 'main-vcn', lifecycle_state: 'AVAILABLE', resource_type: 'vcn', compartment_id: compartmentId, time_created: now }
            ],
            storage_resources: [],
            block_volumes: [
              { id: 'ocid1.volume.oc1..vol1', display_name: 'db-volume', lifecycle_state: 'AVAILABLE', resource_type: 'block_volume', compartment_id: compartmentId, time_created: now }
            ],
            file_systems: [
              { id: 'ocid1.filesystem.oc1..fs1', display_name: 'shared-fs', lifecycle_state: 'ACTIVE', resource_type: 'file_system', compartment_id: compartmentId, time_created: now }
            ]
          },
          total_resources: 8,
          last_updated: now
        };
        return dummy;
      }
      throw error;
    }
  },

  // Get compute instances
  getComputeInstances: async (compartmentId: string): Promise<CloudResource[]> => {
    const response = await api.get<CloudResource[]>(`/cloud/compartments/${compartmentId}/compute-instances`);
    return response.data;
  },

  // Get databases
  getDatabases: async (compartmentId: string): Promise<CloudResource[]> => {
    const response = await api.get<CloudResource[]>(`/cloud/compartments/${compartmentId}/databases`);
    return response.data;
  },

  // Get OKE clusters
  getOKEClusters: async (compartmentId: string): Promise<CloudResource[]> => {
    const response = await api.get<CloudResource[]>(`/cloud/compartments/${compartmentId}/oke-clusters`);
    return response.data;
  },

  // Get API gateways
  getAPIGateways: async (compartmentId: string): Promise<CloudResource[]> => {
    const response = await api.get<CloudResource[]>(`/cloud/compartments/${compartmentId}/api-gateways`);
    return response.data;
  },

  // Get load balancers
  getLoadBalancers: async (compartmentId: string): Promise<CloudResource[]> => {
    const response = await api.get<CloudResource[]>(`/cloud/compartments/${compartmentId}/load-balancers`);
    return response.data;
  },

  // Get network resources
  getNetworkResources: async (compartmentId: string): Promise<CloudResource[]> => {
    const response = await api.get<CloudResource[]>(`/cloud/compartments/${compartmentId}/network-resources`);
    return response.data;
  },

  // Get block volumes
  getBlockVolumes: async (compartmentId: string): Promise<CloudResource[]> => {
    const response = await api.get<CloudResource[]>(`/cloud/compartments/${compartmentId}/block-volumes`);
    return response.data;
  },

  // Get file systems
  getFileSystems: async (compartmentId: string): Promise<CloudResource[]> => {
    const response = await api.get<CloudResource[]>(`/cloud/compartments/${compartmentId}/file-systems`);
    return response.data;
  },

  // Get resource metrics
  getResourceMetrics: async (resourceId: string, resourceType: string): Promise<ResourceMetrics> => {
    const response = await api.get<ResourceMetrics>(`/cloud/resources/${resourceId}/metrics`, {
      params: { resource_type: resourceType }
    });
    return response.data;
  },

  // Execute resource action
  executeResourceAction: async (resourceId: string, action: string): Promise<any> => {
    const response = await api.post(`/cloud/resources/${resourceId}/actions/${action}`);
    return response.data;
  },
};

// React Query Hooks

// Get compartments
export function useCompartments(): UseQueryResult<Compartment[], Error> {
  return useQuery({
    queryKey: cloudQueryKeys.compartments(),
    queryFn: cloudApi.getCompartments,
    staleTime: 10 * 60 * 1000, // 10 minutes (compartments don't change often)
  });
}

// Get all resources in a compartment
export function useAllResources(
  compartmentId: string, 
  resourceFilter?: string[]
): UseQueryResult<AllResourcesResponse, Error> {
  return useQuery({
    queryKey: [...cloudQueryKeys.resources(compartmentId), resourceFilter],
    queryFn: () => cloudApi.getAllResources(compartmentId, resourceFilter),
    enabled: !!compartmentId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Get compute instances
export function useComputeInstances(compartmentId: string): UseQueryResult<CloudResource[], Error> {
  return useQuery({
    queryKey: cloudQueryKeys.computeInstances(compartmentId),
    queryFn: () => cloudApi.getComputeInstances(compartmentId),
    enabled: !!compartmentId,
  });
}

// Get databases
export function useDatabases(compartmentId: string): UseQueryResult<CloudResource[], Error> {
  return useQuery({
    queryKey: cloudQueryKeys.databases(compartmentId),
    queryFn: () => cloudApi.getDatabases(compartmentId),
    enabled: !!compartmentId,
  });
}

// Get OKE clusters
export function useOKEClusters(compartmentId: string): UseQueryResult<CloudResource[], Error> {
  return useQuery({
    queryKey: cloudQueryKeys.okeClusters(compartmentId),
    queryFn: () => cloudApi.getOKEClusters(compartmentId),
    enabled: !!compartmentId,
  });
}

// Get resource metrics (optimized - no aggressive polling)
export function useResourceMetrics(
  resourceId: string, 
  resourceType: string
): UseQueryResult<ResourceMetrics, Error> {
  return useQuery({
    queryKey: cloudQueryKeys.metrics(resourceId),
    queryFn: () => cloudApi.getResourceMetrics(resourceId, resourceType),
    enabled: !!resourceId && !!resourceType,
    staleTime: 5 * 60 * 1000, // 5 minutes for metrics (longer cache)
    // ❌ REMOVED: refetchInterval - use WebSocket for real-time updates instead
    // Real-time metrics should come via WebSocket, not polling
  });
}

// ✅ NEW: Optional manual refresh version for components that need it
export function useResourceMetricsWithRefresh(
  resourceId: string, 
  resourceType: string,
  enableAutoRefresh: boolean = false
): UseQueryResult<ResourceMetrics, Error> {
  return useQuery({
    queryKey: [...cloudQueryKeys.metrics(resourceId), 'manual-refresh'],
    queryFn: () => cloudApi.getResourceMetrics(resourceId, resourceType),
    enabled: !!resourceId && !!resourceType,
    staleTime: 5 * 60 * 1000, // 5 minutes cache
    // Only enable interval if explicitly requested and using smart intervals
    ...(enableAutoRefresh && {
      refetchInterval: 5 * 60 * 1000, // Much longer interval: 5 minutes instead of 1 minute
    }),
  });
}

// Execute resource action mutation
export function useResourceAction(): UseMutationResult<any, Error, { resourceId: string; action: string }> {
  return useMutation({
    mutationFn: ({ resourceId, action }) => cloudApi.executeResourceAction(resourceId, action),
  });
} 

// Get network resources
export function useNetworkResources(compartmentId: string): UseQueryResult<CloudResource[], Error> {
  return useQuery({
    queryKey: [...cloudQueryKeys.compartment(compartmentId), 'network-resources'],
    queryFn: () => cloudApi.getNetworkResources(compartmentId),
    enabled: !!compartmentId,
    staleTime: 5 * 60 * 1000, // 5 minutes (network resources don't change often)
  });
}

// Get block volumes
export function useBlockVolumes(compartmentId: string): UseQueryResult<CloudResource[], Error> {
  return useQuery({
    queryKey: [...cloudQueryKeys.compartment(compartmentId), 'block-volumes'],
    queryFn: () => cloudApi.getBlockVolumes(compartmentId),
    enabled: !!compartmentId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Get file systems
export function useFileSystems(compartmentId: string): UseQueryResult<CloudResource[], Error> {
  return useQuery({
    queryKey: [...cloudQueryKeys.compartment(compartmentId), 'file-systems'],
    queryFn: () => cloudApi.getFileSystems(compartmentId),
    enabled: !!compartmentId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Export the cloudApi instance for direct use
export const cloudService = cloudApi; 