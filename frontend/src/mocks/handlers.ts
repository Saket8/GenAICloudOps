/**
 * MSW API handlers for mocking backend endpoints
 * Provides realistic mock responses for all API calls
 */

import { http, HttpResponse } from 'msw';

// Mock data
const mockUser = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  full_name: 'Admin User',
  is_active: true,
  roles: ['admin']
};

const mockToken = {
  access_token: 'mock-jwt-token',
  token_type: 'bearer',
  expires_in: 3600
};

// Enhanced mock compartments
const mockCompartments = [
  {
    id: 'ocid1.compartment.oc1..prod',
    name: 'Production',
    description: 'Production environment compartment',
    lifecycle_state: 'ACTIVE'
  },
  {
    id: 'ocid1.compartment.oc1..staging',
    name: 'Staging',
    description: 'Staging environment compartment',
    lifecycle_state: 'ACTIVE'
  },
  {
    id: 'test-compartment',
    name: 'Test Environment',
    description: 'Test compartment for development',
    lifecycle_state: 'ACTIVE'
  }
];

// Enhanced mock instances for Cloud Resources
const mockInstances = [
  {
    id: 'ocid1.instance.oc1.us-ashburn-1.test1',
    display_name: 'web-server-1',
    lifecycle_state: 'RUNNING',
    availability_domain: 'US-ASHBURN-AD-1',
    shape: 'VM.Standard2.1',
    time_created: '2024-01-01T00:00:00Z',
    cpu_utilization: 45.2,
    memory_utilization: 67.8,
    region: 'us-ashburn-1',
    fault_domain: 'FAULT-DOMAIN-1'
  },
  {
    id: 'ocid1.instance.oc1.us-ashburn-1.test2',
    display_name: 'database-server',
    lifecycle_state: 'STOPPED',
    availability_domain: 'US-ASHBURN-AD-2',
    shape: 'VM.Standard2.2',
    time_created: '2024-01-02T00:00:00Z',
    cpu_utilization: 0,
    memory_utilization: 0,
    region: 'us-ashburn-1',
    fault_domain: 'FAULT-DOMAIN-2'
  },
  {
    id: 'ocid1.instance.oc1.us-ashburn-1.test3',
    display_name: 'load-balancer',
    lifecycle_state: 'RUNNING',
    availability_domain: 'US-ASHBURN-AD-3',
    shape: 'VM.Standard2.1',
    time_created: '2024-01-03T00:00:00Z',
    cpu_utilization: 25.5,
    memory_utilization: 45.3,
    region: 'us-ashburn-1',
    fault_domain: 'FAULT-DOMAIN-3'
  }
];

// Enhanced monitoring mock data
const mockAlertSummary = {
  compartment_id: 'test-compartment',
  total_alarms: 8,
  active_alarms: 3,
  severity_breakdown: {
    'CRITICAL': 1,
    'HIGH': 2,
    'MEDIUM': 3,
    'LOW': 2,
    'INFO': 0
  },
  recent_activity: {
    last_24h_alerts: 5,
    resolved_alerts: 2,
    alert_rate: 2.1
  },
  top_alerts: [
    {
      name: 'High CPU Usage - web-server-1',
      severity: 'CRITICAL',
      timestamp: '2024-01-01T12:00:00Z'
    },
    {
      name: 'Memory Usage Warning',
      severity: 'HIGH',
      timestamp: '2024-01-01T11:30:00Z'
    }
  ],
  timestamp: new Date().toISOString(),
  health_score: 0.75
};

const mockAlarms = [
  {
    id: 'alarm-1',
    display_name: 'High CPU Usage - web-server-1',
    severity: 'CRITICAL',
    is_enabled: true,
    lifecycle_state: 'ACTIVE',
    namespace: 'oci_computeagent',
    query: 'CpuUtilization[1m].mean() > 80',
    metric_compartment_id: 'ocid1.compartment.oc1..prod',
    time_created: '2024-01-01T12:00:00Z',
    time_updated: '2024-01-01T12:30:00Z'
  },
  {
    id: 'alarm-2',
    display_name: 'Database Memory Warning',
    severity: 'HIGH',
    is_enabled: true,
    lifecycle_state: 'ACTIVE',
    namespace: 'oci_database',
    query: 'MemoryUtilization[5m].mean() > 85',
    metric_compartment_id: 'ocid1.compartment.oc1..prod',
    time_created: '2024-01-01T11:30:00Z',
    time_updated: '2024-01-01T11:45:00Z'
  },
  {
    id: 'alarm-3',
    display_name: 'Network Latency Alert',
    severity: 'MEDIUM',
    is_enabled: false,
    lifecycle_state: 'INACTIVE',
    namespace: 'oci_vcn',
    query: 'NetworkLatency[1m].mean() > 100',
    metric_compartment_id: 'ocid1.compartment.oc1..staging',
    time_created: '2024-01-01T10:15:00Z',
    time_updated: '2024-01-01T10:20:00Z'
  }
];

const mockAlarmHistory = [
  {
    id: 'history-1',
    alarm_id: 'alarm-1',
    status: 'FIRING',
    timestamp: '2024-01-01T12:00:00Z',
    message: 'CPU usage exceeded threshold'
  },
  {
    id: 'history-2',
    alarm_id: 'alarm-2',
    status: 'OK',
    timestamp: '2024-01-01T11:00:00Z',
    message: 'Memory usage returned to normal'
  }
];

const mockPods = [
  {
    metadata: {
      name: 'frontend-pod-1',
      namespace: 'default',
      labels: { app: 'frontend' }
    },
    status: {
      phase: 'Running',
      pod_ip: '10.0.1.1'
    },
    spec: {
      containers: [
        { name: 'frontend', image: 'nginx:latest' }
      ]
    }
  },
  {
    metadata: {
      name: 'backend-pod-1',
      namespace: 'default',
      labels: { app: 'backend' }
    },
    status: {
      phase: 'Running',
      pod_ip: '10.0.1.2'
    },
    spec: {
      containers: [
        { name: 'backend', image: 'python:3.9' }
      ]
    }
  }
];

