import apiClient from './apiClient';

// Types for Cost Analyzer API
export type CostLevel = 'critical' | 'high' | 'medium' | 'low' | 'minimal';

export type OptimizationType = 'rightsizing' | 'scaling' | 'storage_optimization' | 'reserved_instances' | 'spot_instances' | 'resource_cleanup' | 'scheduling';

export interface ResourceCost {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  compartment_id: string;
  compartment_name: string;
  cost_amount: number;
  currency: string;
  period: string;
  usage_metrics: Record<string, any>;
  cost_level: CostLevel;
  last_updated: string;
}

export interface TopCostlyResource {
  resource: ResourceCost;
  rank: number;
  cost_percentage: number;
  optimization_potential?: number;
}

export interface CostTrend {
  period: string;
  cost_amount: number;
  change_percentage?: number;
  date: string;
}

export interface CostAnomaly {
  resource_id: string;
  resource_name: string;
  anomaly_type: string;
  severity: CostLevel;
  detected_at: string;
  current_cost: number;
  expected_cost: number;
  deviation_percentage: number;
  description: string;
}

export interface OptimizationRecommendation {
  recommendation_id: string;
  resource_id: string;
  resource_name: string;
  optimization_type: OptimizationType;
  description: string;
  estimated_savings: number;
  effort_level: string;
  implementation_steps: string[];
  risk_level: string;
  priority: number;
  ai_confidence: number;
}

export interface CostForecast {
  forecast_period: string;
  predicted_cost: number;
  confidence_interval: {
    lower: number;
    upper: number;
  };
  factors_considered: string[];
  forecast_date: string;
}

export interface CompartmentCostBreakdown {
  compartment_id: string;
  compartment_name: string;
  total_cost: number;
  cost_percentage: number;
  resource_count: number;
  top_resources: TopCostlyResource[];
  cost_trends: CostTrend[];
}

export interface CostSummary {
  total_cost: number;
  currency: string;
  period: string;
  resource_count: number;
  compartment_count: number;
  cost_distribution: Record<string, number>;
  optimization_potential: number;
}

export interface CostHealthCheck {
  status: string;
  oci_billing_available: boolean;
  cost_data_fresh: boolean;
  ai_service_available: boolean;
  last_data_update?: string;
  service_name: string;
  timestamp: string;
  version: string;
  metrics: Record<string, any>;
}

export interface TopCostlyResourcesRequest {
  compartment_id?: string;
  limit?: number;
  period?: string;
  resource_types?: string[];
}

export interface TopCostlyResourcesResponse {
  status: string;
  total_resources: number;
  period: string;
  currency: string;
  resources: TopCostlyResource[];
  summary: CostSummary;
  timestamp: string;
  compartment_filter?: string;
}

export interface CostAnalysisRequest {
  compartment_ids?: string[];
  resource_types?: string[];
  period?: string;
  start_date?: string;
  end_date?: string;
  include_forecasting?: boolean;
  include_optimization?: boolean;
  include_anomaly_detection?: boolean;
}

export interface CostAnalysisResponse {
  status: string;
  analysis_id: string;
  timestamp: string;
  period: string;
  summary: CostSummary;
  compartment_breakdown: CompartmentCostBreakdown[];
  cost_trends: CostTrend[];
  anomalies: CostAnomaly[];
  recommendations: OptimizationRecommendation[];
  forecasts?: CostForecast[];
  ai_insights: Record<string, any>;
}

export interface CostInsightsSummary {
  total_cost: number;
  currency: string;
  period: string;
  optimization_potential: number;
  anomaly_count: number;
  high_priority_recommendations: number;
  cost_health_score: number;
  key_insights: string[];
  timestamp: string;
}

export interface PriorityRecommendations {
  total_recommendations: number;
  total_potential_savings: number;
  recommendations: OptimizationRecommendation[];
  timestamp: string;
}

export interface CompartmentTrends {
  compartment_id: string;
  compartment_name: string;
  current_cost: number;
  trends: CostTrend[];
  periods_analyzed: number;
  timestamp: string;
}

