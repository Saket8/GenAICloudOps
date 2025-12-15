import { Pod, PodStatusSummary, Namespace, PodLogs, Container, OwnerReference } from './kubernetesService';

// Mock data for testing Pod Health Analyzer UI
export const mockNamespaces: Namespace[] = [
  {
    name: 'default',
    status: 'Active',
    created_time: '2024-01-15T10:00:00Z',
    labels: { 'kubernetes.io/metadata.name': 'default' },
    annotations: {}
  },
  {
    name: 'kube-system',
    status: 'Active', 
    created_time: '2024-01-15T10:00:00Z',
    labels: { 'kubernetes.io/metadata.name': 'kube-system' },
    annotations: {}
  },
  {
    name: 'production',
    status: 'Active',
    created_time: '2024-01-20T14:30:00Z',
    labels: { 'environment': 'production' },
    annotations: {}
  },
  {
    name: 'staging',
    status: 'Active',
    created_time: '2024-01-22T09:15:00Z',
    labels: { 'environment': 'staging' },
    annotations: {}
  }
];

export const mockContainers: Container[] = [
  {
    name: 'web-server',
    ready: true,
    restart_count: 0,
    image: 'nginx:1.21',
    state: { status: 'running', started_at: '2024-01-25T10:00:00Z' }
  },
  {
    name: 'api-server',
    ready: true,
    restart_count: 2,
    image: 'node:16-alpine',
    state: { status: 'running', started_at: '2024-01-25T10:05:00Z' }
  },
  {
    name: 'database',
    ready: false,
    restart_count: 15,
    image: 'postgres:13',
    state: { 
      status: 'waiting', 
      reason: 'CrashLoopBackOff',
      message: 'back-off 5m0s restarting failed container=database pod=db-pod-xyz_production' 
    }
  }
];

export const mockOwnerReferences: OwnerReference[] = [
  {
    kind: 'ReplicaSet',
    name: 'web-deployment-6d4c5b7f9c',
    uid: 'abc123-def456-ghi789'
  },
  {
    kind: 'Deployment',
    name: 'api-deployment',
    uid: 'xyz789-abc123-def456'
  }
];

export const mockPods: Pod[] = [
  {
    name: 'web-server-6d4c5b7f9c-m8k2p',
    namespace: 'production',
    status: 'Running',
    restart_count: 0,
    node_name: 'worker-node-1',
    created_time: '2024-01-25T10:00:00Z',
    containers: [mockContainers[0]],
    labels: { 
      'app': 'web-server',
      'version': 'v1.2.0',
      'environment': 'production'
    },
    owner_references: [mockOwnerReferences[0]]
  },
  {
    name: 'api-server-5b8c4d6f2a-x7n9q',
    namespace: 'production',
    status: 'Running',
    restart_count: 2,
    node_name: 'worker-node-2',
    created_time: '2024-01-25T10:05:00Z',
    containers: [mockContainers[1]],
    labels: { 
      'app': 'api-server',
      'version': 'v2.1.0',
      'environment': 'production'
    },
    owner_references: [mockOwnerReferences[1]]
  },
  {
    name: 'db-pod-7f3e2a1b9c-k5j8h',
    namespace: 'production',
    status: 'CrashLoopBackOff',
    restart_count: 15,
    node_name: 'worker-node-3',
    created_time: '2024-01-25T09:30:00Z',
    containers: [mockContainers[2]],
    labels: { 
      'app': 'database',
      'version': 'v13.4',
      'environment': 'production'
    },
    owner_references: []
  },
  {
    name: 'redis-cache-4a7b1c8d2e-p9m6n',
    namespace: 'production',
    status: 'Running',
    restart_count: 1,
    node_name: 'worker-node-1',
    created_time: '2024-01-25T11:20:00Z',
    containers: [{
      name: 'redis',
      ready: true,
      restart_count: 1,
      image: 'redis:6.2-alpine',
      state: { status: 'running', started_at: '2024-01-25T11:25:00Z' }
    }],
    labels: { 
      'app': 'redis-cache',
      'environment': 'production'
    },
    owner_references: []
  },
  {
    name: 'monitoring-agent-3f2d8a5c1b-w4t7r',
    namespace: 'kube-system',
    status: 'Running',
    restart_count: 0,
    node_name: 'master-node-1',
    created_time: '2024-01-25T08:00:00Z',
    containers: [{
      name: 'agent',
      ready: true,
      restart_count: 0,
      image: 'monitoring/agent:v1.0',
      state: { status: 'running', started_at: '2024-01-25T08:00:00Z' }
    }],
    labels: { 
      'app': 'monitoring-agent',
      'tier': 'system'
    },
    owner_references: []
  },
  {
    name: 'staging-app-2e9f5c1a6b-q3l8k',
    namespace: 'staging',
    status: 'Pending',
    restart_count: 0,
    node_name: '',
    created_time: '2024-01-25T12:00:00Z',
    containers: [{
      name: 'app',
      ready: false,
      restart_count: 0,
      image: 'myapp:staging-latest',
      state: { 
        status: 'waiting', 
        reason: 'ImagePullBackOff',
        message: 'Failed to pull image "myapp:staging-latest": rpc error: code = NotFound'
      }
    }],
    labels: { 
      'app': 'staging-app',
      'environment': 'staging'
    },
    owner_references: []
  },
  {
    name: 'worker-queue-1a4b7c9d2f-h6j2m',
    namespace: 'production',
    status: 'Running',
    restart_count: 3,
    node_name: 'worker-node-2',
    created_time: '2024-01-25T09:45:00Z',
    containers: [{
      name: 'worker',
      ready: true,
      restart_count: 3,
      image: 'worker:v1.8.0',
      state: { status: 'running', started_at: '2024-01-25T11:30:00Z' }
    }],
    labels: { 
      'app': 'worker-queue',
      'environment': 'production'
    },
    owner_references: []
  }
];

