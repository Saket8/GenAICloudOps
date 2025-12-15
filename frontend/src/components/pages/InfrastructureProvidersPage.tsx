import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { AwsLogo } from '../ui/icons/AwsLogo';
import { AzureLogo } from '../ui/icons/AzureLogo';
import { OciLogo } from '../ui/icons/OciLogo';
import { GcpLogo } from '../ui/icons/GcpLogo';

interface Provider {
    id: string;
    name: string;
    fullName: string;
    subtitle: string;
    logo: (props: { className?: string; title?: string }) => JSX.Element;
    badge: string;
    badgeColor: string;
    route: string;
    disabled?: boolean;
}

const providers: Provider[] = [
    {
        id: 'aws',
        name: 'AWS',
        fullName: 'Amazon Web Services',
        subtitle: 'Infrastructure Dashboard',
        logo: AwsLogo,
        badge: 'AWS',
        badgeColor: 'bg-orange-500',
        route: '/aws/dashboard',
        disabled: false,
    },
    {
        id: 'azure',
        name: 'Azure',
        fullName: 'Microsoft Azure',
        subtitle: 'Infrastructure Dashboard',
        logo: AzureLogo,
        badge: 'Azure',
        badgeColor: 'bg-blue-500',
        route: '/azure/dashboard',
        disabled: true,
    },
    {
        id: 'oci',
        name: 'OCI',
        fullName: 'Oracle Cloud',
        subtitle: 'Infrastructure Dashboard',
        logo: OciLogo,
        badge: 'OCI',
        badgeColor: 'bg-red-500',
        route: '/dashboard',
        disabled: false,
    },
    {
        id: 'gcp',
        name: 'GCP',
        fullName: 'Google Cloud',
        subtitle: 'Infrastructure Dashboard',
        logo: GcpLogo,
        badge: 'GCP',
        badgeColor: 'bg-green-500',
        route: '/gcp/dashboard',
        disabled: true,
    },
];

export function InfrastructureProvidersPage() {
    const navigate = useNavigate();
    const { logout, user } = useAuth();

    const handleProviderClick = (provider: Provider) => {
        if (!provider.disabled) {
            navigate(provider.route);
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
                            Select a cloud provider to view infrastructure dashboards and services
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

                {/* Infrastructure Section */}
                <section className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
                    <div className="p-6 lg:p-8">
                        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6 mb-6">
                            <div>
                                <div className="flex items-center space-x-3">
                                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Infrastructure Providers</h2>
                                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-200">
                                        Multi-cloud
                                    </span>
                                </div>
                                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-xl">
                                    Select the cloud provider you want to explore. Continue to open the tailored operational dashboard for that environment.
                                </p>
                            </div>
                            <div className="flex items-center space-x-2 text-xs text-gray-500 uppercase tracking-wide">
                                <i className="fas fa-server"></i>
                                <span>Infrastructure Layer</span>
                            </div>
                        </div>

                        {/* Providers Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {providers.map((provider) => {
                                const Logo = provider.logo;
                                return (
                                    <button
                                        key={provider.id}
                                        onClick={() => handleProviderClick(provider)}
                                        disabled={provider.disabled}
                                        className={`group relative rounded-lg border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${provider.disabled
                                                ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 cursor-not-allowed opacity-60'
                                                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md'
                                            }`}
                                    >
                                        <div className="p-6 flex flex-col items-center justify-center text-center min-h-[200px] space-y-3">
                                            {/* Logo */}
                                            <div className="w-16 h-16 flex items-center justify-center">
                                                <Logo className="w-full h-full" />
                                            </div>

                                            {/* Badge */}
                                            <div className={`${provider.badgeColor} text-white text-xs font-semibold px-3 py-1 rounded-md`}>
                                                {provider.badge}
                                            </div>

                                            {/* Provider Name */}
                                            <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                                                {provider.fullName}
                                            </h3>

                                            {/* Subtitle */}
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                {provider.subtitle}
                                            </p>

                                            {/* Coming Soon Label */}
                                            {provider.disabled && (
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