const mockAlerts = [
  {
    id: 'alert-1',
    severity: 'warning',
    title: 'High CPU Usage',
    description: 'Instance web-server-1 CPU usage is above 80%',
    timestamp: '2024-01-01T12:00:00Z',
    status: 'active',
    resource_id: 'ocid1.instance.oc1.us-ashburn-1.test1'
  },
  {
    id: 'alert-2',
    severity: 'error',
    title: 'Service Down',
    description: 'Database service is not responding',
    timestamp: '2024-01-01T11:30:00Z',
    status: 'resolved',
    resource_id: 'ocid1.instance.oc1.us-ashburn-1.test2'
  }
];

const mockRemediationActions = [
  {
    id: 'action-1',
    name: 'Restart Service',
    description: 'Restart the application service',
    status: 'completed',
    created_at: '2024-01-01T10:00:00Z',
    executed_at: '2024-01-01T10:05:00Z',
    resource_id: 'ocid1.instance.oc1.us-ashburn-1.test1'
  }
];

const mockChatHistory = [
  {
    id: 'msg-1',
    role: 'user',
    content: 'What is the status of my instances?',
    timestamp: '2024-01-01T09:00:00Z'
  },
  {
    id: 'msg-2',
    role: 'assistant',
    content: 'You have 2 instances: web-server-1 is running, and database-server is stopped.',
    timestamp: '2024-01-01T09:00:05Z'
  }
];