export const mockPodStatusSummary: PodStatusSummary = {
  total_pods: mockPods.length,
  status_counts: {
    'Running': 5,
    'CrashLoopBackOff': 1,
    'Pending': 1
  },
  total_restarts: mockPods.reduce((sum, pod) => sum + pod.restart_count, 0),
  problem_pods: mockPods.filter(pod => 
    pod.status !== 'Running' || pod.restart_count > 5
  ).map(pod => ({
    name: pod.name,
    namespace: pod.namespace,
    status: pod.status,
    restart_count: pod.restart_count,
    node_name: pod.node_name
  })),
  healthy_percentage: Math.round((5 / mockPods.length) * 100)
};

export const mockPodLogs: Record<string, PodLogs> = {
  'db-pod-7f3e2a1b9c-k5j8h': {
    pod_name: 'db-pod-7f3e2a1b9c-k5j8h',
    namespace: 'production',
    container: 'database',
    timestamp: '2024-01-25T12:30:00Z',
    logs: `2024-01-25 12:25:32.123 [ERROR] Failed to start PostgreSQL server
2024-01-25 12:25:32.124 [ERROR] FATAL: could not create shared memory segment: Invalid argument
2024-01-25 12:25:32.125 [ERROR] DETAIL: Failed system call was shmget(key=5432001, size=56, 03600).
2024-01-25 12:25:32.126 [ERROR] HINT: This error usually means that PostgreSQL's request for a shared memory segment exceeded your kernel's SHMMAX parameter, or possibly that it exceeded your kernel's SHMALL parameter.
2024-01-25 12:25:32.127 [INFO] PostgreSQL Database directory appears to contain a database; Skipping initialization
2024-01-25 12:25:32.128 [ERROR] 2024-01-25 12:25:32.128 UTC [1] FATAL: could not create shared memory segment: Invalid argument
2024-01-25 12:25:32.129 [ERROR] 2024-01-25 12:25:32.129 UTC [1] DETAIL: Failed system call was shmget(key=5432001, size=56, 03600).
2024-01-25 12:25:32.130 [ERROR] 2024-01-25 12:25:32.130 UTC [1] HINT: This error usually means that PostgreSQL's request for a shared memory segment exceeded your kernel's SHMMAX parameter.
2024-01-25 12:25:33.001 [INFO] Attempting restart in 10 seconds...
2024-01-25 12:25:43.002 [INFO] Starting PostgreSQL server...
2024-01-25 12:25:43.003 [ERROR] FATAL: could not create shared memory segment: Invalid argument
2024-01-25 12:25:43.004 [ERROR] Container will restart due to failure
2024-01-25 12:25:44.001 [INFO] Container restarting... (attempt 16/∞)`
  },
  'staging-app-2e9f5c1a6b-q3l8k': {
    pod_name: 'staging-app-2e9f5c1a6b-q3l8k',
    namespace: 'staging',
    container: 'app',
    timestamp: '2024-01-25T12:30:00Z',
    logs: `2024-01-25 12:00:15.123 [INFO] Starting container initialization...
2024-01-25 12:00:15.124 [INFO] Checking for required environment variables...
2024-01-25 12:00:15.125 [INFO] Environment check passed
2024-01-25 12:00:15.126 [INFO] Attempting to pull image: myapp:staging-latest
2024-01-25 12:00:16.234 [WARN] Image pull attempt 1 failed: repository does not exist
2024-01-25 12:00:21.345 [WARN] Image pull attempt 2 failed: repository does not exist  
2024-01-25 12:00:26.456 [WARN] Image pull attempt 3 failed: repository does not exist
2024-01-25 12:00:31.567 [ERROR] Failed to pull image "myapp:staging-latest": rpc error: code = NotFound desc = failed to pull and unpack image
2024-01-25 12:00:31.568 [ERROR] ImagePullBackOff: Back-off pulling image "myapp:staging-latest"
2024-01-25 12:00:31.569 [INFO] Will retry in 10 seconds...
2024-01-25 12:00:41.678 [INFO] Retrying image pull...
2024-01-25 12:00:42.789 [ERROR] Pull failed again: repository not found`
  },
  'web-server-6d4c5b7f9c-m8k2p': {
    pod_name: 'web-server-6d4c5b7f9c-m8k2p',
    namespace: 'production',
    container: 'web-server',
    timestamp: '2024-01-25T12:30:00Z',
    logs: `2024-01-25 10:00:15.123 [INFO] Starting Nginx web server...
2024-01-25 10:00:15.200 [INFO] Nginx version: nginx/1.21.6
2024-01-25 10:00:15.201 [INFO] Built with OpenSSL 1.1.1n
2024-01-25 10:00:15.202 [INFO] Configuration file /etc/nginx/nginx.conf syntax is ok
2024-01-25 10:00:15.203 [INFO] Configuration file /etc/nginx/nginx.conf test is successful
2024-01-25 10:00:15.210 [INFO] Starting Nginx master process...
2024-01-25 10:00:15.211 [INFO] Master process started with PID 1
2024-01-25 10:00:15.212 [INFO] Starting worker processes...
2024-01-25 10:00:15.213 [INFO] Worker process started with PID 7
2024-01-25 10:00:15.214 [INFO] Worker process started with PID 8
2024-01-25 10:00:15.215 [INFO] Nginx successfully started and ready to serve requests
2024-01-25 12:28:45.123 [INFO] GET /health 200 - 2ms
2024-01-25 12:29:15.456 [INFO] GET /api/status 200 - 5ms
2024-01-25 12:29:45.789 [INFO] GET /health 200 - 1ms`
  }
};

