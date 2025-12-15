import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface KPI {
    id: string;
    name: string;
    description: string;
    category: 'customer' | 'revenue' | 'operational';
}

const kpis: KPI[] = [
    // Customer Experience KPIs
    {
        id: 'avg-resolution-time',
        name: 'Average Resolution Time',
        description: 'Speed of resolving customer issues.',
        category: 'customer',
    },
    {
        id: 'first-contact-resolution',
        name: 'First Contact Resolution Rate',
        description: '% of issues solved in first interaction.',
        category: 'customer',
    },
    {
        id: 'nps',
        name: 'Net Promoter Score (NPS)',
        description: 'Customer loyalty and satisfaction.',
        category: 'customer',
    },
    {
        id: 'complaint-rate',
        name: 'Complaint Rate',
        description: 'Ratio of complaints per 1,000 subscribers.',
        category: 'customer',
    },
    // Revenue & Billing KPIs
    {
        id: 'billing-accuracy',
        name: 'Billing Accuracy',
        description: '% of invoices without errors.',
        category: 'revenue',
    },
    {
        id: 'revenue-leakage',
        name: 'Revenue Assurance Leakage',
        description: '% of revenue lost due to system/process gaps.',
        category: 'revenue',
    },
    {
        id: 'collection-efficiency',
        name: 'Collection Efficiency',
        description: 'Ratio of billed vs. collected revenue.',
        category: 'revenue',
    },
    // Operational Efficiency KPIs
    {
        id: 'order-fulfillment',
        name: 'Order Fulfillment Cycle Time',
        description: 'Average time to activate a service.',
        category: 'operational',
    },
    {
        id: 'system-availability',
        name: 'System Availability',
        description: '% uptime of BSS platforms.',
        category: 'operational',
    },
    {
        id: 'api-compliance',
        name: 'API Compliance',
        description: '% of TM Forum Open APIs successfully integrated.',
        category: 'operational',
    },
];

export function BusinessOpsPage() {
    const navigate = useNavigate();
    const { logout, user } = useAuth();
    const [selectedKPI, setSelectedKPI] = useState<KPI | null>(null);

    const handleBackToLayers = () => {
        navigate('/layers');
    };

    const handleKPIClick = (kpi: KPI) => {
        setSelectedKPI(kpi);
    };

    const closeDashboard = () => {
        setSelectedKPI(null);
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <div className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="text-center flex-1">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                            Business Ops Dashboard
                        </h1>
                        <p className="mt-2 text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                            Monitor key performance indicators across customer experience, revenue, and operations.
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

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Customer Experience KPIs */}
                    <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-blue-600 dark:text-blue-400">
                                <i className="fas fa-users text-xl"></i>
                            </div>
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Customer Experience</h2>
                        </div>
                        <div className="space-y-4">
                            {kpis.filter(k => k.category === 'customer').map(kpi => (
                                <button
                                    key={kpi.id}
                                    onClick={() => handleKPIClick(kpi)}
                                    className="w-full text-left p-4 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-all duration-200 group"
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                                                {kpi.name}
                                            </h3>
                                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                                {kpi.description}
                                            </p>
                                        </div>
                                        <i className="fas fa-chart-line text-gray-400 group-hover:text-blue-500 mt-1"></i>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </section>

                    {/* Revenue & Billing KPIs */}
                    <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg text-green-600 dark:text-green-400">
                                <i className="fas fa-file-invoice-dollar text-xl"></i>
                            </div>
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Revenue & Billing</h2>
                        </div>
                        <div className="space-y-4">
                            {kpis.filter(k => k.category === 'revenue').map(kpi => (
                                <button
                                    key={kpi.id}
                                    onClick={() => handleKPIClick(kpi)}
                                    className="w-full text-left p-4 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-green-300 dark:hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-900/10 transition-all duration-200 group"
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="font-medium text-gray-900 dark:text-white group-hover:text-green-600 dark:group-hover:text-green-400">
                                                {kpi.name}
                                            </h3>
                                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                                {kpi.description}
                                            </p>
                                        </div>
                                        <i className="fas fa-chart-pie text-gray-400 group-hover:text-green-500 mt-1"></i>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </section>

                    {/* Operational Efficiency KPIs */}
                    <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">
                                <i className="fas fa-cogs text-xl"></i>
                            </div>
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Operational Efficiency</h2>
                        </div>
                        <div className="space-y-4">
                            {kpis.filter(k => k.category === 'operational').map(kpi => (
                                <button
                                    key={kpi.id}
                                    onClick={() => handleKPIClick(kpi)}
                                    className="w-full text-left p-4 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/10 transition-all duration-200 group"
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="font-medium text-gray-900 dark:text-white group-hover:text-purple-600 dark:group-hover:text-purple-400">
                                                {kpi.name}
                                            </h3>
                                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                                {kpi.description}
                                            </p>
                                        </div>
                                        <i className="fas fa-stopwatch text-gray-400 group-hover:text-purple-500 mt-1"></i>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </section>
                </div>

                {/* Grafana Dashboard Modal */}
                {selectedKPI && (
                    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                        <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={closeDashboard}></div>

                            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
                                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                    <div className="flex justify-between items-center mb-4">
                                        <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                                            {selectedKPI.name} - Analytics
                                        </h3>
                                        <button
                                            onClick={closeDashboard}
                                            className="bg-white dark:bg-gray-800 rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                        >
                                            <span className="sr-only">Close</span>
                                            <i className="fas fa-times text-xl"></i>
                                        </button>
                                    </div>
                                    <div className="w-full h-[600px] bg-gray-100 dark:bg-gray-900 rounded-lg flex items-center justify-center border border-gray-200 dark:border-gray-700 relative overflow-hidden">
                                        {/* Placeholder for Grafana Dashboard */}
                                        <div className="text-center">
                                            <div className="mb-4">
                                                <i className="fas fa-chart-area text-6xl text-gray-300 dark:text-gray-600"></i>
                                            </div>
                                            <h4 className="text-xl font-semibold text-gray-700 dark:text-gray-300">Grafana Dashboard</h4>
                                            <p className="text-gray-500 dark:text-gray-400 mt-2">
                                                Visualizing metrics for {selectedKPI.name}
                                            </p>
                                            <div className="mt-6 animate-pulse flex justify-center">
                                                <div className="h-2 w-24 bg-blue-400 rounded"></div>
                                            </div>
                                        </div>

                                        {/* Simulated Iframe Overlay (Optional for realism) */}
                                        <div className="absolute inset-0 bg-gradient-to-br from-transparent to-gray-50/10 pointer-events-none"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
