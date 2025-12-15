import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { api } from './apiClient';
import {
  awsMonitoringService,
  AwsMonitoringScope,
  useAwsMonitoringDashboard,
  useAwsMonitoringHealth,
  useAwsMonitoringSummary,
  useAwsMonitoringAlarms,
  useAwsMonitoringHistory,
  useAwsMonitoringScopes,
} from './awsMonitoringService';

interface AWSOverview {
  account: {
    id: string;
    alias: string;
    region: string;
    environments: Array<{ name: string; status: string }>;
  };
  summary: {
    total_services: number;
    resources_discovered: number;
    active_alerts: number;
    open_incidents: number;
    cost_month_to_date: number;
    budget_burn_rate: number;
    optimization_opportunities: number;
  };
  highlights: Array<{
    id: string;
    title: string;
    impact: string;
    severity: string;
    summary: string;
    recommendation: string;
  }>;
}

interface AWSMetricDatum {
  service: string;
  metric: string;
  namespace: string;
  dimensions: Record<string, string>;
  statistics: {
    period_minutes: number;
    average: number;
    maximum: number;
    minimum: number;
    unit: string;
  };
  trend: number[];
}

interface AWSAlertDatum {
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

interface AWSLogFinding {
  time: string;
  source: string;
  service: string;
  summary: string;
  details: string;
}

interface AWSCost {
  summary: {
    month_to_date_spend: number;
    forecast_end_of_month: number;
    budget: number;
    variance: number;
    optimization_estimate: number;
  };
  service_breakdown: Array<{
    service: string;
    spend: number;
    change_percent: number;
  }>;
  recommendations: Array<{
    id: string;
    title: string;
    service: string;
    potential_savings: number;
    term: string;
    details: string;
  }>;
}

interface AWSSecurity {
  summary: {
    critical_findings: number;
    high_findings: number;
    medium_findings: number;
    low_findings: number;
    iam_users_with_keys: number;
    unused_security_groups: number;
  };
  findings: Array<{
    id: string;
    title: string;
    severity: string;
    service: string;
    resource: string;
    details: string;
    recommendation: string;
  }>;
  rbac: {
    roles: Array<{
      name: string;
      principals: number;
      last_audited: string;
      risk: string;
    }>;
    policies_to_review: Array<{
      name: string;
      principal: string;
      finding: string;
      recommendation: string;
    }>;
  };
}

interface AWSAutomation {
  playbooks: Array<{
    id: string;
    name: string;
    category: string;
    description: string;
    risk: string;
    last_validated: string;
    steps: string[];
  }>;
  approvals: {
    required: boolean;
    approvers: string[];
    pending: number;
  };
}

interface AWSResources {
  compute: {
    ec2: {
      running_instances: number;
      average_cpu: number;
      auto_scaling_groups: number;
      eks_clusters: number;
    };
    lambda: {
      active_functions: number;
      avg_duration_ms: number;
      error_rate: number;
    };
  };
  storage: {
    s3: {
      total_buckets: number;
      object_count: number;
      storage_tb: number;
    };
    efs: {
      file_systems: number;
      avg_utilization: number;
    };
  };
  databases: {
    rds: {
      instances: number;
      aurora_clusters: number;
      avg_cpu: number;
    };
    dynamodb: {
      tables: number;
      throttle_events: number;
    };
  };
  networking: {
    vpcs: number;
    subnets: number;
    load_balancers: {
      alb: number;
      nlb: number;
      gateway: number;
    };
    vpn_connections: number;
  };
}

const awsQueryKeys = {
  all: ['aws'] as const,
  overview: () => [...awsQueryKeys.all, 'overview'] as const,
  monitoring: () => [...awsQueryKeys.all, 'monitoring'] as const,
  cost: () => [...awsQueryKeys.all, 'cost'] as const,
  security: () => [...awsQueryKeys.all, 'security'] as const,
  automation: () => [...awsQueryKeys.all, 'automation'] as const,
  resources: () => [...awsQueryKeys.all, 'resources'] as const,
};

const awsApi = {
  getOverview: async (): Promise<AWSOverview> => {
    const response = await api.get<AWSOverview>('/aws/overview');
    return response.data;
  },
  listNamespaces: async (): Promise<string[]> => {
    const response = await api.get<string[]>('/aws/monitoring/namespaces');
    return response.data;
  },
  getCost: async (): Promise<AWSCost> => {
    const response = await api.get<AWSCost>('/aws/cost/summary');
    return response.data;
  },
  getSecurity: async (): Promise<AWSSecurity> => {
    const response = await api.get<AWSSecurity>('/aws/security/summary');
    return response.data;
  },
  getAutomation: async (): Promise<AWSAutomation> => {
    const response = await api.get<AWSAutomation>('/aws/automation/playbooks');
    return response.data;
  },
  getResources: async (): Promise<AWSResources> => {
    const response = await api.get<AWSResources>('/aws/resources/inventory');
    return response.data;
  },
};

export function useAwsOverview(): UseQueryResult<AWSOverview, Error> {
  return useQuery({
    queryKey: awsQueryKeys.overview(),
    queryFn: awsApi.getOverview,
    staleTime: 5 * 60 * 1000,
  });
}

export function useAwsCost(): UseQueryResult<AWSCost, Error> {
  return useQuery({
    queryKey: awsQueryKeys.cost(),
    queryFn: awsApi.getCost,
    staleTime: 10 * 60 * 1000,
  });
}

export function useAwsSecurity(): UseQueryResult<AWSSecurity, Error> {
  return useQuery({
    queryKey: awsQueryKeys.security(),
    queryFn: awsApi.getSecurity,
    staleTime: 10 * 60 * 1000,
  });
}

export function useAwsAutomation(): UseQueryResult<AWSAutomation, Error> {
  return useQuery({
    queryKey: awsQueryKeys.automation(),
    queryFn: awsApi.getAutomation,
    staleTime: 10 * 60 * 1000,
  });
}

export function useAwsResources(): UseQueryResult<AWSResources, Error> {
  return useQuery({
    queryKey: awsQueryKeys.resources(),
    queryFn: awsApi.getResources,
    staleTime: 10 * 60 * 1000,
  });
}

export const awsService = awsApi;

export const awsMonitoringHooks = {
  useScopes: useAwsMonitoringScopes,
  useSummary: useAwsMonitoringSummary,
  useAlarms: useAwsMonitoringAlarms,
  useHistory: useAwsMonitoringHistory,
  useDashboard: useAwsMonitoringDashboard,
  useHealth: useAwsMonitoringHealth,
  service: awsMonitoringService,
};
