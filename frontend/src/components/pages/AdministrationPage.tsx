import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface AdminTile {
    id: string;
    name: string;
    subtitle: string;
    route: string;
    icon: string;
}

const adminTiles: AdminTile[] = [
    {
        id: 'user-management',
        name: 'User Management',
        subtitle: 'Manage users and roles',
        route: '/user-management',
        icon: 'fas fa-users-cog',
    },
    {
        id: 'settings',
        name: 'Settings',
        subtitle: 'System configuration',
        route: '/settings',
        icon: 'fas fa-cogs',
    },
    {
        id: 'create-user',
        name: 'Create User',
        subtitle: 'Add a new user profile',
        route: '/user-management?action=create',
        icon: 'fas fa-user-plus',
    },
    {
        id: 'create-role',
        name: 'Create Role',
        subtitle: 'Define a new custom role',
        route: '/user-management?action=create-role',
        icon: 'fas fa-user-shield',
    },
];

export function AdministrationPage() {
    const navigate = useNavigate();
    const { user } = useAuth();

    const handleTileClick = (route: string) => {
        navigate(route);
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <div className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-12">
                    <div className="text-center flex-1">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                            Administration
                        </h1>
                        <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                            Manage system settings and user access
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/layers')}
                            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                        >
                            <i className="fas fa-arrow-left mr-2"></i>
                            Back to Layers
                        </button>
                    </div>
                </div>

                {/* Administration Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                    {adminTiles.map((tile) => (
                        <button
                            key={tile.id}
                            onClick={() => handleTileClick(tile.route)}
                            className="group relative rounded-xl border border-blue-500 bg-blue-600 shadow-sm hover:shadow-md transition-all duration-200 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        >
                            <div className="p-8 flex flex-col items-center justify-center text-center min-h-[200px]">
                                <div className="mb-4 w-16 h-16 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white/30 transition-colors duration-200">
                                    <i className={`${tile.icon} text-3xl text-white`}></i>
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2">
                                    {tile.name}
                                </h2>
                                <p className="text-sm text-blue-100">
                                    {tile.subtitle}
                                </p>
                            </div>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
