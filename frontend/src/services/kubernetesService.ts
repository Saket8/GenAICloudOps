import apiClient from './apiClient';

// Types for Kubernetes API responses
export interface Pod {
  name: string;
  namespace: string;
  status: string;
  restart_count: number;
  node_name: string;
  created_time: string;
  containers: Container[];
  labels: Record<string, string>;
  owner_references: OwnerReference[];
}

export interface Container {
  name: string;
  ready: boolean;
  restart_count: number;
  image: string;
  state: ContainerState;
}

export interface ContainerState {
  status: string;
  reason?: string;
  message?: string;
  started_at?: string;
}

export interface OwnerReference {
  kind: string;
  name: string;
  uid: string;
}

export interface PodLogs {
  pod_name: string;
  namespace: string;
  container?: string;
  logs: string;
  timestamp: string;
}

export interface PodStatusSummary {
  total_pods: number;
  status_counts: Record<string, number>;
  total_restarts: number;
  problem_pods: ProblemPod[];
  healthy_percentage: number;
}

export interface ProblemPod {
  name: string;
  namespace: string;
  status: string;
  restart_count: number;
  node_name: string;
}

export interface Namespace {
  name: string;
  status: string;
  created_time: string;
  labels: Record<string, string>;
  annotations: Record<string, string>;
}

export interface ClusterInfo {
  name: string;
  server: string;
  version: string;
  namespace_count: number;
  pod_count: number;
  node_count: number;
  healthy: boolean;
}

export class KubernetesService {
  private baseUrl = '/api/v1/kubernetes';

  // Cluster management
  async getClusterInfo(): Promise<ClusterInfo> {
    const response = await apiClient.get(`${this.baseUrl}/cluster/info`);
    return response.data;
  }

  async configureCluster(kubeconfig: string, clusterName: string = 'default'): Promise<boolean> {
    const response = await apiClient.post(`${this.baseUrl}/cluster/configure`, {
      kubeconfig_content: kubeconfig,
      cluster_name: clusterName
    });
    return response.data.success;
  }

  // Namespace operations
  async getNamespaces(): Promise<Namespace[]> {
    const response = await apiClient.get(`${this.baseUrl}/namespaces`);
    return response.data;
  }

  // Pod operations
  async getPods(namespace?: string): Promise<Pod[]> {
    const params = namespace ? { namespace } : {};
    const response = await apiClient.get(`${this.baseUrl}/pods`, { params });
    return response.data;
  }

  async getPodStatusSummary(namespace?: string): Promise<PodStatusSummary> {
    const params = namespace ? { namespace } : {};
    const response = await apiClient.get(`${this.baseUrl}/pods/status-summary`, { params });
    return response.data;
  }

  async getPodLogs(
    namespace: string, 
    podName: string, 
    options: {
      container?: string;
      lines?: number;
      since?: string;
      tail?: boolean;
    } = {}
  ): Promise<PodLogs> {
    const params = {
      container: options.container,
      lines: options.lines || 100,
      since: options.since,
      tail: options.tail || false
    };
    
    const response = await apiClient.get(
      `${this.baseUrl}/pods/${namespace}/${podName}/logs`, 
      { params }
    );
    return response.data;
  }

  // Utility methods
  async restartPod(namespace: string, podName: string): Promise<boolean> {
    const response = await apiClient.post(
      `${this.baseUrl}/pods/${namespace}/${podName}/restart`
    );
    return response.data.success;
  }

  async deletePod(namespace: string, podName: string): Promise<boolean> {
    const response = await apiClient.delete(
      `${this.baseUrl}/pods/${namespace}/${podName}`
    );
    return response.data.success;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await apiClient.get(`${this.baseUrl}/health`);
    return response.data;
  }
}

export const kubernetesService = new KubernetesService(); 