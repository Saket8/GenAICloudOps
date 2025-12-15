import apiClient from './apiClient';

export interface RBACRole {
  name: string;
  namespace?: string;
  kind: string;
  rules: any[];
  created_time: string;
  labels: Record<string, string>;
}

export interface RBACBinding {
  name: string;
  namespace?: string;
  role_ref: {
    name: string;
    kind: string;
  };
  subjects: Array<{
    kind: string;
    name: string;
    namespace?: string;
  }>;
}

export interface RBACAnalysisResponse {
  roles: RBACRole[];
  bindings: RBACBinding[];
  namespace?: string;
  cluster_name: string;
  total_roles: number;
  total_bindings: number;
  execution_time: number;
}

export interface AccessSummaryResponse {
  cluster_name: string;
  compartment_id: string;
  analysis_scope: {
    namespace?: string;
    rbac_roles_analyzed: number;
    iam_policies_analyzed: number;
  };
  risk_overview: {
    overall_risk_score: number;
    overall_risk_level: string;
    critical_findings_count: number;
  };
  rbac_summary: {
    total_roles: number;
    high_risk_roles: number;
    medium_risk_roles: number;
    low_risk_roles: number;
    average_risk_score: number;
    total_subjects: number;
    top_issues: string[];
  };
  iam_summary: {
    total_policies: number;
    compartments_analyzed: number;
    high_risk_policies: number;
    users_with_admin_access: number;
  };
  critical_findings: string[];
}

export class AccessAnalyzerService {
  /**
   * Get RBAC analysis for a specific namespace
   */
  static async getRBACAnalysis(namespace?: string): Promise<RBACAnalysisResponse> {
    const params = namespace ? { namespace } : {};
    const response = await apiClient.get('/access/rbac', { params });
    return response.data;
  }

  /**
   * Get IAM analysis for a compartment
   */
  static async getIAMAnalysis(compartmentId: string) {
    const response = await apiClient.get('/access/iam', {
      params: { compartment_id: compartmentId }
    });
    return response.data;
  }

  /**
   * Get access control summary
   */
  static async getAccessSummary(compartmentId: string = 'default'): Promise<AccessSummaryResponse> {
    const response = await apiClient.get('/access/summary', {
      params: { compartment_id: compartmentId }
    });
    return response.data;
  }

  /**
   * Generate unified analysis with AI recommendations
   */
  static async generateUnifiedAnalysis(data: {
    compartment_id: string;
    namespace?: string;
    include_root_policies?: boolean;
    generate_recommendations?: boolean;
  }) {
    const response = await apiClient.post('/access/analyze', data);
    return response.data;
  }
} 