// Mock Kubernetes Service for testing
export class MockKubernetesService {
  
  async getNamespaces(): Promise<Namespace[]> {
    // Simulate network delay
    await this.delay(500);
    return mockNamespaces;
  }

  async getPods(namespace?: string): Promise<Pod[]> {
    await this.delay(800);
    
    if (namespace) {
      return mockPods.filter(pod => pod.namespace === namespace);
    }
    return mockPods;
  }

  async getPodStatusSummary(namespace?: string): Promise<PodStatusSummary> {
    await this.delay(600);
    
    const filteredPods = namespace 
      ? mockPods.filter(pod => pod.namespace === namespace)
      : mockPods;
    
    const statusCounts: Record<string, number> = {};
    filteredPods.forEach(pod => {
      statusCounts[pod.status] = (statusCounts[pod.status] || 0) + 1;
    });
    
    const runningCount = statusCounts['Running'] || 0;
    const totalRestarts = filteredPods.reduce((sum, pod) => sum + pod.restart_count, 0);
    const problemPods = filteredPods.filter(pod => 
      pod.status !== 'Running' || pod.restart_count > 5
    ).map(pod => ({
      name: pod.name,
      namespace: pod.namespace,
      status: pod.status,
      restart_count: pod.restart_count,
      node_name: pod.node_name
    }));

    return {
      total_pods: filteredPods.length,
      status_counts: statusCounts,
      total_restarts: totalRestarts,
      problem_pods: problemPods,
      healthy_percentage: filteredPods.length > 0 
        ? Math.round((runningCount / filteredPods.length) * 100) 
        : 0
    };
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
    await this.delay(1000);
    
    const logKey = podName;
    const log = mockPodLogs[logKey];
    
    if (log) {
      return {
        ...log,
        logs: options.lines && options.lines < 100 
          ? log.logs.split('\n').slice(-options.lines).join('\n')
          : log.logs
      };
    }
    
    // Default log for pods without specific logs
    return {
      pod_name: podName,
      namespace: namespace,
      container: options.container || 'main',
      timestamp: new Date().toISOString(),
      logs: `2024-01-25 12:30:00.000 [INFO] Container started successfully
2024-01-25 12:30:01.123 [INFO] Application initialized
2024-01-25 12:30:02.456 [INFO] Ready to serve requests
2024-01-25 12:30:15.789 [INFO] Health check passed
2024-01-25 12:30:30.012 [INFO] Processing incoming requests...`
    };
  }

  async restartPod(namespace: string, podName: string): Promise<boolean> {
    await this.delay(2000);
    console.log(`Mock: Restarting pod ${namespace}/${podName}`);
    return true;
  }

  async deletePod(namespace: string, podName: string): Promise<boolean> {
    await this.delay(1500);
    console.log(`Mock: Deleting pod ${namespace}/${podName}`);
    return true;
  }

  async healthCheck(): Promise<{ status: string; message: string }> {
    await this.delay(200);
    return {
      status: 'healthy',
      message: 'Mock Kubernetes service is working properly'
    };
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export const mockKubernetesService = new MockKubernetesService(); 