import React, { useMemo } from 'react';

interface ChangeDeltaCardProps {
    title: string;
    stats: {
        total: number;
        active: number;
        errors: number;
        stoppedOkeNodes?: number;
        stoppedOther?: number;
    };
    topRecommendation?: {
        description: string;
        estimated_savings: number;
        optimization_type: string;
    } | null;
    criticalFindings?: number;
    loading?: boolean;
}

export const ChangeDeltaCard: React.FC<ChangeDeltaCardProps> = ({
    title,
    stats,
    topRecommendation,
    criticalFindings = 0,
    loading = false
}) => {
    // Generate operational insights based on current state
    const insights = useMemo(() => {
        const items: { icon: string; text: string; severity: 'info' | 'warning' | 'success' | 'error'; link?: string }[] = [];

        // Resource summary
        if (stats.total > 0) {
            items.push({
                icon: 'fa-server',
                text: `${stats.active}/${stats.total} resources operational`,
                severity: stats.active === stats.total ? 'success' : 'info',
                link: '/cloud-resources'
            });
        }

        // Stopped resources context
        if ((stats.stoppedOkeNodes ?? 0) > 0 && (stats.stoppedOther ?? 0) === 0) {
            items.push({
                icon: 'fa-cubes',
                text: `${stats.stoppedOkeNodes} OKE worker nodes scaled down (expected)`,
                severity: 'info',
                link: '/cloud-resources'
            });
        } else if ((stats.stoppedOther ?? 0) > 0) {
            items.push({
                icon: 'fa-exclamation-triangle',
                text: `${stats.stoppedOther} resource${stats.stoppedOther === 1 ? '' : 's'} stopped - review recommended`,
                severity: 'warning',
                link: '/cloud-resources'
            });
        }

        // Cost optimization
        if (topRecommendation) {
            items.push({
                icon: 'fa-coins',
                text: `Cost action: ${topRecommendation.description?.slice(0, 50)}...`,
                severity: 'info',
                link: '/cost-analysis'
            });
        }

        // Security findings
        if (criticalFindings > 0) {
            items.push({
                icon: 'fa-shield-alt',
                text: `${criticalFindings} critical security finding${criticalFindings === 1 ? '' : 's'} detected`,
                severity: 'error',
                link: '/alerts'
            });
        } else {
            items.push({
                icon: 'fa-check-circle',
                text: 'No critical security findings',
                severity: 'success',
                link: '/alerts'
            });
        }

        return items;
    }, [stats, topRecommendation, criticalFindings]);

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'success': return 'text-emerald-500';
            case 'warning': return 'text-amber-500';
            case 'error': return 'text-red-500';
            default: return 'text-blue-500';
        }
    };

    const getSeverityBg = (severity: string) => {
        switch (severity) {
            case 'success': return 'bg-emerald-500/10';
            case 'warning': return 'bg-amber-500/10';
            case 'error': return 'bg-red-500/10';
            default: return 'bg-blue-500/10';
        }
    };

    if (loading) {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500/20 to-indigo-500/20 rounded-xl flex items-center justify-center">
                        <i className="fas fa-lightbulb text-purple-500"></i>
                    </div>
                    <div>
                        <h4 className="font-bold text-gray-800 dark:text-white">{title}</h4>
                        <p className="text-xs text-gray-500">AI-Powered Analysis</p>
                    </div>
                </div>
                <div className="animate-pulse space-y-3">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-10 bg-gray-100 dark:bg-gray-700 rounded-lg"></div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 relative overflow-hidden">
            {/* Background gradient */}
            <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-bl from-purple-500/10 to-transparent rounded-full blur-2xl"></div>

            {/* Header */}
            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20">
                        <i className="fas fa-lightbulb text-white"></i>
                    </div>
                    <div>
                        <h4 className="font-bold text-gray-800 dark:text-white">{title}</h4>
                        <p className="text-xs text-gray-500">AI-Powered Analysis</p>
                    </div>
                </div>
                <span className="text-xs text-gray-400">
                    <i className="fas fa-clock mr-1"></i>
                    Live
                </span>
            </div>

            {/* Insights List */}
            <div className="space-y-3 relative z-10">
                {insights.map((insight, index) => (
                    <a
                        key={index}
                        href={insight.link || '#'}
                        className={`flex items-center gap-3 p-3 rounded-xl ${getSeverityBg(insight.severity)} transition-all hover:scale-[1.02] cursor-pointer group`}
                    >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${getSeverityBg(insight.severity)}`}>
                            <i className={`fas ${insight.icon} ${getSeverityColor(insight.severity)}`}></i>
                        </div>
                        <span className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                            {insight.text}
                        </span>
                        <i className={`fas fa-chevron-right text-xs ${getSeverityColor(insight.severity)} opacity-0 group-hover:opacity-100 transition-opacity`}></i>
                    </a>
                ))}
            </div>

            {/* Timestamp */}
            <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-400 text-center">
                <i className="fas fa-sync-alt mr-1"></i>
                Updated just now • Auto-refreshes every 5 min
            </div>
        </div>
    );
};

export default ChangeDeltaCard;