export const handlers = [
  // Authentication endpoints
  http.post('*/api/v1/auth/login', async ({ request }) => {
    const body = await request.json() as any;
    
    if (body.username === 'admin' && body.password === 'AdminPass123!') {
      return HttpResponse.json({
        access_token: 'mock-jwt-token-123',
        refresh_token: 'mock-refresh-token-123',
        token_type: 'bearer',
        expires_in: 3600
      });
    }
    
    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  http.post('*/api/v1/auth/logout', () => {
    return HttpResponse.json({ message: 'Logged out successfully' });
  }),

  http.get('*/api/v1/auth/me', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (authHeader?.includes('mock-jwt-token')) {
      return HttpResponse.json({
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        full_name: 'Admin User',
        is_active: true,
        roles: ['admin']
      });
    }
    
    return HttpResponse.json(
      { detail: 'Unauthorized' },
      { status: 401 }
    );
  }),

  http.get('*/api/v1/auth/me/permissions', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (authHeader?.includes('mock-jwt-token')) {
      return HttpResponse.json({
        permissions: {
          can_view_dashboard: true,
          can_view_alerts: true,
          can_approve_remediation: true,
          can_execute_remediation: true,
          can_manage_users: true,
          can_manage_roles: true,
          can_view_access_analyzer: true,
          can_view_pod_analyzer: true,
          can_view_cost_analyzer: true,
          can_use_chatbot: true
        }
      });
    }
    
    return HttpResponse.json(
      { detail: 'Unauthorized' },
      { status: 401 }
    );
  }),

  // ADD: Token refresh endpoint
  http.post('*/api/v1/auth/refresh', async ({ request }) => {
    const body = await request.json() as any;
    
    if (body.refresh_token === 'mock-refresh-token-123') {
      return HttpResponse.json({
        access_token: 'mock-jwt-token-456',
        refresh_token: 'mock-refresh-token-456',
        token_type: 'bearer',
        expires_in: 3600
      });
    }
    
    return HttpResponse.json(
      { detail: 'Invalid refresh token' },
      { status: 401 }
    );
  }),

  // ADD: Token verification endpoint
  http.get('*/api/v1/auth/verify-token', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (authHeader?.includes('mock-jwt-token')) {
      return HttpResponse.json({
        valid: true,
        user_id: 1,
        username: 'admin'
      });
    }
    
    return HttpResponse.json(
      { detail: 'Invalid token' },
      { status: 401 }
    );
  }),

  // Cloud/OCI endpoints
  http.get('*/api/v1/cloud/compartments', () => {
    return HttpResponse.json(mockCompartments);
  }),

  // NEW: Get all resources in a compartment (for Dashboard page)
  http.get('*/api/v1/cloud/compartments/:compartmentId/resources', ({ params }) => {
    const compartmentId = params.compartmentId as string;
    
    return HttpResponse.json({
      compartment_id: compartmentId,
      resources: {
        compute_instances: mockInstances,
        databases: [
          {
            id: 'ocid1.database.oc1.us-ashburn-1.db1',
            display_name: 'production-database',
            lifecycle_state: 'AVAILABLE',
            resource_type: 'database',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          },
          {
            id: 'ocid1.database.oc1.us-ashburn-1.db2',
            display_name: 'staging-database',
            lifecycle_state: 'AVAILABLE',
            resource_type: 'database',
            compartment_id: compartmentId,
            time_created: '2024-01-02T00:00:00Z'
          }
        ],
        oke_clusters: [
          {
            id: 'ocid1.cluster.oc1.us-ashburn-1.cluster1',
            display_name: 'production-cluster',
            lifecycle_state: 'ACTIVE',
            resource_type: 'oke_cluster',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          }
        ],
        api_gateways: [
          {
            id: 'ocid1.apigateway.oc1.us-ashburn-1.gw1',
            display_name: 'main-api-gateway',
            lifecycle_state: 'ACTIVE',
            resource_type: 'api_gateway',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          }
        ],
        load_balancers: [
          {
            id: 'ocid1.loadbalancer.oc1.us-ashburn-1.lb1',
            display_name: 'production-lb',
            lifecycle_state: 'ACTIVE',
            resource_type: 'load_balancer',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          }
        ],
        network_resources: [
          {
            id: 'ocid1.vcn.oc1.us-ashburn-1.vcn1',
            display_name: 'main-vcn',
            lifecycle_state: 'AVAILABLE',
            resource_type: 'vcn',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          },
          {
            id: 'ocid1.subnet.oc1.us-ashburn-1.subnet1',
            display_name: 'public-subnet',
            lifecycle_state: 'AVAILABLE',
            resource_type: 'subnet',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          }
        ],
        storage_resources: [
          {
            id: 'ocid1.bucket.oc1.us-ashburn-1.bucket1',
            display_name: 'data-backup-bucket',
            lifecycle_state: 'ACTIVE',
            resource_type: 'bucket',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          }
        ],
        block_volumes: [
          {
            id: 'ocid1.volume.oc1.us-ashburn-1.vol1',
            display_name: 'database-storage',
            lifecycle_state: 'AVAILABLE',
            resource_type: 'block_volume',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          },
          {
            id: 'ocid1.volume.oc1.us-ashburn-1.vol2',
            display_name: 'backup-storage',
            lifecycle_state: 'AVAILABLE',
            resource_type: 'block_volume',
            compartment_id: compartmentId,
            time_created: '2024-01-02T00:00:00Z'
          }
        ],
        file_systems: [
          {
            id: 'ocid1.filesystem.oc1.us-ashburn-1.fs1',
            display_name: 'shared-storage',
            lifecycle_state: 'ACTIVE',
            resource_type: 'file_system',
            compartment_id: compartmentId,
            time_created: '2024-01-01T00:00:00Z'
          }
        ]
      },
      total_resources: 12,
      last_updated: new Date().toISOString()
    });
  }),

  // Individual resource type endpoints for Dashboard
  http.get('*/api/v1/cloud/compartments/:compartmentId/compute-instances', ({ params }) => {
    return HttpResponse.json(mockInstances);
  }),

  http.get('*/api/v1/cloud/compartments/:compartmentId/databases', ({ params }) => {
    return HttpResponse.json([
      {
        id: 'ocid1.database.oc1.us-ashburn-1.db1',
        display_name: 'production-database',
        lifecycle_state: 'AVAILABLE',
        resource_type: 'database',
        compartment_id: params.compartmentId,
        time_created: '2024-01-01T00:00:00Z'
      }
    ]);
  }),

  http.get('*/api/v1/cloud/compartments/:compartmentId/oke-clusters', ({ params }) => {
    return HttpResponse.json([
      {
        id: 'ocid1.cluster.oc1.us-ashburn-1.cluster1',
        display_name: 'production-cluster',
        lifecycle_state: 'ACTIVE',
        resource_type: 'oke_cluster',
        compartment_id: params.compartmentId,
        time_created: '2024-01-01T00:00:00Z'
      }
    ]);
  }),

  http.get('*/api/v1/cloud/compartments/:compartmentId/api-gateways', ({ params }) => {
    return HttpResponse.json([
      {
        id: 'ocid1.apigateway.oc1.us-ashburn-1.gw1',
        display_name: 'main-api-gateway',
        lifecycle_state: 'ACTIVE',
        resource_type: 'api_gateway',
        compartment_id: params.compartmentId,
        time_created: '2024-01-01T00:00:00Z'
      }
    ]);
  }),

  http.get('*/api/v1/cloud/compartments/:compartmentId/load-balancers', ({ params }) => {
    return HttpResponse.json([
      {
        id: 'ocid1.loadbalancer.oc1.us-ashburn-1.lb1',
        display_name: 'production-lb',
        lifecycle_state: 'ACTIVE',
        resource_type: 'load_balancer',
        compartment_id: params.compartmentId,
        time_created: '2024-01-01T00:00:00Z'
      }
    ]);
  }),

  http.get('*/api/v1/cloud/compartments/:compartmentId/network-resources', ({ params }) => {
    return HttpResponse.json([
      {
        id: 'ocid1.vcn.oc1.us-ashburn-1.vcn1',
        display_name: 'main-vcn',
        lifecycle_state: 'AVAILABLE',
        resource_type: 'vcn',
        compartment_id: params.compartmentId,
        time_created: '2024-01-01T00:00:00Z'
      }
    ]);
  }),

  http.get('*/api/v1/cloud/compartments/:compartmentId/block-volumes', ({ params }) => {
    return HttpResponse.json([
      {
        id: 'ocid1.volume.oc1.us-ashburn-1.vol1',
        display_name: 'database-storage',
        lifecycle_state: 'AVAILABLE',
        resource_type: 'block_volume',
        compartment_id: params.compartmentId,
        time_created: '2024-01-01T00:00:00Z'
      }
    ]);
  }),

  http.get('*/api/v1/cloud/compartments/:compartmentId/file-systems', ({ params }) => {
    return HttpResponse.json([
      {
        id: 'ocid1.filesystem.oc1.us-ashburn-1.fs1',
        display_name: 'shared-storage',
        lifecycle_state: 'ACTIVE',
        resource_type: 'file_system',
        compartment_id: params.compartmentId,
        time_created: '2024-01-01T00:00:00Z'
      }
    ]);
  }),

  http.get('*/api/v1/cloud/instances', () => {
    return HttpResponse.json(mockInstances);
  }),

  http.get('*/api/v1/cloud/instances/:instanceId', ({ params }) => {
    const instance = mockInstances.find(i => i.id === params.instanceId);
    
    if (instance) {
      return HttpResponse.json(instance);
    }
    
    return HttpResponse.json(
      { detail: 'Instance not found' },
      { status: 404 }
    );
  }),

  http.post('*/api/v1/cloud/instances/:instanceId/start', ({ params }) => {
    return HttpResponse.json({
      message: `Instance ${params.instanceId} start initiated`
    });
  }),

  http.post('*/api/v1/cloud/instances/:instanceId/stop', ({ params }) => {
    return HttpResponse.json({
      message: `Instance ${params.instanceId} stop initiated`
    });
  }),

  // Kubernetes endpoints
  http.get('*/api/v1/kubernetes/pods', () => {
    return HttpResponse.json(mockPods);
  }),

  http.get('*/api/v1/kubernetes/pods/:podName/logs', ({ params }) => {
    return HttpResponse.json({
      logs: [
        '2024-01-01T12:00:00Z INFO: Application started',
        '2024-01-01T12:01:00Z INFO: Processing request',
        '2024-01-01T12:02:00Z WARN: High memory usage detected',
        '2024-01-01T12:03:00Z INFO: Request completed'
      ]
    });
  }),

  // ===== FIXED MONITORING ENDPOINTS =====
  
  // Alert Summary endpoint (matches MonitoringPage expectations)
  http.get('*/api/v1/monitoring/alerts/summary', ({ request }) => {
    const url = new URL(request.url);
    const compartmentId = url.searchParams.get('compartment_id') || 'test-compartment';
    
    return HttpResponse.json({
      ...mockAlertSummary,
      compartment_id: compartmentId
    });
  }),

  // Alarms endpoint (matches MonitoringPage expectations)  
  http.get('*/api/v1/monitoring/alarms', ({ request }) => {
    const url = new URL(request.url);
    const compartmentId = url.searchParams.get('compartment_id') || 'test-compartment';
    
    return HttpResponse.json(mockAlarms.map(alarm => ({
      ...alarm,
      metric_compartment_id: compartmentId
    })));
  }),

  // Alarm History endpoint (matches MonitoringPage expectations)
  http.get('*/api/v1/monitoring/alarms/history', ({ request }) => {
    const url = new URL(request.url);
    const compartmentId = url.searchParams.get('compartment_id') || 'test-compartment';
    
    return HttpResponse.json(mockAlarmHistory);
  }),

  // Legacy monitoring endpoints for backward compatibility
  http.get('*/api/v1/monitoring/alerts', () => {
    return HttpResponse.json(mockAlerts);
  }),

  http.get('*/api/v1/monitoring/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      services: {
        database: 'healthy',
        oci: 'healthy',
        kubernetes: 'healthy'
      },
      timestamp: new Date().toISOString()
    });
  }),

  http.get('*/api/v1/monitoring/metrics', () => {
    return HttpResponse.json({
      cpu_usage: 45.2,
      memory_usage: 67.8,
      disk_usage: 23.1,
      network_io: 12.5,
      timestamp: new Date().toISOString()
    });
  }),

  // Remediation endpoints
  http.get('*/api/v1/remediation/actions', () => {
    return HttpResponse.json(mockRemediationActions);
  }),

  http.post('*/api/v1/remediation/actions', async ({ request }) => {
    const body = await request.json() as any;
    
    const newAction = {
      id: `action-${Date.now()}`,
      name: body.name,
      description: body.description,
      status: 'pending',
      created_at: new Date().toISOString(),
      resource_id: body.resource_id
    };
    
    return HttpResponse.json(newAction, { status: 201 });
  }),

  http.post('*/api/v1/remediation/actions/:actionId/execute', ({ params }) => {
    return HttpResponse.json({
      message: `Action ${params.actionId} execution started`
    });
  }),

  // GenAI/Chatbot endpoints
  http.get('*/api/v1/chatbot/history', () => {
    return HttpResponse.json(mockChatHistory);
  }),

  http.post('*/api/v1/chatbot/chat', async ({ request }) => {
    const body = await request.json() as any;
    
    // Simulate AI response based on input
    let response = 'I can help you with cloud operations and monitoring.';
    
    if (body.message.toLowerCase().includes('instance')) {
      response = 'You have 3 instances: web-server-1 and load-balancer are running, database-server is stopped.';
    } else if (body.message.toLowerCase().includes('alert')) {
      response = 'You have 3 active alerts: 1 critical (High CPU), 2 high severity alerts.';
    } else if (body.message.toLowerCase().includes('pod')) {
      response = 'You have 2 pods running in the default namespace.';
    }
    
    return HttpResponse.json({
      response,
      timestamp: new Date().toISOString()
    });
  }),

  // GenAI endpoints
  http.post('*/api/v1/genai/analyze', async ({ request }) => {
    const body = await request.json() as any;
    
    return HttpResponse.json({
      analysis: `Analysis of ${body.context}: This appears to be a ${body.type} issue that can be resolved by following these steps...`,
      recommendations: [
        'Check system resources',
        'Review logs for errors',
        'Consider scaling if needed'
      ],
      confidence: 0.85
    });
  }),

  // NEW: GenAI Production Insights endpoint for AlertsPage AI Insights tab
  http.post('*/api/genai/insights/production-analysis', async ({ request }) => {
    const body = await request.json() as any;
    const compartmentId = body.compartment_id || 'test-compartment';
    
    return HttpResponse.json({
      analysis_id: 'prod-analysis-123',
      compartment_id: compartmentId,
      insights: {
        executive_summary: `Comprehensive analysis of ${compartmentId} shows 3 active alerts with 1 critical issue requiring immediate attention. System health score: 75%. Recommended actions: investigate CPU usage patterns and review scaling policies.`,
        predictive_analytics: {
          detected_patterns: [
            {
              title: "Recurring CPU Spikes",
              description: "CPU usage spikes occur every 4 hours, indicating possible batch job interference",
              severity: "HIGH",
              confidence: 0.87,
              recommendations: [
                "Schedule batch jobs during low-traffic periods",
                "Implement CPU usage monitoring with auto-scaling",
                "Review application resource allocation"
              ]
            },
            {
              title: "Memory Leak Pattern",
              description: "Gradual memory increase detected over 6-hour periods",
              severity: "MEDIUM", 
              confidence: 0.72,
              recommendations: [
                "Profile application memory usage",
                "Implement memory monitoring alerts",
                "Consider application restart policies"
              ]
            }
          ],
          predictions: [
            {
              title: "Service Degradation Risk",
              probability: "High (78%)",
              timeframe: "Next 2-4 hours",
              description: "Current CPU usage trends indicate potential service degradation if load increases",
              preventive_actions: [
                "Scale compute resources proactively",
                "Monitor traffic patterns closely",
                "Prepare rollback procedures",
                "Alert on-call team"
              ]
            }
          ]
        },
        proactive_recommendations: [
          {
            priority: "CRITICAL",
            action: "Immediate CPU Investigation",
            description: "Address high CPU usage alert in web-server-1 immediately to prevent service impact",
            estimated_impact: "Prevents potential 15-minute service outage",
            automation_available: true
          },
          {
            priority: "HIGH", 
            action: "Implement Auto-Scaling",
            description: "Configure horizontal pod autoscaling based on CPU and memory thresholds",
            estimated_impact: "Reduces manual intervention by 60%",
            automation_available: true
          },
          {
            priority: "MEDIUM",
            action: "Optimize Alert Thresholds",
            description: "Fine-tune alert thresholds to reduce false positives while maintaining coverage",
            estimated_impact: "Improves alert signal-to-noise ratio by 40%",
            automation_available: false
          }
        ],
        capacity_planning: {
          current_utilization: {
            cpu: 68,
            memory: 74,
            storage: 45
          },
          predicted_growth: "15% over next 30 days",
          scaling_recommendations: [
            "Add 2 additional compute instances within 14 days",
            "Increase memory allocation for database services",
            "Plan storage expansion for logging services"
          ]
        },
        risk_assessment: {
          overall_risk_score: 6.5,
          risk_factors: [
            {
              factor: "High CPU Usage",
              impact: "HIGH",
              probability: "MEDIUM",
              mitigation: "Auto-scaling implementation"
            },
            {
              factor: "Single Point of Failure",
              impact: "CRITICAL",
              probability: "LOW",
              mitigation: "Deploy redundant instances"
            }
          ]
        },
        performance_optimization: {
          opportunities: [
            {
              area: "Database Queries",
              potential_improvement: "25% response time reduction",
              effort: "MEDIUM",
              description: "Optimize slow queries identified in monitoring"
            },
            {
              area: "Caching Strategy",
              potential_improvement: "40% load reduction",
              effort: "HIGH",
              description: "Implement Redis caching for frequently accessed data"
            }
          ]
        },
        next_actions: [
          "Investigate high CPU usage in web-server-1 within 30 minutes",
          "Review and adjust auto-scaling policies",
          "Schedule database performance tuning session",
          "Update monitoring thresholds based on analysis"
        ],
        confidence_score: 0.82,
        generated_at: new Date().toISOString(),
        model_version: "production-insights-v2.1"
      },
      metadata: {
        processing_time_ms: 1250,
        data_sources: ["oci_monitoring", "application_logs", "performance_metrics"],
        analysis_depth: "comprehensive"
      }
    });
  }),

  http.post('*/api/v1/genai/suggest-remediation', async ({ request }) => {
    const body = await request.json() as any;
    
    return HttpResponse.json({
      suggestions: [
        {
          action: 'restart_service',
          description: 'Restart the affected service',
          priority: 'high',
          estimated_time: '2 minutes'
        },
        {
          action: 'scale_up',
          description: 'Scale up the instance',
          priority: 'medium',
          estimated_time: '5 minutes'
        }
      ]
    });
  }),

  // Access Analyzer endpoints
  http.get('*/api/v1/access/analysis', () => {
    return HttpResponse.json({
      findings: [
        {
          id: 'finding-1',
          type: 'excessive_permissions',
          severity: 'medium',
          resource: 'IAM User: test-user',
          description: 'User has more permissions than required',
          recommendation: 'Remove unused permissions'
        }
      ],
      summary: {
        total_findings: 1,
        high_severity: 0,
        medium_severity: 1,
        low_severity: 0
      }
    });
  }),

  http.get('*/api/v1/access/summary', ({ request }) => {
    const url = new URL(request.url);
    const compartmentId = url.searchParams.get('compartment_id') || 'test-compartment';
    
    return HttpResponse.json({
      cluster_name: 'production-cluster',
      compartment_id: compartmentId,
      analysis_scope: {
        namespace: 'default',
        rbac_roles_analyzed: 24,
        iam_policies_analyzed: 12
      },
      risk_overview: {
        overall_risk_score: 68,
        overall_risk_level: 'medium',
        critical_findings_count: 2
      },
      rbac_summary: {
        total_roles: 18,
        high_risk_roles: 2,
        medium_risk_roles: 5,
        low_risk_roles: 11,
        average_risk_score: 42,
        total_subjects: 9,
        top_issues: [
          'cluster-admin bound to user alice',
          'edit role applied cluster-wide'
        ]
      },
      iam_summary: {
        total_policies: 12,
        compartments_analyzed: 3,
        high_risk_policies: 1,
        users_with_admin_access: 1
      },
      critical_findings: [
        'User alice has cluster-admin via RoleBinding in default namespace',
        'Overly broad policy grants inspect on all-resources in tenancy'
      ]
    });
  }),

  // Cost Analyzer endpoints
  http.get('*/api/v1/cost/analysis', () => {
    return HttpResponse.json({
      total_cost: 245.67,
      cost_by_service: {
        'Compute': 150.00,
        'Storage': 45.67,
        'Network': 50.00
      },
      recommendations: [
        {
          service: 'Compute',
          potential_savings: 25.00,
          recommendation: 'Right-size underutilized instances'
        }
      ]
    });
  }),

  http.post('*/api/v1/cost/analyze', async ({ request }) => {
    const body = await request.json() as any;
    const period = body.period || 'monthly';

    // Build a response that matches CostAnalysisResponse
    const costTrends = Array.from({ length: 12 }).map((_, i) => ({
      period: `M${i + 1}`,
      cost_amount: 80 + i * 10,
      change_percentage: i === 0 ? 0 : 5,
      date: new Date(Date.now() - (11 - i) * 30 * 24 * 3600 * 1000).toISOString()
    }));

    const topResources = [
      {
        resource: {
          resource_id: 'ocid1.instance.oc1..r1',
          resource_name: 'web-server-1',
          resource_type: 'compute',
          compartment_id: 'ocid1.compartment.oc1..prod',
          compartment_name: 'Production',
          cost_amount: 450.25,
          currency: 'USD',
          period,
          usage_metrics: { cpu_hours: 240 },
          cost_level: 'high',
          last_updated: new Date().toISOString()
        },
        rank: 1,
        cost_percentage: 36.2,
        optimization_potential: 120.0
      },
      {
        resource: {
          resource_id: 'ocid1.database.oc1..db1',
          resource_name: 'orders-db',
          resource_type: 'database',
          compartment_id: 'ocid1.compartment.oc1..prod',
          compartment_name: 'Production',
          cost_amount: 320.0,
          currency: 'USD',
          period,
          usage_metrics: { storage_gb: 500 },
          cost_level: 'medium',
          last_updated: new Date().toISOString()
        },
        rank: 2,
        cost_percentage: 25.7,
        optimization_potential: 65.5
      }
    ];

    return HttpResponse.json({
      status: 'ok',
      analysis_id: 'cost-analysis-123',
      timestamp: new Date().toISOString(),
      period,
      summary: {
        total_cost: 1245.67,
        currency: 'USD',
        period,
        resource_count: 27,
        compartment_count: 3,
        cost_distribution: { compute: 55, database: 25, storage: 12, network: 8 },
        optimization_potential: 275.25
      },
      compartment_breakdown: [
        {
          compartment_id: 'ocid1.compartment.oc1..prod',
          compartment_name: 'Production',
          total_cost: 865.12,
          cost_percentage: 69.5,
          resource_count: 15,
          top_resources: topResources,
          cost_trends: costTrends
        },
        {
          compartment_id: 'ocid1.compartment.oc1..staging',
          compartment_name: 'Staging',
          total_cost: 280.55,
          cost_percentage: 22.5,
          resource_count: 8,
          top_resources: [],
          cost_trends: costTrends
        }
      ],
      cost_trends: costTrends,
      anomalies: [
        {
          resource_id: 'ocid1.instance.oc1..r1',
          resource_name: 'web-server-1',
          anomaly_type: 'spike',
          severity: 'high',
          detected_at: new Date().toISOString(),
          current_cost: 120.5,
          expected_cost: 85.0,
          deviation_percentage: 41.8,
          description: 'CPU-related cost spike detected'
        }
      ],
      recommendations: [
        {
          recommendation_id: 'rec-1',
          resource_id: 'ocid1.instance.oc1..r1',
          resource_name: 'web-server-1',
          optimization_type: 'rightsizing',
          description: 'Downsize instance from VM.Standard2.2 to VM.Standard2.1',
          estimated_savings: 125.0,
          effort_level: 'medium',
          implementation_steps: [
            'Analyze performance metrics',
            'Schedule maintenance window',
            'Apply shape change and monitor'
          ],
          risk_level: 'medium',
          priority: 4,
          ai_confidence: 0.86
        }
      ],
      forecasts: [
        {
          forecast_period: 'next_month',
          predicted_cost: 1290.0,
          confidence_interval: { lower: 1180, upper: 1380 },
          factors_considered: ['trend', 'seasonality'],
          forecast_date: new Date().toISOString()
        }
      ],
      ai_insights: {
        summary: 'Compute accounts for majority of spend. Rightsizing and scheduling recommended.',
        potential_savings: 275.25
      }
    });
  }),

  // Vault endpoints
  http.get('*/api/v1/vault/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      vault_enabled: true,
      vault_accessible: true,
      secret_count: 5,
      timestamp: new Date().toISOString()
    });
  }),

  http.get('*/api/v1/vault/stats', () => {
    return HttpResponse.json({
      total_secrets: 5,
      secrets_by_type: {
        'api_key': 2,
        'database_password': 1,
        'jwt_secret': 1,
        'generic': 1
      },
      cache_stats: {
        total_cached: 3,
        active_cached: 3,
        cache_ttl_minutes: 15
      },
      vault_enabled: true
    });
  }),

  // Notifications endpoints
  http.get('*/api/v1/notifications', () => {
    return HttpResponse.json([
      {
        id: 'notif-1',
        type: 'alert',
        title: 'High CPU Usage Alert',
        message: 'Instance web-server-1 CPU usage is above 80%',
        severity: 'warning',
        timestamp: '2024-01-01T12:00:00Z',
        read: false
      }
    ]);
  }),

  http.put('*/api/v1/notifications/:notificationId/read', ({ params }) => {
    return HttpResponse.json({
      message: `Notification ${params.notificationId} marked as read`
    });
  }),

  // Health check
  http.get('*/api/v1/health', () => {
    return HttpResponse.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      version: '1.0.0'
    });
  }),

  // WebSocket simulation (for testing)
  http.get('*/api/v1/ws/*', () => {
    return HttpResponse.json({
      message: 'WebSocket connection established',
      status: 'connected'
    });
  }),

  // Explicit mock for WS connect route used by websocketService
  http.get('*/api/v1/ws/connect', ({ request }) => {
    return HttpResponse.json({
      status: 'connected',
      subscriptions: []
    });
  }),

  // ADD: Real-time notifications endpoint
  http.get('*/api/v1/notifications/real-time', ({ request }) => {
    const url = new URL(request.url);
    const compartmentId = url.searchParams.get('compartment_id') || 'test-compartment';
    const hoursBack = url.searchParams.get('hours_back') || '24';
    
    return HttpResponse.json([
      {
        id: 'notif-1',
        type: 'alert',
        title: 'High CPU Usage Alert',
        message: 'Instance web-server-1 CPU usage is above 80%',
        severity: 'warning',
        timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        compartment_id: compartmentId,
        read: false
      },
      {
        id: 'notif-2',
        type: 'info',
        title: 'Backup Completed',
        message: 'Database backup completed successfully',
        severity: 'info',
        timestamp: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
        compartment_id: compartmentId,
        read: true
      }
    ]);
  }),

  // ADD: Metrics endpoint for resource monitoring
  http.get('*/api/v1/cloud/resources/:resourceId/metrics', ({ params, request }) => {
    const url = new URL(request.url);
    const resourceType = url.searchParams.get('resource_type') || 'compute';
    
    return HttpResponse.json({
      resource_id: params.resourceId,
      metrics: {
        cpu_utilization: Math.random() * 100,
        memory_utilization: Math.random() * 100,
        network_bytes_in: Math.random() * 1000000,
        network_bytes_out: Math.random() * 1000000
      },
      timestamp: new Date().toISOString(),
      health_status: 'healthy'
    });
  }),

  // ADD: Resource actions endpoint
  http.post('*/api/v1/cloud/resources/:resourceId/actions/:action', ({ params }) => {
    return HttpResponse.json({
      message: `Action ${params.action} initiated for resource ${params.resourceId}`,
      action_id: `action-${Date.now()}`,
      status: 'in_progress'
    });
  }),

  // ===== COST ANALYZER ENDPOINTS (complete set) =====
  http.get('*/api/v1/cost/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      oci_billing_available: true,
      cost_data_fresh: true,
      ai_service_available: true,
      last_data_update: new Date().toISOString(),
      service_name: 'cost-analyzer',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      metrics: { processed_records: 12450 }
    });
  }),

  http.get('*/api/v1/cost/top', ({ request }) => {
    const url = new URL(request.url);
    const period = url.searchParams.get('period') || 'monthly';
    const limit = Number(url.searchParams.get('limit') || 10);

    const resources = Array.from({ length: limit }).map((_, idx) => ({
      resource: {
        resource_id: `ocid1.instance.oc1..r${idx+1}`,
        resource_name: idx % 2 === 0 ? 'web-server-1' : 'database-server',
        resource_type: idx % 2 === 0 ? 'compute' : 'database',
        compartment_id: 'ocid1.compartment.oc1..prod',
        compartment_name: 'Production',
        cost_amount: 100 + idx * 25,
        currency: 'USD',
        period,
        usage_metrics: { cpu_hours: 120 + idx * 5 },
        cost_level: idx < 2 ? 'high' : idx < 5 ? 'medium' : 'low',
        last_updated: new Date().toISOString()
      },
      rank: idx + 1,
      cost_percentage: Math.max(2, 10 - idx),
      optimization_potential: idx < 4 ? 30 + idx * 10 : undefined
    }));

    return HttpResponse.json({
      status: 'ok',
      total_resources: resources.length,
      period,
      currency: 'USD',
      resources,
      summary: {
        total_cost: resources.reduce((sum: number, r: any) => sum + r.resource.cost_amount, 0),
        currency: 'USD',
        period,
        resource_count: resources.length,
        compartment_count: 3,
        cost_distribution: { compute: 55, database: 30, network: 10, storage: 5 },
        optimization_potential: 420.5
      },
      timestamp: new Date().toISOString(),
      compartment_filter: 'all'
    });
  }),

  http.get('*/api/v1/cost/insights/summary', ({ request }) => {
    const url = new URL(request.url);
    const period = url.searchParams.get('period') || 'monthly';
    return HttpResponse.json({
      total_cost: 1245.67,
      currency: 'USD',
      period,
      optimization_potential: 275.25,
      anomaly_count: 2,
      high_priority_recommendations: 3,
      cost_health_score: 78,
      key_insights: [
        'Compute accounts for 55% of spend',
        '3 underutilized instances detected',
        'Storage growth trending +8% MoM'
      ],
      timestamp: new Date().toISOString()
    });
  }),

  http.get('*/api/v1/cost/recommendations/priority', ({ request }) => {
    const url = new URL(request.url);
    const limit = Number(url.searchParams.get('limit') || 5);
    const recs = Array.from({ length: limit }).map((_, idx) => ({
      recommendation_id: `rec-${idx+1}`,
      resource_id: `ocid1.instance.oc1..r${idx+1}`,
      resource_name: idx % 2 === 0 ? 'web-server-1' : 'database-server',
      optimization_type: idx % 2 === 0 ? 'rightsizing' : 'scheduling',
      description: idx % 2 === 0 ? 'Downsize instance from VM.Standard2.2 to VM.Standard2.1' : 'Stop dev instances outside business hours',
      estimated_savings: 25 * (idx + 1),
      effort_level: idx % 2 === 0 ? 'medium' : 'low',
      implementation_steps: [
        'Assess workload requirements',
        'Apply change during maintenance window',
        'Monitor post-change performance'
      ],
      risk_level: idx % 2 === 0 ? 'medium' : 'low',
      priority: idx % 2 === 0 ? 4 : 3,
      ai_confidence: 0.85
    }));

    return HttpResponse.json({
      total_recommendations: recs.length,
      total_potential_savings: recs.reduce((s, r) => s + r.estimated_savings, 0),
      recommendations: recs,
      timestamp: new Date().toISOString()
    });
  }),

  // ===== REMEDIATION ENDPOINTS (complete set) =====
  http.get('*/api/v1/remediation/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      service: 'remediation',
      timestamp: new Date().toISOString(),
      checks: { database: 'ok', oci_service: 'ok', terraform: 'ok' }
    });
  }),

  http.get('*/api/v1/remediation/actions', () => {
    return HttpResponse.json([
      {
        id: 1,
        title: 'Restart web service',
        description: 'Restart nginx on web-server-1',
        status: 'pending',
        action_type: 'script',
        severity: 'medium',
        environment: 'production',
        service_name: 'web',
        created_at: new Date().toISOString(),
        requires_approval: false,
        rollback_executed: false
      },
      {
        id: 2,
        title: 'Scale database',
        description: 'Increase DB OCPUs to handle load',
        status: 'approved',
        action_type: 'oci_cli',
        severity: 'high',
        environment: 'production',
        service_name: 'database',
        created_at: new Date().toISOString(),
        requires_approval: true,
        rollback_executed: false
      }
    ]);
  }),

  http.get('*/api/v1/remediation/actions/:actionId/status', ({ params }) => {
    return HttpResponse.json({
      action: {
        id: Number(params.actionId),
        title: 'Restart web service',
        description: 'Restart nginx on web-server-1',
        status: 'in_progress',
        action_type: 'script',
        severity: 'medium',
        environment: 'production',
        service_name: 'web',
        requires_approval: false,
        rollback_executed: false
      },
      audit_logs: [
        { id: 1, event_type: 'created', event_description: 'Action created', timestamp: new Date().toISOString() },
        { id: 2, event_type: 'started', event_description: 'Execution started', timestamp: new Date().toISOString() }
      ]
    });
  }),

  http.post('*/api/v1/remediation/actions/:actionId/approve', ({ params }) => {
    return HttpResponse.json({ success: true, message: `Action ${params.actionId} approved` });
  }),

  http.post('*/api/v1/remediation/actions/:actionId/execute', ({ params }) => {
    return HttpResponse.json({ status: 'completed', output: 'Service restarted successfully', duration: 2.1 });
  }),

  http.post('*/api/v1/remediation/actions/:actionId/rollback', ({ params }) => {
    return HttpResponse.json({ status: 'rolled_back', output: 'Rollback completed', duration: 1.2 });
  }),

  http.delete('*/api/v1/remediation/actions/:actionId', ({ params }) => {
    return HttpResponse.json({ success: true, message: `Action ${params.actionId} cancelled` });
  }),

  http.get('*/api/v1/remediation/actions/types', () => {
    return HttpResponse.json({ action_types: [
      { type: 'oci_cli', description: 'Execute OCI CLI commands' },
      { type: 'terraform', description: 'Run Terraform plans' },
      { type: 'script', description: 'Run shell scripts' },
      { type: 'api_call', description: 'Call external APIs' },
      { type: 'kubernetes', description: 'Run kubectl operations' }
    ]});
  }),

  http.get('*/api/v1/remediation/actions/statuses', () => {
    return HttpResponse.json({ statuses: [
      { status: 'pending', description: 'Awaiting approval or execution' },
      { status: 'approved', description: 'Approved for execution' },
      { status: 'in_progress', description: 'Currently executing' },
      { status: 'completed', description: 'Successfully executed' }
    ]});
  }),

  http.get('*/api/v1/remediation/actions/severities', () => {
    return HttpResponse.json({ severities: [
      { severity: 'low', description: 'Low impact' },
      { severity: 'medium', description: 'Moderate impact' },
      { severity: 'high', description: 'High impact' },
      { severity: 'critical', description: 'Critical impact' }
    ]});
  }),

  http.post('*/api/v1/remediation/actions', async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({ id: Math.floor(Math.random()*1000)+3, ...body, status: 'pending', requires_approval: false, rollback_executed: false }, { status: 201 });
  }),

  http.delete('*/api/v1/remediation/actions/cleanup-test-data', () => {
    return HttpResponse.json({ success: true, message: 'Test data cleaned up', deleted_count: 5 });
  }),

  // ===== ACCESS ANALYZER =====
  http.get('*/api/v1/access/rbac', ({ request }) => {
    const url = new URL(request.url);
    const namespace = url.searchParams.get('namespace') || undefined;
    return HttpResponse.json({
      roles: [
        { name: 'cluster-admin', namespace: undefined, kind: 'ClusterRole', rules: [], created_time: new Date().toISOString(), labels: {} },
        { name: 'view', namespace: 'default', kind: 'Role', rules: [], created_time: new Date().toISOString(), labels: {} }
      ],
      bindings: [
        { name: 'admin-binding', namespace: 'default', role_ref: { name: 'cluster-admin', kind: 'ClusterRole' }, subjects: [ { kind: 'User', name: 'alice' } ] }
      ],
      namespace,
      cluster_name: 'production-cluster',
      total_roles: 2,
      total_bindings: 1,
      execution_time: 0.02
    });
  }),

  http.get('*/api/v1/access/iam', ({ request }) => {
    const url = new URL(request.url);
    const compartmentId = url.searchParams.get('compartment_id') || 'ocid1.compartment.oc1..prod';
    return HttpResponse.json({
      compartment_id: compartmentId,
      total_policies: 12,
      high_risk_policies: 2,
      users_with_admin_access: 1,
      policies: []
    });
  }),

  // Fallback for unhandled requests - IMPROVED with better logging
  http.get('*/api/*', ({ request }) => {
    console.warn(`🎭 MSW: Unhandled API request: ${request.method} ${request.url}`);
    return HttpResponse.json(
      { 
        detail: 'Endpoint not implemented in mock',
        url: request.url,
        method: request.method,
        message: 'This endpoint needs to be added to the mock handlers'
      },
      { status: 501 }
    );
  }),

  http.post('*/api/*', ({ request }) => {
    console.warn(`🎭 MSW: Unhandled API request: ${request.method} ${request.url}`);
    return HttpResponse.json(
      { 
        detail: 'Endpoint not implemented in mock',
        url: request.url,
        method: request.method,
        message: 'This endpoint needs to be added to the mock handlers'
      },
      { status: 501 }
    );
  })
]; 