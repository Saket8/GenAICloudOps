import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { userService, UserCreateData, UserUpdateData } from '../../services/userService';
import { roleService, RoleCreateData, RoleUpdateData, Role } from '../../services/roleService';
import { UserWithRoles } from '../../types/auth';
import { LoadingSpinner } from '../ui/LoadingSpinner';

// Permission Tiles Configuration
const PERMISSION_TILES = [
    {
        id: 'cloud_admin',
        name: 'Infrastructure Platform',
        description: 'Access to OCI and AWS cloud resources and dashboards.',
        icon: 'fa-cloud',
        color: 'blue',
    },
    {
        id: 'app_admin',
        name: 'Application Monitoring',
        description: 'Access to application metrics, alerts, and pod health.',
        icon: 'fa-desktop',
        color: 'purple',
    },
    {
        id: 'security_admin',
        name: 'Security Monitoring',
        description: 'Access to security dashboards, access analyzer, and remediation.',
        icon: 'fa-shield-alt',
        color: 'red',
    },
    {
        id: 'sys_admin',
        name: 'Administration',
        description: 'Manage users, roles, and system settings.',
        icon: 'fa-tools',
        color: 'emerald',
    },
];

export function UserManagementPage() {
    const queryClient = useQueryClient();
    const [searchParams, setSearchParams] = useSearchParams();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState<UserWithRoles | null>(null);
    const [editingRole, setEditingRole] = useState<Role | null>(null);

    useEffect(() => {
        const action = searchParams.get('action');
        if (action === 'create') {
            setEditingUser(null);
            setIsModalOpen(true);
            setSearchParams({});
        } else if (action === 'create-role') {
            setEditingRole(null);
            setIsRoleModalOpen(true);
            setSearchParams({});
        }
    }, [searchParams, setSearchParams]);

    const { data: users, isLoading, error } = useQuery({
        queryKey: ['users'],
        queryFn: userService.getUsers,
    });

    const { data: roles } = useQuery({
        queryKey: ['roles'],
        queryFn: roleService.getRoles,
    });

    const createMutation = useMutation({
        mutationFn: userService.createUser,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            setIsModalOpen(false);
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: UserUpdateData }) =>
            userService.updateUser(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            setIsModalOpen(false);
            setEditingUser(null);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: userService.deleteUser,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });

    const createRoleMutation = useMutation({
        mutationFn: roleService.createRole,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] }); // Assuming we might fetch roles somewhere
            setIsRoleModalOpen(false);
        },
    });

    const updateRoleMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: RoleUpdateData }) =>
            roleService.updateRole(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            setIsRoleModalOpen(false);
            setEditingRole(null);
        },
    });

    const handleAddUser = () => {
        setEditingUser(null);
        setIsModalOpen(true);
    };

    const handleEditUser = (user: UserWithRoles) => {
        setEditingUser(user);
        setIsModalOpen(true);
    };

    const handleDeleteUser = async (id: number) => {
        if (window.confirm('Are you sure you want to delete this user?')) {
            await deleteMutation.mutateAsync(id);
        }
    };

    if (isLoading) return <LoadingSpinner message="Loading users..." />;
    if (error) return <div className="text-red-500">Error loading users</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">User Management</h1>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        Manage users, credentials, and permissions.
                    </p>
                </div>
                <button
                    onClick={handleAddUser}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
                >
                    <i className="fas fa-plus mr-2"></i>
                    Add User
                </button>
            </div>

            {/* User List */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                User
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                Roles / Permissions
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                Status
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {users?.map((user) => (
                            <tr key={user.id}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                                            <span className="text-gray-500 dark:text-gray-300 font-medium">
                                                {user.username.charAt(0).toUpperCase()}
                                            </span>
                                        </div>
                                        <div className="ml-4">
                                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                                                {user.full_name || user.username}
                                            </div>
                                            <div className="text-sm text-gray-500 dark:text-gray-400">{user.email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex flex-wrap gap-2">
                                        {user.roles.map((role) => (
                                            <span
                                                key={role.id}
                                                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                                            >
                                                {role.display_name}
                                            </span>
                                        ))}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span
                                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.is_active
                                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                            }`}
                                    >
                                        {user.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button
                                        onClick={() => handleEditUser(user)}
                                        className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-4"
                                    >
                                        Edit
                                    </button>
                                    <button
                                        onClick={() => handleDeleteUser(user.id)}
                                        className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* User Modal */}
            {isModalOpen && (
                <UserModal
                    user={editingUser}
                    roles={roles || []}
                    onClose={() => setIsModalOpen(false)}
                    onSave={async (data) => {
                        if (editingUser) {
                            await updateMutation.mutateAsync({ id: editingUser.id, data });
                        } else {
                            await createMutation.mutateAsync(data as UserCreateData);
                        }
                    }}
                    isSaving={createMutation.isPending || updateMutation.isPending}
                />
            )}

            {/* Role Modal */}
            {isRoleModalOpen && (
                <RoleModal
                    role={editingRole}
                    onClose={() => setIsRoleModalOpen(false)}
                    onSave={async (data) => {
                        if (editingRole) {
                            await updateRoleMutation.mutateAsync({ id: editingRole.id, data });
                        } else {
                            await createRoleMutation.mutateAsync(data as RoleCreateData);
                        }
                    }}
                    isSaving={createRoleMutation.isPending || updateRoleMutation.isPending}
                />
            )}
        </div>
    );
}

interface UserModalProps {
    user: UserWithRoles | null;
    roles: Role[];
    onClose: () => void;
    onSave: (data: UserCreateData | UserUpdateData) => Promise<void>;
    isSaving: boolean;
}

function UserModal({ user, roles, onClose, onSave, isSaving }: UserModalProps) {
    const {
        register,
        handleSubmit,
        watch,
        setValue,
        formState: { errors },
    } = useForm<UserCreateData>({
        defaultValues: {
            username: user?.username || '',
            email: user?.email || '',
            full_name: user?.full_name || '',
            password: '',
            roles: user?.roles.map((r) => r.name) || [],
        },
    });

    const selectedRoles = watch('roles') || [];

    const toggleRole = (roleId: string) => {
        const currentRoles = selectedRoles;
        if (currentRoles.includes(roleId)) {
            setValue(
                'roles',
                currentRoles.filter((id) => id !== roleId)
            );
        } else {
            setValue('roles', [...currentRoles, roleId]);
        }
    };

    const onSubmit = (data: UserCreateData) => {
        onSave(data);
    };

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                    <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
                </div>

                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
                    &#8203;
                </span>

                <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
                    <form onSubmit={handleSubmit(onSubmit)}>
                        <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
                                {user ? 'Edit User' : 'Add New User'}
                            </h3>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Left Column: User Details */}
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Username
                                        </label>
                                        <input
                                            {...register('username', { required: !user })}
                                            disabled={!!user}
                                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 dark:bg-gray-700 dark:text-white sm:text-sm"
                                        />
                                        {errors.username && (
                                            <p className="text-red-500 text-xs mt-1">Username is required</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Email
                                        </label>
                                        <input
                                            {...register('email', { required: true })}
                                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 dark:bg-gray-700 dark:text-white sm:text-sm"
                                        />
                                        {errors.email && (
                                            <p className="text-red-500 text-xs mt-1">Email is required</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Full Name
                                        </label>
                                        <input
                                            {...register('full_name')}
                                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 dark:bg-gray-700 dark:text-white sm:text-sm"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Password {user && '(Leave blank to keep current)'}
                                        </label>
                                        <input
                                            type="password"
                                            {...register('password', { required: !user })}
                                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 dark:bg-gray-700 dark:text-white sm:text-sm"
                                        />
                                        {errors.password && (
                                            <p className="text-red-500 text-xs mt-1">Password is required</p>
                                        )}
                                    </div>
                                </div>

                                {/* Right Column: Permissions (Tiles) */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Roles
                                    </label>
                                    <div className="grid grid-cols-1 gap-4 max-h-96 overflow-y-auto pr-2">
                                        {roles.map((role) => {
                                            const isSelected = selectedRoles.includes(role.name);
                                            return (
                                                <div
                                                    key={role.id}
                                                    onClick={() => toggleRole(role.name)}
                                                    className={`cursor-pointer border rounded-lg p-4 flex items-start space-x-4 transition-all duration-200 ${isSelected
                                                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-500'
                                                        : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                                                        }`}
                                                >
                                                    <div
                                                        className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center ${isSelected
                                                            ? 'bg-blue-100 text-blue-600 dark:bg-blue-800 dark:text-blue-200'
                                                            : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                                                            }`}
                                                    >
                                                        <i className="fas fa-user-tag"></i>
                                                    </div>
                                                    <div className="flex-1">
                                                        <h4
                                                            className={`text-sm font-medium ${isSelected
                                                                ? 'text-blue-900 dark:text-blue-100'
                                                                : 'text-gray-900 dark:text-white'
                                                                }`}
                                                        >
                                                            {role.display_name}
                                                        </h4>
                                                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                                            {role.description}
                                                        </p>
                                                    </div>
                                                    <div className="flex-shrink-0">
                                                        {isSelected ? (
                                                            <i className="fas fa-check-circle text-blue-600 text-lg"></i>
                                                        ) : (
                                                            <i className="far fa-circle text-gray-400 text-lg"></i>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                        {roles.length === 0 && (
                                            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                                                No roles available. Please create roles first.
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                            <button
                                type="submit"
                                disabled={isSaving}
                                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                            >
                                {isSaving ? 'Saving...' : 'Save'}
                            </button>
                            <button
                                type="button"
                                onClick={onClose}
                                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

interface RoleModalProps {
    role: Role | null;
    onClose: () => void;
    onSave: (data: RoleCreateData | RoleUpdateData) => Promise<void>;
    isSaving: boolean;
}

function RoleModal({ role, onClose, onSave, isSaving }: RoleModalProps) {
    const {
        register,
        handleSubmit,
        watch,
        setValue,
        formState: { errors },
    } = useForm<RoleCreateData>({
        defaultValues: {
            name: role?.name || '',
            display_name: role?.display_name || '',
            description: role?.description || '',
            can_view_dashboard: role?.can_view_dashboard ?? true,
            can_view_alerts: role?.can_view_alerts ?? true,
            can_approve_remediation: role?.can_approve_remediation ?? false,
            can_execute_remediation: role?.can_execute_remediation ?? false,
            can_manage_users: role?.can_manage_users ?? false,
            can_manage_roles: role?.can_manage_roles ?? false,
            can_view_access_analyzer: role?.can_view_access_analyzer ?? true,
            can_view_pod_analyzer: role?.can_view_pod_analyzer ?? true,
            can_view_cost_analyzer: role?.can_view_cost_analyzer ?? true,
            can_use_chatbot: role?.can_use_chatbot ?? true,
        },
    });

    const onSubmit = (data: RoleCreateData) => {
        onSave(data);
    };

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                    <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
                </div>

                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
                    &#8203;
                </span>

                <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
                    <form onSubmit={handleSubmit(onSubmit)}>
                        <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
                                {role ? 'Edit Role' : 'Create New Role'}
                            </h3>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Left Column: Role Details */}
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Role Name (Internal ID)
                                        </label>
                                        <input
                                            {...register('name', { required: !role })}
                                            disabled={!!role}
                                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 dark:bg-gray-700 dark:text-white sm:text-sm"
                                            placeholder="e.g., custom_admin"
                                        />
                                        {errors.name && (
                                            <p className="text-red-500 text-xs mt-1">Role Name is required</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Display Name
                                        </label>
                                        <input
                                            {...register('display_name', { required: true })}
                                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 dark:bg-gray-700 dark:text-white sm:text-sm"
                                            placeholder="e.g., Custom Administrator"
                                        />
                                        {errors.display_name && (
                                            <p className="text-red-500 text-xs mt-1">Display Name is required</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Description
                                        </label>
                                        <textarea
                                            {...register('description')}
                                            rows={3}
                                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 dark:bg-gray-700 dark:text-white sm:text-sm"
                                        />
                                    </div>
                                </div>

                                {/* Right Column: Permissions */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Permissions
                                    </label>
                                    <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
                                        {PERMISSION_TILES.map((tile) => {
                                            // Map tile ID to permission field
                                            let permissionField: keyof RoleCreateData | null = null;
                                            switch (tile.id) {
                                                case 'cloud_admin': permissionField = 'can_view_cost_analyzer'; break; // Approximate mapping
                                                case 'app_admin': permissionField = 'can_view_pod_analyzer'; break;
                                                case 'security_admin': permissionField = 'can_view_access_analyzer'; break;
                                                case 'sys_admin': permissionField = 'can_manage_users'; break;
                                                default: break;
                                            }

                                            // Manual mapping for granular permissions
                                            const granularPermissions = [
                                                { key: 'can_view_dashboard', label: 'View Dashboard' },
                                                { key: 'can_view_alerts', label: 'View Alerts' },
                                                { key: 'can_approve_remediation', label: 'Approve Remediation' },
                                                { key: 'can_execute_remediation', label: 'Execute Remediation' },
                                                { key: 'can_manage_users', label: 'Manage Users' },
                                                { key: 'can_manage_roles', label: 'Manage Roles' },
                                                { key: 'can_view_access_analyzer', label: 'Access Analyzer' },
                                                { key: 'can_view_pod_analyzer', label: 'Pod Health' },
                                                { key: 'can_view_cost_analyzer', label: 'Cost Analysis' },
                                                { key: 'can_use_chatbot', label: 'Use Chatbot' },
                                            ];

                                            return null; // Using granular list below instead
                                        })}

                                        {[
                                            { key: 'can_view_dashboard', label: 'View Dashboard' },
                                            { key: 'can_view_alerts', label: 'View Alerts' },
                                            { key: 'can_approve_remediation', label: 'Approve Remediation' },
                                            { key: 'can_execute_remediation', label: 'Execute Remediation' },
                                            { key: 'can_manage_users', label: 'Manage Users' },
                                            { key: 'can_manage_roles', label: 'Manage Roles' },
                                            { key: 'can_view_access_analyzer', label: 'Access Analyzer' },
                                            { key: 'can_view_pod_analyzer', label: 'Pod Health' },
                                            { key: 'can_view_cost_analyzer', label: 'Cost Analysis' },
                                            { key: 'can_use_chatbot', label: 'Use Chatbot' },
                                        ].map((perm) => (
                                            <div key={perm.key} className="flex items-center">
                                                <input
                                                    type="checkbox"
                                                    {...register(perm.key as keyof RoleCreateData)}
                                                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                                />
                                                <label className="ml-2 block text-sm text-gray-900 dark:text-gray-300">
                                                    {perm.label}
                                                </label>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                            <button
                                type="submit"
                                disabled={isSaving}
                                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                            >
                                {isSaving ? 'Saving...' : 'Save'}
                            </button>
                            <button
                                type="button"
                                onClick={onClose}
                                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
