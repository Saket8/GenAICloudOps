import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { OracleBrmLogo } from '../ui/icons/OracleBrmLogo';
import { SingleviewLogo } from '../ui/icons/SingleviewLogo';
import { EricssonBillingLogo } from '../ui/icons/EricssonBillingLogo';
import { AmdoxLogo } from '../ui/icons/AmdoxLogo';

interface ApplicationOption {
    id: string;
    name: string;
    description: string;
    logo: (props: { className?: string; title?: string }) => JSX.Element;
    status: string;
    route: string;
    disabled?: boolean;
    badgeColor: string;
}

const applications: ApplicationOption[] = [
    {
        id: 'oracle_brm',
        name: 'Oracle BRM',
        description: 'Deep monitoring for Oracle Billing and Revenue Management workloads.',
        logo: OracleBrmLogo,
        status: 'Available',
        route: '/operational-insights',
        disabled: false,
        badgeColor: 'bg-purple-500',
    },
    {
        id: 'singleview',
        name: 'Singleview',
        description: 'Singleview operational telemetry coming soon.',
        logo: SingleviewLogo,
        status: 'Coming Soon',
        route: '',
        disabled: true,
        badgeColor: 'bg-gray-500',
    },
    {
        id: 'ericsson_billing',
        name: 'Ericsson Billing',
        description: 'Ericsson billing dashboards available in upcoming release.',
        logo: EricssonBillingLogo,
        status: 'Coming Soon',
        route: '',
        disabled: true,
        badgeColor: 'bg-gray-500',
    },
    {
        id: 'amdox',
        name: 'Amdox',
        description: 'Amdox application monitoring planned for future.',
        logo: AmdoxLogo,
        status: 'Coming Soon',
        route: '',
        disabled: true,
        badgeColor: 'bg-gray-500',
    },
];

export function ApplicationProvidersPage() {
    const navigate = useNavigate();
    const { logout, user } = useAuth();

    const handleApplicationClick = (app: ApplicationOption) => {
        if (!app.disabled && app.route) {
            navigate(app.route);
        }
    };

    const handleBackToLayers = () => {
        navigate('/layers');
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <div className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="text-center flex-1">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                            OBRM Cloud Command Centre
                        </h1>
                        <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                            Select an application to view operational insights and monitoring dashboards
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.username}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
                        </div>
                        <button
                            onClick={async () => {
                                try {
                                    await logout();
                                    navigate('/login');
                                } catch (error) {
                                    console.error('Logout error:', error);
                                }
                            }}
                            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                        >
                            <i className="fas fa-sign-out-alt mr-2"></i>
                            Sign Out
                        </button>
                    </div>
                </div>

                {/* Back to Layers */}
                <button
                    onClick={handleBackToLayers}
                    className="inline-flex items-center text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors mb-6 focus:outline-none"
                >
                    <i className="fas fa-arrow-left mr-2"></i>
                    Back to Layers
                </button>

                {/* Applications Section */}
                <section className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
                    <div className="p-6 lg:p-8">
                        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6 mb-6">
                            <div>
                                <div className="flex items-center space-x-3">
                                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Application Monitoring</h2>
                                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-200">
                                        Operations
                                    </span>
                                </div>
                                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-xl">
                                    Choose an application workload to explore monitoring dashboards. Continue to view aggregated alerts, health, and performance insights.
                                </p>
                            </div>
                            <div className="flex items-center space-x-2 text-xs text-gray-500 uppercase tracking-wide">
                                <i className="fas fa-desktop"></i>
                                <span>Application Layer</span>
                            </div>
                        </div>

                        {/* Applications Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {applications.map((app) => {
                                const Logo = app.logo;
                                return (
                                    <button
                                        key={app.id}
                                        onClick={() => handleApplicationClick(app)}
                                        disabled={app.disabled}
                                        className={`group relative rounded-lg border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ${app.disabled
                                            ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 cursor-not-allowed opacity-60'
                                            : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-purple-400 dark:hover:border-purple-500 hover:shadow-md'
                                            }`}
                                    >
                                        <div className="p-6 flex flex-col items-center justify-center text-center min-h-[200px] space-y-3">
                                            {/* Logo */}
                                            <div className="w-16 h-16 flex items-center justify-center">
                                                <Logo className="w-full h-full" />
                                            </div>

                                            {/* Badge */}
                                            {app.status === 'Available' && (
                                                <div className={`${app.badgeColor} text-white text-xs font-semibold px-3 py-1 rounded-md`}>
                                                    {app.status}
                                                </div>
                                            )}

                                            {/* App Name */}
                                            <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                                                {app.name}
                                            </h3>

                                            {/* Description */}
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                {app.description}
                                            </p>

                                            {/* Coming Soon Label */}
                                            {app.disabled && (
                                                <div className="mt-2">
                                                    <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200">
                                                        Coming Soon
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
