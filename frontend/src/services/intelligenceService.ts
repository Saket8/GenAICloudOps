/**
 * Intelligence Service - API client for Cloud Intelligence Hub
 * 
 * Provides multi-dimensional analytics combining data from
 * multiple OCI APIs for insights not available in OCI Console.
 */
import { api } from './apiClient';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = '/intelligence';

// ===== Types =====

export interface HealthIssue {
    category: 'state' | 'activity' | 'cost' | 'backup' | 'performance';
    severity: 'critical' | 'warning' | 'info';
    message: string;
    deduction: number;
    recommendation?: string;
}

export interface ResourceHealth {
    resource_id: string;
    resource_name: string;
    resource_type: string;
    compartment_id: string;
    score: number;
    level: 'healthy' | 'warning' | 'critical';
    lifecycle_state: string;
    estimated_cost: number;
    issues: HealthIssue[];
    days_stopped?: number;
    time_created?: string;
}

export interface HealthMatrixSummary {
    total_resources: number;
    healthy_count: number;
    warning_count: number;
    critical_count: number;
    total_waste: number;
}

export interface HealthMatrix {
    compartment_id: string;
    timestamp: string;
    summary: HealthMatrixSummary;
    resources: ResourceHealth[];
    by_type: Record<string, ResourceHealth[]>;
}

export interface IntelligenceSummary {
    compartment_id: string;
    timestamp: string;
    total_resources: number;
    healthy_count: number;
    warning_count: number;
    critical_count: number;
    total_waste: number;
    health_distribution: {
        healthy: number;
        warning: number;
        critical: number;
    };
    by_type_counts: Record<string, number>;
}

export interface TopAction {
    id: string;
    category: 'delete_zombie' | 'review_stopped' | 'fix_security' | 'optimize' | 'fix_unavailable';
    icon: string;
    title: string;
    description: string;
    resource_id: string;
    resource_name: string;
    resource_type: string;
    days_stopped?: number;
    potential_savings: number;
    priority: number;
    action_type: 'delete' | 'review' | 'configure' | 'optimize' | 'investigate';
    risk_level: 'low' | 'medium' | 'high';
}

export interface TopActionsResponse {
    actions: TopAction[];
    total_actions: number;
    total_potential_savings: number;
    categories: Record<string, { count: number; savings: number }>;
    generated_at: string;
}

// ===== API Functions =====

export const intelligenceApi = {
    /**
     * Get complete health matrix for visualization
     */
    getHealthMatrix: async (compartmentId: string): Promise<HealthMatrix> => {
        const response = await api.get<HealthMatrix>(
            `${API_BASE}/health-matrix`,
            { params: { compartment_id: compartmentId } }
        );
        return response.data;
    },

    /**
     * Get detailed health for a specific resource
     */
    getResourceHealth: async (resourceId: string, compartmentId: string): Promise<ResourceHealth> => {
        const response = await api.get<ResourceHealth>(
            `${API_BASE}/resource/${resourceId}/health`,
            { params: { compartment_id: compartmentId } }
        );
        return response.data;
    },

    /**
     * Get quick summary for dashboard widgets
     */
    getSummary: async (compartmentId: string): Promise<IntelligenceSummary> => {
        const response = await api.get<IntelligenceSummary>(
            `${API_BASE}/summary`,
            { params: { compartment_id: compartmentId } }
        );
        return response.data;
    },

    /**
     * Force refresh health matrix cache
     */
    refresh: async (compartmentId: string): Promise<{ status: string; message: string }> => {
        const response = await api.post(
            `${API_BASE}/refresh`,
            null,
            { params: { compartment_id: compartmentId } }
        );
        return response.data;
    },

    /**
     * Get prioritized top actions for optimization
     */
    getTopActions: async (compartmentId: string, limit: number = 5): Promise<TopActionsResponse> => {
        const response = await api.get<TopActionsResponse>(
            `${API_BASE}/top-actions`,
            { params: { compartment_id: compartmentId, limit } }
        );
        return response.data;
    },
};

// ===== React Query Hooks =====

export const intelligenceQueryKeys = {
    all: ['intelligence'] as const,
    matrix: (compartmentId: string) => [...intelligenceQueryKeys.all, 'matrix', compartmentId] as const,
    summary: (compartmentId: string) => [...intelligenceQueryKeys.all, 'summary', compartmentId] as const,
    resource: (resourceId: string) => [...intelligenceQueryKeys.all, 'resource', resourceId] as const,
};

/**
 * Hook to fetch health matrix for heatmap visualization
 */
export function useHealthMatrix(compartmentId: string | null) {
    return useQuery({
        queryKey: intelligenceQueryKeys.matrix(compartmentId || ''),
        queryFn: () => intelligenceApi.getHealthMatrix(compartmentId!),
        enabled: !!compartmentId,
        staleTime: 5 * 60 * 1000, // 5 minutes (backend caches for 1 hour)
        refetchOnWindowFocus: false,
    });
}

/**
 * Hook to fetch intelligence summary for dashboard
 */
export function useIntelligenceSummary(compartmentId: string | null) {
    return useQuery({
        queryKey: intelligenceQueryKeys.summary(compartmentId || ''),
        queryFn: () => intelligenceApi.getSummary(compartmentId!),
        enabled: !!compartmentId,
        staleTime: 5 * 60 * 1000,
        refetchOnWindowFocus: false,
    });
}

/**
 * Hook to fetch detailed health for a specific resource
 */
export function useResourceHealth(resourceId: string | null, compartmentId: string | null) {
    return useQuery({
        queryKey: intelligenceQueryKeys.resource(resourceId || ''),
        queryFn: () => intelligenceApi.getResourceHealth(resourceId!, compartmentId!),
        enabled: !!resourceId && !!compartmentId,
        staleTime: 5 * 60 * 1000,
    });
}

/**
 * Hook to fetch top actions for optimization
 */
export function useTopActions(compartmentId: string | null, limit: number = 5) {
    return useQuery({
        queryKey: [...intelligenceQueryKeys.all, 'topActions', compartmentId, limit] as const,
        queryFn: () => intelligenceApi.getTopActions(compartmentId!, limit),
        enabled: !!compartmentId,
        staleTime: 2 * 60 * 1000, // 2 minutes
        refetchOnWindowFocus: false,
    });
}

/**
 * Hook to refresh health matrix
 */
export function useRefreshHealthMatrix() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (compartmentId: string) => intelligenceApi.refresh(compartmentId),
        onSuccess: (_, compartmentId) => {
            // Invalidate cached data
            queryClient.invalidateQueries({ queryKey: intelligenceQueryKeys.matrix(compartmentId) });
            queryClient.invalidateQueries({ queryKey: intelligenceQueryKeys.summary(compartmentId) });
        },
    });
}

