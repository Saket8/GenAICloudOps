import apiClient from './apiClient';

export interface Role {
    id: number;
    name: string;
    display_name: string;
    description?: string;
    can_view_dashboard: boolean;
    can_view_alerts: boolean;
    can_approve_remediation: boolean;
    can_execute_remediation: boolean;
    can_manage_users: boolean;
    can_manage_roles: boolean;
    can_view_access_analyzer: boolean;
    can_view_pod_analyzer: boolean;
    can_view_cost_analyzer: boolean;
    can_use_chatbot: boolean;
}

export interface RoleCreateData {
    name: string;
    display_name: string;
    description?: string;
    can_view_dashboard?: boolean;
    can_view_alerts?: boolean;
    can_approve_remediation?: boolean;
    can_execute_remediation?: boolean;
    can_manage_users?: boolean;
    can_manage_roles?: boolean;
    can_view_access_analyzer?: boolean;
    can_view_pod_analyzer?: boolean;
    can_view_cost_analyzer?: boolean;
    can_use_chatbot?: boolean;
}

export interface RoleUpdateData {
    display_name?: string;
    description?: string;
    can_view_dashboard?: boolean;
    can_view_alerts?: boolean;
    can_approve_remediation?: boolean;
    can_execute_remediation?: boolean;
    can_manage_users?: boolean;
    can_manage_roles?: boolean;
    can_view_access_analyzer?: boolean;
    can_view_pod_analyzer?: boolean;
    can_view_cost_analyzer?: boolean;
    can_use_chatbot?: boolean;
}

export const roleService = {
    getRoles: async (): Promise<Role[]> => {
        const response = await apiClient.get('/roles/');
        return response.data;
    },

    createRole: async (data: RoleCreateData): Promise<Role> => {
        const response = await apiClient.post('/roles/', data);
        return response.data;
    },

    updateRole: async (id: number, data: RoleUpdateData): Promise<Role> => {
        const response = await apiClient.put(`/roles/${id}`, data);
        return response.data;
    },

    deleteRole: async (id: number): Promise<void> => {
        await apiClient.delete(`/roles/${id}`);
    },
};
