import apiClient from './apiClient';
import { UserWithRoles, RegisterData } from '../types/auth';

export interface UserCreateData extends RegisterData {
    roles?: string[];
}

export interface UserUpdateData {
    full_name?: string;
    email?: string;
    is_active?: boolean;
    roles?: string[];
}

export const userService = {
    getUsers: async (): Promise<UserWithRoles[]> => {
        const response = await apiClient.get('/users/');
        return response.data;
    },

    createUser: async (data: UserCreateData): Promise<UserWithRoles> => {
        const response = await apiClient.post('/users/', data);
        return response.data;
    },

    updateUser: async (id: number, data: UserUpdateData): Promise<UserWithRoles> => {
        const response = await apiClient.put(`/users/${id}`, data);
        return response.data;
    },

    deleteUser: async (id: number): Promise<void> => {
        await apiClient.delete(`/users/${id}`);
    },
};