class CostAnalyzerService {
  private readonly baseURL = '/cost';

  // Health check
  async getHealthCheck(): Promise<CostHealthCheck> {
    const response = await apiClient.get(`${this.baseURL}/health`);
    return response.data;
  }

  // Get top costly resources
  async getTopCostlyResources(params: TopCostlyResourcesRequest = {}): Promise<TopCostlyResourcesResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.compartment_id) queryParams.append('compartment_id', params.compartment_id);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.period) queryParams.append('period', params.period);
    if (params.resource_types?.length) queryParams.append('resource_types', params.resource_types.join(','));

    const response = await apiClient.get(`${this.baseURL}/top?${queryParams.toString()}`);
    return response.data;
  }

  // Perform comprehensive cost analysis
  async analyzeCosts(request: CostAnalysisRequest): Promise<CostAnalysisResponse> {
    const response = await apiClient.post(`${this.baseURL}/analyze`, request);
    return response.data;
  }

  // Get cost insights summary
  async getCostInsightsSummary(period: string = 'monthly'): Promise<CostInsightsSummary> {
    const response = await apiClient.get(`${this.baseURL}/insights/summary?period=${period}`);
    return response.data;
  }

  // Get priority recommendations
  async getPriorityRecommendations(limit: number = 5, minSavings?: number): Promise<PriorityRecommendations> {
    const queryParams = new URLSearchParams();
    queryParams.append('limit', limit.toString());
    if (minSavings) queryParams.append('min_savings', minSavings.toString());

    const response = await apiClient.get(`${this.baseURL}/recommendations/priority?${queryParams.toString()}`);
    return response.data;
  }

  // Get compartment cost trends
  async getCompartmentTrends(compartmentId: string, periods: number = 12): Promise<CompartmentTrends> {
    const response = await apiClient.get(`${this.baseURL}/trends/${compartmentId}?periods=${periods}`);
    return response.data;
  }

  // Utility methods for data transformation and formatting
  formatCurrency(amount: number, currency: string = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  }

  formatPercentage(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value / 100);
  }

  getCostLevelColor(level: CostLevel): string {
    const colors: Record<CostLevel, string> = {
      critical: 'text-red-600 bg-red-100',
      high: 'text-orange-600 bg-orange-100',
      medium: 'text-yellow-600 bg-yellow-100',
      low: 'text-blue-600 bg-blue-100',
      minimal: 'text-green-600 bg-green-100',
    };
    return colors[level] || colors.medium;
  }

  getOptimizationTypeIcon(type: OptimizationType): string {
    const icons: Record<OptimizationType, string> = {
      rightsizing: 'fas fa-expand-arrows-alt',
      scaling: 'fas fa-chart-line',
      storage_optimization: 'fas fa-hdd',
      reserved_instances: 'fas fa-bookmark',
      spot_instances: 'fas fa-star',
      resource_cleanup: 'fas fa-trash-alt',
      scheduling: 'fas fa-clock',
    };
    return icons[type] || 'fas fa-cog';
  }

  getAnomalySeverityColor(severity: CostLevel): string {
    const colors: Record<CostLevel, string> = {
      critical: 'text-red-600',
      high: 'text-orange-600',
      medium: 'text-yellow-600',
      low: 'text-blue-600',
      minimal: 'text-green-600',
    };
    return colors[severity] || colors.medium;
  }

  // Export functionality (will be used for PDF/CSV generation)
  prepareCostDataForExport(data: CostAnalysisResponse): any {
    return {
      summary: data.summary,
      resources: data.compartment_breakdown.flatMap(comp => 
        comp.top_resources.map(resource => ({
          ...resource.resource,
          compartment_name: comp.compartment_name,
          rank: resource.rank,
          optimization_potential: resource.optimization_potential
        }))
      ),
      recommendations: data.recommendations,
      anomalies: data.anomalies,
      trends: data.cost_trends,
      forecasts: data.forecasts,
      generated_at: new Date().toISOString()
    };
  }
}

// Export singleton instance
export const costAnalyzerService = new CostAnalyzerService();
export default costAnalyzerService; 